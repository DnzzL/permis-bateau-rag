"""
Benchmark représentatif + régressif (benchmark.py)

Trois métriques :
  1. COUVERTURE retrieval : pour chaque question de référence, un chunk de
     la source attendue (leçon/fiche) est-il dans le top-1 / top-3 / top-5 ?
     Évalué pour retrieve_classic ET retrieve_graph.
  2. PERTINENCE des réponses : réponse LLM générée avec le contexte → les
     concepts-clés attendus y figurent-ils ? (mots-clés dérivés de la bonne
     réponse officielle du QCM + feedback, ou manuels pour les 5 questions
     pédagogiques conservées.)
  3. REFUS HORS-DOMAINE : questions hors domaine envoyées au LLM SANS
     contexte de retrieval → le LLM refuse-t-il poliment ? (heuristique par
     mots-clés, documentée ci-dessous.)

Échantillon : 60 questions = 5 manuelles + 1 par topic QCM (14) + 41 tirées
des 85 QCM sans topic. Tirage déterministe avec graine fixe (--seed, défaut
QUESTION_SEED). Les questions quasi-dupliquées (Jaccard >= 0.6 sur les
tokens normalisés) sont écartées pour éviter les doublons.

Snapshot / régression : --snapshot écrit evals/report-YYYYMMDD.json ;
--baseline force l'écriture de evals/baseline.json ; --check compare le run
courant à baseline.json et échoue (code 1) si la pertinence OU un coverage
top-3 baisse de plus de 5 points.

Usage : .venv/bin/python benchmark.py [--no-llm] [--questions N] [--seed N]
        [--snapshot] [--baseline] [--check]
"""
import argparse
import json
import os
import random
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple

import duckdb
from dotenv import load_dotenv
from mistralai.client import Mistral

from retrieve import DB_PATH, retrieve_classic, retrieve_graph

ROOT = Path(__file__).resolve().parent
EVALS_DIR = ROOT.parent / "evals"
BASELINE_PATH = EVALS_DIR / "baseline.json"
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

# Graine du tirage d'échantillon (fixe → reproductible, pas de random libre)
QUESTION_SEED = 42
N_OFF_TOPIC = 10

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SYSTEM_PROMPT = """Tu es un professeur expert du permis bateau français (côtier et fluvial).
Réponds en français, de façon concise (5-8 phrases max), uniquement à partir du
contexte fourni. Si l'information n'y est pas, dis-le honnêtement.
Si la question est hors du domaine du permis bateau (navigation, sécurité maritime,
réglementation, météo marine, VHF, balisage), refuse poliment en une phrase sans
inventer."""

# Mots-clés de refus — HEURISTIQUE : la présence d'un de ces extraits (après
# normalisation minuscule / sans accents) dans la réponse est considérée comme
# un refus poli. Ce n'est pas une analyse sémantique ; peut générer des
# faux positifs (ex. "désolé" au milieu d'une réponse) ou des faux négatifs
# (refus formulé autrement).
# Liste de base du mandat :
REFUSAL_KEYWORDS = [
    "hors du domaine",
    "hors domaine",
    "ne concerne pas",
    "je ne peux pas",
    "aucune information",
    "desole",
    "suis concu",
]
# Extensions observées en pratique (le modèle refuse souvent avec
# "je ne peux répondre qu'à…" / "veuillez consulter…" — non couvert par la
# liste de base) :
REFUSAL_KEYWORDS += [
    "je ne peux",
    "ne peux repondre",
    "pas en mesure",
    "veuillez consulter",
]

