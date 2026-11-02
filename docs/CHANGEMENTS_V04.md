# Checker-ko v0.4 — travaux de phase 1

## Réalisé

- Navigation principale à cinq entrées : Accueil, Vérifier, Actualités, Sources, Mes vérifications. La page Actualités présente un état vide explicite : aucun flux n'est encore vérifié.
- Création de dossiers photo, vidéo MP4 ou texte/lien. Les dossiers sans image conservent les preuves et la conclusion humaine.
- Vidéo : contrôle du conteneur MP4, `ffprobe` pour la durée et la résolution, trois images-clés via `ffmpeg`, limites configurables de 50 Mo et 30 s, délai d'exécution de 15–20 s par commande. Les images-clés sont comparables aux archives et utilisables dans REWIND WEB.
- REWIND WEB : action principale de recherche, copie JPEG sans EXIF/GPS, choix Google Lens ou TinEye, saisie des observations humaines.
- Dossiers existants conservés. La migration SQLite rend `verification_cases.asset_id` facultatif et crée une sauvegarde horodatée avant modification. Une copie complète du dossier `private_data` a été créée avant les travaux.
- `APP_ENV=development|production` : les comptes et archives fictives ne sont créés automatiquement qu'en développement ; les comptes d'exemple existants sont refusés en production.

## Limites connues

- La vidéo n'est disponible que si `ffmpeg` et `ffprobe` sont installés. Le binaire était absent du poste de test : le traitement réel n'a donc pas été exécuté avec un MP4 dans cet environnement.
- L'interface conserve des vues techniques et le rapport existants. Le parcours vidéo affiche une image-clé principale et permet de choisir une autre image-clé pour REWIND.
- Les dossiers texte n'ont pas de miniature. La région saisie est consignée dans l'audit ; une colonne et un filtre régionaux viendront en phase 2.
- `APP_ENV=production` évite les comptes d'exemple, mais ne rend pas encore l'application prête pour Internet : le jeton reste dans `localStorage`, et HTTPS, limites de connexion et migrations PostgreSQL restent à préparer.
- `npm audit` signale deux avis de sévérité modérée dans React Router. La correction proposée impose le passage majeur à v7 et n'a pas été appliquée automatiquement.

## Vérifications exécutées

- Backend : `backend\.venv\Scripts\python.exe -m pytest -q` — 17 tests réussis, dont une simulation complète d'extraction de trois images-clés et de leur comparaison.
- Migration vérifiée sur une copie de la base existante : 3 dossiers, 2 preuves, 2 conclusions et 6 médias conservés, sans erreur de clé étrangère. Commande : `backend\.venv\Scripts\python.exe backend\tests\check_existing_migration.py` depuis la racine.
- Frontend : `npm.cmd run check` — réussi ; `npm.cmd run build` — réussi hors du bac à sable, Vite a produit `dist`.
- `npm.cmd audit` — terminé avec deux avis modérés ; aucune correction forcée.

Voir [ROADMAP.md](ROADMAP.md) pour la suite et [INSTALLATION_WINDOWS.md](INSTALLATION_WINDOWS.md) pour les commandes.
