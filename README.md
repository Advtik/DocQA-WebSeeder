# DocQA

Local Document Q&A over uploaded PDF files.

This project follows the provided technical design:

- FastAPI backend
- PyMuPDF PDF parsing
- sentence-transformers embeddings
- FAISS vector search
- Ollama + Mistral answer generation
- Minimal React/Vite frontend

No external APIs are used at inference time. Ollama must be running locally.

## Project Structure

```text
DocQA/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── models/
│   │   └── config.py
│   ├── tests/
│   ├── uploads/
│   ├── requirements.txt
│   ├── run.ps1
│   └── run.sh
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── api.js
    │   ├── App.jsx
    │   └── main.jsx
    └── package.json
```

## Prerequisites

Install and start Ollama:

```powershell
ollama pull mistral
ollama serve
```

Use Python 3.11+ for the backend and Node.js 20+ for the frontend.

## Run Backend

```powershell
cd "C:\Dev Work\DocQA\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The first backend startup may download the `sentence-transformers/all-MiniLM-L6-v2`
embedding model if it is not already cached locally.

Backend endpoints:

- `POST /upload` with multipart field `file`
- `POST /ask` with JSON `{ "document_id": "...", "question": "...", "top_k": 5 }`
- `GET /health`

API docs are available at:

```text
http://localhost:8000/docs
```

## Run Frontend

```powershell
cd "C:\Dev Work\DocQA\frontend"
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The frontend calls the backend at `http://localhost:8000`. To override:

```powershell
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev
```

## Configuration

Copy `backend/.env.example` to `backend/.env` if you want local overrides.

Important settings:

- `OLLAMA_URL=http://localhost:11434`
- `OLLAMA_MODEL=mistral`
- `EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2`
- `CHUNK_SIZE=1800`
- `CHUNK_OVERLAP=200`
- `DEFAULT_TOP_K=5`
- `MIN_SIMILARITY_SCORE=0.05`

## Tests

```powershell
cd "C:\Dev Work\DocQA\backend"
pytest
```

The included tests cover chunking, prompt construction, vector search, upload validation,
and request validation.
