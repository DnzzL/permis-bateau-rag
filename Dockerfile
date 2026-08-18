# ─────────────────────────────────────────────────────────────────────────────
# Image de l'API permis bateau RAG — déployée sur Dokploy (VPS).
#
# La base DuckDB (rag/permis.duckdb) est GITIGNORÉE : elle n'est pas dans
# l'image. Elle est montée en volume à /data/permis.duckdb (voir
# docker-compose.yml) — copie-la sur le VPS avec :
#   scp rag/permis.duckdb user@vps:/chemin/dokploy/data/permis.duckdb
#
# Les clés API (VOYAGE_API_KEY, MISTRAL_API_KEY…) passent par .env au runtime,
# jamais dans l'image.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances verrouillées par uv (uv export --frozen > requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code applicatif — les modules sont copiés à la racine pour que les imports
# locaux (from retrieve import ...) se résolvent comme en dev (cwd rag/).
COPY rag/rag.py rag/prompts.py rag/retrieve.py rag/rate_limit.py rag/api.py ./
# La base est montée en volume, mais on crée le point de montage par défaut.
RUN mkdir -p /data

# Uvicorn : un seul worker (le rate limiter est en mémoire — un seul process).
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

EXPOSE 8000