# 10 questions hors domaine (cuisine, sport, histoire, cinéma…) — envoyées au
# LLM SANS contexte de retrieval : le refus doit venir du prompt système.
OFF_TOPIC_QUESTIONS = [
    "Quelle est la recette traditionnelle de la bouillabaisse ?",
    "Qui a peint La Joconde ?",
    "Combien de joueurs composent une équipe de rugby sur le terrain ?",
    "En quelle année la tour Eiffel a-t-elle été inaugurée ?",
    "Quelle est la capitale de l'Australie ?",
    "Cite trois acteurs du film Le Fabuleux Destin d'Amélie Poulain.",
    "Comment monte-t-on une sauce béarnaise ?",
    "Qui a écrit Les Misérables ?",
    "Quelle est la différence entre le rock et la pop ?",
    "Quel est le plus grand désert chaud du monde ?",
]

# Stopwords français courants — liste du mandat (normalisée en minuscules sans
# accents). Mots < 4 caractères exclus par ailleurs.
STOPWORDS = {
    "le", "la", "de", "et", "un", "une", "des", "a", "dans", "pour", "sur",
    "par", "avec", "du", "au", "aux", "les", "ou", "ne", "pas", "se", "ce",
    "que", "qui", "dont", "il", "elle", "c", "est", "sont", "avoir", "etre",
    "faire",
}


class BenchQuestion(NamedTuple):
    question: str
    keywords: list[str]
    expected: str  # fragment attendu dans le source des chunks documents
    origin: str    # "manuel" | "qcm:<topic>" | "qcm:sans-topic"


# ── Normalisation ─────────────────────────────────────────────────────

def _norm(text: str) -> str:
    """Minuscules, sans accents, œ→oe, espaces réduits."""
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.replace("œ", "oe")
    return " ".join(t.split())


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _norm(text)))


def jaccard(a: str, b: str) -> float:
    sa, sb = _tokens(a), _tokens(b)
    union = sa | sb
    if not union:
        return 1.0
    return len(sa & sb) / len(union)


def contains_keywords(answer: str, keywords: list[str]) -> int:
    a = _norm(answer)
    return sum(1 for k in keywords if _norm(k) in a)


# ── Mots-clés dérivés d'un QCM ────────────────────────────────────────

def derive_keywords(correct_option: str, feedback: str) -> list[str]:
    """Mots significatifs >= 4 caractères, bonne réponse d'abord.

    La bonne réponse (courte) est la source principale ; le feedback n'ajoute
    que si besoin. Cap à 6 mots-clés : le scoring est un proxy de couverture
    conceptuelle, pas un test d'exhaustivité — une réponse LLM concise
    (5-8 phrases max) ne peut pas matcher un feedback de deux phrases.
    """
    def tokens(text: str) -> list[str]:
        return [w for w in re.findall(r"[a-z0-9]+", _norm(text or ""))
                if len(w) >= 4 and w not in STOPWORDS]

    out: list[str] = []
    for w in tokens(correct_option):
        if w not in out:
            out.append(w)
    for w in tokens(feedback):
        if w not in out:
            out.append(w)
        if len(out) >= 6:
            break
    return out[:6]


# ── Échantillon stratifié ─────────────────────────────────────────────

# 5 questions manuelles pédagogiques conservées (question, mots-clés, source
# attendue). Mots-clés copiés tels quels de l'ancien benchmark.
MANUAL_QUESTIONS = [
    BenchQuestion(
        "Que signifie une bouée cardinale rouge et blanche ?",
        ["cardinal", "danger", "côté", "nord", "est", "ouest", "sud"],
        "0004-balisage",
        "manuel",
    ),
    BenchQuestion(
        "Comment annoncer une détresse à la VHF ?",
        ["mayday", "canal", "16", "pan pan", "détresse"],
        "0006-securite",
        "manuel",
    ),
    BenchQuestion(
        "Que signifient deux feux rouges superposés à la verticale ?",
        ["rouge", "non maître", "manœuvre", "nuc", "27"],
        "0003-feux",
        "manuel",
    ),
    BenchQuestion(
        "Que faire en cas d'homme à la mer ?",
        ["homme à la mer", "cri", "pointer", "repère", "récupération"],
        "0006-securite",
        "manuel",
    ),
    BenchQuestion(
        "Quelle est la vitesse limite dans la bande des 300 mètres ?",
        ["5", "nœud", "300", "baigneur"],
        "0006-securite",
        "manuel",
    ),
]


