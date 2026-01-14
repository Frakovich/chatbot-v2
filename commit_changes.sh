#!/bin/bash
# This script first stages all changes and then performs the git commit.

echo "Étape 1: Préparation de tous les changements (git add .)..."
git add .
echo "Changements préparés."
echo ""
echo "Étape 2: Création du commit..."

git commit -m "feat: Réorganisation de la structure du projet et correction du pilote d'affichage

Ce commit réorganise la structure du projet en déplaçant les fichiers
liés aux pilotes du répertoire 'drivers_backup' vers la racine du projet.

Les changements clés incluent :
- Le répertoire 'drivers_backup' a été supprimé, et son contenu a été
  déplacé à la racine du projet pour un accès et une gestion simplifiés.
- 'waveshare_config.py' et d'autres scripts de test sont maintenant à la racine.
- Un nouveau fichier 'display.py' a été créé, encapsulant la logique du pilote
  d'affichage ST7789 dans une classe orientée objet, basée sur le script
  fonctionnel 'test_bonjour_3_ecrans.py'.
- 'push_to_talk_v2.py' a été mis à jour pour importer correctement le pilote
  d'affichage et la configuration depuis leurs nouveaux emplacements, résolvant
  ainsi les précédentes erreurs 'ModuleNotFoundError'.
- Le fichier 'requirements.txt', qui était précédemment référencé dans un
  répertoire inexistant, a été déplacé à la racine et est maintenant
  correctement intégré au processus d'installation.
- Le 'README.md' a été significativement mis à jour pour refléter ces changements,
  fournir des instructions d'installation précises et guider les utilisateurs
  sur la manière de configurer et d'exécuter le chatbot sur Raspberry Pi 5.

Ceci établit une base solide pour le développement futur, avec le moteur
principal du chatbot et la fonctionnalité d'affichage désormais opérationnels
sur Raspberry Pi 5."

echo ""
echo "Commit créé avec succès."