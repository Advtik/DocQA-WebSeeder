import React from 'react';

import { useState } from 'react';

export default function QuestionInput({ disabled, isLoading, onAsk }) {
  const [question, setQuestion] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    onAsk(trimmed);
  }

  return (
    <section className="section-block">
      <h2>Ask Question</h2>
      <form className="question-form" onSubmit={handleSubmit}>
        <textarea
          disabled={disabled || isLoading}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={disabled ? 'Upload a PDF to enable questions' : 'Ask about the uploaded document'}
          rows="4"
          value={question}
        />
        <button disabled={disabled || isLoading || !question.trim()} type="submit">
          {isLoading ? 'Thinking...' : 'Ask'}
        </button>
      </form>
    </section>
  );
}