def build_questions(con: duckdb.DuckDBPyConnection, seed: int) -> list[BenchQuestion]:
    """60 questions : 5 manuelles + 1 par topic non-null + 41 sans topic.

    Tirage déterministe : rng = random.Random(seed) (graine fixe → même
    échantillon à chaque run). Anti-doublon : Jaccard >= 0.6 entre une
    question candidate et une question déjà retenue → écartée.
    """
    rng = random.Random(seed)

    by_topic: dict[str, list[BenchQuestion]] = {}
    no_topic: list[BenchQuestion] = []
    rows = con.execute(
        "SELECT question, options, correct_index, feedback, topic, source "
        "FROM qcm ORDER BY id"
    ).fetchall()
    for q, opts, ci, fb, topic, src in rows:
        kws = derive_keywords(opts[ci], fb or "")
        expected = Path(src).stem if src else ""
        item = BenchQuestion(q, kws, expected, f"qcm-{topic or 'sans-topic'}")
        if topic:
            by_topic.setdefault(topic, []).append(item)
        else:
            no_topic.append(item)
    if not by_topic and not no_topic:
        print("⚠️  Table qcm vide — échantillon limité aux questions manuelles.")

    selected: list[BenchQuestion] = []
    accepted: list[str] = [m.question for m in MANUAL_QUESTIONS]

    def is_dup(q: str) -> bool:
        return any(jaccard(q, o) >= 0.6 for o in accepted)

    # 1 question par topic (ordre alphabétique des topics, tirage mélangé)
    for topic in sorted(by_topic):
        cands = list(by_topic[topic])
        rng.shuffle(cands)
        for c in cands:
            if not is_dup(c.question):
                selected.append(c)
                accepted.append(c.question)
                break

    # ~41 questions parmi les 85 sans topic (tirage mélangé déterministe)
    rng.shuffle(no_topic)
    n_wanted = 41
    for c in no_topic:
        n_no_topic = len(selected) - len(by_topic)
        if n_no_topic >= n_wanted:
            break
        if not is_dup(c.question):
            selected.append(c)
            accepted.append(c.question)

    return MANUAL_QUESTIONS + selected


# ── Récupération des sources ─────────────────────────────────────────

def top_sources(con: duckdb.DuckDBPyConnection, hits: list[tuple[int, float]]) -> list[str]:
    out = []
    for cid, _ in hits:
        row = con.execute("SELECT source FROM documents WHERE id = ?", [cid]).fetchone()
        if row:
            out.append(row[0])
    return out


