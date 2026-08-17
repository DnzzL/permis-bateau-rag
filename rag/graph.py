"""
T3 — Graphe de connaissances (graph.py)
Extracts entities + relationships from each chunk using Mistral,
normalizes them, and populates DuckDB tables:
  - entities(id, name, type, description)
  - relationships(source_id, target_id, relation, chunk_id)
  - document_entities(chunk_id, entity_id)

Entity types (boating domain):
  boat_type, navigation_light, mark, rule, situation, equipment,
  zone, signal, weather, concept

Relation types:
  identifies, applies_to, has_priority_over, requires, part_of,
  located_in, signals, regulated_by
"""
import json
import os
import sys
import time
from pathlib import Path

import duckdb
from mistralai.client import Mistral
from dotenv import load_dotenv

# Cherche .env dans rag/ ET dans le dossier parent du projet
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "permis.duckdb"

# Mistral config
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

ENTITY_TYPES = [
    "boat_type", "navigation_light", "mark", "rule", "situation",
    "equipment", "zone", "signal", "weather", "concept",
]

RELATION_TYPES = [
    "identifies", "applies_to", "has_priority_over", "requires",
    "part_of", "located_in", "signals", "regulated_by",
]

EXTRACTION_PROMPT = """Tu es un expert du permis bateau français (côtier et fluvial).
À partir du texte suivant, extrais les entités et relations pertinentes pour un
graphe de connaissances de révision.

RÈGLES STRICTES:
- Entités: uniquement des concepts du domaine nautique (types de bateaux, feux,
  balises, règles, situations, équipements, zones, signaux, vents, concepts).
  Pas de nombres, pas de mots génériques, pas de phrases.
- Chaque entité: name (nom court, singulier, sans article), type (une des
  valeurs listées), description (1 phrase max).
- Relations: entre DEUX entités déjà listées. relation_type (une des valeurs
  listées), source et target sont les noms exacts des entités.
- Ne force pas de relations si le texte n'en contient pas.
- Réponds UNIQUEMENT en JSON valide, sans commentaires ni markdown:
{"entities": [{"name": "...", "type": "...", "description": "..."}],
 "relations": [{"source": "...", "target": "...", "relation_type": "..."}]}

Types d'entités: {entity_types}
Types de relations: {relation_types}

TEXTE À ANALYSER:
---
{chunk}
---"""


# ── Extraction via Mistral ───────────────────────────────────────────

def extract_from_chunk(client, chunk_text: str, chunk_id: int) -> dict:
    """Appel Mistral pour extraire entités + relations d'un chunk."""
    # Remplacement explicite (pas .format() : les accolades du JSON d'exemple
    # seraient interprétées comme des champs de format → KeyError).
    prompt = (
        EXTRACTION_PROMPT
        .replace("{chunk}", chunk_text)
        .replace("{entity_types}", ", ".join(ENTITY_TYPES))
        .replace("{relation_types}", ", ".join(RELATION_TYPES))
    )

    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": "Tu es un extracteur de graphe de connaissances précis."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=4000,
    )

    content = response.choices[0].message.content
    if content is None:
        return {"entities": [], "relations": []}
    # Nettoie d'éventuels fences markdown
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[1].lstrip("json\n")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  ⚠️ Chunk {chunk_id}: JSON invalide ({e}); skipping")
        return {"entities": [], "relations": []}

    # Filtre les types inconnus
    entities = [e for e in data.get("entities", [])
                if e.get("type") in ENTITY_TYPES and e.get("name")]
    relations = [r for r in data.get("relations", [])
                 if r.get("relation_type") in RELATION_TYPES]
    return {"entities": entities, "relations": relations}


# ── Normalisation / déduplication ────────────────────────────────────

def normalize_name(name: str) -> str:
    """Normalise un nom d'entité pour la dédup.

    - minuscules, sans accents, tirets/underscores → espaces
    - articles (le/la/les/l'/un/une) et prépositions (de/du/des/d'/à/au/aux)
      supprimés : "gilet_de_sauvetage" == "gilet_sauvetage"
    - singularisation de chaque mot
    """
    import unicodedata

    n = name.strip().lower()
    # Accents → ASCII
    n = unicodedata.normalize("NFD", n)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    # Séparateurs → espaces
    n = n.replace("_", " ").replace("-", " ").replace("'", " ").replace(".", " ")
    words = n.split()
    # Vire articles et prépositions
    stop = {"le", "la", "les", "l", "un", "une", "des", "de", "du", "d",
            "a", "au", "aux", "en", "et", "ou", "sur", "sous", "pour", "vers"}
    words = [w for w in words if w not in stop]
    # Singularisation de chaque mot
    for i, w in enumerate(words):
        if w.endswith("aux"):
            words[i] = w[:-3] + "al"
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            words[i] = w[:-1]
    return " ".join(words)


