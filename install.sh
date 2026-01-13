#!/bin/bash

# Couleurs
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}🚀 Lancement de l'installation Chatbot V2...${NC}"

# 1. Mise à jour système et outils de compilation
echo "🔄 Mise à jour système..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git libportaudio2 portaudio19-dev python3-dev

# 2. Installation d'Ollama
# On vérifie si le script est dans drivers_backup ou à la racine
if [ -f "drivers_backup/install_ollama.sh" ]; then
    echo "🧠 Installation d'Ollama (via script local)..."
    chmod +x drivers_backup/install_ollama.sh
    bash drivers_backup/install_ollama.sh
else
    echo "🧠 Installation d'Ollama (via web)..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 3. Installation des dépendances Python
echo "🐍 Installation des bibliothèques Python..."
# On installe ce qui est demandé + ce qui manque pour le micro (sounddevice, scipy)
# Note: On utilise --break-system-packages car Raspberry Pi OS (Bookworm) l'impose souvent
pip3 install rpi-lgpio spidev Pillow numpy sounddevice scipy --break-system-packages

# 4. Préparation des scripts
echo "🛠️ Préparation des scripts..."
chmod +x drivers_backup/*.py
chmod +x drivers_backup/*.sh 2>/dev/null

echo -e "${GREEN}✅ Installation terminée !${NC}"
echo "Pour tester le micro : python3 drivers_backup/test_mic_usb.py"
echo "Pour tester l'écran : python3 drivers_backup/test_primaries_center.py"
