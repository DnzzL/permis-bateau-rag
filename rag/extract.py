"""
T1 — Extraction HTML + QCM
Parses lessons/*.html, reference/*.html, and learning-records/*.md
into a clean JSONL corpus + a separate QCM JSON array.
"""
import json
import re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "rag" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Topic mapping from lesson files ──────────────────────────────────
LESSON_TOPIC = {
    "0001": "vue-ensemble",
    "0002": "regles-route",
    "0003": "feux-navigation",
    "0004": "balisage-maritime",
    "0005": "meteo-vents",
    "0006": "securite-equipements",
    "0007": "reglementation",
    "0008": "mouillage-manoeuvres",
    "0009": "carte-navigation",
    "0010": "examen-blanc-cotier",
    "0011": "navigation-fluviale",
    "0012": "fluvial-reglementation-securite",
    "0013": "panneaux-fluviaux",
    "0014": "passage-ecluse",
    "0015": "examen-blanc-fluvial",
}

REF_TOPIC = {
    "regles-route": "regles-route",
    "feux": "feux-navigation",
    "balisage": "balisage-maritime",
    "meteo": "meteo-vents",
    "reglementation": "reglementation",
    "fluvial": "navigation-fluviale",
    "panneaux-fluviaux": "panneaux-fluviaux",
    "signaux-bateaux-fluviaux": "panneaux-fluviaux",
    "radio-vhf": "securite-equipements",
    "glossaire": "glossaire",
}

# ── HTML text extraction ─────────────────────────────────────────────

# Sentinel prefixed to every text fragment coming from an h1/h2/h3 tag, so the
# flat serialised text still carries its structure and `split_sections` can cut
# on real headings. \x02 (STX) never occurs in the corpus, so a line starting
# with it is unambiguously a heading.
HEADING_SENTINEL = "\x02"
_HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3}


class TextExtractor(HTMLParser):
    """Extract clean text from HTML, preserving paragraph/h2/h3 structure."""
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = False
        self._heading_level: int | None = None
        # `tr` is a block boundary: table rows are visual lines, so each row
        # must be emitted on its own line instead of being glued to the next
        # row (e.g. "Sud … Q(6)+LFl … Ouest … Q(9) …" on one line).
        self._block_tags = {"h2", "h3", "h4", "p", "li", "div", "br", "hr", "tr"}

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag in ("script", "style", "svg", "nav", "footer", "header"):
            self._skip = True
            return
        cls = attrs_d.get("class", "")
        if cls is not None and ("quiz-question" in cls or "exam-question" in cls):
            self._skip = True
            return
        if tag in self._block_tags and not self._skip:
            if self.parts and not self.parts[-1].endswith("\n"):
                self.parts.append("\n")
        if tag in _HEADING_TAGS and not self._skip:
            self._heading_level = _HEADING_TAGS[tag]

    def handle_endtag(self, tag):
        if tag in _HEADING_TAGS:
            self._heading_level = None
        if tag in ("script", "style", "svg", "nav", "footer", "header"):
            self._skip = False
            return
        if tag in self._block_tags and not self._skip:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        text = data.strip()
        if text:
            if self._heading_level is not None:
                text = f"{HEADING_SENTINEL}{self._heading_level}{HEADING_SENTINEL}{text}"
            self.parts.append(text + " ")

    def get_text(self) -> str:
        raw = "".join(self.parts)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r" {2,}", " ", raw)
        lines = [l.strip() for l in raw.split("\n")]
        lines = [l for l in lines if l]
        return "\n".join(_order_cardinal_feux(lines))


# Glyphes de forme des bouées cardinales (marqueurs de colonne visuelle).
_SHAPE_GLYPH_PREFIX = ("▲", "▼", "⟡", "⟣", "◇", "▢", "▣", "⬢", "⬡", "●", "◯", "△", "▽", "✦", "✧", "⧖")


def _order_cardinal_feux(lines: list[str]) -> list[str]:
    """Re-order compact multi-column cards so each cardinal reads fully in
    visual order (marker → danger → passer → feu → shape) instead of the DOM
    order that interleaves column lines.

    The HTML source of e.g. lessons/0004-balisage-maritime.html emits each
    card as: marker, danger, passer, shape, feu. The shape line sits between
    the "passer" line and the "Feu :" line, so the serialised text ended with
    "…Feu : Q(6)+LFl — 6+1 long\n⬅️ OUEST …": the feu of one cardinal abuts
    the NEXT cardinal's marker with no separator, which misattributes the feu
    inside a chunk (chunk 7 of the balisage lesson). Hoisting the "Feu :"
    line just above its shape line puts a full clause between a card's feu and
    the following card's marker, and keeps marker → danger → passer → feu
    contiguous.

    The rule is deliberately local: it only fires when a "Feu :" line is
    immediately preceded by a shape-glyph line — a pattern that occurs nowhere
    else in the corpus (verified by probing every extracted document) — so all
    other lessons and reference sheets are left untouched.
    """
    out = list(lines)
    for i in range(1, len(out)):
        if out[i].startswith("Feu :") and out[i - 1].startswith(_SHAPE_GLYPH_PREFIX):
            out[i - 1], out[i] = out[i], out[i - 1]
    return out


