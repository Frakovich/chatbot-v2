# Drivers Waveshare Triple LCD HAT (Working Backup)

Ce dossier contient les fichiers de configuration et de test validés pour le Waveshare Triple LCD HAT sur Raspberry Pi 5.

## Fichiers inclus

- **waveshare_config.py** : Fichier de configuration principal. Contient les définitions des broches (GPIO/SPI) et les paramètres de correction des couleurs (RGB/BGR) validés.
- **requirements.txt** : Les dépendances Python nécessaires (`spidev`, `rpi-lgpio`, etc.).
- **fix_colors_test.py** : Test simple pour vérifier que :
  - Centre = ROUGE
  - Gauche = VERT
  - Droite = BLEU
- **test_primaries_*.py** : Scripts de diagnostic pour tester les couleurs primaires (Rouge, Vert, Bleu) sur chaque écran individuellement.
- **turn_yellow_096_1.py** : Exemple de script qui remplit l'écran 1 (Gauche) entièrement en jaune (technique "Brute Force" pour éviter les problèmes d'offset).

## Installation sur un nouveau système

1. Installer les dépendances système et Python :
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-spidev
   pip3 install -r requirements.txt --break-system-packages
   ```

2. Activer le SPI sur le Raspberry Pi :
   ```bash
   sudo raspi-config
   # Interface Options -> SPI -> Yes
   ```

3. Tester les écrans :
   ```bash
   python3 fix_colors_test.py
   ```
   
## Notes Techniques

- **Écran Central (1.3")** : Contrôleur ST7789. Mode RGB (`madctl=0x00`).
- **Écrans Latéraux (0.96")** : Contrôleur ST7735S. Mode BGR (`madctl=0x08`).
- **Remplissage écran** : Pour les petits écrans ST7735S, il est recommandé d'écrire dans toute la mémoire RAM (132x162) pour éviter les artefacts visuels dus aux offsets (offsets 24/0 souvent problématiques selon l'orientation).

## Microphone USB

Le dossier contient également `test_mic_usb.py` pour valider le microphone.

1.  **Pré-requis** :
    ```bash
    sudo apt-get install libportaudio2 libasound2-dev
    pip3 install sounddevice scipy numpy --break-system-packages
    ```

2.  **Test automatique** :
    ```bash
    python3 test_mic_usb.py
    ```
    Ce script détecte automatiquement le micro USB et essaie plusieurs fréquences (48k, 44.1k, 16k).

3.  **Test manuel (VU-mètre)** :
    Pour voir si le micro capte du son en temps réel dans le terminal :
    ```bash
    arecord -D hw:2,0 -c 1 -f S16_LE -V mono /dev/null
    ```
    *(Ajustez `hw:2,0` si votre micro n'est pas sur la carte 2)*.

## IA & Chatbot (Ollama)

Pour l'intelligence artificielle locale :

1.  **Installation automatique** :
    ```bash
    chmod +x install_ollama.sh
    ./install_ollama.sh
    ```
    *(Ou manuellement : `curl -fsSL https://ollama.com/install.sh | sh`)*.

2.  **Téléchargement du modèle** (si `install_ollama.sh` a échoué à cause du réseau) :
    ```bash
    ollama pull llama3.2
    ```

3.  **Test du cerveau** :
    ```bash
    ollama run llama3.2
    ```
    Tapez `/bye` pour quitter.