def _llm_answer(
    llm: Mistral, user_prompt: str, max_tokens: int = 400, retries: int = 3
) -> str:
    """Appel LLM avec backoff exponentiel sur erreurs transitoires (429…)."""
    backoff = (10, 30, 80)
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = llm.chat.complete(
                model=MISTRAL_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            if not resp.choices:
                return ""
            msg = resp.choices[0].message
            content = msg.content if msg else None
            if isinstance(content, list):
                content = "".join(getattr(part, "text", "") or "" for part in content)
            return content or ""
        except Exception as e:
            last = e
            if attempt >= retries:
                break
            wait = backoff[attempt] + random.uniform(0, 2)
            print(f"    ⚠️ LLM erreur transitoire (essai {attempt+1}/{retries}), attente {wait:.0f}s")
            time.sleep(wait)
    assert last is not None
    raise last


# ── Run principal ─────────────────────────────────────────────────────

def run(con: duckdb.DuckDBPyConnection, args: argparse.Namespace) -> dict[str, Any]:
    qs = build_questions(con, args.seed)
    qs = qs[: args.questions] if args.questions else qs
    n = len(qs)

    cover = {"classic": {k: 0 for k in (1, 3, 5)}, "graph": {k: 0 for k in (1, 3, 5)}}
    answers: list[str] = []

    llm: Mistral | None = None if args.no_llm else Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))

    for i, q in enumerate(qs):
        print(f"\n[{i+1}/{n}] ({q.origin}) {q.question[:70]}")
        hits_g = retrieve_graph(con, q.question, 5)
        hits_c = retrieve_classic(con, q.question, 5)

        for mode, hits in (("classic", hits_c), ("graph", hits_g)):
            srcs = top_sources(con, hits)
            for k in (1, 3, 5):
                if any(q.expected in s for s in srcs[:k]):
                    cover[mode][k] += 1
            top = srcs[0].split("/")[-1] if srcs else "?"
            tag = "✓" if q.expected in srcs[0] else "✗"
            print(f"    {mode:8s} top-1: {top[:55]} {tag}")

        # Réponse LLM (contexte du mode graph), sauf en --no-llm
        if llm is not None:
            context = []
            for cid, _score in hits_g:
                row = con.execute(
                    "SELECT source, chunk_text FROM documents WHERE id = ?", [cid]
                ).fetchone()
                if row:
                    context.append(f"[{row[0]}]\n{row[1]}")
            user_prompt = f"CONTEXTE:\n{chr(10).join(context)}\n\nQUESTION: {q.question}"
            try:
                answers.append(_llm_answer(llm, user_prompt))
            except Exception as e:
                print(f"    ⚠️ LLM error: {e}")
                answers.append("")

    # ── Rapport : couverture ─────────────────────────────────────────
    print(f"\n{'='*56}")
    print("COUVERTURE RETRIEVAL (source attendue dans top-k)")
    for mode in ("classic", "graph"):
        row = " | ".join(f"top-{k}: {cover[mode][k]}/{n}" for k in (1, 3, 5))
        print(f"  {mode:8s} {row}")

    metrics: dict[str, Any] = {
        "date": date.today().isoformat(),
        "question_seed": args.seed,
        "n_questions": n,
        "coverage": {
            mode: {
                f"top{k}": {"n": cover[mode][k], "pct": round(100 * cover[mode][k] / max(n, 1), 1)}
                for k in (1, 3, 5)
            }
            for mode in ("classic", "graph")
        },
    }

    # ── Rapport : pertinence (mode LLM) ──────────────────────────────
    if llm is not None and answers:
        print("\nPERTINENCE DES RÉPONSES (mots-clés attendus présents)")
        score_sum, full = 0, 0
        for i, q in enumerate(qs):
            a = answers[i] if i < len(answers) else ""
            hit = contains_keywords(a, q.keywords)
            score_sum += hit / max(len(q.keywords), 1)
            status = "✓" if hit == len(q.keywords) else f"~{hit}/{len(q.keywords)}"
            print(f"  {status}  {q.question[:60]}")
            if hit == len(q.keywords):
                full += 1
        avg = score_sum / max(n, 1)
        print(f"\n  Score moyen de couverture conceptuelle : {avg*100:.0f}%")
        print(f"  Réponses complètes (tous les concepts)  : {full}/{n}")
        metrics["pertinence"] = {
            "avg_pct": round(avg * 100, 1),
            "full": full,
            "total": n,
        }

    # ── Rapport : refus hors-domaine (mode LLM) ──────────────────────
    if llm is not None:
        print("\nREFUS HORS-DOMAINE (questions hors domaine, SANS contexte)")
        refused = 0
        for i, q in enumerate(OFF_TOPIC_QUESTIONS):
            try:
                content = _llm_answer(llm, q, max_tokens=200)
            except Exception as e:
                print(f"    ⚠️ LLM error: {e}")
                content = ""
            ok = any(_norm(k) in _norm(content) for k in REFUSAL_KEYWORDS)
            if ok:
                refused += 1
            else:
                print(f"       (non-refus détecté → réponse: {_norm(content)[:100]})")
            print(f"  {'✓' if ok else '✗'}  {q[:60]}")
        print(f"\n  Taux de refus hors-domaine : {refused}/{len(OFF_TOPIC_QUESTIONS)}")
        metrics["refus_hors_domaine"] = {
            "refused": refused,
            "total": len(OFF_TOPIC_QUESTIONS),
            "pct": round(100 * refused / max(len(OFF_TOPIC_QUESTIONS), 1), 1),
        }

    print(f"{'='*56}")
    return metrics


