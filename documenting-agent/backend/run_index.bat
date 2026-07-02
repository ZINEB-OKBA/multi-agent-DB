@echo off
:: 1. Se déplacer dans le dossier du projet Python (backend)
cd /d "C:\Users\hp\Desktop\documenting-agent\backend"

:: 2. Écrire la date dans le fichier de log
echo === Exécution du Job Indexation du %date% à %time% === >> cron_output.log

:: 3. Lancer le script en pointant sur le Python situé dans le dossier parent (..)
"C:\Users\hp\Desktop\documenting-agent\.venv\Scripts\python.exe" cron_index.py >> cron_output.log 2>&1

echo === Fin d'exécution === >> cron_output.log