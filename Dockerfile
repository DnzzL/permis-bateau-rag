# ─────────────────────────────────────────────────────────────────────────────
# Image de l'API permis bateau RAG — déployée sur Dokploy (VPS).
#
# La base DuckDB (rag/permis.duckdb, 3,8 Mo) est COMMITÉE dans le repo : elle
# est copiée dans l'image → clone & déploiement immédiats. Pour servir une base
# fraîche, monte-la en volume et surcharge PERMIS_DB_PATH (docker-compose).
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

# Base DuckDB pré-construite (commitée dans le repo) — point de montage par
# défaut, surchargeable via PERMIS_DB_PATH.
COPY rag/permis.duckdb /data/permis.duckdb
RUN mkdir -p /data
ENV PERMIS_DB_PATH=/data/permis.duckdb

# Uvicorn : un seul worker (le rate limiter est en mémoire — un seul process).
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

EXPOSE 8000
