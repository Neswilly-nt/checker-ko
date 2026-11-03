# Checker-ko v0.9 — interface multilingue

## Changements

- Ajout d'une interface localisée en français, malagasy et anglais, avec sélection immédiate depuis l'écran de connexion et l'en-tête de l'application.
- La langue choisie est mémorisée dans `localStorage` sous `checker-ko.locale`. Le français est utilisé par défaut. Le changement de langue ne recharge pas l'application et conserve l'état des écrans ouverts.
- Ajout du formatage localisé des dates et de messages d'erreur génériques selon le statut HTTP.
- Ajout d'un contrôle de parité des clés des trois ressources via `npm run i18n:check`.

Les noms propres, régions, affirmations, titres d'articles, observations, preuves et justifications restent des données originales et ne sont pas traduits ni réécrits. La génération des rapports A4 et leur contenu enregistré ne changent pas.

## Vérification linguistique

Le malagasy de l'interface est une première traduction et doit être relu par une personne compétente avant diffusion journalistique. Les messages d'erreur applicatifs inconnus sont présentés avec un message générique localisé afin de ne pas exposer de détails techniques.

## Validation

Exécuter `npm run i18n:check`, `npm run check`, `npm run build` dans `frontend`, et `python -m pytest` dans `backend`.
