# Travail Git en équipe

`develop` est la branche intégrée et celle que suivent les deux services Render. `main` reste la branche stable du dépôt. Chaque modification passe par une branche personnelle et une Pull Request (PR) vers `develop`. Le merge est une décision humaine : aucun merge automatique n'est configuré.

## Première contribution

Le propriétaire du dépôt invite les personnes qui doivent pousser des branches directement : GitHub → dépôt `Neswilly-nt/checker-ko` → **Settings** → **Collaborators and teams** → **Add people**. Chaque personne accepte l'invitation et configure son accès GitHub. Une personne sans accès en écriture peut forker le dépôt et ouvrir une PR depuis son fork. Ne partager ni compte GitHub ni jeton personnel.

```powershell
git clone https://github.com/Neswilly-nt/checker-ko.git
cd checker-ko
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c feat/ma-modification
```

Si le dépôt est déjà cloné, commencer à `git fetch origin`. Choisir un nom de branche distinct par modification (`feat/...`, `fix/...`, `docs/...`). Un collaborateur utilisant un fork remplace `origin` par le nom de son propre remote pour le push et choisit `Neswilly-nt/checker-ko:develop` comme destination de la PR.

## Modifier, tester et proposer

Avant le commit, vérifier les fichiers :

```powershell
git status --short
git diff --check
git add <fichiers-voulus>
git diff --cached --name-only
git diff --cached
git commit -m "feat: décrire le changement"
git push -u origin feat/ma-modification
```

Ouvrir ensuite une PR vers **`develop`** dans GitHub : vérifier explicitement le champ **base**, car GitHub peut proposer `main`, sa branche par défaut. Décrire le changement, les tests exécutés, les migrations éventuelles et les effets sur le déploiement. Faire relire la PR, attendre la réussite des jobs `backend` et `frontend` dans **Checks**, puis fusionner manuellement. Corriger tout échec CI avant le merge. Ne jamais faire `git push --force` sur une branche partagée.

Pour mettre sa branche à jour avant le merge :

```powershell
git fetch origin
git switch feat/ma-modification
git merge origin/develop
```

Résoudre les conflits, relancer les tests concernés et pousser de nouveau la branche. Les contrôles locaux utiles sont `npm run check`, `npm run i18n:check` et `npm run build` dans `frontend/`, puis `python -m pytest -q` dans `backend/`. La CI vérifie aussi PostgreSQL, Alembic et les dépendances.

## Ce qui part en ligne

Après un merge dans `develop`, GitHub Actions exécute la CI sur le nouveau commit. Les deux services Render sont configurés avec `autoDeployTrigger: checksPass` : ils déploient ce commit seulement si les contrôles GitHub réussissent. Un push sur une branche de fonctionnalité ou sur `main` ne met pas à jour ces services. Vérifier le commit déployé et les journaux de **checker-ko-demo-api** et **checker-ko-demo-web** dans Render, puis contrôler la connexion et une page utilisant l'API. Si le backend échoue au démarrage ou si la migration échoue, le site peut rester sur une version différente : consulter les deux déploiements et suivre la procédure de restauration de [Render + Supabase](RENDER_SUPABASE_DEMO.md).

La première activation demande un **Blueprint sync** du `render.yaml` fusionné dans le tableau de bord Render, ou le réglage **Auto-Deploy → After CI Checks Pass** sur chacun des deux services. Vérifier que **Blueprint Auto Sync** est activé pour que les changements suivants de `render.yaml` soient pris en compte. Une modification manuelle du service peut être remplacée par une synchronisation Blueprint.

Une PR qui modifie la base ou le stockage doit prévoir une migration non destructive et un plan de retour. Avant un tel merge, réaliser et vérifier une sauvegarde **PostgreSQL et Storage**. Ne pas tester avec des dossiers journalistiques réels sur la démonstration.

## Données et secrets

Ne jamais ajouter à Git `backend/private_data/`, des bases SQLite, médias d'enquête, exports PDF, sauvegardes, fichiers `.env` réels ou secrets. Les fixtures de `backend/demo_assets/` sont fictives. Les variables secrètes vivent dans Render et Supabase, jamais dans `VITE_...` ni dans les PR. Si un secret est publié, le révoquer et coordonner sa rotation avec l'équipe. Le dépôt déployé est une démonstration publique, pas un environnement validé pour de vrais dossiers journalistiques.