# ── Snapshot / baseline / check ──────────────────────────────────────

def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📄 {path.relative_to(ROOT.parent)} écrit")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise


def check_regression(metrics: dict[str, Any]) -> int:
    """Compare les métriques courantes à baseline.json. Échoue (1) si la
    pertinence OU un coverage top-3 a baissé de plus de 5 points."""
    try:
        base = _load_json(BASELINE_PATH)
    except (OSError, ValueError) as e:
        print(f"❌ baseline illisible : {BASELINE_PATH} — {e}")
        print("   Lance d'abord : python benchmark.py --baseline")
        return 1

    fails: list[str] = []
    try:
        for mode in ("classic", "graph"):
            b = float(base["coverage"][mode]["top3"]["pct"])
            c = float(metrics["coverage"][mode]["top3"]["pct"])
            if b - c > 5.0:
                fails.append(f"coverage top-3 {mode}: {b}% -> {c}% (baisse de {b - c:.1f} pts)")

        if "pertinence" in base and "pertinence" in metrics:
            b = float(base["pertinence"]["avg_pct"])
            c = float(metrics["pertinence"]["avg_pct"])
            if b - c > 5.0:
                fails.append(f"pertinence: {b}% -> {c}% (baisse de {b - c:.1f} pts)")
    except (KeyError, TypeError, ValueError) as e:
        print(f"❌ baseline.json au format inattendu : {e}")
        return 1

    if fails:
        print("❌ RÉGRESSION DÉTECTÉE :")
        for f in fails:
            print(f"   - {f}")
        return 1
    print("✅ Aucune régression : pertinence et coverage top-3 dans les 5 points.")
    return 0


# ── CLI ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark couverture + pertinence + refus hors-domaine")
    parser.add_argument("--questions", type=int, default=None, help="Limite le nb de questions du domaine (défaut : tout l'échantillon)")
    parser.add_argument("--no-llm", action="store_true", help="Saute la génération de réponses (couverture seule)")
    parser.add_argument("--seed", type=int, default=QUESTION_SEED, help=f"Graine de l'échantillon (défaut {QUESTION_SEED})")
    parser.add_argument("--snapshot", action="store_true", help="Écrit evals/report-YYYYMMDD.json")
    parser.add_argument("--baseline", action="store_true", help="Force l'écriture de evals/baseline.json")
    parser.add_argument("--check", action="store_true", help="Compare le run courant à baseline.json (code 1 si régression)")
    args = parser.parse_args()

    if not os.environ.get("VOYAGE_API_KEY"):
        print("❌ VOYAGE_API_KEY not set.")
        raise SystemExit(1)
    if not args.no_llm and not os.environ.get("MISTRAL_API_KEY"):
        print("❌ MISTRAL_API_KEY not set (ou passe --no-llm).")
        raise SystemExit(1)
    if args.no_llm and (args.snapshot or args.baseline or args.check):
        print("❌ --snapshot/--baseline/--check exigent le mode LLM complet (retire --no-llm).")
        raise SystemExit(1)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        metrics = run(con, args)
    finally:
        con.close()

    if args.snapshot:
        _write_json(EVALS_DIR / f"report-{date.today():%Y%m%d}.json", metrics)
    if args.baseline:
        _write_json(BASELINE_PATH, metrics)
    if args.check:
        sys.exit(check_regression(metrics))


if __name__ == "__main__":
    main()