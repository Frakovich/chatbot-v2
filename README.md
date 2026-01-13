# Chatbot V2 - Guide d'Installation sur Raspberry Pi

Ce guide explique comment installer ce projet sur une nouvelle carte SD pour Raspberry Pi.

## 1. Préparation du système
Avant de commencer, assurez-vous que les interfaces matérielles sont activées.

1. Ouvrez un terminal sur le Pi ou via SSH.
2. Lancez la configuration : `sudo raspi-config`
3. Allez dans **Interface Options** et activez :
   - **SPI** (nécessaire pour l'écran Waveshare)
   - **I2C**
   - **SSH** (recommandé pour le contrôle à distance)
4. Redémarrez le Pi : `sudo reboot`

## 2. Récupération du projet
Clonez ce dépôt GitHub sur votre nouveau Pi :
```bash
cd ~
git clone https://github.com/Frakovich/chatbot-v2.git
cd chatbot-v2
```

## 3. Installation des dépendances Python
Installez les bibliothèques nécessaires au fonctionnement des composants :
```bash
pip install -r drivers_backup/requirements.txt
```

## 4. Installation de Ollama
Lancez le script d'installation automatique pour l'IA :
```bash
chmod +x drivers_backup/install_ollama.sh
./drivers_backup/install_ollama.sh
```

## 5. Tests du matériel
Une fois l'installation terminée, vérifiez que tout fonctionne :

- **Micro USB :**
  ```bash
  python drivers_backup/test_mic_usb.py
  ```
- **Écran Waveshare :**
  ```bash
  python drivers_backup/test_primaries_center.py
  ```

---
*Note : Assurez-vous d'avoir une connexion internet stable pendant l'installation.*
