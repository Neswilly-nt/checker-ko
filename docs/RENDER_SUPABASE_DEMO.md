# Démonstration temporaire Render + Supabase

Le Blueprint décrit les deux services Render gratuits déjà utilisés pour la démonstration et un projet Supabase gratuit. Les données de démonstration doivent rester fictives. Cette configuration ne valide pas l'application pour des dossiers journalistiques réels.

## Mises à jour automatiques

Les services API et web suivent `develop` et utilisent `autoDeployTrigger: checksPass`. Après la fusion manuelle d'une PR vers `develop`, Render attend la réussite des contrôles GitHub Actions sur le nouveau commit avant de lancer les deux déploiements. Un échec CI bloque ce déploiement automatique. Un build ou un démarrage Render peut encore échouer après la CI : vérifier les deux statuts dans Render, puis tester la connexion et une page qui utilise l'API. Les déploiements des deux services ne sont pas atomiques.

Après la fusion de ce changement, synchroniser une fois le Blueprint dans Render, ou régler **Auto-Deploy → After CI Checks Pass** dans les paramètres de **chacun** des deux services. Vérifier que **Blueprint Auto Sync** est activé si `render.yaml` doit continuer à piloter ces paramètres. Ne pas réimporter le Blueprint comme une nouvelle application : conserver les deux services et leurs secrets existants. Voir [le flux Git de l'équipe](GIT_WORKFLOW.md) pour les branches, PR et contrôles.

## Architecture de session

Le frontend utilise `VITE_CHECKER_API_URL=/api`. Ajouter sur la Static Site Render une règle Rewrite **avant** celle de React Router :

| Source | Destination | Action |
| --- | --- | --- |
| `/api/*` | `https://<nom-du-web-service-api>.onrender.com/api/*` | Rewrite |
| `/*` | `/index.html` | Rewrite |

Render sert les réponses de l'API à l'URL initiale du frontend. Le navigateur garde ainsi une origine unique ; le cookie reste hôte seulement, `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/api`. Le proxy transmet l'origine du navigateur au backend : définir `CHECKER_CORS_ORIGINS` sur l'origine HTTPS exacte de la Static Site, sans chemin, slash final ni wildcard. Le backend exige cet `Origin` et `X-Checker-CSRF: 1` sur le login et chaque écriture par cookie. La CSP du site n'autorise `connect-src 'self'`.

Le Blueprint fournit le Rewrite vers `checker-ko-demo-api.onrender.com`. Si Render refuse ce nom parce qu'il est déjà pris, modifier le nom du service **et** la destination du Rewrite dans le Dashboard. Les noms doivent correspondre exactement.

Une connexion directe du navigateur à un deuxième domaine est prise en charge par `VITE_CHECKER_API_URL=https://<api>/api`, `credentials: include`, CORS avec origine exacte et `CHECKER_COOKIE_SAMESITE=none` (toujours `Secure`). Elle est moins robuste : certains navigateurs bloquent les cookies tiers. Le proxy same-origin est la configuration recommandée.

Pour le mode direct, la CSP du Static Site doit également ajouter l'origine exacte de l'API à `connect-src`; conserver le proxy permet de garder `connect-src 'self'`.

## Ressources et variables

1. Créer manuellement un projet Supabase gratuit **neuf**, dans la région disponible proche de Render. Ne pas réutiliser une base d'équipe ou des données journalistiques.
2. Dans Storage, créer le bucket `checker-private` avec **Public bucket désactivé**. L'application vérifie cette propriété au démarrage; aucun lien public ou URL signée n'est remis au navigateur.
3. Copier la chaîne **Session pooler** depuis Supabase Connect (IPv4) et l'adapter en `postgresql+psycopg://...:5432/postgres?sslmode=require`. Encoder les caractères spéciaux du mot de passe. Le mode transaction (6543) n'est pas utilisé par cette configuration SQLAlchemy/Alembic.
4. Pour une nouvelle installation seulement, synchroniser `render.yaml` après avoir créé les ressources et renseigné les secrets. Variables non secrètes définies dans le Blueprint :

| Service API | Valeur |
| --- | --- |
| `APP_ENV` | `production` |
| `CHECKER_DATA_DIR` | `/tmp/checker-ko` (temporaire, aucun média durable ici) |
| `CHECKER_STORAGE_BACKEND` | `supabase` |
| `CHECKER_SUPABASE_STORAGE_BUCKET` | `checker-private` |
| `CHECKER_DEMO_MODE` | `true` (ne peuple pas le catalogue réel ni les flux RSS) |
| `CHECKER_COOKIE_SAMESITE` | `lax` |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | `2` / `0` |
| `VIDEO_MAX_MB` / `VIDEO_MAX_SECONDS` | `15` / `15` |
| `CHECKER_SECRET` | secret aléatoire unique, 32 caractères minimum |
| `DATABASE_URL` | chaîne session-pooler avec pilote `postgresql+psycopg` et SSL |
| `CHECKER_CORS_ORIGINS` | origine HTTPS exacte du frontend Render |
| `CHECKER_SUPABASE_URL` | URL HTTPS du projet Supabase, sans chemin |
| `CHECKER_SUPABASE_SERVICE_ROLE_KEY` | clé Secret `sb_secret_…` (recommandée) ou ancienne clé `service_role`, uniquement dans les secrets Render |

Pour les nouvelles clés Supabase `sb_secret_…`, l'adaptateur envoie la clé dans l'en-tête `apikey` seulement. Les anciennes clés JWT `service_role` sont envoyées dans `apikey` et `Authorization: Bearer`. Ne jamais fournir une clé `sb_publishable_…` pour cet accès serveur.

Variables Static Site : `VITE_CHECKER_API_URL=/api`. Une variable Vite est publique après compilation : n'y placer aucun secret.

Les migrations Alembic s'exécutent au démarrage du conteneur. Le Web Service gratuit n'a pas de Shell; les commandes d'administration et de sauvegarde se lancent depuis un poste opérateur temporairement configuré avec les variables secrètes, sans les enregistrer dans le dépôt ou l'historique.

Le réglage du stockage ne migre pas les fichiers existants : une base qui référence des objets locaux ne peut pas être basculée vers Supabase sans copier les fichiers et mettre à jour/vérifier leurs références. Pour cette démo, partir d'un projet et d'une base vierges; concevoir et tester un outil de backfill avant toute migration de données existantes.

## Base de démonstration fictive

Après migrations et création/vérification du bucket privé, exécuter depuis l'environnement opérateur, avec le projet Supabase de démo uniquement :

```sh
APP_ENV=production CHECKER_DEMO_MODE=true CHECKER_DEMO_SEED=enabled \
  python -m app.cli seed-demo
```

Le mot de passe est demandé de façon interactive. La commande refuse si la base contient déjà un compte ou un dossier. Elle crée une seule journaliste fictive `demo.journaliste@example.test`, un dessin généré en mémoire, un dossier, une note et un rapport fictifs. L'application n'insère alors ni flux RSS réels ni annuaire institutionnel. `CHECKER_DEMO_SEED` est une autorisation ponctuelle de commande, jamais une variable Render permanente.

Les comptes utilisateurs ne disposent d'aucune route d'inscription publique. Pour ajouter un compte démo, utiliser `python -m app.cli create-user` depuis le poste opérateur. Ne pas y copier de vrais dossiers.

## Sauvegarde et restauration testables

Une sauvegarde complète comprend la base **et** les objets : les sauvegardes PostgreSQL ne contiennent pas les fichiers Storage. Créer un répertoire de sauvegarde privé, chiffré et hors du dépôt; contrôler les quotas avant transfert.

Utiliser la version 3 de Supabase CLI et lier le poste opérateur au projet de démo (`supabase link --project-ref <ref>`). Ne pas enregistrer de jeton dans le dépôt.

```sh
pg_dump --schema=public --format=custom --no-owner --no-acl "$DATABASE_URL" --file checker-ko-demo.dump
supabase storage cp ss://checker-private/ ./checker-private/ --recursive --experimental --remote
```

Vérifier la liste des objets avec `supabase storage ls ss://checker-private/ --recursive --experimental --remote`, conserver le dump et le répertoire ensemble, puis tester une restauration dans **un autre projet Supabase gratuit vierge** : restaurer avec `pg_restore --no-owner --no-acl` dans la base isolée, puis recopier les objets :

```sh
pg_restore --no-owner --no-acl --dbname "$RESTORE_DATABASE_URL" checker-ko-demo.dump
supabase storage cp ./checker-private/ ss://checker-private/ --recursive --experimental --remote
```

Comparer le nombre d'utilisateurs/dossiers/médias, les empreintes SHA-256, puis vérifier connexion, rapport et aperçu de média. **Ne pas exécuter `pg_restore` sur une base contenant des données à conserver.** Le cycle Supabase distant reste à effectuer manuellement; aucun compte cloud ou secret n'est disponible dans cet environnement.

## Limites du palier gratuit

- Render Free Web Service : 0,1 CPU, 512 MiB RAM, arrêt après 15 minutes d'inactivité, démarrage à froid d'environ une minute, filesystem éphémère, pas de disque persistant ni de Shell; ce palier est destiné à l'essai et pas à la production.
- Render peut suspendre les services gratuits si les quotas mensuels de ressources sortantes ou de build sont dépassés. Le premier démarrage avec les migrations et les lectures/écritures Storage peut être lent.
- Supabase Free : projet susceptible d'être mis en pause après une semaine de faible activité. Pas de sauvegardes automatiques de fichiers Storage; l'équipe doit exporter la base et les objets séparément.
- FFmpeg/ffprobe sont inclus dans l'image Docker. L'analyse vidéo est limitée à 15 Mo et 15 secondes pour ce profil, mais la durée peut dépasser les timeouts en charge ou sur un CPU gratuit.
- C2PA Tool n'est pas fourni dans l'image Linux : l'application affiche `indisponible` et ne présente pas cette absence comme une preuve. Ne pas traiter une absence de manifeste comme une conclusion.
- Les tests navigateur locaux et PostgreSQL isolés ne remplacent pas le test final sur les URLs Render réellement attribuées. Ce guide ne constitue pas une déclaration de préparation à la production.
