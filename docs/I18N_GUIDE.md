# Guide i18n de Checker-ko

## Langues et ressources

L’interface propose le français (`fr`), le malagasy (`mg`) et l’anglais (`en`). Les dictionnaires JSON plats se trouvent dans `frontend/src/locales/`. Le français est la langue initiale et de secours. Les trois fichiers doivent garder les mêmes clés et les mêmes paramètres `{{name}}`.

## Traduire les vues React

Pour une chaîne statique dans JSX, utiliser le composant `<Tx id="section.key" />`. Pour une chaîne construite ou utilisée dans une fonction, utiliser `const { t } = useI18n()` puis `t('section.key', { name })`. Ajouter chaque clé aux trois dictionnaires. `npm run i18n:check` vérifie les clés, les paramètres, les textes visibles JSX et les appels aux clés de traduction.

Le changement de langue met à jour le rendu React sans recharger la page. Il ne démonte pas les formulaires et ne remplace pas les valeurs saisies. Les erreurs HTTP connues passent par `errorMessage`; éviter d’afficher directement des messages techniques bruts.

## Terminologie couverte

Les libellés communs, la navigation, les formulaires et états, le répertoire de sources, les observations statistiques, l’actualité, les vérifications photo/vidéo/texte, les évaluations, les conclusions, la comparaison et les rapports utilisent les ressources trilingues. Les noms de plateformes, formats, marques et organismes gardent leur nom officiel.

Le malagasy emploie notamment « Loharano » pour les sources, « Fanombanana » pour l’évaluation, « Fehin-kevitra » pour la conclusion et « Porofon-kevitra » pour les éléments de preuve. Ces choix sont cohérents dans l’interface, mais demandent encore une relecture par un journaliste malgachophone, en particulier pour les libellés d’évaluation des sources, les états de conclusion et les messages de validation.

## Contenus qui restent originaux

Ne pas traduire automatiquement les affirmations, titres et textes de publications, notes et preuves, verdicts saisis, justifications, coordonnées, noms et descriptions d’institutions, ni noms de régions. Ces champs proviennent des dossiers et documents de référence. Une future traduction de description institutionnelle devra utiliser des champs localisés distincts, être attribuée à une source et ne jamais remplacer le texte original. Aucune traduction de contenu institutionnel n’est considérée comme officiellement validée ici.

Les libellés de secteurs administratifs connus sont traduits à l’affichage seulement : leur valeur d’origine est conservée lors des filtres et des enregistrements. Les dates suivent la langue active.

## Relecture humaine requise

La version malagasy est une traduction de travail, pas une validation éditoriale officielle. Avant diffusion, demander une relecture à une personne maîtrisant le malagasy rédactionnel et les usages journalistiques de Madagascar. Elle devrait vérifier la terminologie statistique, les formulations de conclusion et d’évaluation, ainsi que la clarté des messages courts sur mobile. Les traductions anglaises et françaises sont également à relire pour le style rédactionnel.

Le titre du login alterne les formulations « image », « vidéo » et « affirmation ». Les trois variantes malagasy sont une traduction de travail et doivent être relues par la rédaction avant diffusion.

## Validation

Depuis `frontend/`, lancer `npm run i18n:check`, `npm run check` et `npm run build`. Le contrôle des textes JSX est une détection pragmatique : les chaînes métier ou données injectées au runtime ne sont pas traduisibles comme des libellés d’interface et doivent rester intactes.
