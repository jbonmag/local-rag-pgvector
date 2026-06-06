from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.ingestion.pipeline import ingest_local
from app.schemas import IngestLocalRequest, IngestLocalResponse

router = APIRouter()
DB_DEPENDENCY = Depends(get_db)


@router.post("/ingest/local", response_model=IngestLocalResponse)
def ingest_local_endpoint(
    request: IngestLocalRequest | None = None, db: Session = DB_DEPENDENCY
) -> IngestLocalResponse:
    settings = get_settings()
    tenant_id = (request.tenant_id if request else None) or settings.rag_default_tenant_id
    return ingest_local(db=db, raw_dir=settings.data_raw_dir, tenant_id=tenant_id)
