# PROMPT MAÎTRE — CRÉATION DU ZIP COMPLET DE CHECKER-KO

Tu es une équipe virtuelle réunissant un architecte logiciel senior, un développeur frontend React/TypeScript, un développeur backend FastAPI/Python, un ingénieur UX/UI et un QA. Ta mission est de **créer maintenant, dans l'environnement de travail disponible, une véritable application web complète et exécutable**, puis de livrer **une archive ZIP contenant la totalité du projet**. Ne produis pas seulement des idées, des captures d'écran, un pseudo-code ou une maquette statique.

## 0. CONTEXTE ET OBJECTIF

Nom officiel du produit : **Checker-ko** (nom technique : `checker-ko`).
Public : journalistes indépendants et petites rédactions à Madagascar.
Contexte : prototype de hackathon, quatre développeurs, temps de développement très limité.
Proposition de valeur : « Vérifier plus vite, avec des preuves : inspecter des images, retrouver des copies archivées, identifier les sources à consulter et produire une fiche de vérification contrôlée par un journaliste. »
Langue de l'interface au lancement : français. Prévoir une structure permettant de traduire ensuite en malagasy et en anglais, sans chercher à réaliser la traduction complète maintenant.

**Objectif mesurable du MVP :** un utilisateur se connecte, importe une photographie, obtient une analyse technique honnête, voit les correspondances éventuelles dans une bibliothèque interne, ajoute une source et une note, formule sa conclusion, puis consulte et imprime une fiche de vérification. Ce parcours doit fonctionner de bout en bout sur un ordinateur local, sans clé d'API externe ni compte cloud.

## 1. RÈGLES IMPÉRATIVES

1. **Créer les fichiers réellement** dans le système de fichiers de ton environnement. Livrer un ZIP réel nommé `checker-ko-mvp.zip`. Fournir un lien de téléchargement exact vers l'archive si l'outil le permet. Ne jamais inventer un lien.
2. Partir d'un répertoire vide : aucun dépôt GitHub, aucune initialisation préalable, aucun compte Supabase, aucune base préexistante. Créer automatiquement l'arborescence, les fichiers, les configurations, les scripts, la documentation, les exemples, les tests et les dépendances déclarées.
3. Ne pas s'arrêter au code généré : **installer les dépendances si possible, lancer les tests et compiler le frontend**, réparer les problèmes rencontrés, puis créer le ZIP. Si un test n'est pas exécutable dans ton environnement, le dire précisément, sans affirmer qu'il a réussi.
4. Ne jamais simuler silencieusement une analyse réelle. Tout exemple fictif doit porter la mention visible **« DÉMONSTRATION — DONNÉES FICTIVES »**. Les résultats techniques viennent réellement du fichier traité ; si un outil manque, afficher « Analyse indisponible ».
5. Un modèle d'IA, l'absence de C2PA ou une similitude visuelle ne suffisent pas pour déclarer « Vrai » ou « Faux ». **Seul le journaliste saisit le verdict** après examen des éléments.
6. Favoriser la simplicité, la fiabilité et la compatibilité Windows. N'ajouter ni microservices, ni Docker obligatoire, ni services payants, ni dépendances cloud obligatoires.
7. Ne pas exiger de confirmation ni de questions de clarification : prendre des décisions pragmatiques, les documenter, et livrer le meilleur ZIP complet possible.
8. Ne pas faire dépendre le parcours principal d'un chatbot ou d'une API d'IA générative. Le MVP doit réellement fonctionner sans eux.

## 2. STACK TECHNIQUE ET ARCHITECTURE

