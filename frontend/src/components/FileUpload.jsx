import React from 'react';
import { useState } from 'react';
import { uploadPdf } from '../api.js';

export default function FileUpload({ onUploaded, documentInfo }) {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) {
      setError('Choose a PDF file first.');
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      const response = await uploadPdf(file);
      onUploaded(response);
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <section className="section-block">
      <h2>Upload PDF</h2>
      <form className="upload-form" onSubmit={handleSubmit}>
        <input
          accept="application/pdf,.pdf"
          disabled={isUploading}
          onChange={(event) => setFile(event.target.files?.[0] || null)}
          type="file"
        />
        <button disabled={isUploading || !file} type="submit">
          {isUploading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {documentInfo && (
        <div className="status-box">
          <strong>{documentInfo.filename}</strong>
          <span>{documentInfo.chunk_count} chunks indexed</span>
          <code>{documentInfo.document_id}</code>
        </div>
      )}
    </section>
  );
}
