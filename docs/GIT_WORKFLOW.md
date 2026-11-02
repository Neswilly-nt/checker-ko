# Travail Git en équipe

`main` représente la version stable et `develop` est la branche d'intégration active. Pour Checker-ko, travailler et pousser directement sur `develop`; ne pas créer de branche de fonctionnalité ni ouvrir de Pull Request pour ce flux. Synchroniser `develop` avec `origin/develop` avant de commencer. Garder les commits cohérents, en Conventional Commits, et vérifier les contrôles CI après le push. Éviter les commits qui cassent volontairement l'application.

Utiliser des messages Conventional Commits, par exemple `feat(video): ...`, `fix(ui): ...`, `test(api): ...`, `docs: ...` ou `chore(repo): ...`. Garder chaque commit cohérent et vérifiable. Avant une Pull Request, lancer `npm run check` et `npm run build` dans `frontend/`, puis `python -m pytest -q` dans `backend/`. La CI répète ces contrôles sur les pushes et Pull Requests vers `main`.

Ne jamais ajouter à Git `backend/private_data/`, des bases SQLite, des médias d'enquête, des exports PDF, des sauvegardes, des fichiers `.env` réels, des secrets ou des copies locales des outils médias. Vérifier `git status --short`, `git diff --cached --name-only` et le contenu indexé avant chaque commit. `.gitignore` protège les chemins connus, mais ne remplace pas une revue. Si un secret est publié, interrompre sa diffusion, le révoquer et coordonner la correction avec l'équipe ; ne pas réécrire l'historique partagé sans accord.

Les fixtures de `backend/demo_assets/` sont fictives et nécessaires aux tests. Les archives privées restent sur le poste de l'équipe, hors du dépôt et de la CI. Les nouvelles données de test doivent être synthétiques ou accompagnées des droits nécessaires.

Pour mettre à jour `develop` : récupérer `origin/develop`, intégrer ses changements localement et relancer les tests. Ne jamais utiliser `git push --force`. Les fonctionnalités photo, vidéo, texte, preuves, sources et conclusions doivent rester couvertes lors de leur modification.

## Avis de dépendances

Le contrôle npm local a signalé deux avis de sévérité modérée liés à React Router 6. Ils demandent un examen ciblé avec `npm audit` et une mise à jour testée, sans `npm audit fix --force` ni migration majeure automatique. Le projet n'est pas prêt pour une exposition publique avant une revue de sécurité plus large ; voir [les limites](LIMITES.md).
