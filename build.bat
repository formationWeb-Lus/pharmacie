@echo off
echo Installation des dependances...
python -m pip install -r requirements.txt
echo Construction de l'application...
python -m PyInstaller --noconfirm --clean --windowed --name Pharmacie --onedir main.py
echo.
echo Application creee dans dist\Pharmacie
pause
