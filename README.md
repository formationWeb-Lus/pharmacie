# Pharmacie Desktop

Application Windows de gestion de pharmacie, fonctionnant hors ligne avec SQLite.

## Fonctionnalités MVP
- Tableau de bord
- Gestion des produits
- Gestion du stock
- Vente rapide
- Historique des ventes
- Rapports PDF
- Export Excel
- Base SQLite locale
- Architecture prête pour licence, sauvegarde cloud et mises à jour

## Installation développeur

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Créer l'EXE

```bash
build.bat
```

Le résultat sera dans `dist/Pharmacie/Pharmacie.exe`.

## Créer l'installateur

Installer Inno Setup sous Windows puis lancer :

```text
installer/Pharmacie.iss
```

## Données
La base est stockée dans :

`%LOCALAPPDATA%\Pharmacie\pharmacie.db`

Cela permet au logiciel de fonctionner hors ligne et évite de placer les données dans le dossier d'installation.
