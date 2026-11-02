# Accueil compact — Checker-ko v0.4.4

Le 3 novembre 2026, l'accueil a été réduit à un titre court, un seul bouton « Nouvelle vérification », trois indicateurs sur une ligne et une liste des cinq dossiers récents au maximum. Le grand bandeau d'introduction et son second appel à l'action ont été retirés. Chaque ligne récente montre le titre, la date, le statut, le type (photo, vidéo ou texte) et l'ouverture du dossier. Le titre long est tronqué visuellement et reste disponible dans l'attribut `title` et le nom accessible du lien.

Le backend a reçu une modification limitée de `GET /api/cases` : `content_type` est calculé depuis la présence d'une vidéo ou d'un média ; `total` compte les dossiers accessibles au-delà de la limite de 100 éléments renvoyés ; `concluded` compte les dossiers ayant au moins une conclusion enregistrée, y compris ceux en relecture. Aucun schéma ni donnée historique n'a été modifié.

## Mesures dans Chrome

Tests avec une copie isolée de CK-001 à CK-004. À 1366 × 768 et 100 %, l'ancienne section récente commençait à **605 px** et la première ligne finissait à **768 px**. Après modification, la section commence à **263 px** et les quatre lignes se terminent à **558 px** ; la hauteur totale de la page est **768 px**, sans défilement vertical sur cet écran de test.

À 100 %, les tailles 1920 × 1080, 1366 × 768, 1280 × 720, 1024 × 768 et 390 × 844 ont été vérifiées dans Chrome headless. Le contrôle à 125 % utilise une largeur et une hauteur CSS équivalentes, car le zoom natif de l'interface Chrome n'est pas piloté par ce test CDP. Sur les dix mesures : aucun débordement horizontal global, aucun lien de l'accueil hors écran et les cinq entrées de navigation restent présentes. Le menu mobile ouvre « Sources » et une ligne récente ouvre son dossier. Sur mobile, le défilement vertical reste naturel.

Captures locales : [avant, 1366 × 768](../backups/dashboard-v044/before-1366x768.png), [après, 1366 × 768](../backups/dashboard-v044/after-1366x768.png), [avant, mobile](../backups/dashboard-v044/before-390x844.png), [après, mobile](../backups/dashboard-v044/after-390x844.png). Les mesures brutes se trouvent dans `backups/dashboard-v044/*-measurements.json`.

## Validation

- `npm.cmd run check` : réussi.
- `npm.cmd run build` : réussi.
- `python -m pytest -q backend/tests` : 19 tests réussis.
- Aucune hauteur fixe et aucun `overflow-y: hidden` ne masquent la liste.
