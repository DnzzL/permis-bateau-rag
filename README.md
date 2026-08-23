# ⛵ Permis Bateau RAG

Chatbot RAG (Retrieval-Augmented Generation) pour réviser l'examen du **permis bateau côtier & fluvial** en France, entraîné sur un corpus personnel de cours, fiches et QCM.

Pose une question sur les règles de route, les feux, le balisage, la VHF, les écluses… et le chatbot répond avec des **sources citées**, ou tire un **QCM aléatoire** avec correction expliquée.

---

## ✨ Fonctionnalités

| Mode | Description |
| --- | --- |
| `chat` | Question → retrieval vectoriel → réponse streamée avec sources |
| `quiz` | QCM aléatoire du corpus (ou filtré par thème) avec correction détaillée |
| `benchmark` | Mesure la couverture du retrieval et la pertinence des réponses |

- **Retrieval vectoriel** : similarité cosinus sur embeddings Voyage, chunks découpés par section (h1/h2/h3) et préfixés de leur chemin de titres
- **Sources citées** à chaque réponse (leçon / fiche / note)
- **Détection hors-sujet** : refuse poliment les questions sans rapport avec la navigation
- Streaming des réponses

## 🏗️ Architecture

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ T1       │   │ T2       │   │ T4       │   │ T5       │
│ extract  │→  │ embed    │→  │ retrieve │→  │ rag (CLI)│
│ HTML/MD  │   │ Voyage + │   │ cos_sim  │   │ chat/quiz│
│ → JSONL  │   │ DuckDB   │   │ top-k    │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

Toutes les étapes produisent/consomment une base DuckDB unique (`rag/permis.duckdb`) avec 2 tables : `documents`, `qcm`.

