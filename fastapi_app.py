"""
FastAPI-based web interface for the RAG query engine.
Exposes a small API surface to mirror rag_query.py functionality.
"""
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_query import RAGQueryEngineFAISS


app = FastAPI(
    title="Scientific Papers RAG API",
    description=(
        "Simple FastAPI service that wraps the FAISS-based RAG query engine "
        "to provide programmatic access to stats and question answering."
    ),
    version="0.1.0",
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class Source(BaseModel):
    title: str
    filename: str
    chunk_id: int = Field(0, description="Chunk identifier within the document")
    similarity_score: float = Field(
        0.0, description="Similarity score returned by FAISS for this chunk"
    )


class RelevantDocument(BaseModel):
    content: str
    metadata: dict
    similarity_score: float


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question to ask the RAG system")
    k: int = Field(5, ge=1, le=200, description="Number of similar chunks to retrieve")


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]
    relevant_docs: List[RelevantDocument]


class StatsResponse(BaseModel):
    total_vectors: int
    total_documents: int
    embedding_dimension: int
    embedding_model: str
    llm_model: str
    index_location: str


def get_engine() -> RAGQueryEngineFAISS:
    """
    Return an initialized RAGQueryEngineFAISS instance stored on the app state.
    Engine instances are heavy, so we initialize once and reuse.
    """
    engine: Optional[RAGQueryEngineFAISS] = getattr(app.state, "engine", None)
    if engine is None:
        engine = RAGQueryEngineFAISS()
        app.state.engine = engine
    return engine


@app.on_event("startup")
def startup_event() -> None:
    """
    Ensure the engine is created at startup so that subsequent requests are fast.
    Exceptions are allowed to bubble so the server fails fast when misconfigured.
    """
    get_engine()


@app.get("/health", tags=["system"])
def health() -> dict:
    """Lightweight health endpoint for uptime checks."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def frontend() -> HTMLResponse:
    """Serve the minimal single-page app."""
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            "<h1>Frontend not found</h1><p>Create frontend/index.html to enable the web UI.</p>",
            status_code=501,
        )
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/stats", response_model=StatsResponse, tags=["system"])
def stats() -> StatsResponse:
    """Expose system statistics such as document counts and vector totals."""
    engine = get_engine()
    try:
        stats_data = engine.get_system_stats()
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return StatsResponse(**stats_data)


@app.post("/ask", response_model=QueryResponse, tags=["queries"])
def ask(request: QueryRequest) -> QueryResponse:
    """
    Answer a question using the FAISS-backed retrieval pipeline.
    Mirrors rag_query.ask but exposes the result as JSON.
    """
    engine = get_engine()
    try:
        result = engine.ask(request.question, k=request.k)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Required index files are missing. "
                "Run rag_builder.py or rag_builder_faiss.py before querying."
            ),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return QueryResponse(
        question=result["question"],
        answer=result["answer"],
        sources=[Source(**source) for source in result.get("sources", [])],
        relevant_docs=[
            RelevantDocument(
                content=doc.get("content", ""),
                metadata=doc.get("metadata", {}),
                similarity_score=doc.get("similarity_score", 0.0),
            )
            for doc in result.get("relevant_docs", [])
        ],
    )
