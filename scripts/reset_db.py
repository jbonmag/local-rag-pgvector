import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from app.db import SessionLocal


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Reset RAG data tables.")
    parser.add_argument("--yes-i-know", action="store_true", help="Required safety flag.")
    args = parser.parse_args()
    if not args.yes_i_know:
        raise SystemExit("Refusing to reset tables without --yes-i-know.")

    with SessionLocal() as db:
        db.execute(
            text(
                """
                TRUNCATE feedback, retrieval_logs, chunk_embeddings, chunks,
                         document_versions, documents
                RESTART IDENTITY CASCADE
                """
            )
        )
        db.commit()
    print("RAG tables reset.")


if __name__ == "__main__":
    main()