- **Extraction** (`extract.py`) : parseur zéro-dépendance (stdlib `html.parser`) → `corpus.jsonl` + `qcm.json`
- **Embedding** (`embed.py`) : [Voyage AI](https://voyageai.com) `voyage-3-lite` (512 dims). **Découpage par section** : une section h1/h2/h3 = un chunk, fusionnée sous 60 mots, re-découpée en fenêtre glissante (400/50) seulement si elle dépasse 400 mots — une frontière de chunk n'est jamais au milieu d'un tableau ou d'une carte de balise. Chaque chunk est préfixé de son chemin de titres (« Balisage Maritime / Marques cardinales »)
- **Retrieval** (`retrieve.py`) : cos_sim sur tous les chunks → top-k
- **Chatbot** (`rag.py`) : orchestration retrieval → contexte → Mistral (streaming)

## 🚀 Démarrage rapide

### Prérequis

- Python ≥ 3.12 (projet géré avec [uv](https://docs.astral.sh/uv/))
- Clés API : [Voyage AI](https://dashboard.voyageai.com) et [Mistral](https://console.mistral.ai)

### Installation

```bash
cd rag
uv sync                    # installe les dépendances dans .venv/
cp .env.example .env       # puis remplissez vos clés
```

Variables d'environnement (fichier `.env` à la racine du projet ou dans `rag/`) :

| Variable | Défaut | Description |
| --- | --- | --- |
| `VOYAGE_API_KEY` | — | Clé API Voyage AI (embeddings) |
| `VOYAGE_MODEL` | `voyage-3-lite` | Modèle d'embedding (512 dims) |
| `MISTRAL_API_KEY` | — | Clé API Mistral (extraction + chat) |
| `MISTRAL_MODEL` | `mistral-small-latest` | Modèle de chat |

### Utilisation

```bash
# Chat
.venv/bin/python rag.py chat "Qui est prioritaire entre deux voiliers ?"

# QCM aléatoire
.venv/bin/python rag.py quiz

# QCM sur un thème précis
.venv/bin/python rag.py quiz --topic feux

# Benchmark QCM : couverture + pertinence (60 questions, graine fixe)
.venv/bin/python benchmark.py

# Benchmark chatbot : 24 questions composites multi-sources
.venv/bin/python benchmark_composite.py
```

## 🔄 Reconstruire la base depuis zéro

Si la base DuckDB n'existe pas ou que vous voulez la régénérer avec un autre corpus :

```bash
cd rag
.venv/bin/python extract.py   # 1. corpus.jsonl + qcm.json depuis lessons/, reference/, learning-records/
.venv/bin/python embed.py     # 2. chunks + embeddings Voyage → DuckDB (coût ≈ gratuit)
```

Deux étapes suffisent : la reconstruction complète ne fait aucun appel facturé au-delà des embeddings Voyage.

## 📁 Structure

```
permis bateau/
├── lessons/           # 15 leçons HTML (tronc commun, côtier, fluvial, examens blancs)
├── reference/         # 19 fiches HTML (feux, balisage, VHF, signaux, CE, trafic, carte, détresse…)
├── learning-records/  # 19 notes de révision Markdown
├── backlog/           # suivi de projet (Backlog.md)
├── REFERENCE-AUDIT.md # audit vs sources officielles (exhaustivité + justesse)
├── QCM-AUDIT.md       # audit de justesse des 165 QCM
├── evals/             # snapshots de benchmark (régression)
└── rag/
    ├── extract.py     # T1 — parsing du corpus
    ├── embed.py       # T2 — chunking par section + embeddings + DuckDB
    ├── retrieve.py    # T4 — retrieval vectoriel
    ├── rag.py         # T5 — chatbot CLI
    ├── benchmark.py   # Benchmark QCM (couverture/pertinence)
    ├── benchmark_composite.py  # Benchmark chatbot (questions multi-sources)
    └── data/          # artefacts générés (ignorés par git)
```

## 📊 Résultats du benchmark

Benchmark étendu : **60 questions** (5 manuelles + échantillon stratifié des 165 QCM, graine fixe 42) + 10 pièges hors-domaine. Le panel QCM est volontairement dur (détails chiffrés, réponses courtes) :

| Métrique | Résultat |
| --- | --- |
| Bonne réponse couverte en top-1 | 80 % |
| Bonne réponse couverte en top-3 | **88 %** (91 % en top-9, le budget servi au chatbot) |
| Couverture conceptuelle des réponses | ~69 % (proxy mots-clés volontairement conservateur) |
| Réponses complètes (tous les concepts) | ~9/60 — des réponses correctes courtes scoreront rarement 100 % |
| Refus hors-domaine (10 pièges, sans contexte) | ~9-10/10 |

La couverture vérifie que la **bonne réponse QCM est couverte par le contenu des top-k** (proxy : substring ou rappel ≥ 50 % des tokens significatifs — les QCM reformulent les leçons). Les fiches de détail (`carte-marine.html`, `signaux-detresse.html`…) sont désormais top-1 sur leurs sujets.

Spot-checks manuels des réponses (mille nautique = 1852 m, latitude sur les bords verticaux, sonde soulignée = découvrante…) : **réponses factuellement exactes**. Le scoring mots-clés sous-estime la qualité réelle. La pertinence varie de ±3 pts entre runs (non-déterminisme LLM) — d'où le seuil de 5 pts du `--check`.

**Régression** : `rag/benchmark.py --snapshot` écrit `evals/report-<date>.json`, `--baseline` fige la référence, `--check` échoue (code 1) si pertinence ou top-3 régresse de plus de 5 points — à brancher en CI.

### Benchmark chatbot (questions composites)

Le benchmark QCM ne mesure pas l'usage réel : une question de QCM se répond depuis **une** section. `benchmark_composite.py` évalue 24 questions multi-sources du type « Mistral force 7 demain, bateau catégorie C, sortie en zone 2 : je sors ? », chacune avec ses sources requises et ses faits attendus définis avant tout retrieval :

| Métrique (top-9) | Résultat |
| --- | --- |
| Rappel des sources requises | 93 % |
| Sources distinctes dans le contexte | 5,0 |
| Faits attendus présents dans la réponse | 73-77 % |

⚠️ **Bruit de mesure** : à `temperature 0.2`, deux exécutions identiques s'écartent de ±6,3 pt sur la couverture factuelle (mesuré : 73,3 %, puis 77,2 % et 77,4 %). Ne rien conclure sous ~7 pt d'écart.

### Pourquoi pas de graphe de connaissances

Un GraphRAG a été implémenté (extraction Mistral par chunk → 1 481 entités, 2 055 relations, expansion 1-hop + rerank), mesuré, puis **retiré**. Il n'apportait rien, sur deux protocoles indépendants :

| | classic | graph | graph « diversité d'entités » |
| --- | --- | --- | --- |
| QCM, couverture top-k (60 q.) | 80 / 88 / 92 % | identique au chunk près | — |
| Composite, rappel sources (24 q.) | 93,1 % | 92,0 % | 93,1 % |
| Composite, faits couverts | 73,3 % | 76,4 % | 76,3 % |

Le +3,1 pt du graphe est indistinguable du bruit : `t = 0,78`, IC95 `[-4,7 ; +11,0]`, 6 victoires / 4 défaites / 14 égalités — et deux runs de `classic` contre lui-même s'écartent de ±6,3 pt, soit **plus que l'avantage revendiqué**. Ce n'est pas un effet de saturation : à top-3 (69 %), top-4 (78 %) et top-6 (84 %), où il reste de la marge, les chiffres sont identiques.

Trois causes mesurées :

- **71 % des entités n'apparaissent que dans un seul chunk** (1 053 / 1 481) — elles ne relient rien.
- L'expansion 1-hop retenait **67 à 83 % du corpus** comme candidats : le graphe ne filtrait pas, il resélectionnait.
- Les entités multi-chunks sont génériques (`vent`, `mouillage`, `écluse`, `VHF`) : elles relient tout à tout.

Deux bugs avaient aussi masqué le diagnostic : le bonus récompensait les chunks *seed* (qui partagent 100 % de leurs entités avec eux-mêmes), et son plafond de 0,30 valait **66 rangs** d'écart de `cos_sim` — il écrasait la similarité vectorielle au lieu de la nuancer. Corrigés, le graphe devenait strictement équivalent au retrieval vectoriel.

Un GraphRAG paie sur un corpus grand, à entités denses et récurrentes, pour des questions à sauts implicites. Ce corpus est petit (206 chunks), plat et à questions quasi mono-section : le vectoriel seul y est déjà quasi optimal. Le code reste dans l'historique git (`rag/graph.py`, supprimé le 2026-08-23) si le corpus change de nature.

**Limite du protocole** : les 24 questions composites sont multi-sources mais pas vraiment multi-*hop* — elles nomment explicitement les domaines concernés, donc l'embedding trouve les deux sans saut implicite. Un jeu à sauts réellement implicites resterait à construire pour clore définitivement la question.

## 🌐 API HTTP & déploiement (Dokploy)

Le chatbot est exposé comme **API FastAPI** (`rag/api.py`) qui sert aussi le **front statique** (`web/index.html`) — architecture *single-origin* (un seul process, un seul port, pas de CORS) :

| Endpoint | Description |
| --- | --- |
| `GET /` | **Front statique** — chat minimal (page unique, sans build) |
| `GET /health` | État de la base (chunks, QCM) + modèle + limite de rate limiting |
| `POST /api/chat` | `{"question", "top_k"}` → `{answer, sources, model}` — `top_k` par défaut 9 (~1 300 mots de contexte) |

- **Rate limiting** basique par IP (fenêtre glissante en mémoire, `RATE_LIMIT_MAX`/`RATE_LIMIT_WINDOW`, défaut 15 req/60 s, `429` au-delà).
- **CORS** (optionnel) : inutile pour le front inclus (même origine) ; utile seulement si tu appelles l'API depuis un autre domaine. Origines via `CORS_ORIGINS` (défaut neutre : `http://localhost:5173,http://localhost:8000`).
- **Clés API** (`VOYAGE_API_KEY`, `MISTRAL_API_KEY`) : `.env` au runtime, jamais dans l'image (voir `.env.server.example`).
- **Base DuckDB commitée** (3,8 Mo) : copiée dans l'image → déploiement immédiat, aucun `scp`. Pour servir une base fraîche, monte-la en volume et surcharge `PERMIS_DB_PATH`.

**Déploiement** (`Dockerfile` + `docker-compose.yml`) : dans Dokploy, Application « Docker Compose » → ce repo, onglet Environment : `VOYAGE_API_KEY`, `MISTRAL_API_KEY` (et `CORS_ORIGINS` seulement si front externe). Rien d'autre : le front est servi à `/` et l'API à `/api/chat` sur le même port.

## ⚖️ Licence

**Code** : [MIT](LICENSE) — libre d'utilisation, modification et redistribution.

**Données d'apprentissage** (`lessons/`, `reference/`, `learning-records/`) : corpus personnel de l'auteur. Reproduites ici pour permettre la reconstruction de la base — merci de ne pas les redistribuer séparément sans autorisation.

---

*Projet personnel — révision de l'examen du permis bateau côtier & fluvial (2026).*
