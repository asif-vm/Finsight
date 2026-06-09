# FinSight — Financial Document Intelligence System

> Natural language querying of financial documents using RAG, LangChain, and Groq (Llama 3 70B).

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=flat-square&logo=react)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square&logo=docker)
![LangChain](https://img.shields.io/badge/LangChain-RAG-orange?style=flat-square)

---

## What it does

FinSight lets you upload financial documents (PDFs, annual reports, earnings calls) and query them in plain English. It retrieves the most relevant chunks from the document, passes them to Llama 3 70B via Groq, and returns a grounded answer with source citations.

**Example queries:**
- *"What was Apple's total revenue in FY2022?"*
- *"Summarize the key risk factors in this report."*
- *"What did the CEO say about growth strategy?"*

---

## Architecture

```
User Query
    │
    ▼
React Frontend (Vite)
    │  HTTP
    ▼
FastAPI Backend
    ├── /upload     → Save PDF to documents/
    ├── /ingest     → Chunk → Embed → Store in ChromaDB
    ├── /query      → MMR Retrieval → Groq LLM → Response
    ├── /search     → Direct similarity search
    ├── /documents  → List uploaded files
    └── /health     → Status check
    │
    ├── ChromaDB (vector store)
    │     └── HuggingFace Embeddings (all-MiniLM-L6-v2)
    │
    └── Groq API (Llama 3 70B)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Axios |
| Backend | FastAPI, Python 3.11 |
| RAG Framework | LangChain |
| Vector Store | ChromaDB |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| LLM | Groq — Llama 3 70B |
| PDF Parsing | PyPDF |
| Containerization | Docker, Docker Compose |

---

## Quick Start

### Prerequisites
- Docker Desktop
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Run with Docker

```bash
git clone https://github.com/asif-vm/finsight.git
cd finsight

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Start everything
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Run locally (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn api:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Usage

1. **Upload** — Click "Upload Document" and select a PDF or TXT financial document
2. **Ingest** — Click "Ingest" to chunk, embed, and store the document
3. **Query** — Ask any question in natural language
4. **Sources** — Every answer includes source citations with page numbers

---

## RAG Pipeline Details

- **Chunking**: Recursive character splitting (1000 chars, 200 overlap) optimized for financial prose
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` running locally on CPU
- **Retrieval**: MMR (Maximal Marginal Relevance) — fetches 10 candidates, returns 5 diverse results
- **Prompt**: Custom financial analyst prompt enforcing source citation and numerical accuracy
- **LLM**: Llama 3 70B via Groq (temperature=0.1 for factual consistency)

---

## Project Structure

```
finsight/
├── backend/
│   ├── api.py            # FastAPI endpoints
│   ├── ingest.py         # PDF loading, chunking, embedding
│   ├── retriever.py      # RAG chain, MMR search, Groq LLM
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main chat UI
│   │   └── App.css       # ChatGPT-style dark theme
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API and retriever status |
| POST | `/upload` | Upload a PDF or TXT document |
| POST | `/ingest` | Process and embed all documents |
| POST | `/query` | Natural language query with RAG |
| POST | `/search` | Direct similarity search |
| GET | `/documents` | List uploaded documents |
| DELETE | `/documents/{filename}` | Delete a document |

---

## Environment Variables

```bash
GROQ_API_KEY=your_groq_api_key_here
```

---

*Built as part of a portfolio targeting financial AI roles. Designed to demonstrate production-grade RAG system design with real-world financial document use cases.*
