import json
from pathlib import Path

from dotenv import load_dotenv

from app.config import get_settings
from app.db import SessionLocal
from app.llm.local_generation import LocalGenerator
from app.retrieval.hybrid import answer_question


def main() -> None:
    load_dotenv()
    settings = get_settings()
    golden_path = Path(__file__).with_name("golden.jsonl")
    rows = [
        json.loads(line)
        for line in golden_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    generator = LocalGenerator(settings)

    total = 0
    passed = 0
    with SessionLocal() as db:
        for row in rows:
            total += 1
            response = answer_question(
                db=db,
                question=row["question"],
                tenant_id=settings.rag_default_tenant_id,
                top_k=5,
                generator=generator,
            )
            requires_context = bool(row["requires_context"])
            ok = bool(response.sources) if requires_context else not response.sufficient_context
            passed += int(ok)
            print(
                json.dumps(
                    {
                        "id": row["id"],
                        "passed": ok,
                        "sufficient_context": response.sufficient_context,
                        "sources": len(response.sources),
                    },
                    ensure_ascii=False,
                )
            )

    print(
        json.dumps(
            {"total": total, "passed": passed, "pass_rate": passed / total if total else 0}
        )
    )


if __name__ == "__main__":
    main()
