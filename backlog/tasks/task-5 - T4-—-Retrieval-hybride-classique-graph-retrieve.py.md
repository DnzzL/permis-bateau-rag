---
id: TASK-5
title: T4 — Retrieval hybride classique + graph (retrieve.py)
status: Done
assignee: []
created_date: '2026-08-07 19:50'
updated_date: '2026-08-14 13:54'
labels: []
dependencies:
  - TASK-3
ordinal: 5000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
retrieve_classic(query, k=5): embed query → cos_sim → top-k. retrieve_graph(query, k=5): embed → top-k chunks → entités → 1-hop neighbors → chunks liés → dedup → rerank. Test auto sur les 145 QCM: quel mode trouve la bonne réponse dans le top-5?
<!-- SECTION:NOTES:END -->
