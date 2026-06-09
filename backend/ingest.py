"""
FinSight - Financial Document Intelligence System
Document Ingestion Module
Loads, chunks, and embeds financial documents into ChromaDB vector store
"""

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

# Paths
DOCS_DIR = Path("documents")
CHROMA_DIR = Path("chroma_db")

# Embedding model — free, runs locally
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking config — optimized for financial documents
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_documents(docs_dir: Path) -> List:
    """Load all PDFs and text files from documents directory"""
    documents = []

    pdf_files = list(docs_dir.glob("*.pdf"))
    for pdf_path in pdf_files:
        print(f"Loading PDF: {pdf_path.name}")
        loader = PyPDFLoader(str(pdf_path))
        documents.extend(loader.load())

    txt_files = list(docs_dir.glob("*.txt"))
    for txt_path in txt_files:
        print(f"Loading TXT: {txt_path.name}")
        loader = TextLoader(str(txt_path))
        documents.extend(loader.load())

    print(f"\nTotal documents loaded: {len(documents)} pages")
    return documents


def chunk_documents(documents: List) -> List:
    """Split documents into chunks for embedding"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"Total chunks created: {len(chunks)}")
    return chunks


def get_embeddings():
    """Load HuggingFace embedding model"""
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return embeddings


def build_vector_store(chunks: List, embeddings) -> Chroma:
    """Build ChromaDB vector store from document chunks"""
    print("Building ChromaDB vector store...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="financial_docs",
    )
    # NOTE: vector_store.persist() is no longer needed — Chroma 0.4.x+ auto-persists
    print(f"Vector store saved to: {CHROMA_DIR}")
    return vector_store


def load_vector_store(embeddings) -> Chroma:
    """Load existing ChromaDB vector store"""
    print("Loading existing ChromaDB vector store...")
    vector_store = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="financial_docs",
    )
    return vector_store


def ingest_documents():
    """Main ingestion pipeline"""
    print("=" * 50)
    print("FinSight - Document Ingestion Pipeline")
    print("=" * 50)

    DOCS_DIR.mkdir(exist_ok=True)
    CHROMA_DIR.mkdir(exist_ok=True)

    pdf_count = len(list(DOCS_DIR.glob("*.pdf")))
    txt_count = len(list(DOCS_DIR.glob("*.txt")))

    if pdf_count + txt_count == 0:
        print(f"\nNo documents found in {DOCS_DIR}/")
        print("Please add PDF or TXT files to the documents/ folder and run again.")
        return None

    documents = load_documents(DOCS_DIR)
    chunks = chunk_documents(documents)
    embeddings = get_embeddings()
    vector_store = build_vector_store(chunks, embeddings)

    print("\nIngestion complete!")
    print(f"Documents: {pdf_count + txt_count}")
    print(f"Chunks: {len(chunks)}")
    print(f"Vector store: {CHROMA_DIR}")
    return vector_store


if __name__ == "__main__":
    ingest_documents()