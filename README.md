# DocQA

A fully local PDF Question Answering system powered by a Retrieval-Augmented Generation (RAG) pipeline. Upload a PDF, ask questions, and get accurate answers — no external APIs, no internet required.

---

## Features

- Upload and process PDF documents
- Intelligent text chunking and semantic embedding
- Fast similarity search using FAISS
- Local LLM answer generation via Ollama
- Streaming responses (Server-Sent Events)
- One-command setup with Docker Compose

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector Store | FAISS |
| LLM Runtime | Ollama (`llama3.2:1b`) |
| Containerization | Docker & Docker Compose |

---

## System Architecture

The system follows a standard RAG pipeline: PDF → chunking → embedding → FAISS index → semantic retrieval → local LLM generation.

For a detailed breakdown, see [System Architecture](SYSTEM_ARCHITECTURE.md).

---

## Demo

[Demo Video](#)

---

## Project Structure

```
DocQA/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   ├── routers/
│   │   │   ├── ask.py
│   │   │   └── upload.py
│   │   ├── services/
│   │   │   ├── chunking_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── pdf_service.py
│   │   │   ├── qa_service.py
│   │   │   └── vector_store_service.py
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnswerDisplay.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   └── QuestionInput.jsx
│   │   ├── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── index.html
│   └── package.json
├── docker-compose.yml
├── ollama-init.sh
├── README.md
└── SYSTEM_ARCHITECTURE.md
```

---

## Setup

### Prerequisite

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Run

```bash
git clone https://github.com/your-username/DocQA.git
cd DocQA
docker-compose up --build
```

> **Note:** The first run downloads the `llama3.2:1b` model via Ollama. This may take **5–15 minutes** depending on your internet speed. Subsequent startups are fast.

### Access

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API Docs | http://localhost:8000/docs |

---

## Usage

1. Open `http://localhost:5173`
2. Upload a PDF document
3. Type a question and click **Ask**
4. The answer streams back in real time

---

## Notes

- **Fully local** — no data leaves your machine; no OpenAI or any external API is used
- **First startup is slow** due to the one-time model download; all subsequent runs start in seconds
- **Model tradeoff** — `llama3.2:1b` is optimised for speed on CPU; for higher accuracy on capable hardware, swap the model in `.env`