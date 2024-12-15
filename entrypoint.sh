#!/bin/bash

# Start Ollama in the background
/bin/ollama serve &

# Get the process ID
pid=$!

# Wait for Ollama to start
sleep 5

# Pull the desired model
echo "Pulling model..."
ollama pull llama3.2:1b
echo "Model pulled successfully"

# Wait for Ollama to finish
wait $pid