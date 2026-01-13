#!/bin/bash
echo "=== Installation de Ollama et Llama 3.2 ==="

# Installation du service Ollama
echo "[1/2] Installation de Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Telechargement du modele
echo "[2/2] Telechargement de Llama 3.2 (2.0 Go)..."
ollama pull llama3.2

echo "=== Termine ! ==="
echo "Vous pouvez tester avec : ollama run llama3.2"
