# Outils médias Windows — v0.4.3

Checker-ko détecte d'abord `FFMPEG_PATH`, `FFPROBE_PATH` et `C2PATOOL_PATH` lorsqu'elles pointent vers des fichiers exécutables ; sinon il cherche `ffmpeg`, `ffprobe` et `c2patool` dans `PATH`. Le démarrage ne requiert aucun de ces outils pour les dossiers texte et photo. L'API `GET /api/health` expose leur disponibilité.

Dans PowerShell, depuis la racine du projet :

```powershell
where.exe ffmpeg
where.exe ffprobe
where.exe c2patool
ffmpeg -version
ffprobe -version
c2patool -V
```

La version portable officielle de c2patool 0.28.4 provient de https://github.com/contentauth/c2patool/releases/tag/v0.28.4. L'archive Windows `v0.28.4-x86_64-pc-windows-msvc.zip` a été contrôlée avec SHA-256 `00e5bcfef95fcf913cc3d67825d7d50ea1eb1180c7fdbef746c9ce3b65e272f1`. Pour cette installation locale :

```powershell
$env:C2PATOOL_PATH=(Resolve-Path '.\tools\media\c2patool\c2patool\c2patool.exe').Path
& $env:C2PATOOL_PATH -V
```

FFmpeg pour Windows est proposé par la page officielle https://ffmpeg.org/download.html, qui renvoie vers les builds de https://www.gyan.dev/ffmpeg/builds/. Après extraction d'un build `essentials`, affecter les deux chemins :

```powershell
$env:FFMPEG_PATH=(Resolve-Path '.\tools\media\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe').Path
$env:FFPROBE_PATH=(Resolve-Path '.\tools\media\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffprobe.exe').Path
& $env:FFMPEG_PATH -version
& $env:FFPROBE_PATH -version
```

Les deux outils sont maintenant installés sous `tools/media/`. Sans variable explicite, Checker-ko détecte ces copies portables au démarrage. Les variables ci-dessus restent utiles pour choisir une autre version ; elles sont propres à la session PowerShell. La version FFmpeg installée est `9.0.2-essentials_build` et l'archive `ffmpeg-release-essentials.7z` a été vérifiée avec SHA-256 `4705843ccaaf54257c16ad90f3e952ece33c17df964ecf7bfdbb0f49c7171077` publié par le distributeur. La copie ZIP incomplète ne doit pas être utilisée.

Pour vérifier les copies portables :

```powershell
& .\tools\media\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe -version
& .\tools\media\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffprobe.exe -version
& .\tools\media\c2patool\c2patool\c2patool.exe -V
```

Essais réels c2patool : l'image JPEG de démonstration sans manifeste retourne `absent` ; `sample/C.jpg` livré avec l'archive officielle retourne `present`, avec émetteur non approuvé ; un octet modifié dans l'image signée retourne `non_fiable` et `assertion.dataHash.mismatch` ; un fichier texte non pris en charge retourne `erreur`. Le test d'outil absent est couvert par Pytest. Aucun de ces états ne valide la scène photographiée.

Essai vidéo réel : `test-v043.mp4`, vidéo synthétique de quatre secondes générée localement par FFmpeg, a été importée via l'API, avec trois images clés, miniatures récupérées et comparaison d'archives appelée pour chacune. Un MP4 invalide est refusé par l'API. `py7zr` a été installé uniquement pour tenter l'extraction ; son filtre BCJ2 ne suffisait pas. L'extraction finale a utilisé `7zr.exe` depuis la version officielle de https://www.7-zip.org/download.html.
