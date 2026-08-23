"""
T4 — Retrieval (retrieve.py)

retrieve_classic : embedding de la requête → cos_sim sur tous les chunks → top-k.
Retourne une liste de (chunk_id, score) triée.

Un second mode, retrieve_graph (graphe d'entités + relations extraites par LLM,
expansion 1-hop puis rerank), a été implémenté puis retiré : mesuré sur le QCM
(60 questions) ET sur un jeu de 24 questions composites multi-sources, il ne
produisait aucun écart distinguable du bruit de génération. Voir la section
« Pourquoi pas de graphe de connaissances » du README pour les chiffres.

Le test auto (--test) évalue le retrieval sur les QCMs : pour chaque question,
trouve-t-on un chunk de la leçon d'origine dans le top-5 ?
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import cast

import duckdb
import voyageai
from dotenv import load_dotenv
from voyageai.client import Client as VoyageClient

ROOT = Path(__file__).resolve().parent

# Chemin de la base DuckDB — surchargeable par env (Docker/Dokploy :
# PERMIS_DB_PATH=/data/permis.duckdb avec un volume monté).
DB_PATH = Path(os.environ.get("PERMIS_DB_PATH", str(ROOT / "permis.duckdb")))
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-3-lite")


# Cherche .env dans rag/ ET dans le dossier parent du projet
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_embed_cache: dict[str, list[float]] = {}


# ── Embedding ────────────────────────────────────────────────────────

def embed_query(client: VoyageClient, text: str) -> list[float]:
    """Embedding d'une requête (avec cache par texte)."""
    if text not in _embed_cache:
        result = client.embed(texts=[text], model=VOYAGE_MODEL)
        # Le SDK type embeddings[0] comme List[float] | List[int] ; au runtime
        # ce sont toujours des floats (voyage-3-lite).
        _embed_cache[text] = cast(list[float], result.embeddings[0])
    return _embed_cache[text]


# ── Retrieval classique ──────────────────────────────────────────────

def retrieve_classic(con: duckdb.DuckDBPyConnection, query: str, top_k: int = 5) -> list[tuple[int, float]]:
    """Embedding → cos_sim sur tous les chunks → top-k (id, score)."""
    client = VoyageClient(os.environ.get("VOYAGE_API_KEY", ""))
    q_emb = embed_query(client, query)
    rows = con.execute(
        """
        SELECT id, list_cosine_similarity(embedding, ?) AS score
        FROM documents
        ORDER BY score DESC
        LIMIT ?
        """,
        [q_emb, top_k],
    ).fetchall()
    # score est un DOUBLE DuckDB — pas besoin de float()
    return [(r[0], r[1]) for r in rows]


# ── Test auto sur QCMs ───────────────────────────────────────────────

def _qcm_chunks(con: duckdb.DuckDBPyConnection) -> dict[str, list[int]]:
    """Source du QCM (leçon d'origine) → ids des chunks de cette leçon.

    Cible de vérité : la leçon dont le QCM est tiré. Plus robuste qu'un
    matching verbatim du feedback (souvent reformulé par rapport aux chunks).
    """
    rows = con.execute("SELECT DISTINCT source FROM qcm WHERE source IS NOT NULL").fetchall()
    chunks = con.execute("SELECT id, source FROM documents").fetchall()
    index: dict[str, list[int]] = {}
    for src, in rows:
        index[src] = [cid for cid, csrc in chunks if csrc == src]
    return index


def run_test(con: duckdb.DuckDBPyConnection, n_questions: int = 145) -> None:
    """Un chunk de la leçon d'origine du QCM est-il dans le top-5 ?"""
    rows = con.execute(
        "SELECT question, source FROM qcm WHERE source IS NOT NULL LIMIT ?", [n_questions]
    ).fetchall()
    src_index = _qcm_chunks(con)

    hits_ok = 0
    total = 0
    for q, src in rows:
        target_chunks = src_index.get(src, [])
        if not target_chunks:
            continue
        total += 1
        hits = [cid for cid, _ in retrieve_classic(con, q, top_k=5)]
        if any(t in hits for t in target_chunks):
            hits_ok += 1

    print(f"\n{'='*50}")
    print(f"Test sur {total} QCMs (leçon d'origine dans top-5)")
    print(f"  retrieve_classic : {hits_ok}/{total} ({hits_ok/max(total,1)*100:.0f}%)")
    print(f"{'='*50}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieval vectoriel")
    parser.add_argument("query", nargs="?", help="Requête (mode interactif)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--test", action="store_true", help="Test auto sur QCMs")
    parser.add_argument("--n-questions", type=int, default=145)
    args = parser.parse_args()

    if not os.environ.get("VOYAGE_API_KEY"):
        print("❌ VOYAGE_API_KEY not set.")
        raise SystemExit(1)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    if args.test:
        run_test(con, args.n_questions)
        con.close()
        return

    if not args.query:
        # Mode interactif
        print("Mode interactif — tape une question (Ctrl+C pour quitter)")
        while True:
            try:
                q = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not q:
                continue
            _show_results(con, q, args)
    else:
        _show_results(con, args.query, args)
    con.close()


def _show_results(con, query: str, args) -> None:
    print(f"\nRequête: {query}")
    print(f"\n--- top-{args.top_k} ---")
    for cid, score in retrieve_classic(con, query, args.top_k):
        src = con.execute("SELECT source, chunk_index, substr(chunk_text,1,90) FROM documents WHERE id=?", [cid]).fetchone()
        if src:
            print(f"  [{cid}] {score:.3f} | {src[0]} #{src[1]} | {src[2]}...")


if __name__ == "__main__":
    main()
