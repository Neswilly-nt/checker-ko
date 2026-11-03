# Architecture Checker-ko

Checker-ko combine un frontend React/TypeScript et une API FastAPI. Le navigateur ne reçoit que des données JSON et des aperçus JPEG; les originaux restent dans un répertoire de données privé.

```text
Navigateur React + Vite / frontend statique
          |
          | même origine HTTPS en production (/api)
          v
Proxy TLS -> FastAPI -> SQLAlchemy -> PostgreSQL (production)
                         |              SQLite (développement local)
                         +-> volume privé images/vidéos
```

## Identité et permissions

- Les mots de passe sont hachés avec scrypt salé. Les JWT HS256 durent quatre heures et portent un identifiant de session stocké en base.
- Le navigateur utilise un cookie `HttpOnly`, `SameSite=Lax` et `Secure` en production. Le logout révoque l'identifiant côté serveur. Le Bearer reste disponible uniquement en développement et tests.
- Les écritures via cookie exigent `X-Checker-CSRF: 1`; CORS n'autorise que les origines configurées avec credentials.
- Un journaliste accède à ses dossiers. Un éditeur peut accéder à un dossier appartenant à un autre journaliste seulement après demande de relecture; il ne peut pas approuver son propre dossier.
- Rapports, images et aperçus passent par des routes authentifiées. Les originaux vidéo et images sont hors du répertoire servi par le frontend.

## Persistance et fichiers

- SQLite reste le choix sans configuration locale. Ses adaptations de schéma historiques sauvegardent la base avant toute reconstruction et conservent les identifiants et relations.
- PostgreSQL utilise psycopg et le schéma est géré par Alembic. Le démarrage de l'application ne crée pas automatiquement les tables PostgreSQL.
- `CHECKER_DATA_DIR` contient base SQLite locale et/ou fichiers privés selon l'environnement. Pour PostgreSQL, ce répertoire doit être un volume persistant non public.
- Les images acceptées sont JPEG, PNG et WebP (10 Mio, 25 millions de pixels maximum). Les MP4 sont limités en taille, durée et dimensions; ffprobe/ffmpeg sont appelés sans shell et avec délais.
- Les aperçus sont générés sans EXIF/GPS, authentifiés et `no-store`. C2PA et pHash produisent des indices, jamais une décision de vérité.

## Actualités, sécurité et exploitation

- La veille v0.5 importe des flux RSS contrôlés par le serveur. Elle limite les hôtes/adresses, ne suit pas les redirections, borne le flux à 1,5 Mo, refuse les entités XML et n'accepte que des liens d'articles HTTP(S).
- Les textes sont affichés par React, sans `dangerouslySetInnerHTML`. Les en-têtes API incluent `no-store`, `nosniff`, `Referrer-Policy`, `X-Frame-Options` et une CSP en production; le proxy doit également appliquer les protections aux pages statiques et HSTS.
- Les journaux applicatifs vont vers stdout/stderr et ne contiennent ni corps, cookie, JWT, mot de passe ni query string. Les événements d'audit éditorial restent séparés en base.
- Le déploiement préproduction et les limites restantes sont décrits dans [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) et [DEPLOYMENT.md](DEPLOYMENT.md). Checker-ko n'est pas déclaré prêt pour la production à ce stade.
