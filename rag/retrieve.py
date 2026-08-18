"""
T4 — Retrieval hybride (retrieve.py)

Deux stratégies de recherche, testées l'une contre l'autre :

- retrieve_classic : embedding de la requête → cos_sim sur tous les chunks → top-k
- retrieve_graph   : embedding → top-k chunks → entités liées → voisins 1-hop
                    (relations) → chunks liés à ces entités → fusion + rerank

Chaque mode retourne une liste de (chunk_id, score) triée.
Le test auto (--test) évalue les deux modes sur les QCMs : pour chaque question,
trouve-t-on le chunk contenant le feedback (réponse) dans le top-5 ?
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


# ── Retrieval par graphe ─────────────────────────────────────────────

def retrieve_graph(con: duckdb.DuckDBPyConnection, query: str, top_k: int = 5) -> list[tuple[int, float]]:
    """Embedding → top-k chunks → entités → voisins 1-hop → chunks liés → fusion."""
    client = VoyageClient(os.environ.get("VOYAGE_API_KEY", ""))
    q_emb = embed_query(client, query)

    # 1. Top-k chunks par similarité (base du graphe)
    seed = con.execute(
        """
        SELECT id FROM documents
        ORDER BY list_cosine_similarity(embedding, ?) DESC
        LIMIT ?
        """,
        [q_emb, max(top_k, 8)],
    ).fetchall()
    seed_ids = [r[0] for r in seed]

    # 2. Entités liées aux chunks seed
    entity_ids = con.execute(
        "SELECT DISTINCT entity_id FROM document_entities WHERE chunk_id IN (SELECT UNNEST(?))",
        [seed_ids],
    ).fetchall()
    ent_ids = [r[0] for r in entity_ids]

    # 3. Voisins 1-hop (relations)
    neighbor_ids = con.execute(
        """
        SELECT DISTINCT CASE WHEN source_id IN (SELECT UNNEST(?)) THEN target_id
                             ELSE source_id END
        FROM relationships
        WHERE source_id IN (SELECT UNNEST(?)) OR target_id IN (SELECT UNNEST(?))
        """,
        [ent_ids, ent_ids, ent_ids],
    ).fetchall()
    hop_ids = list({r[0] for r in neighbor_ids} | set(ent_ids))

    # 4. Chunks liés aux entités (seed + voisins)
    candidate_ids = con.execute(
        """
        SELECT DISTINCT chunk_id FROM document_entities
        WHERE entity_id IN (SELECT UNNEST(?))
        """,
        [hop_ids],
    ).fetchall()
    cand = [r[0] for r in candidate_ids]
    if not cand:
        return retrieve_classic(con, query, top_k)

    # 5. Score = similarité cos + bonus graphique en UNE requête batch.
    #    Bonus : partage d'entités avec les chunks seed (propagation 1-hop),
    #    plafonné à 0.3 — fait remonter les chunks découverts via le graphe.
    scored = con.execute(
        """
        WITH seed_entities AS (
            SELECT DISTINCT entity_id FROM document_entities
            WHERE chunk_id IN (SELECT UNNEST(?))
        ),
        shared AS (
            SELECT de.chunk_id, COUNT(DISTINCT de.entity_id) AS n
            FROM document_entities de
            JOIN seed_entities se ON se.entity_id = de.entity_id
            WHERE de.chunk_id IN (SELECT UNNEST(?))
            GROUP BY de.chunk_id
        )
        SELECT d.id,
               list_cosine_similarity(d.embedding, ?)
               + LEAST(0.02 * COALESCE(s.n, 0), 0.3) AS score
        FROM documents d
        LEFT JOIN shared s ON s.chunk_id = d.id
        ORDER BY score DESC
        LIMIT ?
        """,
        [seed_ids, cand, q_emb, top_k],
    ).fetchall()
    return [(r[0], r[1]) for r in scored]


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
    """Évalue retrieve_classic vs retrieve_graph : un chunk de la leçon
    d'origine du QCM est-il dans le top-5 ?"""
    rows = con.execute(
        "SELECT question, source FROM qcm WHERE source IS NOT NULL LIMIT ?", [n_questions]
    ).fetchall()
    src_index = _qcm_chunks(con)

    results = {"classic": 0, "graph": 0}
    total = 0
    for q, src in rows:
        target_chunks = src_index.get(src, [])
        if not target_chunks:
            continue
        total += 1
        for mode, fn in (("classic", retrieve_classic), ("graph", retrieve_graph)):
            hits = [cid for cid, _ in fn(con, q, top_k=5)]
            if any(t in hits for t in target_chunks):
                results[mode] += 1

    print(f"\n{'='*50}")
    print(f"Test sur {total} QCMs (leçon d'origine dans top-5)")
    print(f"  retrieve_classic : {results['classic']}/{total} ({results['classic']/max(total,1)*100:.0f}%)")
    print(f"  retrieve_graph   : {results['graph']}/{total} ({results['graph']/max(total,1)*100:.0f}%)")
    print(f"{'='*50}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieval hybride")
    parser.add_argument("query", nargs="?", help="Requête (mode interactif)")
    parser.add_argument("--mode", choices=["classic", "graph", "both"], default="both")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--test", action="store_true", help="Test auto sur QCMs")
    parser.add_argument("--n-questions", type=int, default=145)
    args = parser.parse_args()

    if not os.environ.get("VOYAGE_API_KEY"):
        print("❌ VOYAGE_API_KEY not set.")
        raise SystemExit(1)

    con = duckdb.connect(str(DB_PATH))
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
    for mode in ("classic", "graph"):
        if args.mode not in ("both", mode):
            continue
        fn = retrieve_classic if mode == "classic" else retrieve_graph
        results = fn(con, query, args.top_k)
        print(f"\n--- {mode} (top-{args.top_k}) ---")
        for cid, score in results:
            src = con.execute("SELECT source, chunk_index, substr(chunk_text,1,90) FROM documents WHERE id=?", [cid]).fetchone()
            if src:
                print(f"  [{cid}] {score:.3f} | {src[0]} #{src[1]} | {src[2]}...")


if __name__ == "__main__":
    main()
