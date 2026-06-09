"""
FinSight - Financial Document Intelligence System
FastAPI Backend
REST API for document ingestion and financial Q&A
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os
from pathlib import Path

from ingest import ingest_documents
from retriever import FinSightRetriever

# Initialize FastAPI
app = FastAPI(
    title="FinSight API",
    description="Financial Document Intelligence System powered by RAG",
    version="1.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global retriever instance
retriever: Optional[FinSightRetriever] = None
DOCS_DIR = Path("documents")
DOCS_DIR.mkdir(exist_ok=True)


# Request/Response models
class QueryRequest(BaseModel):
    question: str


class Source(BaseModel):
    content: str
    source: str
    page: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]


class SearchRequest(BaseModel):
    query: str
    k: int = 5


class StatusResponse(BaseModel):
    status: str
    message: str
    documents_loaded: bool


# Routes
@app.get("/", response_model=StatusResponse)
async def root():
    return {
        "status": "ok",
        "message": "FinSight Financial Document Intelligence API",
        "documents_loaded": retriever is not None,
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "retriever_ready": retriever is not None}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a financial document (PDF or TXT)"""
    if not file.filename.endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported",
        )

    file_path = DOCS_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": f"File '{file.filename}' uploaded successfully",
        "filename": file.filename,
        "path": str(file_path),
    }


@app.post("/ingest")
async def run_ingestion():
    """Ingest all documents in the documents folder"""
    global retriever

    doc_count = len(list(DOCS_DIR.glob("*.pdf"))) + len(
        list(DOCS_DIR.glob("*.txt"))
    )

    if doc_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents found. Please upload documents first.",
        )

    try:
        ingest_documents()
        retriever = FinSightRetriever()
        return {
            "message": "Ingestion complete",
            "documents_processed": doc_count,
            "status": "ready",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query financial documents using natural language"""
    global retriever

    if retriever is None:
        raise HTTPException(
            status_code=400,
            detail="No documents loaded. Please upload and ingest documents first.",
        )

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = retriever.query(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_documents(request: SearchRequest):
    """Direct similarity search in document store"""
    global retriever

    if retriever is None:
        raise HTTPException(
            status_code=400,
            detail="No documents loaded. Please upload and ingest documents first.",
        )

    try:
        results = retriever.search(request.query, request.k)
        return {"query": request.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    pdfs = [f.name for f in DOCS_DIR.glob("*.pdf")]
    txts = [f.name for f in DOCS_DIR.glob("*.txt")]
    return {
        "documents": pdfs + txts,
        "count": len(pdfs) + len(txts),
    }


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document"""
    file_path = DOCS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(file_path)
    return {"message": f"'{filename}' deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)