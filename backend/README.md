# DocQA Backend

FastAPI backend for local PDF question answering.

## Run

```powershell
cd "C:\Dev Work\DocQA\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start Ollama separately:

```powershell
ollama pull mistral
ollama serve
```

## API

- `POST /upload`: upload a PDF as multipart field `file`
- `POST /ask`: ask a question with `document_id`, `question`, and optional `top_k`
- `GET /health`: backend status, indexed document count, and Ollama availability

## Notes

- Uploaded files are stored in `uploads/`.
- FAISS indices and chunk text are stored in memory per `document_id`.
- Scanned/image-only PDFs return a clear error because OCR is outside the MVP scope.