# ── Section splitting ────────────────────────────────────────────────

_SENTINEL_RE = re.compile(re.escape(HEADING_SENTINEL) + r"(\d)" + re.escape(HEADING_SENTINEL))


def strip_sentinels(text: str) -> str:
    """Remove heading sentinels, restoring plain readable text."""
    return _SENTINEL_RE.sub("", text)


def split_sections(text: str) -> list[dict]:
    """Cut sentinel-tagged text into sections, one per h1/h2/h3.

    Returns [{"heading": "Doc title / Section / Sub-section", "text": body}].
    The heading path is the stack of enclosing headings, so a chunk carries its
    own context ("Balisage maritime / Marques cardinales") instead of appearing
    as an anonymous slab of words to the embedder.

    Text appearing before the first heading becomes a section with an empty
    heading; a heading with no body is dropped (it only feeds the path of the
    sections nested under it).
    """
    sections: list[dict] = []
    stack: list[str] = []  # heading titles, index 0 = level 1
    body: list[str] = []

    def flush():
        joined = "\n".join(body).strip()
        if joined:
            sections.append({"heading": " / ".join(t for t in stack if t), "text": joined})
        body.clear()

    for line in text.split("\n"):
        m = _SENTINEL_RE.match(line)
        if not m:
            body.append(strip_sentinels(line))
            continue
        flush()
        level = int(m.group(1))
        title = strip_sentinels(line).strip()
        # Truncate the stack to this level, then set it (a level can be skipped,
        # e.g. h1 → h3, so pad rather than assume contiguity).
        del stack[level - 1:]
        while len(stack) < level - 1:
            stack.append("")
        stack.append(title)
    flush()
    return sections


def _strip_tags(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text).strip()


def extract_quizzes(html: str) -> list[dict]:
    """Find all quiz-question and exam-question divs, extract structured QCM.
    Uses regex-based parsing to avoid external dependencies."""
    quizzes = []

    # Find opening tags of quiz/exam divs
    tag_pattern = re.compile(
        r'<div\s+class="((?:quiz|exam)-question)"([^>]*)>',
        re.DOTALL,
    )

    for tag_match in tag_pattern.finditer(html):
        attrs_str = tag_match.group(2)
        tag_end = tag_match.end()

        # Extract attributes independently (order-independent)
        correct_m = re.search(r'data-correct="([^"]*)"', attrs_str)
        feedback_m = re.search(r'data-feedback="([^"]*)"', attrs_str)
        topic_m = re.search(r'data-topic="([^"]*)"', attrs_str)

        if not correct_m:
            continue
        correct = correct_m.group(1).strip()
        feedback = feedback_m.group(1).strip() if feedback_m else ""
        topic = topic_m.group(1).strip() if topic_m else None

        # Find matching closing </div> by counting div depth
        inner, _ = _extract_div_inner(html, tag_end)
        if not inner:
            continue

        # Extract question text from <p> tag
        q_match = re.search(r"<p[^>]*>(.*?)</p>", inner, re.DOTALL)
        question = _strip_tags(q_match.group(1)) if q_match else ""
        question = re.sub(r"^\d+[\.\s—\-]+\s*", "", question)
        if not question:
            continue

        # Extract options from <li> tags
        options = [_strip_tags(li) for li in re.findall(r"<li[^>]*>(.*?)</li>", inner, re.DOTALL)]
        if not options:
            continue

        try:
            correct_index = int(correct.split(",")[0])
        except (ValueError, IndexError):
            continue

        quizzes.append({
            "question": question,
            "options": options,
            "correct_index": correct_index,
            "feedback": feedback,
            "topic": topic,
        })

    return quizzes


def _extract_div_inner(html: str, start: int) -> tuple[str, int]:
    """Given the position right after a <div ...> opening tag, extract inner
    content up to the matching </div>, handling nested divs."""
    depth = 1
    i = start
    while i < len(html) and depth > 0:
        # Look for next <div or </div
        next_open = html.find("<div", i)
        next_close = html.find("</div>", i)
        if next_close == -1:
            break
        # If there's an opening before the closing, increment depth
        if next_open != -1 and next_open < next_close:
            depth += 1
            i = html.find(">", next_open) + 1
        else:
            depth -= 1
            if depth == 0:
                return html[start:next_close], next_close + len("</div>")
            i = next_close + len("</div>")
    return "", start


