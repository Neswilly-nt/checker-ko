# Checker-ko v0.4.1 — refonte compacte des dossiers

## Fichiers modifiés

- `frontend/src/CaseWorkspace.tsx` : espace de travail du dossier et fiche dédiée.
- `frontend/src/App.tsx` : raccordement des routes existantes au nouvel espace de travail ; suppression de l'ancien rendu du dossier.
- `frontend/src/styles.css` : styles compacts, adaptés à 1366 × 768 et au mobile.
- `frontend/vite.config.ts` : ports du frontend et de l'API configurables pour les tests locaux, avec les mêmes valeurs par défaut.
- `scripts/smoke-v041.py` : test navigateur facultatif via Chrome DevTools.

## Changements visuels et interactions

- L'affirmation apparaît une seule fois dans un en-tête court avec numéro, statut, nombre de preuves et état de la conclusion.
- Trois actions visibles ouvrent à la demande la recherche, le formulaire rapide de preuve ou la conclusion. Les champs avancés de preuve (date, organisme, métadonnées utiles, détails) et les détails techniques sont repliables.
- « Mes recherches » est une liste dense des preuves, avec source, observation, relation, consultation et modification. L'état vide reste court.
- Le verdict est rédigé dans un panneau ouvert volontairement ; l'historique et la relecture facultative restent accessibles.
- « Voir ma fiche » apparaît après conclusion et mène à `/dossiers/:id/rapport`. Le rapport A4 n'est plus rendu sous le dossier.
- Les dossiers photo, vidéo et texte gardent leurs recherches adaptées. Les images-clés vidéo, REWIND WEB, pHash, EXIF, C2PA et les archives restent disponibles dans des panneaux repliables.
- Les boutons et champs ont des états de focus visibles. Sur mobile, les trois actions et les preuves se réorganisent sans débordement horizontal.

## Tests exécutés

- `npm.cmd run check` : réussi.
- `npm.cmd run build` : réussi.
- `backend\.venv\Scripts\python.exe -m pytest -q` : 17 tests réussis.
- Chrome sans interface sur **une copie isolée** de la base contenant CK-004 : affichage de CK-004, ouverture du formulaire de preuve, création et modification d'une preuve, ouverture et enregistrement d'un verdict, consultation du rapport dédié, contrôle de la largeur mobile. La base d'origine n'a pas été modifiée. Captures dans `backups/browser-v041/`.

## Limites

- Le test navigateur est un contrôle ciblé ; il ne couvre pas tous les parcours photo et vidéo ni tous les navigateurs.
- La recherche inversée externe reste manuelle et dépend des services tiers.
- Les formulaires ne sauvegardent pas automatiquement les champs non soumis ; seule la preuve enregistrée est persistée.
