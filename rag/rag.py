"""
T5 — Chatbot CLI (rag.py)

Modes :
  chat  : question → retrieval (graph par défaut, classic en fallback)
          → contexte → réponse Mistral streamée avec sources
  quiz  : QCM aléatoire du corpus avec correction détaillée

Usage :
  .venv/bin/python rag.py chat "Qui est prioritaire entre deux voiliers ?"
  .venv/bin/python rag.py chat --no-graph "Quelle est la VHF d'appel ?"
  .venv/bin/python rag.py quiz
  .venv/bin/python rag.py quiz --topic feux
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path

import duckdb
from dotenv import load_dotenv
from mistralai.client import Mistral

from retrieve import DB_PATH, retrieve_classic, retrieve_graph
from prompts import SYSTEM_PROMPT

ROOT = Path(__file__).resolve().parent
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# ── Sources ──────────────────────────────────────────────────────────

def format_sources(con: duckdb.DuckDBPyConnection, hits: list[tuple[int, float]]) -> str:
    """Contexte compact à partir des chunks retrouvés + chemins sources."""
    parts = []
    for cid, score in hits:
        row = con.execute(
            "SELECT source, chunk_text FROM documents WHERE id = ?", [cid]
        ).fetchone()
        if row:
            src, text = row
            parts.append(f"[Source {src} — score {score:.2f}]\n{text}")
    return "\n\n".join(parts)


# ── Chat ─────────────────────────────────────────────────────────────

def chat(con: duckdb.DuckDBPyConnection, question: str, use_graph: bool = True, top_k: int = 4) -> None:
    client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))
    if use_graph:
        hits = retrieve_graph(con, question, top_k)
    else:
        hits = retrieve_classic(con, question, top_k)

    context = format_sources(con, hits)
    user_prompt = (
        f"CONTEXTE (extraits du cours permis bateau):\n{context}\n\n"
        f"QUESTION: {question}"
    )

    print("\n🤖 Réponse (streamée)...\n")
    stream = client.chat.stream(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    answer = ""
    for ev in stream:
        try:
            delta = ev.data.choices[0].delta.content
        except Exception:
            delta = None
        if delta is None:
            continue
        # Le SDK type le contenu comme str | List[ContentChunk] ; au runtime
        # c'est une str, mais on gère les deux cas.
        if isinstance(delta, str):
            chunk = delta
        else:
            chunk = "".join(getattr(part, "text", "") or "" for part in delta)
        answer += chunk
        print(chunk, end="", flush=True)
    print()

    print("\n📚 Sources utilisées :")
    for cid, score in hits:
        row = con.execute("SELECT source FROM documents WHERE id = ?", [cid]).fetchone()
        if row:
            print(f"  • {row[0]} (score {score:.2f})")


# ── Quiz ─────────────────────────────────────────────────────────────

def quiz(con: duckdb.DuckDBPyConnection, topic: str | None = None) -> None:
    if topic:
        rows = con.execute(
            "SELECT id, question, options, correct_index, feedback, topic, source "
            "FROM qcm WHERE topic = ? ORDER BY RANDOM() LIMIT 1",
            [topic],
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT id, question, options, correct_index, feedback, topic, source "
            "FROM qcm ORDER BY RANDOM() LIMIT 1"
        ).fetchall()
    if not rows:
        print(f"❌ Aucun QCM trouvé pour le thème « {topic} ».")
        topics = con.execute("SELECT DISTINCT topic FROM qcm WHERE topic IS NOT NULL").fetchall()
        print("Thèmes disponibles :", ", ".join(t[0] for t in topics))
        return

    qid, question, options, correct, feedback, qtopic, source = rows[0]
    letters = "ABCDEFGH"
    print("\n" + "=" * 60)
    print(f"📝 QCM ({qtopic or 'sans thème'})")
    print(question)
    for i, opt in enumerate(options):
        print(f"  {letters[i]}. {opt}")

    # Correction
    client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", ""))
    ans = input("\nTa réponse (A/B/C/D, Entrée pour voir la correction) : ").strip().upper()
    if ans and ans[0] in letters:
        user_idx = letters.index(ans[0])
        correct_letter = letters[correct]
        ok = user_idx == correct
        print(f"\n{'✅ Correct !' if ok else f'❌ Non — la bonne réponse est {correct_letter}'}")
        print(f"La réponse était : {correct_letter}. {options[correct]}")
    else:
        print(f"\nCorrection : {letters[correct]}. {options[correct]}")

    if feedback:
        print(f"\n💡 Explication : {feedback}")


# ── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Chatbot permis bateau (RAG)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_chat = sub.add_parser("chat", help="Pose une question au chatbot")
    p_chat.add_argument("question", help="La question à poser")
    p_chat.add_argument("--no-graph", action="store_true", help="Désactive le mode graphe (retrieval classique)")
    p_chat.add_argument("--top-k", type=int, default=4)

    p_quiz = sub.add_parser("quiz", help="QCM aléatoire")
    p_quiz.add_argument("--topic", help="Thème du QCM (ex: feux, balisage)")
    args = parser.parse_args()

    if not os.environ.get("MISTRAL_API_KEY"):
        print("❌ MISTRAL_API_KEY not set.")
        raise SystemExit(1)
    if not os.environ.get("VOYAGE_API_KEY"):
        print("❌ VOYAGE_API_KEY not set.")
        raise SystemExit(1)

    con = duckdb.connect(str(DB_PATH))
    if args.command == "chat":
        chat(con, args.question, use_graph=not args.no_graph, top_k=args.top_k)
    elif args.command == "quiz":
        quiz(con, args.topic)
    con.close()


if __name__ == "__main__":
    main()