# ── Main extraction ──────────────────────────────────────────────────

def extract_all():
    documents: list[dict] = []
    quizzes: list[dict] = []

    # ── Lessons ──
    lessons_dir = ROOT / "lessons"
    for f in sorted(lessons_dir.glob("*.html")):
        stem = f.stem  # e.g. "0002-regles-route-priorites"
        lesson_id = stem[:4]
        topic = LESSON_TOPIC.get(lesson_id, "divers")
        html = f.read_text(encoding="utf-8")
        extractor = TextExtractor()
        extractor.feed(html)
        tagged = extractor.get_text()
        text = strip_sentinels(tagged)
        if text.strip():
            documents.append({
                "source": f"lessons/{f.name}",
                "type": "lesson",
                "topic": topic,
                "text": text,
                "sections": split_sections(tagged),
            })
        # Extract quizzes
        qs = extract_quizzes(html)
        for q in qs:
            q["source"] = f"lessons/{f.name}"
            q["lesson_topic"] = topic
        quizzes.extend(qs)

    # ── Reference sheets ──
    ref_dir = ROOT / "reference"
    for f in sorted(ref_dir.glob("*.html")):
        stem = f.stem  # e.g. "balisage"
        topic = REF_TOPIC.get(stem, "divers")
        html = f.read_text(encoding="utf-8")
        extractor = TextExtractor()
        extractor.feed(html)
        tagged = extractor.get_text()
        text = strip_sentinels(tagged)
        if text.strip():
            documents.append({
                "source": f"reference/{f.name}",
                "type": "reference",
                "topic": topic,
                "text": text,
                "sections": split_sections(tagged),
            })

    # ── Learning records (Markdown) ──
    lr_dir = ROOT / "learning-records"
    for f in sorted(lr_dir.glob("*.md")):
        markdown = f.read_text(encoding="utf-8")
        # Infer topic from content keywords
        topic = "divers"
        kw_topics = [
            # Order matters: most specific first
            ("examen blanc", "examen-blanc-cotier"),
            ("examen blanc fluvial", "examen-blanc-fluvial"),
            ("tronc commun", "vue-ensemble"),
            ("règles de route", "regles-route"),
            ("regles de route", "regles-route"),
            ("feux de navigation", "feux-navigation"),
            ("feux-navigation", "feux-navigation"),
            ("balisage maritime", "balisage-maritime"),
            ("balisage-maritime", "balisage-maritime"),
            ("météo", "meteo-vents"),
            ("meteo", "meteo-vents"),
            ("sécurité", "securite-equipements"),
            ("securite", "securite-equipements"),
            ("mouillage", "mouillage-manoeuvres"),
            ("carte", "carte-navigation"),
            ("réglementation", "reglementation"),
            ("reglementation", "reglementation"),
            ("fluvial", "navigation-fluviale"),
            ("écluse", "passage-ecluse"),
            ("panneaux", "panneaux-fluviaux"),
            ("tronc commun", "vue-ensemble"),
        ]
        lower = markdown.lower()
        for kw, t in kw_topics:
            if kw in lower:
                topic = t
                break
        documents.append({
            "source": f"learning-records/{f.name}",
            "type": "learning-record",
            "topic": topic,
            "text": markdown,
            # Les learning-records n'ont qu'un titre `#` et aucun `##` : pas de
            # sections exploitables, embed.py retombe sur la fenêtre glissante.
            "sections": [],
        })

    return documents, quizzes


if __name__ == "__main__":
    try:
        docs, qcms = extract_all()
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        raise SystemExit(1) from e

    # Write corpus.jsonl
    corpus_path = OUT_DIR / "corpus.jsonl"
    try:
        with open(corpus_path, "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"❌ Failed to write {corpus_path}: {e}")
        raise SystemExit(1) from e

    # Write qcm.json
    qcm_path = OUT_DIR / "qcm.json"
    try:
        with open(qcm_path, "w", encoding="utf-8") as f:
            json.dump(qcms, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"❌ Failed to write {qcm_path}: {e}")
        raise SystemExit(1) from e

    # Stats
    total_chars = sum(len(d["text"]) for d in docs)
    print(f"✅ Extracted {len(docs)} documents ({total_chars:,} chars)")
    print(f"✅ Extracted {len(qcms)} QCM questions")
    print(f"   → {corpus_path}")
    print(f"   → {qcm_path}")

    # Topic breakdown
    from collections import Counter
    n_sections = sum(len(d.get("sections") or []) for d in docs)
    print(f"   {n_sections} sections (h1/h2/h3) across "
          f"{sum(1 for d in docs if d.get('sections'))} documents")

    topic_counts = Counter(d["topic"] for d in docs)
    print("\nTopics:")
    for t, c in topic_counts.most_common():
        print(f"  {t}: {c} docs")
