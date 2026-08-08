"""CLI entry point for the PDF RAG application.

Usage:
    python main.py ingest              # parse PDFs in data/pdfs, embed, load into Qdrant
    python main.py ask "your question" # ask a single question
    python main.py chat                # interactive Q&A loop
"""
import argparse
import sys

from src.config import settings
from src.rag_pipeline import RAGAnswer, RAGPipeline


def print_answer(result: RAGAnswer) -> None:
    print("\nAnswer:")
    print(result.answer)

    if result.found and result.citations:
        print("\nSources:")
        for c in result.citations:
            print(f"  - {c.doc_name} | Page {c.page_number} | similarity={c.score}")
            snippet = c.snippet.strip()
            if len(snippet) > 300:
                snippet = snippet[:300].rsplit(" ", 1)[0] + "..."
            print(f'    Retrieved Text: "{snippet}"')
    print()


def cmd_ingest(_args) -> None:
    pipeline = RAGPipeline(settings)
    count = pipeline.ingest()
    print(f"\nDone. Indexed {count} chunks.")


def cmd_ask(args) -> None:
    pipeline = RAGPipeline(settings)
    result = pipeline.query(args.question)
    print_answer(result)


def cmd_chat(_args) -> None:
    pipeline = RAGPipeline(settings)
    print("RAG PDF Q&A - type 'exit' to quit.\n")
    while True:
        try:
            question = input("Ask a question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        try:
            result = pipeline.query(question)
            print_answer(result)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {exc}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple RAG app over local PDFs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_ingest = subparsers.add_parser("ingest", help="Parse PDFs and load them into Qdrant.")
    p_ingest.set_defaults(func=cmd_ingest)

    p_ask = subparsers.add_parser("ask", help="Ask a single question.")
    p_ask.add_argument("question", type=str, help="The question to ask.")
    p_ask.set_defaults(func=cmd_ask)

    p_chat = subparsers.add_parser("chat", help="Interactive Q&A loop.")
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
