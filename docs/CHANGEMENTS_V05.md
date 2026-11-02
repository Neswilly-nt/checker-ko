# Changements v0.5 — Actualités

- Ajout d'une veille RSS persistée en SQLite, avec journal de synchronisation et déduplication.
- Ajout de la page Actualités : recherche, filtres secteur/région/source, tri chronologique, états vide et erreur.
- Ajout de « Vérifier cette information » : création idempotente d'un dossier privé prérempli avec le titre, l'URL et les métadonnées documentées.
- Les régions restent inconnues lorsqu'aucune information documentée ne les établit ; aucun verdict n'est produit automatiquement.
- Migration additive : les nouvelles tables n'altèrent ni les dossiers ni les médias existants.
