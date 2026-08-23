"""Benchmark COMPOSITE — qualité du chatbot sur des questions multi-sources.

Complète benchmark.py, qui mesure le QCM. Une question de QCM se répond depuis
UNE section ; un utilisateur du chatbot, lui, pose des questions qui exigent de
composer depuis plusieurs fiches (« Mistral force 7 demain, bateau catégorie C,
sortie en zone 2 : je sors ? »). Ce fichier mesure ce cas-là.

Jeu de questions : evals/composite.json — 24 questions, chacune avec ses
sources requises et ses faits attendus, définis à la lecture du corpus AVANT
tout retrieval, et validés comme réellement présents dans le corpus.

Trois métriques :
  1. RAPPEL DES SOURCES REQUISES — fraction des sources indispensables
     présentes dans le top-k.
  2. DIVERSITÉ — nombre de sources distinctes dans le top-k. Un retrieval qui
     ramène k chunks de la même leçon ne peut pas répondre à une question
     multi-sources, même avec d'excellents scores de similarité.
  3. COUVERTURE FACTUELLE — faits attendus présents dans la réponse générée.
     La métrique la plus proche de la qualité perçue du chatbot.

⚠️ Bruit de mesure : la génération tourne à temperature 0.2. Deux exécutions
identiques de la même configuration s'écartent typiquement de ±6,3 pt sur la
couverture factuelle (mesuré : deux runs du même retrieval ont donné 77,2 % et
77,4 %, et un troisième 73,3 %). Ne pas conclure sur un écart de moins de
~7 pt sans rejouer plusieurs fois.

Ce harnais a servi à trancher le sort du graphe de connaissances — voir la
section « Pourquoi pas de graphe de connaissances » du README.

Usage : .venv/bin/python benchmark_composite.py [--top-k 9] [--no-llm] [--snapshot]
"""
import argparse
import json
import os
import statistics
from pathlib import Path
from typing import Any

import duckdb
from dotenv import load_dotenv
from mistralai.client import Mistral

from benchmark import _llm_answer, contains_keywords
from retrieve import DB_PATH, retrieve_classic

ROOT = Path(__file__).resolve().parent
EVALS = ROOT.parent / "evals"

load_dotenv()
load_dotenv(ROOT.parent / ".env")


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark composite (qualité chatbot)")
    ap.add_argument("--top-k", type=int, default=9, help="Budget de contexte, en chunks")
    ap.add_argument("--no-llm", action="store_true", help="Retrieval seul, sans génération")
    ap.add_argument("--snapshot", action="store_true", help="Écrit evals/composite-report.json")
    args = ap.parse_args()

    if not os.environ.get("VOYAGE_API_KEY"):
        raise SystemExit("❌ VOYAGE_API_KEY manquante.")
    if not args.no_llm and not os.environ.get("MISTRAL_API_KEY"):
        raise SystemExit("❌ MISTRAL_API_KEY manquante (ou --no-llm).")

    qs = json.loads((EVALS / "composite.json").read_text(encoding="utf-8"))["questions"]
    con = duckdb.connect(str(DB_PATH), read_only=True)
    src_of = dict(con.execute("SELECT id, source FROM documents").fetchall())
    llm = None if args.no_llm else Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    recall: list[float] = []
    diversity: list[int] = []
    factcov: list[float] = []
    per_q: list[dict[str, Any]] = []

    for i, q in enumerate(qs):
        hits = retrieve_classic(con, q["q"], args.top_k)
        srcs = [src_of[c] for c, _ in hits]
        req = set(q["required_sources"])
        found = req & set(srcs)
        r = len(found) / max(len(req), 1)
        recall.append(r)
        diversity.append(len(set(srcs)))
        row: dict[str, Any] = {"q": q["q"], "recall": r, "diversity": len(set(srcs))}

        line = f"[{i+1}/{len(qs)}] rappel {r*100:3.0f}%  sources distinctes {len(set(srcs)):2d}"
        if llm is not None:
            ctx = []
            for cid, _ in hits:
                t = con.execute(
                    "SELECT source, chunk_text FROM documents WHERE id=?", [cid]
                ).fetchone()
                if t:
                    ctx.append(f"[{t[0]}]\n{t[1]}")
            prompt = f"CONTEXTE:\n{chr(10).join(ctx)}\n\nQUESTION: {q['q']}"
            try:
                ans = _llm_answer(llm, prompt)
            except Exception as e:
                print(f"    ⚠️ LLM: {e}")
                ans = ""
            hit = contains_keywords(ans, q["facts"])
            fc = hit / max(len(q["facts"]), 1)
            factcov.append(fc)
            row["fact_coverage"] = fc
            line += f"  faits {hit}/{len(q['facts'])}"
        miss = sorted(req - found)
        if miss:
            line += f"  manque: {', '.join(s.split('/')[-1] for s in miss)}"
        print(f"{line}  | {q['q'][:52]}")
        per_q.append(row)

    print(f"\n{'='*72}")
    print(f"RÉSULTATS — {len(qs)} questions composites, top-k={args.top_k}")
    print(f"  rappel des sources requises : {statistics.mean(recall)*100:.1f}%")
    print(f"  sources distinctes (moyenne): {statistics.mean(diversity):.1f}")
    if factcov:
        print(f"  faits couverts              : {statistics.mean(factcov)*100:.1f}%  (±6,3 pt de bruit)")
    print(f"{'='*72}")

    if args.snapshot:
        metrics = {
            "top_k": args.top_k,
            "n_questions": len(qs),
            "recall_pct": round(statistics.mean(recall) * 100, 1),
            "distinct_sources": round(statistics.mean(diversity), 2),
            "fact_coverage_pct": round(statistics.mean(factcov) * 100, 1) if factcov else None,
            "per_question": per_q,
        }
        out = EVALS / "composite-report.json"
        out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📄 {out} écrit")
    con.close()


if __name__ == "__main__":
    main()
