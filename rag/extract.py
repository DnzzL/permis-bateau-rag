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

class TextExtractor(HTMLParser):
    """Extract clean text from HTML, preserving paragraph/h2/h3 structure."""
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = False
        self._block_tags = {"h2", "h3", "h4", "p", "li", "div", "br", "hr"}

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

    def handle_endtag(self, tag):
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
            self.parts.append(text + " ")

    def get_text(self) -> str:
        raw = "".join(self.parts)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r" {2,}", " ", raw)
        lines = [l.strip() for l in raw.split("\n")]
        return "\n".join(l for l in lines if l)


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
        text = extractor.get_text()
        if text.strip():
            documents.append({
                "source": f"lessons/{f.name}",
                "type": "lesson",
                "topic": topic,
                "text": text,
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
        text = extractor.get_text()
        if text.strip():
            documents.append({
                "source": f"reference/{f.name}",
                "type": "reference",
                "topic": topic,
                "text": text,
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
    topic_counts = Counter(d["topic"] for d in docs)
    print("\nTopics:")
    for t, c in topic_counts.most_common():
        print(f"  {t}: {c} docs")
