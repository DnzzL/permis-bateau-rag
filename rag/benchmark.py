"""
Benchmark rapide de couverture et pertinence (benchmark.py)

Deux niveaux d'évaluation :
  1. COUVERTURE retrieval : pour chaque question de référence, le chunk
     pertinent (bonne leçon/fiche) est-il dans le top-1 / top-3 / top-5 ?
  2. PERTINENCE des réponses : réponse LLM générée avec le contexte → les
     concepts clés attendus y figurent-ils ?

Usage : .venv/bin/python benchmark.py [--questions N] [--no-llm]
"""
import argparse
import os
import sys
from pathlib import Path

import duckdb
from dotenv import load_dotenv
from mistralai.client import Mistral

from retrieve import DB_PATH, retrieve_classic, retrieve_graph

ROOT = Path(__file__).resolve().parent
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SYSTEM_PROMPT = """Tu es un professeur expert du permis bateau français (côtier et fluvial).
Réponds en français, de façon concise (5-8 phrases max), uniquement à partir du
contexte fourni. Si l'information n'y est pas, dis-le honnêtement."""

# (question, [mots-clés attendus dans la réponse])
QUESTIONS = [
    ("Qui est prioritaire entre deux voiliers qui se croisent ?",
     ["tribord", "bâbord", "amure", "vent"]),
    ("Que signifie une bouée cardinale rouge et blanche ?",
     ["cardinal", "danger", "côté", "nord", "est", "ouest", "sud"]),
    ("Comment annoncer une détresse à la VHF ?",
     ["mayday", "canal", "16", "pan pan", "détresse"]),
    ("Que signifient deux feux rouges superposés à la verticale ?",
     ["rouge", "non maître", "manœuvre", "nuc", "27"]),
    ("Quelle est la vitesse limite dans la bande des 300 mètres ?",
     ["5", "nœud", "300", "baigneur"]),
    ("Que faire en cas d'homme à la mer ?",
     ["homme à la mer", "cri", "pointer", "repère", "récupération"]),
    ("Comment se déroule le passage d'une écluse ?",
     ["écluse", "amarre", "ralenti", "attente", "feu"]),
    ("Quel est le canal VHF à utiliser pour un appel de détresse ?",
     ["16", "vhf", "canal"]),
    ("Que signifie le pavillon bleu ?",
     ["plongée", "divers", "pavillon", "bleu"]),
    ("Quelle est la règle pour dépasser un autre bateau ?",
     ["dépassement", "rattrapé", "s'écarter", "route"]),
    ("Qu'est-ce que le balisage cardinal ?",
     ["cardinal", "quadrant", "nord", "sud", "est", "ouest", "danger"]),
    ("Quels équipements de sécurité sont obligatoires à bord ?",
     ["gilet", "vhf", "extincteur", "fusée", "obligatoire"]),
    ("Comment se lit une carte marine ?",
     ["carte", "sonde", "profondeur", "échelle", "nord"]),
    ("Qu'est-ce que le mistral ?",
     ["mistral", "vent", "nord", "ouest", "vallée"]),
    ("Quelle est la procédure pour un appel MAYDAY ?",
     ["mayday", "trois", "16", "position", "nature"]),
]

# Source "attendue" pour chaque question (fragment de chemin) — jugement humain
EXPECTED_SOURCES = [
    "0002-regles-route", "0004-balisage", "0006-securite", "0003-feux",
    "0006-securite", "0006-securite", "0014-passage-ecluse", "0006-securite",
    "0004-balisage", "0002-regles-route", "0004-balisage", "0006-securite",
    "0009-carte-navigation", "0005-meteo-vents", "0006-securite",
]


def _norm(text: str) -> str:
    return " ".join(text.lower().replace("œ", "oe").split())


def contains_keywords(answer: str, keywords: list[str]) -> int:
    a = _norm(answer)
    return sum(1 for k in keywords if _norm(k) in a)


def top_sources(con: duckdb.DuckDBPyConnection, hits: list[tuple[int, float]]) -> list[str]:
    out = []
    for cid, _ in hits:
        row = con.execute("SELECT source FROM documents WHERE id = ?", [cid]).fetchone()
        if row:
            out.append(row[0])
    return out