def build_graph(extractions: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Assemble entités dédup + relations résolues + lien chunk→entité."""
    # entities: norm_name -> {"name": canonical, "type": ..., "description": ...}
    entity_map: dict[str, dict] = {}
    relations_out: list[dict] = []
    doc_links: list[dict] = []

    for chunk_id, extraction in enumerate(extractions):
        local_ids: dict[str, str] = {}  # nom original -> norm

        for e in extraction["entities"]:
            norm = normalize_name(e["name"])
            if norm not in entity_map:
                entity_map[norm] = {
                    "key": norm,  # clé canonique (normalisée)
                    "name": e["name"].strip(),
                    "type": e["type"],
                    "description": e.get("description", ""),
                }
            local_ids[e["name"].strip().lower()] = norm

        # Résout les relations vers les entités normalisées
        for r in extraction["relations"]:
            src_key = r["source"].strip().lower()
            tgt_key = r["target"].strip().lower()
            src_norm = local_ids.get(src_key) or normalize_name(src_key)
            tgt_norm = local_ids.get(tgt_key) or normalize_name(tgt_key)
            if src_norm in entity_map and tgt_norm in entity_map:
                relations_out.append({
                    "source": src_norm,
                    "target": tgt_norm,
                    "relation": r["relation_type"],
                    "chunk_id": chunk_id,
                })
            else:
                print(f"  ⚠️ chunk {chunk_id}: relation {src_norm}→{tgt_norm} non résolue")

        # Liens chunk → entités
        for norm in local_ids.values():
            if norm in entity_map:
                doc_links.append({"chunk_id": chunk_id, "entity": norm})

    return list(entity_map.values()), relations_out, doc_links


# ── Main ─────────────────────────────────────────────────────────────

def write_graph(entities: list[dict], relations: list[dict], doc_links: list[dict]) -> None:
    """Écrit le graphe dans DuckDB (tables entities/relationships/document_entities)."""
    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS entities")
    con.execute("DROP TABLE IF EXISTS relationships")
    con.execute("DROP TABLE IF EXISTS document_entities")
    con.execute("""
        CREATE TABLE entities (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            type VARCHAR,
            description VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE relationships (
            source_id INTEGER,
            target_id INTEGER,
            relation VARCHAR,
            chunk_id INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE document_entities (
            chunk_id INTEGER,
            entity_id INTEGER
        )
    """)

    # Insert entities
    entity_id: dict[str, int] = {}
    for i, e in enumerate(entities):
        entity_id[e["key"]] = i
        con.execute(
            "INSERT INTO entities VALUES (?, ?, ?, ?)",
            (i, e["name"], e["type"], e["description"]),
        )

    # Insert relationships (résout nom → id)
    for r in relations:
        src = entity_id.get(r["source"])
        tgt = entity_id.get(r["target"])
        if src is not None and tgt is not None:
            con.execute(
                "INSERT INTO relationships VALUES (?, ?, ?, ?)",
                (src, tgt, r["relation"], r["chunk_id"]),
            )

    # Insert doc links
    for link in doc_links:
        eid = entity_id.get(link["entity"])
        if eid is not None:
            con.execute(
                "INSERT INTO document_entities VALUES (?, ?)",
                (link["chunk_id"], eid),
            )

    # Stats finales
    row_ent = con.execute("SELECT COUNT(*) FROM entities").fetchone()
    row_rel = con.execute("SELECT COUNT(*) FROM relationships").fetchone()
    row_dl = con.execute("SELECT COUNT(*) FROM document_entities").fetchone()
    n_ent = row_ent[0] if row_ent else 0
    n_rel = row_rel[0] if row_rel else 0
    n_dl = row_dl[0] if row_dl else 0
    print(f"\n✅ Graph written to {DB_PATH}")
    print(f"   entities: {n_ent}, relationships: {n_rel}, doc_links: {n_dl}")

    # Top types
    types = con.execute(
        "SELECT type, COUNT(*) FROM entities GROUP BY type ORDER BY 2 DESC"
    ).fetchall()
    print("\nEntity types:")
    for t, c in types:
        print(f"  {t}: {c}")

    # Relations les plus fréquentes
    rels = con.execute(
        "SELECT relation, COUNT(*) FROM relationships GROUP BY relation ORDER BY 2 DESC"
    ).fetchall()
    print("\nRelation types:")
    for t, c in rels:
        print(f"  {t}: {c}")

    con.close()


def main():
    # Mode rebuild : reconstruit le graphe depuis le checkpoint sans appeler l'API
    if "--rebuild" in sys.argv:
        checkpoint_path = ROOT / "data" / "checkpoint_extractions.json"
        if not checkpoint_path.exists():
            raise SystemExit("❌ Pas de checkpoint — lance l'extraction d'abord.")
        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise SystemExit(f"❌ Checkpoint illisible: {e}")
        n = max((item["chunk_id"] for item in saved), default=-1) + 1
        extractions: list[dict | None] = [None] * n
        for item in saved:
            extractions[item["chunk_id"]] = item.get("extraction") or {"entities": [], "relations": []}
        print(f"Rebuild depuis checkpoint : {len(saved)} chunks")
        entities, relations, doc_links = build_graph(
            [e if e is not None else {"entities": [], "relations": []} for e in extractions]
        )
        print(f"Normalisé: {len(entities)} entités uniques, {len(relations)} relations, "
              f"{len(doc_links)} liens chunk→entité")
        write_graph(entities, relations, doc_links)
        return

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("❌ MISTRAL_API_KEY not set. Export it and retry.")
        raise SystemExit(1)

    client = Mistral(api_key=api_key)

    # 1. Lire les chunks depuis DuckDB
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute("SELECT id, chunk_text FROM documents ORDER BY id").fetchall()
    con.close()
    if not rows:
        raise SystemExit("❌ No chunks in DB — run T2 (embed.py) first.")
    print(f"Loaded {len(rows)} chunks")

    # 2. Extraction par chunk avec checkpoint JSON (reprise après interruption)
    checkpoint_path = ROOT / "data" / "checkpoint_extractions.json"
    extractions: list[dict | None] = [None] * len(rows)
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, json.JSONDecodeError):
            saved = []
            print("⚠️ Checkpoint illisible — extraction depuis zéro")
        for item in saved:
            if "chunk_id" in item and 0 <= item["chunk_id"] < len(rows):
                extractions[item["chunk_id"]] = item.get("extraction") or {"entities": [], "relations": []}
        done = sum(1 for e in extractions if e is not None)
        print(f"ℹ️ Checkpoint trouvé : {done}/{len(rows)} chunks déjà traités")

    for idx, (chunk_id, text) in enumerate(rows):
        if extractions[idx] is not None:
            continue
        print(f"[{idx+1}/{len(rows)}] chunk {chunk_id}...", end=" ", flush=True)
        try:
            extraction = extract_from_chunk(client, text, chunk_id)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            extraction = {"entities": [], "relations": []}
        print(f"({len(extraction['entities'])} entités, {len(extraction['relations'])} relations)")
        extractions[idx] = extraction
        # Sauvegarde incrémentale
        try:
            checkpoint_path.parent.mkdir(exist_ok=True)
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(
                    [{"chunk_id": i, "extraction": e} for i, e in enumerate(extractions) if e is not None],
                    f, ensure_ascii=False, indent=1,
                )
        except OSError as e:
            print(f"⚠️ Écriture checkpoint impossible: {e}")
        time.sleep(0.1)  # rate limiting doux

    # 3. Normalisation
    # Les None résiduels (chunks jamais traités) deviennent des extractions vides
    # tout en gardant l'alignement des index pour les chunk_id.
    entities, relations, doc_links = build_graph(
        [e if e is not None else {"entities": [], "relations": []} for e in extractions]
    )
    print(f"\nNormalisé: {len(entities)} entités uniques, {len(relations)} relations, "
          f"{len(doc_links)} liens chunk→entité")

    # 4. Écriture dans DuckDB
    write_graph(entities, relations, doc_links)


if __name__ == "__main__":
    main()
