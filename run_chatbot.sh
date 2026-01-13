#!/bin/bash
# Script de lancement du Chatbot V2

echo "Démarrage du Chatbot..."

# 1. S'assurer qu'Ollama tourne
if pgrep -x "ollama" > /dev/null
then
    echo "Ollama est déjà lancé."
else
    echo "Démarrage d'Ollama..."
    ollama serve &
    sleep 5
fi

# 2. Lancer l'interface utilisateur (écran)
echo "Lancement de l'interface (UI)..."
python chatbot-ui.py &
UI_PID=$!
sleep 5 # Attendre que l'UI initialise l'écran et le socket

# 3. Lancer la logique (Cerveau)
echo "Lancement du cerveau..."
python chatbot_logic.py &
LOGIC_PID=$!

echo "Chatbot opérationnel ! Appuyez sur Ctrl+C pour quitter."

# Gestion de l'arrêt propre
trap "kill $UI_PID $LOGIC_PID; exit" SIGINT SIGTERM

wait