def run(con: duckdb.DuckDBPyConnection, n_questions: int, no_llm: bool) -> None:
    qs = QUESTIONS[:n_questions]
    expected = EXPECTED_SOURCES[:n_questions]

    cover = {"classic": {k: 0 for k in (1, 3, 5)}, "graph": {k: 0 for k in (1, 3, 5)}}
    answers: list[str] = []
    hit_sources: dict[str, list[str]] = {}

    llm = None if no_llm else Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))

    for i, (q, _kw) in enumerate(qs):
        exp = expected[i]
        print(f"\n[{i+1}/{len(qs)}] {q[:70]}")
        hits_g = retrieve_graph(con, q, 5)
        hits_c = retrieve_classic(con, q, 5)
        hit_sources[q] = top_sources(con, hits_g)

        for mode, hits in (("classic", hits_c), ("graph", hits_g)):
            srcs = top_sources(con, hits)
            for k in (1, 3, 5):
                if any(exp in s for s in srcs[:k]):
                    cover[mode][k] += 1
            top = srcs[0].split("/")[-1] if srcs else "?"
            tag = "✓" if exp in srcs[0] else "✗"
            print(f"    {mode:8s} top-1: {top[:55]} {tag}")

        # Réponse LLM (mode graph)
        if llm is not None:
            context = []
            for cid, score in hits_g:
                row = con.execute("SELECT source, chunk_text FROM documents WHERE id = ?", [cid]).fetchone()
                if row:
                    context.append(f"[{row[0]}]\n{row[1]}")
            user_prompt = f"CONTEXTE:\n{chr(10).join(context)}\n\nQUESTION: {q}"
            try:
                resp = llm.chat.complete(
                    model=MISTRAL_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=400,
                )
                msg = resp.choices[0].message
                content = msg.content if msg else None
                if isinstance(content, list):
                    content = "".join(getattr(part, "text", "") or "" for part in content)
                answers.append(content or "")
            except Exception as e:
                print(f"    ⚠️ LLM error: {e}")
                answers.append("")

    # ── Rapport ─────────────────────────────────────────────────────
    n = len(qs)
    print(f"\n{'='*56}")
    print("COUVERTURE RETRIEVAL (bonne source dans top-k)")
    for mode in ("classic", "graph"):
        row = " | ".join(f"top-{k}: {cover[mode][k]}/{n}" for k in (1, 3, 5))
        print(f"  {mode:8s} {row}")

    if llm is not None and answers:
        print("\nPERTINENCE DES RÉPONSES (mots-clés attendus présents)")
        score_sum, full = 0, 0
        for i, (q, kw) in enumerate(qs):
            a = answers[i] if i < len(answers) else ""
            hit = contains_keywords(a, kw)
            score_sum += hit / len(kw)
            status = "✓" if hit == len(kw) else f"~{hit}/{len(kw)}"
            print(f"  {status}  {q[:60]}")
            if hit == len(kw):
                full += 1
        avg = score_sum / max(len(qs), 1)
        print(f"\n  Score moyen de couverture conceptuelle : {avg*100:.0f}%")
        print(f"  Réponses complètes (tous les concepts)  : {full}/{len(qs)}")

    print(f"{'='*56}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark couverture + pertinence")
    parser.add_argument("--questions", type=int, default=len(QUESTIONS))
    parser.add_argument("--no-llm", action="store_true", help="Saute la génération de réponses")
    args = parser.parse_args()

    if not os.environ.get("VOYAGE_API_KEY"):
        print("❌ VOYAGE_API_KEY not set.")
        raise SystemExit(1)
    if not args.no_llm and not os.environ.get("MISTRAL_API_KEY"):
        print("❌ MISTRAL_API_KEY not set (ou passe --no-llm).")
        raise SystemExit(1)

    con = duckdb.connect(str(DB_PATH))
    run(con, args.questions, args.no_llm)
    con.close()


if __name__ == "__main__":
    main()
