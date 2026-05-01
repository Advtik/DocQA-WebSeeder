const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || `Request failed with status ${response.status}`;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail);
  }
  return data;
}

export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  return parseResponse(response);
}

export async function askQuestion({ documentId, question }) {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      document_id: documentId,
      question,
    }),
  });

  return parseResponse(response);
}

export function askStream(documentId, question, onToken, onDone, onError, onSource) {
  const params = new URLSearchParams({
    document_id: documentId,
    question,
    top_k: 5,
  });

  const es = new EventSource(`${API_BASE_URL}/ask/stream?${params}`);

  es.onmessage = (e) => {
    if (e.data === "[DONE]") {
      es.close();
      onDone();
      return;
    }
    try {
      const { token, error, source } = JSON.parse(e.data);
      if (error) { es.close(); onError(error); return; }
      if (source && onSource) onSource(source);
      if (token) onToken(token);
    } catch {}
  };

  es.onerror = () => { es.close(); onError("Connection lost"); };
  return () => es.close(); // returns a cleanup fn
}
