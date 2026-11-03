# API REST — Checker-ko

URL locale : `http://127.0.0.1:8000`. Swagger interactif : `/docs`. Authentification des routes privées : `Authorization: Bearer <jeton>`.

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/health` | État de l'API, FFmpeg/ffprobe et c2patool |
| POST | `/api/auth/login` | Connexion locale et JWT |
| GET | `/api/auth/me` | Utilisateur courant |
| GET | `/api/cases?q=` | Dossiers accessibles, `content_type` (`photo`, `video`, `texte`) et compteurs `total` / `concluded` calculés sur tous les dossiers accessibles |
| POST | `/api/cases` | Nouveau dossier texte ou lien, avec `region` facultative |
| GET | `/api/regions` | Référentiel national des 24 régions et options supplémentaires |
| POST | `/api/media/upload` | Multipart (`file`, `caption`, `source_url`, `sector`, `region`) |
| POST | `/api/video/upload` | Multipart MP4 (`file`, `caption`, `source_url`, `sector`, `region`) |
| GET | `/api/cases/{id}` | Dossier, média, correspondances, preuves, verdicts |
| POST | `/api/cases/{id}/analyze` | Réexaminer l'état C2PA |
| GET | `/api/cases/{id}/matches` | Correspondances internes uniquement |
| POST | `/api/cases/{id}/evidence` | Ajouter un élément |
| PUT/DELETE | `/api/cases/{id}/evidence/{evidence_id}` | Modifier / retirer |
| GET/POST/PATCH | `/api/cases/{id}/evidence/{evidence_id}/assessment` | Consulter ou documenter l'évaluation de cette preuve |
| GET | `/api/cases/{id}/evidence/{evidence_id}/assessment/history` | Historique traçable des révisions |
| GET | `/api/cases/{id}/assessments/summary` | Éléments favorables, contraires, contexte et incertitudes |
| POST | `/api/cases/{id}/verdict` | Conclure par intervention humaine |
| POST | `/api/cases/{id}/request-review` | Relecture facultative |
| POST | `/api/cases/{id}/review` | Décision du rédacteur distinct de l'auteur |
| GET | `/api/cases/{id}/report` | Données structurées du rapport privé |
| GET | `/api/media/{id}/preview` | Aperçu JPEG privé avec autorisation |
| GET | `/api/sources?sector=&region=&organization_type=&q=` | Annuaire institutionnel actif |
| GET | `/api/sources/{id}` | Détail d'une institution ; archives réservées à l'éditeur |
| POST/PUT | `/api/sources`, `/api/sources/{id}` | Administration des fiches, rôle `editor` |

## Exemples de payloads

`POST /api/auth/login` :

```json
{"email":"journaliste@checker.local","password":"Journaliste2026!"}
```

Réponse (schéma, jeton illustratif non valide) :

```json
{"access_token":"<jeton-JWT-fourni-par-API>","token_type":"bearer","user":{"id":1,"name":"Journaliste Démo","email":"journaliste@checker.local","role":"journalist"}}
```

`POST /api/cases/1/evidence` :

```json
{"title":"Archive interne fictive","url":null,"date_of_source":null,"note":"Similitude visuelle à confirmer","relation_type":"contexte","archived_media_id":1}
```

`POST /api/cases/1/verdict` :

```json
{"verdict":"Non déterminé","reasoning":"Les éléments réunis ne permettent pas de confirmer la date et le lieu de cette photo."}
```

`GET /api/health`, exemple avec outils portables :

```json
{"status":"ok","c2patool_installed":true,"ffmpeg_installed":true,"mode":"development"}
```

Un média JSON contient `analysis.tool_status`, `analysis.c2pa_status`, `analysis.claim.signature`, `analysis.claim.emetteur`, `analysis.warnings`, `sha256`, `phash`, `exif` filtrés. Les valeurs sont calculées depuis l'image, pas simulées.

## Permissions et erreurs

- 401 : jeton absent ou invalide ; 403 : dossier non autorisé ; 404 : ressource introuvable ; 413 : plus de 10 MiB ; 415 : image invalide ; 422 : entrée incorrecte.
- Seuls les fichiers propres ou les archives fictives partagées participent aux correspondances accessibles.
- `review` exige un statut `review_requested` et un rôle `editor` distinct du propriétaire.
- Toute décision humaine enregistre un nouvel enregistrement `verdicts` et une trace d'audit.
- `GET /api/sources?include_archived=true` est réservé au rôle `editor` et montre les anciennes fiches fictives identifiées comme archives.

## Annuaire professionnel v0.7.1

- `POST /api/sources` et `PUT /api/sources/{id}` : rôle `editor`. Une fiche marquée vérifiée ou partiellement vérifiée exige `reference_url` et `last_checked_at` au format `YYYY-MM-DD`.
- `PATCH /api/sources/{id}/archive` : rôle `editor`, corps `{"archived":true}` pour archiver ou `false` pour réactiver. La fiche et ses contacts ne sont pas supprimés.
- `POST /api/sources/{id}/contacts` et `PUT /api/sources/{id}/contacts/{contact_id}` : rôle `editor`. Au moins une coordonnée publique, `reference_url` et `verified_at` sont obligatoires. La liste des contacts figure dans `GET /api/sources` et `GET /api/sources/{id}`.

## Observations statistiques v0.7.1

`POST /api/statistics/observations` est réservé au rôle `editor`. Le corps contient `publication_key`, `indicator`, `value`, `unit`, `year`, une `region` facultative et `source_locator` (page/table/figure/section). La clé sélectionne un document du catalogue contrôlé ; son titre et son URL sont stockés comme provenance. `GET /api/statistics?q=&sector=` retourne ces observations sous chaque publication. Le catalogue seul n’introduit aucune valeur numérique.
# Catalogue documentaire

`GET /api/statistics?q=&sector=` retourne les publications documentées accessibles à l’utilisateur, avec les observations persistées sous leur publication. `observation_count` reflète le nombre de résultats après filtrage. Le catalogue ne collecte pas automatiquement les documents ni les chiffres.
