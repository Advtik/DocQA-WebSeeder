import React from 'react';
import { useEffect, useRef, useState } from 'react';
import AnswerDisplay from './components/AnswerDisplay.jsx';
import FileUpload from './components/FileUpload.jsx';
import QuestionInput from './components/QuestionInput.jsx';
import { askStream } from './api.js';

export default function App() {
  const [documentInfo, setDocumentInfo] = useState(null);
  const [streamingText, setStreamingText] = useState('');
  const [askError, setAskError] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [hasReceivedToken, setHasReceivedToken] = useState(false);
  const [backendSourceInfo, setBackendSourceInfo] = useState(null);
  const cleanupRef = useRef(null);
  const pendingTextRef = useRef('');
  const typingTimerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (cleanupRef.current) cleanupRef.current();
      stopTypingLoop();
    };
  }, []);

  function stopTypingLoop() {
    if (typingTimerRef.current) {
      window.clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }
    setIsTyping(false);
  }

  function startTypingLoop() {
    if (typingTimerRef.current) return;

    setIsTyping(true);
    typingTimerRef.current = window.setInterval(() => {
      const pending = pendingTextRef.current;
      if (!pending) {
        stopTypingLoop();
        return;
      }

      const step = pending.length > 40 ? 4 : 2;
      setStreamingText((prev) => prev + pending.slice(0, step));
      pendingTextRef.current = pending.slice(step);
    }, 18);
  }

  function handleAsk(question) {
    if (!documentInfo?.document_id) {
      setAskError('Upload a PDF before asking a question.');
      return;
    }

    if (cleanupRef.current) cleanupRef.current();
    stopTypingLoop();
    pendingTextRef.current = '';

    setIsAsking(true);
    setAskError('');
    setStreamingText('');
    setHasReceivedToken(false);
    setBackendSourceInfo(null);

    cleanupRef.current = askStream(
      documentInfo.document_id,
      question,
      (token) => {
        setHasReceivedToken(true);
        pendingTextRef.current += token;
        startTypingLoop();
      },
      () => setIsAsking(false),
      (err) => {
        setAskError(err);
        setIsAsking(false);
        stopTypingLoop();
      },
      (source) => setBackendSourceInfo(source),
    );
  }

  function handleUploaded(uploadResponse) {
    setDocumentInfo(uploadResponse);
    setStreamingText('');
    setAskError('');
    setHasReceivedToken(false);
    setBackendSourceInfo(null);
    pendingTextRef.current = '';
  }

  return (
    <main className="app-shell">
      <section className="panel">
        <header className="app-header">
          <p className="eyebrow">Local PDF Question Answering</p>
          <h1>DocQA</h1>
        </header>

        <FileUpload onUploaded={handleUploaded} documentInfo={documentInfo} />
        <QuestionInput
          disabled={!documentInfo}
          isLoading={isAsking}
          onAsk={handleAsk}
        />
        <AnswerDisplay
          streamingText={streamingText}
          isStreaming={isAsking || isTyping}
          isWaitingForToken={isAsking && !hasReceivedToken && !streamingText}
          sourceInfo={
            streamingText || isAsking
              ? {
                  filename: backendSourceInfo?.filename || documentInfo?.filename,
                  chunkCount:
                    backendSourceInfo?.chunk_count || documentInfo?.chunk_count,
                }
              : null
          }
          error={askError}
        />
      </section>
    </main>
  );
}
