# Chatbot V2 - Branche de Développement (Whisplay Style)

Cette branche contient une adaptation du projet [Whisplay](https://github.com/PiSugar/whisplay-ai-chatbot) pour fonctionner spécifiquement avec votre matériel Waveshare et Ollama en local.

## 🛠 Matériel Supporté
- **Raspberry Pi 5**
- **Waveshare Triple LCD HAT** (Utilise l'écran central 1.3")
- **Microphone USB**
- **Haut-parleurs** (Sortie Jack ou USB)

## 🚀 Installation Rapide

### 1. Préparation du système
Activez les interfaces SPI et I2C via `sudo raspi-config` puis redémarrez.

### 2. Installation des dépendances système
Certaines bibliothèques audio nécessitent des paquets système :
```bash
sudo apt-get update
sudo apt-get install -y python3-pyaudio portaudio19-dev espeak flac libasound2-dev
```

### 3. Installation des dépendances Python
```bash
pip install -r requirements.txt --break-system-packages
```

### 4. Configuration de l'IA (Ollama)
Assurez-vous qu'Ollama est installé et que le modèle est téléchargé :
```bash
# Si pas encore fait :
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

## 🎮 Utilisation

Lancez le chatbot avec le script tout-en-un :
```bash
chmod +x run_chatbot.sh
./run_chatbot.sh
```

**Fonctionnement :**
1. L'interface s'affiche sur l'écran Waveshare.
2. Appuyez sur le **bouton KEY1** de la carte Waveshare.
3. Parlez pendant 5 secondes.
4. Le robot affiche "Thinking..." puis vous répond vocalement et par écrit.

## 📂 Structure de la Branche
- `whisplay_adapter.py` : Traduit les commandes Whisplay pour votre matériel Waveshare.
- `chatbot-ui.py` : Gère l'affichage graphique et les emojis.
- `chatbot_logic.py` : Gère le son, la reconnaissance vocale et l'IA.
- `run_chatbot.sh` : Script de lancement automatique.
