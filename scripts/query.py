import argparse

from dotenv import load_dotenv

from app.config import get_settings
from app.db import SessionLocal
from app.llm.local_generation import LocalGenerator
from app.retrieval.hybrid import answer_question


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Ask the local RAG system a question.")
    parser.add_argument("question")
    parser.add_argument("--tenant-id")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    settings = get_settings()
    tenant_id = args.tenant_id or settings.rag_default_tenant_id
    generator = LocalGenerator(settings)
    with SessionLocal() as db:
        response = answer_question(db, args.question, tenant_id, args.top_k, generator)
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
