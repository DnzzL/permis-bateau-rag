"""API HTTP du chatbot permis bateau (RAG) — pour hébergement Dokploy.

Endpoints :
  GET  /health     → état de la base (chunks, QCM) + limite configurée
  POST /api/chat   → question → retrieval (graph ou classic) → réponse Mistral

Rate limiting basique par IP (fenêtre glissante en mémoire, 429 au-delà),
CORS restreint aux origines configurées (CORS_ORIGINS, virgule-séparé).

Lancement local :
  cd rag && .venv/bin/uvicorn api:app --reload --port 8000
"""
import os
import threading
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mistralai.client import Mistral
from pydantic import BaseModel, Field

from prompts import SYSTEM_PROMPT
from rate_limit import RateLimiter
from retrieve import DB_PATH, retrieve_classic, retrieve_graph

ROOT = Path(__file__).resolve().parent
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
# Front statique servi par le même process (pattern single-origin) :
# dev = ../web depuis rag/, conteneur = STATIC_DIR défini dans le Dockerfile.
STATIC_DIR = Path(os.environ.get("STATIC_DIR", str(ROOT.parent / "web")))

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import duckdb  # noqa: E402
# ── Connexion base (une seule, partagée — DuckDB en lecture seule) ────
_con: duckdb.DuckDBPyConnection | None = None
_con_lock = threading.Lock()


def get_con() -> duckdb.DuckDBPyConnection:
    global _con
    if _con is None:
        with _con_lock:
            if _con is None:
                _con = duckdb.connect(str(DB_PATH), read_only=True)
    return _con


# ── Rate limiting ─────────────────────────────────────────────────────
limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    """IP réelle du client (derrière un reverse proxy Dokploy/Traefik)."""
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── App FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="Permis Bateau RAG API",
    description="Chatbot RAG pour la révision de l'examen du permis bateau (côtier & fluvial).",
    version="0.2.1",
)

_cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500, description="Question sur le permis bateau")
    use_graph: bool = True
    top_k: int = Field(default=4, ge=1, le=8)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, str | float]]
    model: str
@app.get("/health")
def health() -> dict[str, object]:
    con = get_con()
    row_chunks = con.execute("SELECT COUNT(*) FROM documents").fetchone()
    row_qcm = con.execute("SELECT COUNT(*) FROM qcm").fetchone()
    chunks = row_chunks[0] if row_chunks else 0
    qcm = row_qcm[0] if row_qcm else 0
    return {
        "status": "ok",
        "chunks": chunks,
        "qcm": qcm,
        "model": MISTRAL_MODEL,
        "rate_limit": {"max": limiter.max_requests, "window_s": limiter.window_s},
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request) -> ChatResponse:
    ip = _client_ip(request)
    if not limiter.allow(ip):
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes. Limite : {limiter.max_requests} / {limiter.window_s}s — réessaie dans un instant.",
        )

    con = get_con()
    try:
        if req.use_graph:
            hits = retrieve_graph(con, req.question, req.top_k)
        else:
            hits = retrieve_classic(con, req.question, req.top_k)
    except Exception as exc:  # clé Voyage absente/invalide, API injoignable…
        raise HTTPException(
            status_code=502,
            detail=f"Erreur retrieval (clé VOYAGE_API_KEY ?) : {exc}",
        ) from exc

    context = "\n\n".join(
        f"[Source {src} — score {score:.2f}]\n{text}"
        for src, text, score in _chunk_rows(con, hits)
    )

    client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))
    user_prompt = (
        f"CONTEXTE (extraits du cours permis bateau):\n{context}\n\n"
        f"QUESTION: {req.question}"
    )
    try:
        stream = client.chat.stream(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
    except Exception as exc:  # clé absente ou API injoignable
        raise HTTPException(status_code=502, detail=f"Erreur LLM : {exc}") from exc

    answer = ""
    for ev in stream:
        try:
            delta = ev.data.choices[0].delta.content
        except Exception:
            delta = None
        if delta is None:
            continue
        if isinstance(delta, str):
            answer += delta
        else:
            answer += "".join(getattr(part, "text", "") or "" for part in delta)

    sources = [
        {"source": src, "score": round(score, 2)}
        for src, _text, score in _chunk_rows(con, hits)
    ]
    return ChatResponse(answer=answer, sources=sources, model=MISTRAL_MODEL)


def _chunk_rows(con: duckdb.DuckDBPyConnection, hits: list[tuple[int, float]]):
    """(source, chunk_text, score) pour chaque hit, ordre du retrieval."""
    rows = []
    for cid, score in hits:
        row = con.execute("SELECT source, chunk_text FROM documents WHERE id = ?", [cid]).fetchone()
        if row:
            rows.append((row[0], row[1], score))
    return rows


# ── Front statique (single-origin : le même process sert le front et l'API) ──
# Monté en dernier : les routes /health et /api/chat ci-dessus priment ; tout
# le reste (/, /style…) vient du dossier web/.
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="web")
