# Checker-ko v0.8 — vérification multimédia

## Changements

- Les trois images extraites par FFmpeg conservent désormais leur horodatage en secondes. Dans le dossier, le journaliste peut sélectionner une image-clé, voir les archives qui lui ressemblent, la comparer côte à côte et l'ajouter au carnet comme média du dossier.
- Les publications sociales peuvent être consignées avec leur URL, leur plateforme, le compte affiché, la date de publication affichée et la date de captation séparée. Les champs non connus restent vides. Cette saisie ne vérifie pas l'identité d'un compte et n'accède à aucun contenu privé.
- Les résultats pHash sont affichés comme un nombre de différences sur 64 bits. Une comparaison visuelle et son indicateur n'établissent ni identité, ni authenticité, ni date, ni lieu.
- Google Lens et TinEye restent des recherches déclenchées manuellement. La copie nettoyée est téléchargée à la demande; le média n'est jamais transmis automatiquement. Le journaliste conserve ses constatations dans le carnet existant.
- La fiche imprimable reprend la provenance sociale, les observations et les images-clés conservées, en laissant la conclusion à la validation humaine.

## Données et migrations

La migration est additive : ajout de `video_timestamp_seconds` à `media_assets`, ajout de `media_id` à `evidence` et création de `case_social_posts`. Les images sources, dossiers, preuves et conclusions ne sont pas supprimés. Le script `backend/tests/check_existing_migration.py` exécute la migration sur une copie de la base locale et vérifie les comptes, les colonnes attendues et les clés étrangères.

Les images restent dans le stockage privé. Les URL de prévisualisation exigent l'authentification et les comparaisons n'acceptent que les médias du dossier ou les archives déjà accessibles à l'utilisateur.

## Validation

- `python -m pytest -q` : 26 tests réussis, dont traitement réel d'une image et d'une vidéo MP4 avec les outils locaux quand ils sont présents.
- `npm run check` : réussi.
- `npm run build` : réussi après correction des types multimédias.
- Migration sur copie de `backend/private_data/checker.db` : dossiers et preuves conservés, colonnes et table sociales créées, aucune violation de clé étrangère.

Les contrôles portent sur les outils FFmpeg et C2PA existants. Checker-ko ne déduit pas de verdict d'authenticité à partir d'une similarité visuelle ou de métadonnées.
