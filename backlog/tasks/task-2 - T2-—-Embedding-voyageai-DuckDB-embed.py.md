---
id: TASK-2
title: T2 — Embedding voyageai + DuckDB (embed.py)
status: Done
assignee: []
created_date: '2026-08-07 19:50'
updated_date: '2026-08-14 12:39'
labels: []
dependencies:
  - TASK-1
ordinal: 2000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Chunker le corpus (RecursiveCharacterTextSplitter, 400 tokens, overlap 50). Embedder via voyageai. Créer permis.duckdb avec table documents (id, chunk_text, embedding FLOAT[1024], metadata JSON, topic). Test: 3 requêtes de validation.
<!-- SECTION:NOTES:END -->
