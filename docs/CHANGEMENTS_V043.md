# Checker-ko v0.4.3 — état vérifié

## Terminé

- Sauvegarde du projet avant modification dans `backups/pre-v043-20261102-230553` ; sauvegarde automatique SQLite `checker.db.pre-v043-*.bak` avant migration du schéma.
- Migration additive, rejouable, des sources et des régions. Les dix organismes fictifs sont archivés, les cinq institutions documentées sont actives, et les identifiants des dossiers, preuves, conclusions et médias sont conservés.
- Annuaire compact avec recherche, secteur, région, type, détail, lien officiel et ajout au carnet d'un dossier. Édition réservée à la rédaction.
- Référentiel central des 24 régions, partagé par les sources et les dossiers photo, vidéo et texte.
- Correction de la largeur et du retour à la ligne du slogan de la barre latérale. CSS responsive de l'annuaire sans masquage global du débordement.
- Configuration des chemins exécutables FFmpeg, ffprobe et c2patool ; analyse C2PA distinguant manifeste absent, certificat non approuvé et échec de validation.

## Vérifications

- Migration sur copie d'une sauvegarde antérieure : deux passages sans doublon, dix anciennes fiches archivées, cinq fiches réelles actives, clés étrangères valides.
- `pytest` : 19 tests réussis, dont un essai MP4 et C2PA sur les exécutables réels.
- `npm run check` : réussi.
- `npm run build` : réussi.
- FFmpeg et ffprobe 9.0.2 : MP4 synthétique de 4 secondes importé par l'API, durée et dimensions contrôlées, trois images clés, miniatures et recherche d'archives vérifiées.
- c2patool 0.28.4 : exécution réelle sur image sans manifeste, image C2PA fournie par le projet et image altérée.
- Chrome headless : 112 mesures sur quatre pages, sept résolutions et quatre largeurs CSS équivalentes aux zooms demandés ; aucun débordement global ni slogan hors de la barre latérale.
- Chrome headless : ouverture de CK-004 et ajout d'une institution au carnet sur une copie des données historiques.

## Limites et dépendances

- Les fichiers FFmpeg et c2patool sont détectés automatiquement dans `tools/media` ou par les variables de chemin.
- Les contacts directs des institutions restent non renseignés faute de vérification indépendante.
- `npm audit --omit=dev` signale deux avis modérés liés à React Router 6 ; la version corrigée indiquée est une mise à jour majeure.
- Les essais Chrome aux résolutions et zooms demandés sont documentés séparément dans `TESTS_RESPONSIVE.md`.

## Redémarrage Windows

Ouvrir deux terminaux PowerShell depuis la racine du projet :

```powershell
cd .\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd .\frontend
npm.cmd run dev
```

Ouvrir `http://127.0.0.1:5173/`. L'API utilise la base locale `backend/private_data/checker.db` si aucune variable d'environnement ne la remplace.
