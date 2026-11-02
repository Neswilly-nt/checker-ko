# Architecture Checker-ko (v0.4, phase 1)

Les dossiers `verification_cases` acceptent désormais un `asset_id` nul pour les affirmations sans image. Les dossiers vidéo ont une ligne `case_videos` et trois images-clés stockées dans `media_assets`. La première image-clé est l'image principale du dossier ; les trois peuvent être comparées aux archives internes. Le MP4 original reste dans `private_data/videos`, hors du frontend. Les aperçus JPEG passent par une route authentifiée et ne contiennent pas d'EXIF/GPS.

À l'ouverture d'une ancienne base SQLite, `init_db` sauvegarde la base puis reconstruit `verification_cases` en conservant les identifiants et leurs liens. `APP_ENV=production` empêche l'initialisation et la connexion des comptes d'exemple. Les données fictives existantes restent identifiées.

Le frontend utilise cinq entrées de navigation. Actualités est un état vide jusqu'à la vérification de flux réels. La recherche inversée externe demeure manuelle : les observations, pas les résultats automatiques des services, sont enregistrées comme preuves.

```text
Navigateur React/TypeScript + Vite (127.0.0.1:5173)
          |
          | /api/* avec Bearer JWT (proxy Vite en développement)
          v
FastAPI (127.0.0.1:8000)
  |            |                    |
  |            |                    +-- subprocess c2patool si installé
  |            +-- stockage privé : originals UUID, génération d'aperçus JPEG
  +-- SQLAlchemy -> SQLite (base locale)
```

## Principes

- **Backend autoritatif** : utilisateurs, propriétaires, preuves, décisions, états, analyses et audit viennent du serveur. Interdit d'attribuer le verdict au modèle.
- Authentification : `scrypt` salé, JWT HS256 de 4 heures, secret local généré et non expédié. Démonstration uniquement : stockage du token dans `localStorage` côté frontend.
- Autorisation : seul le propriétaire peut modifier le dossier, les preuves et la conclusion ; seul un rédacteur autre que l'auteur peut relire un dossier explicitement soumis. Le média privé ne peut être prévisualisé que par son propriétaire ou un relecteur habilité. Les archives fictives sont partagées aux utilisateurs authentifiés.
- Import : taille ≤ 10 MiB, contenu décodé et vérifié via Pillow, pixels limités, nom de fichier nettoyé, octets originaux stockés en dehors de Vite. Les miniatures sont générées à la volée sans données GPS EXIF.
- REWIND : pHash 64 bits calculé sur le fichier ; distance Hamming ≤ `PHASH_THRESHOLD` (12). Degrés de similarité visuelle = `100 * (1-distance/64)`, **sans portée probabiliste**.
- C2PA : appelle `c2patool fichier` avec `subprocess.run([binary,path], shell=False, timeout=10)` ; analyse le JSON ; un manifeste valide ne suffit pas pour établir l'authenticité d'un fait ou d'une légende.
- P0 de bout en bout : connexion → import → analyse → REWIND → preuve → verdict humain → rapport privé → impression navigateur.

## Tables

`users`, `media_assets`, `media_analyses`, `verification_cases`, `evidence`, `verdicts`, `source_directory`, `audit_events`. SQLite applique les clés étrangères via `PRAGMA foreign_keys=ON`.

## Déploiement ultérieur

Prévoir : Alembic, `psycopg` pour PostgreSQL, gestion des secrets externalisée, sessions HTTP-only, HTTPS, CSRF, rate limiting, validation approfondie des médias, protection antivirus, quotas, supervision, sauvegardes chiffrées, journalisation non sensible et stratégie de rétention. Les scripts Windows installent et lancent uniquement sur la machine locale.
