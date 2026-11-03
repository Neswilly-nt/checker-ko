# Recette guidée de la démonstration Checker-ko

Date de démarrage : 2026-11-03. Site : https://checker-ko-demo-web-3pw3.onrender.com/.

Cette recette avance une action à la fois. Un statut **PASS** exige un résultat observé et décrit par la personne qui teste ou une réponse vérifiable. Les essais utilisent uniquement des données fictives. Aucun essai destructif n'est prévu sur le site public.

## État vérifié avant les essais guidés

- La page d'accueil renvoie HTTP 200 le 2026-11-03. `/api/health` renvoie HTTP 200 avec `mode=production`, `ffmpeg_installed=true`, `c2patool_installed=false`.
- Sans session, `/api/auth/me` renvoie HTTP 401 le 2026-11-03 : la protection de cette route fonctionne. Cela ne prouve pas encore la protection de toutes les autres routes.
- La capture transmise par l'utilisateur le 2026-11-03 montre un accueil avec un nom et un rôle utilisateur, un dossier visible et une action de déconnexion : une session connectée est affichée. Le passage par le formulaire de connexion et la déconnexion n'ont pas encore été observés ; l'étape 1 reste donc **NOT TESTED** dans son ensemble.
- Selon `render.yaml`, la démonstration est configurée pour PostgreSQL via `DATABASE_URL` et les médias privés dans Supabase Storage (`checker-private`). `backend/app/main.py` exige PostgreSQL avec TLS au démarrage en mode production et utilise un cookie de session `HttpOnly`, `Secure`, `SameSite=Lax`, limité à `/api`, avec contrôle de l'origine et en-tête CSRF pour les écritures. Les valeurs effectives des secrets et le contenu de la base hébergée ne sont pas accessibles par ces contrôles.
- Le commit déployé sur cette nouvelle URL n'est pas déterminable à partir de la page et des réponses API consultées. Le code local inspecté est `0411788`; il ne prouve pas la version hébergée.
- Risque à suivre : sur Render, les fichiers locaux sous `/tmp` sont éphémères. La durabilité des médias dépend donc de la configuration réelle de Supabase Storage et d'une sauvegarde conjointe de la base et des objets. La procédure est décrite dans `docs/RENDER_SUPABASE_DEMO.md`.

## Suivi fonctionnel

| Étape | Fonctionnalité | Test prévu | Résultat | Date | Preuve ou capture | Anomalie | Correction nécessaire |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Connexion et déconnexion | Ouvrir la démonstration et se connecter avec un compte de démonstration autorisé ; vérifier ensuite la déconnexion | NOT TESTED | 2026-11-03 | Capture de l'accueil avec session utilisateur ; formulaire et déconnexion non observés | Aucune anomalie de connexion établie | — |
| 2 | Gestion des dossiers | Créer un dossier fictif, le retrouver et le rouvrir | NOT TESTED | — | — | — | — |
| 3 | Vérification d'affirmations | Saisir une affirmation fictive et inspecter les étapes | NOT TESTED | — | — | — | — |
| 4 | Vérification d'images | Importer une image d'essai non confidentielle et consulter l'analyse | NOT TESTED | — | — | — | — |
| 5 | Vérification de vidéos | Importer un court MP4 d'essai et consulter les images-clés | NOT TESTED | — | — | — | — |
| 6 | Carnet de preuves | Ajouter une preuve fictive puis la retrouver dans le dossier | NOT TESTED | — | — | — | — |
| 7 | Évaluation des sources | Évaluer une source d'essai et consulter son historique | NOT TESTED | — | — | — | — |
| 8 | Rapports | Générer et ouvrir le rapport d'un dossier d'essai | NOT TESTED | — | — | — | — |
| 9 | Annuaire institutionnel | Rechercher et filtrer les fiches existantes | NOT TESTED | — | — | — | — |
| 10 | Observations statistiques | Consulter une observation réelle avec sa provenance, si elle existe | NOT TESTED | — | — | — | — |
| 11 | Actualités et veille RSS | Consulter les actualités et leurs filtres, sans lancer de synchronisation publique | NOT TESTED | — | — | — | — |
| 12 | Interface FR/MG/EN | Changer de langue et revenir sans perdre une saisie d'essai | NOT TESTED | — | — | — | — |
| 13 | Persistance et contrôle des accès | Recharger un dossier fictif, puis vérifier les accès avec des rôles de démonstration autorisés | NOT TESTED | — | — | — | — |

Les contrôles HTTP anonymes ci-dessus sont des vérifications préparatoires, et non des résultats PASS des étapes guidées. La capture de l'accueil montre une session active ; ni la connexion par formulaire ni la déconnexion n'ont encore été observées.

## Modifications en attente de revue

La branche `feat/uiux-source-guidance` simplifie la création d'un dossier : un seul formulaire Photo, Vidéo ou Texte est visible. Elle améliore la lisibilité des pages internes et affiche dans un dossier jusqu'à trois fiches du répertoire correspondant à son secteur et à sa région, avec la raison de la suggestion, la référence publique et le statut de vérification. Une suggestion ne valide pas l'affirmation. Les dossiers présentent également le type, le statut, les dates et une action « Continuer ». Les libellés « conservés en local » ont été retirés des trois langues. Ces modifications **ne sont pas encore en ligne**.

Contrôles locaux du 2026-11-03 : Pytest **33 PASS, 1 SKIPPED**, `npm run i18n:check` **PASS**, `npm run check` **PASS**, `npm run build` **PASS**. La vérification i18n a été faite après correction des libellés de la landing page présents dans le `develop` initial. La recette visuelle mobile et les parcours fonctionnels en ligne restent **NOT TESTED** ; aucune capture de ces parcours n'est encore disponible.

### Prochaine action guidée

Dans la démonstration actuelle, ouvrir « Nouvelle vérification ». Ensuite, noter l'écran obtenu avant de saisir une affirmation fictive et de créer un dossier. Aucun résultat de création ne sera déclaré PASS avant son observation.
