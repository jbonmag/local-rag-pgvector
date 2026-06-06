from dotenv import load_dotenv

from app.config import get_settings
from app.db import SessionLocal
from app.ingestion.pipeline import ingest_local


def main() -> None:
    load_dotenv()
    settings = get_settings()
    with SessionLocal() as db:
        result = ingest_local(db, settings.data_raw_dir, settings.rag_default_tenant_id)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
