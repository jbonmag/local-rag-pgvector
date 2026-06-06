from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.llm.local_generation import LocalGenerator
from app.retrieval.hybrid import answer_question
from app.schemas import QueryRequest, QueryResponse

router = APIRouter()
DB_DEPENDENCY = Depends(get_db)


@router.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest, db: Session = DB_DEPENDENCY) -> QueryResponse:
    settings = get_settings()
    tenant_id = request.tenant_id or settings.rag_default_tenant_id
    generator = LocalGenerator(settings=settings)
    return answer_question(
        db=db,
        question=request.question,
        tenant_id=tenant_id,
        top_k=request.top_k,
        generator=generator,
    )