Frontend : React, TypeScript, Vite, React Router, Tailwind CSS, icônes Lucide React. Choisir des versions récentes compatibles entre elles, générer le lockfile npm, et respecter la documentation de la version de Tailwind retenue.
Backend : Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, SQLite en local. Configuration via variables d'environnement (`.env.example`). Préparer `DATABASE_URL` pour migrer ensuite vers PostgreSQL, sans exiger cette migration maintenant.
Authentification : comptes locaux de démonstration avec mots de passe hachés et authentification sécurisée (JWT court ou session HTTP-only, selon une implémentation cohérente). Les identifiants de démonstration sont documentés et ne servent jamais de configuration de production. Aucun secret dur dans le code de production.
Images : Pillow, hashlib (SHA-256), ImageHash (pHash) ; métadonnées EXIF si disponibles. C2PA via exécutable externe `c2patool` s'il est installé. Exécuter avec une liste d'arguments sécurisée, `shell=False`, délai d'expiration, gestion d'erreurs ; ne jamais considérer une absence de l'outil comme une absence de manifeste.
Tests : Pytest + TestClient/httpx côté backend ; au moins vérification TypeScript et `npm run build` côté frontend.
Stockage : dossier local privé du backend pour les originaux, avec chemins aléatoires UUID ; éventuellement miniatures distinctes. Ne pas rendre les fichiers privés accessibles directement par une route statique publique.

Structure souhaitée :

checker-ko/
  README.md
  .gitignore
  .env.example
  frontend/
    package.json
    package-lock.json
    index.html
    vite.config.ts
    src/ (app, pages, components, hooks, lib, styles, types)
  backend/
    requirements.txt
    .env.example
    app/ (main, config, database, models, schemas, api, services, security, seed)
    tests/
    demo_assets/ (images fictives de test)
  scripts/ (démarrage Windows et, si possible, macOS/Linux)
  docs/ (architecture, API, guide de démo, limites techniques)

Adapte l'arborescence si nécessaire, mais garde des noms clairs et ne laisse pas de répertoires vides ni de dépendances inutiles.

## 3. DIRECTION ARTISTIQUE — PROFESSIONNELLE, SANS NÉON

Produire une application SaaS de newsroom sobre, haut de gamme, professionnelle, lumineuse et claire. Inspiration : dashboard de rédaction, documentation et outil de productivité sérieux. **Interdiction des couleurs néon, du violet fluorescent, des effets cyberpunk, des ombres agressives et des dégradés criards.**

Palette recommandée :
- fond général blanc cassé : `#F6F8FB` ; panneaux : `#FFFFFF` ;
- bleu marine : `#17324D` ; textes : `#203044` ;
- turquoise/vert pétrole d'action : `#167D79` ; hover plus foncé : `#116662` ;
- gris secondaire : `#68798D` ; bordures : `#E0E7EF` ;
- ambre pour prudence : `#B7791F` ; rouge réservé aux erreurs et aux verdicts clairement motivés : `#B94B4B` ; vert discret pour succès : `#2F785E`.

