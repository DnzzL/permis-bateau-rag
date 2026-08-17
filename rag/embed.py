"""
T2 — Embedding voyageai + DuckDB
Chunks the corpus, embeds each chunk with Voyage AI, stores in DuckDB.
Also loads the QCM questions into a separate table (for later eval/quiz mode).
"""
import json
import os
import re
from pathlib import Path

import duckdb
from voyageai.client import Client as VoyageClient
from dotenv import load_dotenv

# Cherche .env dans rag/ ET dans le dossier parent du projet
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DB_PATH = ROOT / "permis.duckdb"

# Voyage AI config — model chosen at runtime, dimension auto-detected.
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-3-lite")
CHUNK_WORDS = 400
CHUNK_OVERLAP = 50


# ── Chunking ─────────────────────────────────────────────────────────

def chunk_text(text: str, words: int = CHUNK_WORDS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping word-based chunks."""
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    if len(tokens) <= words:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + words, len(tokens))
        chunk = " ".join(tokens[start:end])
        chunks.append(chunk)
        if end == len(tokens):
            break
        start = end - overlap
    return chunks


# ── Embedding ────────────────────────────────────────────────────────

def embed_batch(texts: list[str], input_type: str, client) -> list[list[float]]:
    """Embed a list of texts with Voyage AI. Handles large batches in pages."""
    embeddings: list[list[float]] = []
    BATCH = 128  # Voyage API batch limit
    for i in range(0, len(texts), BATCH):
        page = texts[i : i + BATCH]
        result = client.embed(
            texts=page,
            model=VOYAGE_MODEL,
            input_type=input_type,  # "document" or "query"
        )
        batch_emb = getattr(result, "embeddings", None)
        if batch_emb is None:
            raise RuntimeError(f"Voyage AI returned no embeddings for batch {i // BATCH}")
        embeddings.extend(batch_emb)
    return embeddings


# ── Main ─────────────────────────────────────────────────────────────

def load_corpus(path: Path) -> list[dict]:
    """Load corpus.jsonl, raising a clean error on failure."""
    docs = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    docs.append(json.loads(line))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"❌ Failed to load {path}: {e}") from e
    return docs


def load_qcm(path: Path) -> list[dict]:
    """Load qcm.json, raising a clean error on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"❌ Failed to load {path}: {e}") from e


def main():
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        print("❌ VOYAGE_API_KEY not set. Export it and retry.")
        raise SystemExit(1)

    client = VoyageClient(api_key=api_key)

    # 1. Load corpus
    corpus_path = DATA / "corpus.jsonl"
    docs = load_corpus(corpus_path)
    print(f"Loaded {len(docs)} documents from {corpus_path}")

    # 2. Chunk
    chunks: list[dict] = []
    for doc in docs:
        for i, text in enumerate(chunk_text(doc["text"])):
            chunks.append({
                "source": doc["source"],
                "type": doc["type"],
                "topic": doc["topic"],
                "chunk_index": i,
                "chunk_text": text,
            })
    print(f"Chunked into {len(chunks)} chunks ({CHUNK_WORDS} words, {CHUNK_OVERLAP} overlap)")

    # 3. Embed all chunks
    print(f"Embedding {len(chunks)} chunks with {VOYAGE_MODEL}...")
    chunk_texts = [c["chunk_text"] for c in chunks]
    chunk_embeddings = embed_batch(chunk_texts, "document", client)
    if not chunk_embeddings:
        raise SystemExit("❌ No embeddings returned — check API key/quota.")
    first_embedding = chunk_embeddings[0]
    if first_embedding is None:
        raise SystemExit("❌ Empty embedding returned by Voyage AI.")
    dim = len(first_embedding)
    print(f"Embedding dimension: {dim}")

    # 4. Create DuckDB
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))

    # embedding stored as DOUBLE[] (variable-length list) → fully static DDL,
    # no dynamic SQL, no injection surface.
    con.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            source VARCHAR,
            type VARCHAR,
            topic VARCHAR,
            chunk_index INTEGER,
            chunk_text VARCHAR,
            embedding DOUBLE[]
        )
    """)

    con.executemany(
        "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (i, c["source"], c["type"], c["topic"], c["chunk_index"], c["chunk_text"], emb)
            for i, (c, emb) in enumerate(zip(chunks, chunk_embeddings))
        ],
    )
    print(f"Inserted {len(chunks)} rows into documents table")

    # 5. Load QCM questions
    qcm_path = DATA / "qcm.json"
    qcms = load_qcm(qcm_path)

    con.execute("""
        CREATE TABLE qcm (
            id INTEGER PRIMARY KEY,
            question VARCHAR,
            options VARCHAR[],  -- list of options
            correct_index INTEGER,
            feedback VARCHAR,
            topic VARCHAR,
            source VARCHAR
        )
    """)

    con.executemany(
        "INSERT INTO qcm VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                i,
                q["question"],
                q["options"],
                q["correct_index"],
                q["feedback"],
                q.get("topic"),
                q.get("source"),
            )
            for i, q in enumerate(qcms)
        ],
    )
    print(f"Inserted {len(qcms)} QCM questions into qcm table")

    # 6. Verify
    row_docs = con.execute("SELECT COUNT(*) FROM documents").fetchone()
    row_qcm = con.execute("SELECT COUNT(*) FROM qcm").fetchone()
    n_docs = row_docs[0] if row_docs else 0
    n_qcm = row_qcm[0] if row_qcm else 0
    print(f"\n✅ DuckDB ready: {DB_PATH}")
    print(f"   documents: {n_docs} rows, qcm: {n_qcm} rows")

    # 7. Sanity check: vector search on a sample query (fully parameterized)
    print("\n── Sanity check: vector search ──")
    test_queries = [
        "Qui est prioritaire quand deux voiliers se croisent ?",
        "Quels sont les feux d'un bateau à l'ancre la nuit ?",
    ]
    for q in test_queries:
        q_emb = embed_batch([q], "query", client)[0]
        row = con.execute(
            """
            SELECT source, topic, chunk_index,
                   list_cosine_similarity(embedding, ?) AS score
            FROM documents
            ORDER BY score DESC
            LIMIT 1
            """,
            [q_emb],
        ).fetchone()
        if row is None:
            continue
        print(f"\nQuery: {q}")
        print(f"  Top hit: {row[0]} [{row[1]}] chunk {row[2]} — score {row[3]:.3f}")

    con.close()


if __name__ == "__main__":
    main()
