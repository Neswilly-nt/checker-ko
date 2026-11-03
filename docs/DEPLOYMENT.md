# Préparation d'un déploiement de préproduction

Pour le profil de démonstration temporaire gratuit, consulter [Render + Supabase](RENDER_SUPABASE_DEMO.md). Ce profil utilise exclusivement un projet Supabase neuf et des dossiers fictifs.

Cette procédure prépare une installation reproductible dans un réseau de préproduction privé. Elle ne publie pas le service et ne réutilise pas la base SQLite, les comptes de démonstration ou les fichiers présents sur un poste de développement.

## Architecture cible

- Nginx ou un proxy équivalent termine TLS et sert le build frontend statique.
- Le navigateur et `/api` utilisent la même origine HTTPS. Le proxy transmet `/api` à Uvicorn sur une interface locale, non exposée.
- PostgreSQL est privé, avec TLS sur le lien applicatif si la base est distante.
- `CHECKER_DATA_DIR` est un volume persistant privé contenant images, vidéos et secrets locaux éventuels; il n'est jamais un répertoire servi par Nginx.
- Accès réseau à la préproduction limité par VPN, pare-feu ou allowlist IP. Aucun port API ou PostgreSQL n'est ouvert au public.

## Pré-requis

- Hôte Linux géré, Python 3.11+, Node.js 20+, PostgreSQL supporté, Nginx avec certificat TLS interne ou certificat émis pour l'environnement privé.
- Outils FFmpeg/ffprobe installés côté serveur pour conserver l'analyse vidéo; `C2PATOOL_PATH` peut pointer vers le binaire C2PA si celui-ci est installé et vérifié.
- Un rôle PostgreSQL dédié, sans droits superutilisateur, et un gestionnaire de secrets de l'hébergeur.
- Un répertoire de données dédié, propriétaire du compte système de l'application, permissions `0700`; sauvegardes chiffrées séparées.

## Installation reproductible

1. Récupérer la branche de la PR dans un répertoire neuf, vérifier le commit et installer les dépendances Python depuis `backend/requirements.txt`. Construire le frontend avec `npm ci` puis `npm run build` depuis `frontend/`.
2. Créer une base PostgreSQL vide et un rôle applicatif à privilèges minimaux. N'importer aucune base locale ni aucune image de `private_data`.
3. Injecter dans l'environnement de service :

   - `APP_ENV=production`
   - `DATABASE_URL=postgresql+psycopg://...` avec TLS (`sslmode=require` ou paramètre équivalent du fournisseur)
   - `CHECKER_SECRET`, aléatoire, dédié à cet environnement, d'au moins 32 caractères
   - `CHECKER_DATA_DIR`, chemin absolu vers le volume privé
   - `CHECKER_CORS_ORIGINS=https://<hôte-interne-de-préproduction>` (origine exacte, sans wildcard)
   - `LOG_LEVEL=INFO`, `FFMPEG_PATH` et `FFPROBE_PATH` vers les exécutables validés

   Les valeurs réelles sont fournies par le gestionnaire de secrets et ne sont jamais commitées dans `.env`.

4. Dans `backend/`, exécuter `python -m alembic upgrade head`. Cette migration de base crée le schéma initial; son downgrade est volontairement bloqué pour éviter la suppression des données. Les migrations futures doivent être additives ou inclure un plan de conservation/restauration vérifié.
5. Créer un éditeur d'amorçage par console sécurisée : `python -m app.cli create-user --email <adresse> --name <nom> --role editor`. Le mot de passe est saisi et confirmé sans apparaître dans l'historique shell. Créer ensuite chaque compte journaliste de la même manière; aucune création de compte publique ni aucun compte de démo n'est activé en production.
6. Lancer l'application sous un compte système non privilégié, par exemple `uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips=127.0.0.1`. N'exposer Uvicorn qu'au proxy local.
7. Servir `frontend/dist` via Nginx; router `/api/` vers Uvicorn et les autres chemins vers `index.html`. Activer TLS, HSTS, CSP, `X-Content-Type-Options`, `Referrer-Policy`, limites de débit sur login/téléversements et plafond de taille vidéo/image. Ne pas activer de mise en cache pour `/api/`.
8. Rendre la préproduction accessible uniquement via VPN/allowlist. Vérifier `/api/health`, login, cookie `HttpOnly; Secure`, logout/révocation, uploads, affichage vidéo, rapports privés et absence d'accès croisé entre comptes. Utiliser uniquement les données synthétiques de test.

Le serveur ne crée pas automatiquement les tables PostgreSQL. Ne pas contourner Alembic avec `Base.metadata.create_all`.

## Exemple de proxy préproduction

Adapter l'adresse privée, le réseau VPN et les chemins de certificat à l'hôte; le serveur Nginx ne doit pas écouter sur une interface publique.

```nginx
# Dans le bloc http de nginx.conf
limit_req_zone $binary_remote_addr zone=checker_login:10m rate=5r/m;

server {
    listen 10.20.0.10:443 ssl;
    server_name checker-preprod.internal.example;
    allow 10.20.0.0/16;
    deny all;

    ssl_certificate     /etc/ssl/private/checker-preprod.crt;
    ssl_certificate_key /etc/ssl/private/checker-preprod.key;
    root /srv/checker-ko/frontend/dist;
    client_max_body_size 60m;

    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location = /api/auth/login {
        limit_req zone=checker_login burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_read_timeout 60s;
    }
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

La limite de login est un exemple initial, à ajuster au trafic et aux usages légitimes. Ajouter une politique de limitation distincte sur les téléversements et vérifier cette configuration par un scan HTTP avant de considérer la préproduction validée.

## Sauvegardes et journaux

- Sauvegarder PostgreSQL en format custom avec `pg_dump`; chiffrer avant transfert vers le stockage de sauvegarde et appliquer une rétention documentée.
- Sauvegarder aussi `CHECKER_DATA_DIR`. Pour conserver les relations entre dossiers et médias, prendre un snapshot cohérent ou suspendre les écritures pendant la capture coordonnée base + volume.
- Tester périodiquement `pg_restore` dans une instance isolée, la lecture des dossiers et l'accès aux médias restaurés. Une sauvegarde non restaurée n'est pas validée.
- Envoyer stdout/stderr vers le collecteur de journaux de l'hébergeur. Les lignes applicatives contiennent méthode, chemin sans query string, statut et durée; ne jamais ajouter cookies, JWT, mots de passe, corps des requêtes ou données de dossier.
- Surveiller erreurs 401/403/5xx, échecs de collecte RSS, espace disque du volume et erreurs de sauvegarde; configurer rotation et rétention hors de l'application.

## Retour arrière et données existantes

- Avant une mise à jour, créer et vérifier une sauvegarde PostgreSQL et du volume médias; appliquer la migration en préproduction et comparer le schéma avant/après.
- Ne pas exécuter de downgrade destructif. En cas d'échec, restaurer la sauvegarde dans une instance isolée puis basculer le service seulement après validation.
- Les données locales SQLite restent dans leur installation d'origine. Leur transfert éventuel vers PostgreSQL nécessite une procédure séparée, un export chiffré, une correspondance de schéma contrôlée et une validation explicite; cette procédure ne copie aucune donnée existante.
- Aucun déploiement, transfert de données ni ouverture publique n'est effectué par cette branche.
