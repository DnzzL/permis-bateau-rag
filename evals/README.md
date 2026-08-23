# Évaluations du benchmark RAG « permis bateau »

Ce dossier contient les rapports des deux benchmarks (le pipeline
embed/retrieve n'est pas touché) :

- `rag/benchmark.py` — **QCM** : couverture, pertinence, refus hors-domaine.
  Snapshots `report-<date>.json`, référence `baseline.json`.
- `rag/benchmark_composite.py` — **chatbot** : 24 questions multi-sources
  (`composite.json`), rapport `composite-report.json`. Le QCM ne mesure pas
  l'usage réel, une question de QCM se répondant depuis une seule section.

## Les 3 métriques

### 1. Couverture retrieval (top-1 / top-3 / top-5)

Pour chacune des **60 questions** de l'échantillon, on sait *a priori* quelle
leçon/fiche contient la réponse (le `source` du QCM pour les questions QCM,
un fragment de chemin pour les 5 questions manuelles). On vérifie qu'un chunk
de cette source apparaît dans le top-1 / top-3 / top-5 du classement.
`--top-k N` ajoute le palier réellement servi au chatbot (défaut 9) ; les
paliers 1/3/5 restent rapportés pour rester comparables aux snapshots
antérieurs. C'est le mode `--no-llm` (pas d'appel LLM, pas de clé Mistral
requise).

### 2. Pertinence des réponses (LLM)

Chaque question est envoyée au LLM avec le contexte du retrieval dans le
top-k (défaut 9, soit ~1 300 mots — le budget servi par l'API). Pour chaque question, des **mots-clés attendus** sont définis :

- 5 questions manuelles pédagogiques : mots-clés écrits à la main ;
- questions issues du QCM : mots-clés **dérivés mécaniquement** de la bonne
  réponse officielle (`options[correct_index]`) + du `feedback` : tokens
  `[a-z0-9]+` normalisés (minuscules, sans accents), longueur ≥ 4 caractères,
  hors stopwords français courants.

Le score de pertinence = proportion moyenne de mots-clés présents dans la
réponse. La dérivation étant mécanique, les listes peuvent être longues
(≈ 10 à 20 mots) : le barème « réponses complètes (tous les mots-clés) » est
donc très strict et peut rester proche de zéro — c'est attendu, ce n'est pas
une régression. On lit en priorité le **score moyen %**.

### 3. Refus hors-domaine (LLM, sans contexte)

10 questions clairement hors du domaine (cuisine, sport, histoire, cinéma,
géographie…) sont envoyées au LLM **sans contexte de retrieval**, avec un
prompt système renforcé qui demande de refuser poliment. La détection du
refus est une **heuristique** : la réponse normalisée doit contenir un des
mots-clés de `REFUSAL_KEYWORDS` (`hors du domaine`, `je ne peux pas`, `ne
concerne pas`, `désolé`, `suis conçu`, …, + extensions observées en pratique
comme « je ne peux répondre qu'à… », « veuillez consulter… »). Impossible de
garantir 100 % de fiabilité : en cas de doute, l'afficheur console montre un
extrait de la réponse sur un non-refus détecté.

## Graine (`question_seed`)

L'échantillon de 60 questions est reconstruit à chaque run par un tirage
**déterministe** : `random.Random(seed)` avec `--seed N` (défaut : `42`).
Structure : 5 manuelles + 1 par topic non-null (14 topics) + 41 tirées parmi
les 85 QCM sans topic. Anti-doublon : Jaccard ≥ 0,6 sur les tokens normalisés
entre une question candidate et une question déjà retenue → écartée.
La graine est enregistrée dans chaque rapport : même seed = même échantillon.

## Fichiers

| Fichier | Contenu |
| --- | --- |
| `report-YYYYMMDD.json` | Rapport du dernier run `--snapshot` |
| `baseline.json` | Référence pour `--check` (écrit par `--baseline`) |

## Comment relancer

```bash
cd rag
# Couverture seule (rapide, pas de LLM)
.venv/bin/python benchmark.py --no-llm
# Run complet (LLM, plusieurs minutes) + snapshot + baseline
.venv/bin/python benchmark.py --snapshot --baseline
# Contrôle de régression en CI (échec = code 1 si pertinence ou top-3 baisse > 5 pts)
.venv/bin/python benchmark.py --check
```

Note : `--snapshot` / `--baseline` / `--check` exigent le mode LLM complet ;
si une 429 (rate limit) survient, le script réessaie avec un backoff
exponentiel (10 s → 30 s → 80 s).

## Ajouter une question

Dans `rag/benchmark.py` :

- **Question du domaine** : l'échantillon se construit tout seul depuis la
  table `qcm` (stratification par topic + tirage sans topic). Pour forcer une
  question précise, ajoutez-la aux `MANUAL_QUESTIONS` (question, mots-clés
  attendus, fragment de source attendu, origine `manuel`).
- **Question hors domaine** : ajoutez-la à `OFF_TOPIC_QUESTIONS` (le total
  affiché s'adapte automatiquement au nombre d'éléments de la liste).

Puis relancez `--no-llm` puis `--snapshot --baseline` pour régénérer la
référence. Si vous changez la graine, les 60 questions changent : l'ancien
`baseline.json` n'est plus comparable — régénérez-le.