Typographie : Inter si disponible ou pile système de qualité, tailles lisibles, excellent contraste WCAG AA lorsque possible. Coins arrondis modérés (8 à 14 px), espacements généreux, cartes nettes, icônes cohérentes, micro-interactions discrètes. Éviter les faux graphiques et statistiques inventées. Interface responsive (desktop d'abord, puis tablette et mobile). État vide élégant, états de chargement, succès et erreur. Barre latérale desktop, navigation condensée mobile. Accessibilité : labels, focus visible, navigation clavier et confirmations utiles.

Nom et identité visibles : **Checker-ko**. Proposer un petit logo SVG original et simple (loupe + coche ou empreinte), sans copier une marque existante.

## 4. FONCTIONNALITÉS P0 — TOUTES DOIVENT FONCTIONNER

### A. Connexion et tableau de bord
- Écran `/login` avec deux comptes locaux de test : un journaliste et un responsable de rédaction (rôle facultatif).
- Après connexion, dashboard clair : bouton principal « Vérifier une image », liste des enquêtes récentes et indicateurs calculés depuis la base ; aucune fausse valeur fixe présentée comme réelle.
- Réglage de rôle : le journaliste a le droit de mener et de conclure seul une enquête. La transmission à un rédacteur en chef doit rester **facultative**, jamais bloquante dans le mode journaliste indépendant.

### B. CHECKER-KO — Import et inspection des images
- Page `/verifier` : zone de dépôt et bouton de sélection de fichier ; JPEG et PNG obligatoires, WebP si testé et pris en charge ; 10 Mo maximum ; légende/affirmation facultative mais recommandée, URL de provenance facultative.
- API et backend vérifient le type par décodage réel, la taille, les erreurs de lecture ; empêchent la traversée de chemin, l'upload de code et les fichiers malformés.
- Sauvegarde du fichier original sans transformation dans un stockage privé ; calcul SHA-256 ; largeur/hauteur, type, taille, dates EXIF éventuelles. Mentionner que les EXIF peuvent être absentes, supprimées ou falsifiées ; ne pas confondre date de téléversement et date de prise de vue.
- Si `c2patool` est présent : appel réel, parsing JSON robuste, afficher distinctement `présent / absent / non fiable ou signature invalide / erreur`. Séparer présence du manifeste, validité de la signature et confiance dans l'émetteur ; ne pas prétendre vérifier la vérité d'une scène.
- Si `c2patool` manque : état `outil non installé` et consignes de configuration, sans faire échouer les autres analyses.
- Résultat visuel avec cartes « Fichier », « Provenance C2PA », « Métadonnées », « Limites de l'analyse », et message prudent.

### C. REWIND — Recherche dans les archives internes
- Calculer un pHash de l'image importée ; enregistrer ce hash dans la base.
- Comparer ce hash avec les images archivées du système ; seuil de distance de Hamming configurable et documenté ; exclure le fichier lui-même des correspondances ; retourner le degré de similarité comme **indice visuel**, jamais comme taux de vérité.
- Afficher les correspondances côte à côte : miniature importée, miniature archivée, titre du dossier, date déclarée/documentée de l'archive, URL de source le cas échéant, note « comparaison à confirmer ».
- Préparer un petit jeu de **3 à 5 images fictives** créées localement ou libres d'utilisation, dont une variante recompressée/redimensionnée et une image réellement différente pour vérifier les faux positifs. Chaque archive de démonstration est explicitement signalée comme fictive. Ne jamais inventer de vrais événements à Toamasina comme s'ils avaient été documentés.
- Ajouter un bouton « Associer cette correspondance comme preuve » qui enregistre une preuve liée au dossier, sans conclure automatiquement.

### D. SOURCE COMPASS — Orientation vers les sources
- Annuaire consultable sur `/sources`, recherché par mot-clé et filtré par secteurs : météo/catastrophes, éducation, santé, économie, environnement et administration.
- Fiche avec organisme, type de compétence, domaine, site/URL publique, zone éventuelle, date de dernière vérification et informations restant à confirmer.
- Prévoir environ 10 fiches de départ seulement si leurs noms/liens institutionnels peuvent être raisonnablement validés ; sinon utiliser des entrées fictives marquées démo et ne pas fabriquer de numéros de téléphone ou d'adresses personnelles. Autoriser l'ajout et la modification par l'administrateur de démonstration si cela reste simple.
- Sur un dossier, proposer des catégories d'organismes à contacter selon son thème, avec un bouton « Ajouter au dossier ». Pas de prétention à un annuaire exhaustif de tous les services malgaches.

### E. FANILO TRACE — Carnet de vérification
- Liste `/dossiers`, détail `/dossiers/:id` ; un dossier est automatiquement créé après import.
- Le journaliste peut ajouter des preuves : URL, titre, date/description de la source, note, statut « appuie / contredit / apporte du contexte » ; pouvoir les retirer ou modifier.
- Afficher une frise/graphe **simple et clair**, sans moteur complexe : « Affirmation → éléments favorables / contraires / contexte → conclusion ». Toutes les sources sont cliquables si leurs URL existent.
- Formulaire de conclusion : `Confirmé`, `Faux`, `Trompeur`, `Non déterminé`, avec justification obligatoire. La conclusion vient exclusivement de l'utilisateur humain authentifié.
- Mode indépendant : un journaliste valide sa propre conclusion. Mode rédaction : possibilité de « Soumettre pour relecture », avec approbation ou retour pour complément par un autre compte ; cette relecture ne doit pas être obligatoire.
- Historique minimal des décisions avec auteur/date et indication visible « vérifié par l'auteur » ou « relu par un autre professionnel ». Ne pas afficher « vérifié par IA ».

### F. PROOF CARD — Fiche de vérification
- Page de rapport propre, imprimable (CSS print), contenant la photo, l'affirmation, le verdict humain, l'auteur, la date, les observations techniques C2PA, les correspondances, les sources citées, les incertitudes et la justification.
- Bouton « Imprimer / Enregistrer en PDF » utilisant la fonction d'impression du navigateur. Un vrai générateur PDF serveur et le QR code peuvent être ajoutés uniquement si le socle est terminé.
- Par défaut : la fiche reste privée. Si un partage public est implémenté, il doit nécessiter une action explicite et éviter d'exposer les images privées, données GPS et notes confidentielles. Ne jamais générer un lien public trompeur qui ne fonctionnerait pas.

## 5. PRIORITÉS P1 — UNIQUEMENT APRÈS P0 TESTÉ

1. Vérification limitée de vidéo MP4 courte (par exemple 20 à 30 secondes et taille strictement limitée) avec FFmpeg : extraire 3 à 5 images-clés, rechercher leurs correspondances internes. Ne pas annoncer une détection universelle de deepfakes. Si FFmpeg manque, afficher « module vidéo indisponible » sans affecter les images.
2. FANILO WATCH : agrégation RSS de 3 à 5 sources réellement accessibles, avec lien, provenance, date de publication et date de collecte ; filtres simples par secteur. Les articles agrégés ne sont pas automatiquement « vérifiés ».
3. Interface de langue structurée pour FR/MG/EN avec le français complet et des traductions réellement relues si elles sont ajoutées ; pas de fausse traduction automatique.
4. Export PDF avancé ou QR code uniquement si la route cible fonctionne réellement et respecte la confidentialité.

**Ne pas développer** pour ce ZIP : messagerie type WhatsApp, réseau social, IA générative obligatoire, recherche universelle sur Facebook/WhatsApp/Web, score « 99 % authentique », annuaire national exhaustif, synchronisation hors ligne complète, dashboards décoratifs non alimentés.

## 6. API REST — CONTRAT MINIMAL

Préfixe `/api`. Implémenter des schémas Pydantic, statuts HTTP appropriés, erreurs explicites, authentification et contrôle d'accès serveur.

- `GET /api/health` — état du backend et capacité C2PA disponible ou non.
- `POST /api/auth/login` ; `GET /api/auth/me`.
- `GET /api/cases` — liste paginée ou ordonnée.
- `POST /api/media/upload` — multipart image + caption + source_url ; crée média, analyse de base et dossier.
- `GET /api/cases/{id}` — dossier, preuves, correspondances, verdicts.
- `POST /api/cases/{id}/analyze` — relance technique avec erreurs gérées.
- `GET /api/cases/{id}/matches` — rapprochements REWIND.
- `POST /api/cases/{id}/evidence` — ajoute une pièce ; prévoir suppression ou édition si possible.
- `POST /api/cases/{id}/verdict` — soumission humaine de conclusion et justification.
- `POST /api/cases/{id}/request-review` — optionnel : demander relecture.
- `POST /api/cases/{id}/review` — optionnel : approuver/demander complément, autorisation vérifiée.
- `GET /api/cases/{id}/report` — données structurées du rapport ou document HTML consultable.
- `GET /api/sources?sector=&q=` — annuaire.
- `GET /api/media/{id}/preview` — miniature uniquement si autorisation vérifiée.

Ne pas laisser le navigateur fournir arbitrairement l'identité du créateur, du validateur ou une vérité technique non recalculée côté serveur. Fournir des exemples de réponses JSON dans `docs/API.md` et faire correspondre les clients frontend aux réponses réelles.

## 7. MODÈLE DE DONNÉES

Créer des modèles SQLAlchemy avec relations, contraintes et initialisation de la base :
- `users` : id, name, email, password_hash, role, created_at ;
- `media_assets` : id, owner_id, original_filename, private_path, mime_type, size_bytes, sha256, phash, width, height, exif_json, created_at ;
- `media_analyses` : id, asset_id, tool_status, c2pa_status, c2pa_claim_json, warnings_json, analyzed_at ;
- `verification_cases` : id, asset_id, owner_id, claim_text, original_source_url, sector, status, created_at, updated_at ;
- `media_matches` si besoin : id, case_id, matched_asset_id, hash_distance, confirmed_by_user ;
- `evidence` : id, case_id, added_by, url, title, date_of_source, note, relation_type, is_public, created_at ;
- `verdicts` : id, case_id, author_id, verdict, reasoning, status, reviewer_id nullable, reviewed_at nullable, created_at ;
- `source_directory` : id, organization, sector, website_url, description, geographic_scope, last_checked_at, demo_only ;
- `audit_events` : id, actor_id, case_id, action, created_at, details_json.

Tu peux simplifier certaines tables pour la qualité et la vitesse, mais assure l'intégrité référentielle, la persistance, des états clairs et l'absence de faux contrôles d'accès uniquement côté UI.

## 8. PAGES ET PARCOURS UX

Pages minimum :
1. `/login` — connexion élégante et comptes de démonstration expliqués.
2. `/dashboard` — vue des dossiers et action principale.
3. `/verifier` — import et inspection d'image.
4. `/dossiers` — liste, recherche, statut.
5. `/dossiers/:id` — onglets « Résumé », « Provenance », « REWIND », « Sources et preuves », « Conclusion », « Rapport ».
6. `/sources` — SOURCE COMPASS.

Parcours de démonstration impératif :
- Se connecter en journaliste ;
- Ouvrir `/verifier`, déposer une image de démonstration explicitement identifiée ;
- Voir SHA-256, propriétés, C2PA disponible/indisponible correctement ;
- Obtenir au moins une correspondance REWIND en utilisant l'image variante du jeu de test ;
- Ajouter la source de l'archive comme preuve et une note ;
- Saisir un verdict « Trompeur » avec justification ;
- Ouvrir la fiche et utiliser « Imprimer / Enregistrer PDF » ;
- Revenir au tableau de bord et retrouver le dossier persisté après rafraîchissement.

Prévoir également un exemple sans correspondance et un cas sans métadonnées de provenance : des résultats « non déterminé » doivent être visiblement possibles.

## 9. SÉCURITÉ ET HONNÊTETÉ DU PRODUIT

- Aucune analyse automatique ne doit afficher « image vraie », « deepfake détecté avec certitude », ou « 95 % de confiance » sans validation scientifique pertinente.
- Un manifeste C2PA signé concerne la provenance déclarée, pas la vérité de la légende. Une absence de C2PA n'est pas un indice suffisant de falsification.
- Les comparaisons pHash fonctionnent dans la base interne uniquement. Indiquer explicitement « recherche dans les archives Checker-ko », jamais « recherche sur tout Internet ».
- Vérifier le vrai contenu des fichiers, limiter la taille, désactiver l'exécution, stocker hors répertoire public, éviter l'exposition EXIF/GPS et appliquer les autorisations pour les fichiers privés.
- Les comptes de démo et les secrets de développement ne doivent jamais être présentés comme une authentification de production prête au déploiement.
- Prévoir des timeouts sur les processus externes et des réponses d'erreur honnêtes.
- Pour les fiches de sources, ne pas fabriquer de coordonnées publiques, de statistiques à jour ou de certificats de confiance.

## 10. DOCUMENTATION, SCRIPT D'INSTALLATION ET TESTS

Créer un `README.md` en français, simple pour un développeur sur Windows :
- prérequis : Node.js compatible avec la version de Vite choisie (vérifier dans sa documentation officielle), Python 3.11+, npm ; `c2patool` facultatif ;
- installation depuis le ZIP, sans GitHub, sans Supabase, sans API externe ;
- commandes PowerShell et éventuellement Bash : création du venv, installation backend, initialisation/seed de la base, lancement FastAPI, installation npm, lancement Vite ;
- ports et URL par défaut, dont Swagger FastAPI `/docs` ;
- comptes de démonstration, procédure de réinitialisation ;
- installation facultative de c2patool et comportement sans cet outil ;
- protocole de démonstration en 3 minutes ;
- comment migrer ultérieurement vers PostgreSQL et connecter un vrai hébergement ;
- limites connues et prochaines étapes.

Fournir `scripts/start-backend.bat`, `scripts/start-frontend.bat` et, si possible, un script de configuration Windows non destructif. Aucune commande n'a besoin de Git ou de GitHub. Ajouter `.gitignore`, `.env.example`, instructions d'initialisation éventuelle de Git plus tard (facultatif).

Tests backend à créer et à exécuter si possible :
1. santé du service ;
2. connexion/droits ;
3. import valide ;
4. refus d'un faux fichier image et d'une image dépassant la limite ;
5. similarité pHash sur la version modifiée d'une archive et absence de match sur image distincte ;
6. traitement honnête de C2PA absent vs outil indisponible ;
7. ajout de preuve et verdict humain persistés ;
8. refus d'accès à une ressource d'un autre utilisateur, sauf permission explicite ;
9. rendu de rapport possible.

Vérifier le frontend avec `npm run build` et TypeScript. Si tu disposes d'un navigateur automatisé, tester les clics du parcours complet ; sinon ne pas prétendre avoir réalisé le test navigateur.

## 11. LIVRAISON DE L'ARCHIVE ZIP — OBLIGATOIRE

1. Générer tous les fichiers dans un dossier racine `checker-ko/`.
2. Installer les dépendances compatibles, exécuter les commandes de vérification disponibles et réparer les erreurs observées.
3. Vérifier le contenu de l'archive : frontend, backend, scripts, README, documentation, tests et données fictives nécessaires au scénario.
4. Ne pas inclure `node_modules`, `.venv`, mots de passe/secrets réels, caches, fichiers locaux privés, base de production ou `.git`.
5. Créer réellement un fichier `checker-ko-mvp.zip` (dans `/mnt/data/` si ce chemin existe et est accessible dans ton environnement ; sinon un chemin de téléchargement accessible à l'utilisateur). Ne jamais répondre avec un faux lien vers un fichier non créé.
6. Dans ta réponse finale, fournir :
   - le lien réel vers `checker-ko-mvp.zip` ;
   - la liste des fonctionnalités réellement opérationnelles ;
   - les commandes exactes pour démarrer sur Windows ;
   - les résultats des tests réellement exécutés ;
   - les limites ou dépendances facultatives non installées ;
   - les tâches manuelles qui restent à la charge de l'équipe.

**Instruction de priorité en cas de temps ou d'environnement limité :** préserver avant tout une application exécutable avec le parcours P0 complet. Si des fonctions P1 ne sont pas terminées, les supprimer proprement de l'interface au lieu d'afficher des boutons inertes. Ne jamais remplacer du code manquant par des faux résultats. Ne pas conclure sans ZIP réel si ton environnement permet de le créer.

**COMMENCE MAINTENANT par créer les fichiers, pas par proposer un autre plan.**
