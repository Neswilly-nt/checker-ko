# État de préparation à la production

**Statut : NON PRÊT POUR LA PRODUCTION.** Cette branche corrige plusieurs risques de l'application et prépare les migrations et le pré-déploiement. Aucun déploiement n'a été effectué. L'ouverture publique reste bloquée tant que les contrôles ci-dessous ne sont pas validés dans un environnement PostgreSQL de préproduction isolé.

## Point de départ vérifié

- `develop` était propre et pointait sur `4306e2015b46a0bb54f50494ca0d875a7d2df8ab` (`merge: finalize trilingual interface`, PR #3).
- Les PR #1, #2 et #3 sont fusionnées. L'Action CI du commit `4306e20` a terminé avec succès. L'échec Action observé concerne l'ancien commit de `main` (`e6adb56`), pas `develop`.
- Le module Actualités v0.5 est bien fusionné : collecte RSS, déduplication, historique de synchronisation, interface de veille et création de dossiers de vérification sont dans `develop` (commits `c596239`, `2f34314`, avec correction `1309b10`). Il ne s'agit pas d'une branche ou PR encore en attente.
- Les sources RSS sont définies côté serveur. Les collectes sont déclenchées par un éditeur. Les publications importées restent des pistes, pas des verdicts.

## Mesures préparées sur cette branche

| Domaine | Constat initial | Mesure apportée | Limite restante |
| --- | --- | --- | --- |
| Sessions JWT | Le navigateur conservait le JWT dans `localStorage`. | Session portée par cookie `HttpOnly`, `SameSite=Lax`, `Secure` en production, durée de 4 h, identifiant de session vérifié en base et révocation au logout. Le navigateur n'envoie plus de jeton Bearer. | Le vol d'une session active reste possible; limiter l'accès aux postes et surveiller les connexions. Valider les cookies derrière le proxy HTTPS de préproduction. |
| CSRF / CORS | CORS était limité aux deux origines locales sans cookies; aucun contrôle CSRF. | CORS à origines configurables avec credentials; header non-simple `X-Checker-CSRF` obligatoire pour login et écritures par cookie; contrôle de l'origine fournie. | Le déploiement doit conserver le proxy de même origine recommandé, configurer exactement l'origine HTTPS et ne jamais utiliser `*`. |
| Permissions | Les dossiers sont privés par propriétaire; un éditeur ne voit les dossiers d'un journaliste qu'après demande de relecture. | Contrôles existants conservés; tests étendus pour rapport privé. Les images originales et aperçus sont servis par une route authentifiée; les vidéos et images-clés restent dans le volume privé. | Vérifier les mêmes cas avec deux comptes distincts dans PostgreSQL de préproduction et les rôles opérationnels réels. |
| XSS | React échappe les textes; aucun rendu HTML brut repéré. Les liens d'articles RSS n'étaient pas filtrés. | Les liens importés sont limités à `http(s)` sans identifiants; DTD/entités XML interdits; CSP et en-têtes de sécurité API en production. | Ajouter également la CSP et HSTS au serveur statique/proxy; effectuer un test navigateur et revue XSS avant ouverture publique. |
| SSRF | Seuls les flux prédéfinis sont collectés; DNS vérifiait seulement certaines plages privées et le contenu était lu avant contrôle de taille. | HTTPS, port 443, adresses résolues globales, redirections désactivées, proxy d'environnement désactivé, lecture en flux plafonnée à 1,5 Mo. | Conserver une règle de sortie réseau n'autorisant que les hôtes RSS attendus; le pinning DNS au socket n'est pas réalisé. |
| Médias | Fichiers image transformés et enregistrés hors webroot; limites de taille, dimensions et type en place. Vidéos analysées sans shell et sans route de téléchargement public. | Les fichiers restent sous `CHECKER_DATA_DIR`; les aperçus sont `no-store`, authentifiés et vérifiés contre le dossier. | Utiliser un volume persistant chiffré, non monté publiquement, et tester restauration conjointe du volume et de la base. |
| Base de données | SQLite local; `create_all` et adaptations historiques spécifiques à SQLite. | Support SQLite local conservé. PostgreSQL utilise `psycopg` et une migration Alembic initiale; l'application ne crée plus le schéma PostgreSQL à son démarrage. | La migration a besoin d'une exécution et d'une vérification PostgreSQL réelle; aucune instance PostgreSQL n'était disponible lors de cet audit. |
| Dépendances Python | La plage Pillow résolvait Pillow 12.3.0, signalé par l'audit de dépendances. | Pillow est désormais contraint à `>=13.0,<14`; `pip-audit -r requirements.txt` ne trouve plus de vulnérabilité dans les versions résolues. | Refaire l'audit sur l'environnement Linux exact de préproduction et à chaque mise à jour. |
| Journaux / secrets | Aucun contrat de production documenté. | `CHECKER_SECRET` obligatoire (32 caractères minimum); secrets injectés à l'exécution; journaux API structurés sans query string ni en-têtes d'authentification. | Configurer rotation, rétention et alertes côté hébergeur; les journaux applicatifs ne remplacent pas les événements d'audit en base. |
| Dépendances frontend | `react-router-dom` 6.30.1 affecté par les avis d'open redirect et d'injection de constructeur React Router. | Passage à React Router DOM 7.18.5 (React 18 supporté, Node 20 minimum); `npm audit` après changement ne signale aucune vulnérabilité. | Refaire l'audit avant chaque mise en production, car les avis et versions évoluent. |

## Contrôles bloquants avant toute annonce de disponibilité

1. Exécuter Pytest, TypeScript, le contrôle i18n, le build frontend et les contrôles de dépendances sur cette branche; conserver leurs résultats dans la PR.
2. Exécuter les migrations `alembic upgrade head` sur une base PostgreSQL vierge, puis tester les permissions, sessions, médias, rapports et sauvegardes sur cette base.
3. Vérifier un cycle de restauration PostgreSQL + fichiers médias depuis une sauvegarde chiffrée.
4. Déployer la procédure de [préproduction](DEPLOYMENT.md) dans un réseau privé, avec TLS, hôtes et origines configurés; ne copier aucune donnée existante.
5. Valider la CSP complète sur les pages statiques, le comportement des cookies en HTTPS, le débit/limitation des connexions et les contrôles de sortie réseau RSS.
6. Effectuer une revue humaine des résultats FR/MG/EN et des règles d'accès de deux journalistes et d'un éditeur.

La version publique ne doit être déclarée prête qu'après fermeture de tous ces points et validation des tests correspondants. Les listes d'avis React Router sont référencées par [GHSA-wrjc-x8rr-h8h6](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6) et [GHSA-337j-9hxr-rhxg](https://github.com/advisories/GHSA-337j-9hxr-rhxg).

## Vérifications locales de cette branche

- Pytest : 28 réussis, 1 ignoré (les binaires/outils médias portables sont absents), 1 avertissement de dépréciation du client de test Starlette.
- Frontend : contrôle TypeScript, contrôle i18n (556 clés), build Vite et `npm audit --audit-level=moderate` réussis; aucune vulnérabilité npm connue.
- Python : `pip-audit -r backend/requirements.txt` réussi après le relèvement de Pillow; aucune vulnérabilité connue dans la résolution actuelle.
- Alembic : `upgrade head` puis `alembic check` réussis sur une SQLite temporaire. Ce résultat valide la révision et la cohérence des modèles, pas l'exécution PostgreSQL.

## Vérifications de la branche Render + Supabase

**État au 3 novembre 2026 : démonstration temporaire en préparation, pas prête pour la production.** Aucun service cloud n'a été créé et aucun déploiement n'a été lancé. Les vérifications ci-dessous utilisent des données synthétiques et une base PostgreSQL Docker jetable.

| Contrôle | Résultat |
| --- | --- |
| Pytest SQLite local | 32 passés, 1 ignoré |
| Pytest PostgreSQL 16 isolé | 32 passés, 1 ignoré |
| `alembic upgrade head` PostgreSQL vierge et `alembic check` | Réussis, aucun écart de schéma |
| RLS avec rôle restreint | Réussi; lecture directe refusée |
| Sauvegarde/restauration PostgreSQL locale | Dump custom restauré dans une seconde base vierge; utilisateur et dossier fictifs relus après restauration |
| TypeScript et i18n | Réussis; 556 clés FR/MG/EN concordantes |
| Build frontend et `npm audit --audit-level=moderate` | Réussis, aucune vulnérabilité modérée ou supérieure détectée |
| `pip-audit` | Aucune vulnérabilité connue dans les dépendances auditées |
| YAML Render et `git diff --check` | Réussis |

L'image Docker API a été construite et démarrée localement; `/api/health` a répondu 200, Alembic a migré la base SQLite du conteneur et FFmpeg était détecté. Un test est ignoré lorsque les outils externes médias ne sont pas disponibles. C2PA Tool n'est pas inclus dans l'image démo et doit être présenté comme indisponible; FFmpeg est inclus et les vidéos sont limitées à 15 Mo et 15 secondes.

L'automatisation du navigateur a été arrêtée par le mécanisme Windows, qui n'a pas pu déterminer l'URL active de Chrome. La connexion, la déconnexion, le rechargement et l'accès à l'image protégée ne sont donc pas validés dans un navigateur réel. Aucun compte Supabase n'est connecté : bucket distant, connectivité Render, test de restauration distante des objets et migrations sur Supabase restent à faire manuellement avec un projet neuf et des données fictives. La restauration PostgreSQL a été testée uniquement dans des bases locales isolées.

Le Blueprint désactive le déploiement automatique et configure un proxy `/api/*` same-origin recommandé pour éviter les cookies tiers. Il faut encore confirmer les domaines Render, le rewrite et les en-têtes reçus dans l'environnement de démonstration. Le disque Render gratuit est éphémère; Supabase Storage doit porter les médias. Les fichiers locaux existants ne sont pas transférés automatiquement lors d'un changement de `CHECKER_STORAGE_BACKEND`; ne pas basculer une base existante sans outil de backfill et vérification des empreintes. Partir d'un projet Supabase vierge. Le plan gratuit, sans SLA et avec ressources limitées, n'est pas destiné à des données réelles ni à un usage durable.

Voir [RENDER_SUPABASE_DEMO.md](RENDER_SUPABASE_DEMO.md) pour les variables, procédures de restauration et étapes manuelles. Une revue humaine et la CI restent requises; ne pas fusionner ni activer le déploiement sans validation.
