# ⛵ Permis Bateau RAG

Chatbot RAG (Retrieval-Augmented Generation) pour réviser l'examen du **permis bateau côtier & fluvial** en France, entraîné sur un corpus personnel de cours, fiches et QCM.

Pose une question sur les règles de route, les feux, le balisage, la VHF, les écluses… et le chatbot répond avec des **sources citées**, ou tire un **QCM aléatoire** avec correction expliquée.

---

## ✨ Fonctionnalités

| Mode | Description |
| --- | --- |
| `chat` | Question → retrieval (graphe par défaut, classique en fallback) → réponse streamée avec sources |
| `quiz` | QCM aléatoire du corpus (ou filtré par thème) avec correction détaillée |
| `benchmark` | Mesure la couverture du retrieval et la pertinence des réponses |

- **Retrieval hybride** : similarité cosinus (embeddings Voyage) **+** graphe de connaissances (entités + relations extraites par LLM)
- **Sources citées** à chaque réponse (leçon / fiche / note)
- **Détection hors-sujet** : refuse poliment les questions sans rapport avec la navigation
- Streaming des réponses

## 🏗️ Architecture

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ T1       │   │ T2       │   │ T3       │   │ T4       │   │ T5       │
│ extract  │→  │ embed    │→  │ graph    │→  │ retrieve │→  │ rag (CLI)│
│ HTML/MD  │   │ Voyage + │   │ entités  │   │ hybride  │   │ chat/quiz│
│ → JSONL  │   │ DuckDB   │   │ + rel.   │   │ rerank   │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

Toutes les étapes produisent/consomment une base DuckDB unique (`rag/permis.duckdb`) avec 5 tables : `documents`, `qcm`, `entities`, `relationships`, `document_entities`.

- **Extraction** (`extract.py`) : parseur zéro-dépendance (stdlib `html.parser`) → `corpus.jsonl` + `qcm.json`
- **Embedding** (`embed.py`) : [Voyage AI](https://voyageai.com) `voyage-3-lite` (512 dims), chunks de 400 mots avec 50 mots de recouvrement
- **Graphe** (`graph.py`) : extraction LLM [Mistral](https://mistral.ai) `mistral-small-latest` — 10 types d'entités, 8 types de relations, dédup par nom normalisé
- **Retrieval** (`retrieve.py`) : classique (cos_sim) vs graphe (seed → entités → voisins 1-hop → chunks liés → rerank avec bonus de partage d'entités)
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
# Chat (mode graphe par défaut)
.venv/bin/python rag.py chat "Qui est prioritaire entre deux voiliers ?"

# Chat en retrieval classique (fallback)
.venv/bin/python rag.py chat --no-graph "Comment annoncer une détresse à la VHF ?"

# QCM aléatoire
.venv/bin/python rag.py quiz

# QCM sur un thème précis
.venv/bin/python rag.py quiz --topic feux

# Benchmark couverture + pertinence (15 questions de référence)
.venv/bin/python benchmark.py
```

## 🔄 Reconstruire la base depuis zéro

Si la base DuckDB n'existe pas ou que vous voulez la régénérer avec un autre corpus :

```bash
cd rag
.venv/bin/python extract.py   # 1. corpus.jsonl + qcm.json depuis lessons/, reference/, learning-records/
.venv/bin/python embed.py     # 2. chunks + embeddings Voyage → DuckDB (coût ≈ gratuit)
.venv/bin/python graph.py     # 3. entités + relations Mistral → DuckDB (⚠️ facturé, ~80 appels)
```

Le graphe s'exécute chunk par chunk avec un checkpoint JSON (`rag/data/checkpoint_extractions.json`) : une interruption ne perd pas le travail, et `graph.py --rebuild` reconstruit la table à partir du checkpoint sans rappeler l'API.

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
    ├── embed.py       # T2 — embeddings + DuckDB
    ├── graph.py       # T3 — graphe de connaissances
    ├── retrieve.py    # T4 — retrieval hybride
    ├── rag.py         # T5 — chatbot CLI
    ├── benchmark.py   # Benchmark couverture/pertinence
    └── data/          # artefacts générés (ignorés par git)
```

## 📊 Résultats du benchmark

Benchmark étendu : **60 questions** (5 manuelles + échantillon stratifié des 165 QCM, graine fixe 42) + 10 pièges hors-domaine. Le panel QCM est volontairement dur (détails chiffrés, réponses courtes) :

| Métrique | Résultat |
| --- | --- |
| Bonne réponse couverte en top-1 | classic 80 % · graph 82 % |
| Bonne réponse couverte en top-3 | **classic 90 % · graph 92 %** |
| Couverture conceptuelle des réponses | ~67 % (proxy mots-clés volontairement conservateur) |
| Réponses complètes (tous les concepts) | ~9/60 — des réponses correctes courtes scoreront rarement 100 % |
| Refus hors-domaine (10 pièges, sans contexte) | ~9-10/10 |

La couverture vérifie que la **bonne réponse QCM est couverte par le contenu des top-k** (proxy : substring ou rappel ≥ 50 % des tokens significatifs — les QCM reformulent les leçons). Les fiches de détail (`carte-marine.html`, `signaux-detresse.html`…) sont désormais top-1 sur leurs sujets.

Spot-checks manuels des réponses (mille nautique = 1852 m, latitude sur les bords verticaux, sonde soulignée = découvrante…) : **réponses factuellement exactes**. Le scoring mots-clés sous-estime la qualité réelle. La pertinence varie de ±3 pts entre runs (non-déterminisme LLM) — d'où le seuil de 5 pts du `--check`.

**Régression** : `rag/benchmark.py --snapshot` écrit `evals/report-<date>.json`, `--baseline` fige la référence, `--check` échoue (code 1) si pertinence ou top-3 régresse de plus de 5 points — à brancher en CI.

Le mode graphe n'améliore pas le classement sémantique (corpus petit et bien structuré) mais **diversifie les sources** : il découvre des fiches de référence (`feux.html`, `signaux-bateaux-fluviaux.html`) que le retrieval classique rate.

## ⚖️ Licence

**Code** : [MIT](LICENSE) — libre d'utilisation, modification et redistribution.

**Données d'apprentissage** (`lessons/`, `reference/`, `learning-records/`) : corpus personnel de l'auteur. Reproduites ici pour permettre la reconstruction de la base — merci de ne pas les redistribuer séparément sans autorisation.

---

_Projet personnel — révision de l'examen du permis bateau côtier & fluvial (2026)._
