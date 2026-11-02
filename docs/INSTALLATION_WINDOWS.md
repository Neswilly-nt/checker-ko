# Installation Windows

Depuis le dossier `checker-ko` :

```powershell
.\scripts\setup-windows.bat
.\scripts\start-all.bat
```

Ouvrir `http://127.0.0.1:5173`. Les comptes locaux de développement figurent dans le README. Pour tester :

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm.cmd run check
npm.cmd run build
npm.cmd audit
```

Si PowerShell bloque `npm.ps1`, utiliser `npm.cmd` comme ci-dessus. La base et les images privées se trouvent dans `backend\private_data` par défaut. Sauvegarder ce dossier avant déplacement ou mise à jour. La migration v0.4 crée aussi un fichier `checker.db.pre-v04-<date>.bak` avant de rendre l'image facultative pour un dossier.

## Dépendances facultatives

- `ffmpeg` et `ffprobe` sur le `PATH` : nécessaires aux MP4. Installer les deux exécutables provenant du projet FFmpeg, puis redémarrer l'API. Sans eux, les photos et les dossiers texte restent disponibles.
- `c2patool` sur le `PATH` : lecture facultative de manifestes. Son absence indique une analyse indisponible, jamais une preuve de manipulation.

Les limites vidéo se règlent par `VIDEO_MAX_MB` et `VIDEO_MAX_SECONDS`. `APP_ENV=development` est le défaut local ; `APP_ENV=production` désactive les comptes d'exemple. Ne pas exposer le serveur sur Internet avant les travaux de sécurité de phase 4.
