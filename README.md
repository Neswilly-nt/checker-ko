# Checker-ko v0.7.1

Checker-ko est un outil local d'aide à la vérification journalistique. Il rassemble les dossiers, les médias, les sources et les preuves, puis laisse au journaliste la rédaction de la conclusion. Il ne détermine pas automatiquement la véracité d'une affirmation.

## Fonctionnalités

- Accueil compact avec indicateurs calculés et cinq dossiers récents ; navigation adaptée au mobile.
- Dossiers photo (JPEG, PNG, WebP), vidéo MP4, texte et lien ; recherche et historique local.
- Analyse des métadonnées, SHA-256, pHash, EXIF filtrées et C2PA si `c2patool` est disponible.
- Analyse MP4 et extraction d'images clés avec FFmpeg et ffprobe.
- Comparaison avec les archives internes et recherche inversée assistée par le journaliste.
- Carnet de preuves, conclusion humaine, relecture facultative et rapport imprimable en PDF depuis le navigateur.
- Annuaire de cinq institutions malgaches partiellement v?rifi?es, gestion des contacts publics avec r?f?rences et dates, archivage r?versible des fiches et r?f?rentiel des 24 r?gions.
- Veille RSS Actualités avec une source malgache réellement vérifiée, collecte journalisée, filtres et création idempotente d'un dossier de vérification. Voir [les flux](docs/FLUX_ACTUALITES.md).
- Évaluation de source par preuve : critères rapides et avancés, portée documentaire, appréciation explicable et historique. Voir [la méthodologie](docs/METHODOLOGIE_EVALUATION_SOURCES.md).
- Catalogue de trois publications document?es avec observations persistantes saisies par la r?daction (valeur, unit?, ann?e, r?gion et r?f?rence pr?cise de page/table). Elles s?ajoutent au carnet comme contexte ; aucune valeur n?est pr?remplie. Voir les r?f?rences dans docs/SOURCES_STATISTIQUES.md et les changements v0.7.1 dans docs/CHANGEMENTS_V071.md.

Les résultats techniques et les fiches de l'annuaire servent au recoupement : aucun résultat ne constitue à lui seul une preuve de véracité. Les images de `backend/demo_assets/` sont des exemples fictifs nécessaires aux tests.

## Architecture et prérequis

Le frontend est en React, TypeScript et Vite (`frontend/`). L'API est en FastAPI, SQLAlchemy et SQLite (`backend/`). Les médias, la base et le secret local restent dans `backend/private_data/`, exclu de Git. Voir [l'architecture](docs/ARCHITECTURE.md) et le [contrat API](docs/API.md).

- Windows 10/11, Python 3.11 ou plus, Node.js 22.12 ou plus, npm.
- FFmpeg et ffprobe pour les vidéos ; `c2patool` facultatif pour examiner les manifestes C2PA. Voir [l'installation des outils médias](docs/INSTALLATION_OUTILS_MEDIAS.md).
- Accès aux registres Python et npm pour la première installation.

## Installation Windows

Depuis la racine du dépôt, dans PowerShell ou CMD :

```powershell
.\scripts\setup-windows.bat
.\scripts\start-all.bat
```

Ouvrir `http://127.0.0.1:5173`. L'API répond sur `http://127.0.0.1:8000/api/health` et sa documentation sur `http://127.0.0.1:8000/docs`.

Pour lancer séparément les services :

```powershell
.\scripts\start-backend.bat
.\scripts\start-frontend.bat
```

Installation manuelle du backend :

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Installation manuelle du frontend, dans un autre terminal :

```powershell
cd frontend
npm ci
npm run dev
```

Pour Linux ou macOS, `./scripts/start-linux-macos.sh` installe puis lance les services locaux.

## Configuration et données

[`backend/.env.example`](backend/.env.example) décrit `APP_ENV`, `DATABASE_URL`, `CHECKER_DATA_DIR`, `CHECKER_SECRET`, `PHASH_THRESHOLD` et les limites vidéo. Le backend lit les **variables d'environnement du processus** ; copier un fichier `.env` ne suffit pas à le charger. `APP_ENV` vaut `development` par défaut. Le secret de développement est généré localement dans `backend/private_data/.local_secret` si `CHECKER_SECRET` n'est pas fourni.

Les comptes de démonstration intégrés sont réservés au développement local : `journaliste@checker.local` / `Journaliste2026!` et `redaction@checker.local` / `Redaction2026!`. Leur connexion est refusée lorsque `APP_ENV=production`. Ne publiez jamais la base ou les médias de `backend/private_data/`, même si les fichiers sont ignorés par Git. Sauvegardez ce répertoire séparément et protégez ses copies.

FFmpeg, ffprobe et c2patool peuvent être installés dans le `PATH` ou désignés par `FFMPEG_PATH`, `FFPROBE_PATH` et `C2PATOOL_PATH`. Des copies portables placées localement sous `tools/media/` sont également détectées ; ce dossier est exclu de Git. Sans FFmpeg, la vérification vidéo est indisponible ; les dossiers photo et texte restent utilisables. Sans c2patool, l'état C2PA est indiqué comme indisponible.

## Vérification du code

```powershell
cd frontend
npm ci
npm run check
npm run build
```

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Les tests API utilisent un répertoire temporaire et n'ouvrent pas la base privée. Le test de bout en bout des outils médias réels est sauté si les binaires et son échantillon local ne sont pas installés. La CI exécute les mêmes contrôles sans données d'enquête.

## Limites et travail en équipe

La branche de préparation ajoute des sessions cookie révocables, PostgreSQL/Alembic et des contrôles CSRF/CORS, mais Checker-ko reste destiné à une utilisation locale tant que les critères de [préparation production](docs/PRODUCTION_READINESS.md) ne sont pas validés. Aucun déploiement public n'est effectué. Les fichiers médias originaux peuvent contenir des métadonnées sensibles. Une correspondance pHash et un manifeste C2PA ne valident pas le contenu d'une scène. Les contacts et documents des institutions doivent être vérifiés pour chaque enquête.

Pour contribuer, consulter [le flux Git de l'équipe](docs/GIT_WORKFLOW.md). Documentation complémentaire : [installation Windows](docs/INSTALLATION_WINDOWS.md), [sources de Madagascar](docs/SOURCES_MADAGASCAR.md), [limitations](docs/LIMITES.md), [préparation production](docs/PRODUCTION_READINESS.md), [procédure de préproduction](docs/DEPLOYMENT.md), [changement v0.7.1](docs/CHANGEMENTS_V071.md), [historique v0.4.3](docs/CHANGEMENTS_V043.md) et [accueil compact](docs/UX_ACCUEIL_V044.md).
