"""
FinSight - Financial Document Intelligence System
Retriever Module
Handles vector search and RAG chain construction
"""

import os
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = Path("chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

FINANCIAL_PROMPT = PromptTemplate(
    template="""You are FinSight, an expert financial analyst AI assistant.
Use the following financial document context to answer the question accurately.
Always cite specific numbers, dates, and sources when available.
If the answer is not in the context, say "I don't have enough information in the documents to answer this."

Context:
{context}

Question: {question}

Answer (be specific and cite sources):""",
    input_variables=["context", "question"],
)


def get_embeddings():
    """Load HuggingFace embedding model"""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vector_store(embeddings) -> Chroma:
    """Load ChromaDB vector store"""
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"Vector store not found at {CHROMA_DIR}. "
            "Please run ingest.py first."
        )
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="financial_docs",
    )


def get_llm():
    """Groq cloud LLM — Llama3 70B, fast and free tier available"""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,
    )


def get_retriever(vector_store: Chroma):
    """Create retriever with MMR search for diversity"""
    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 10,
            "lambda_mult": 0.7,
        },
    )


def build_rag_chain(retriever, llm):
    """Build RAG chain with financial prompt"""
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": FINANCIAL_PROMPT},
    )


def format_sources(source_documents: List[Document]) -> List[Dict]:
    """Format source documents for API response"""
    sources = []
    for doc in source_documents:
        sources.append(
            {
                "content": doc.page_content[:500],
                "source": doc.metadata.get("source", "Unknown"),
                "page": str(doc.metadata.get("page", "N/A")),
            }
        )
    return sources


class FinSightRetriever:
    """Main retriever class for FinSight"""

    def __init__(self):
        print("Initializing FinSight Retriever...")
        self.embeddings = get_embeddings()
        self.vector_store = get_vector_store(self.embeddings)
        self.llm = get_llm()
        self.retriever = get_retriever(self.vector_store)
        self.rag_chain = build_rag_chain(self.retriever, self.llm)
        print("FinSight Retriever ready!")

    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system"""
        result = self.rag_chain({"query": question})
        return {
            "question": question,
            "answer": result["result"],
            "sources": format_sources(result["source_documents"]),
        }

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Direct similarity search"""
        docs = self.vector_store.similarity_search(query, k=k)
        return format_sources(docs)