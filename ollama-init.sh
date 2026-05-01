#!/bin/sh

echo "Starting Ollama..."
ollama serve &

sleep 5

echo "Pulling model..."
ollama pull llama3.2:1b

wait