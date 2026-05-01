import React from 'react';

export default function AnswerDisplay({
  streamingText,
  isStreaming,
  isWaitingForToken,
  sourceInfo,
  error,
}) {
  const isEmpty = !streamingText && !isStreaming && !error;

  return (
    <section className="section-block answer-area">
      <h2>Answer</h2>

      {error && <p className="error">{error}</p>}

      {isEmpty && (
        <p className="muted">The answer will appear here after you ask a question.</p>
      )}

      {isWaitingForToken && (
        <div className="answer-loading" aria-live="polite">
          <span className="loader-dot"></span>
          <span>Finding the most relevant parts of the PDF...</span>
        </div>
      )}

      {(streamingText || isStreaming) && (
        <p className="answer-text">
          {streamingText}
          {isStreaming && <span className="typing-cursor" aria-hidden="true"></span>}
        </p>
      )}

      {sourceInfo?.filename && (
        <div className="source-card">
          <span>Source</span>
          <strong>{sourceInfo.filename}</strong>
          {sourceInfo.chunkCount ? (
            <small>{sourceInfo.chunkCount} indexed sections searched</small>
          ) : null}
        </div>
      )}
    </section>
  );
}
