# Limites et contrôles de Checker-ko v0.4.4

## Contrôles locaux

Le 3 novembre 2026, `npm run check`, `npm run build` et les 19 tests Pytest du backend ont réussi dans l'environnement Windows de développement. Pytest a émis trois avertissements de dépréciation liés au client de test Starlette et au gestionnaire de démarrage FastAPI. Les tests utilisent un répertoire temporaire séparé et ne modifient pas la base privée.

Les outils FFmpeg, ffprobe et c2patool peuvent être installés localement sous `tools/media/` ou fournis via le `PATH`. Ce dossier n'est pas publié. En CI, le test de traitement réel de média est ignoré si les binaires et l'échantillon requis ne sont pas présents ; les contrôles API qui simulent leur absence ou leur réponse restent exécutés.

`npm audit --omit=dev` a signalé deux avis modérés transitifs concernant `react-router` et `react-router-dom` 6. Les correctifs proposés par npm requièrent React Router 7, une mise à niveau majeure qui n'a pas été appliquée sans migration et vérification ciblées.

## Limites produit et sécurité

- REWIND compare les médias accessibles dans l'archive locale. Le pHash est heuristique et ne recherche pas sur Internet.
- La recherche inversée assistée est manuelle ; les observations et liens sont saisis par le journaliste.
- C2PA décrit une provenance déclarée ; un manifeste ne confirme pas la scène ou sa légende. La confiance de l'émetteur dépend d'une chaîne de confiance configurée.
- Les cinq institutions de l'annuaire sont marquées partiellement vérifiées. Les contacts et les documents utiles doivent être contrôlés pour chaque dossier. L'annuaire ne prouve aucune affirmation.
- Le PDF est produit par la fonction d'impression du navigateur et doit être relu avant diffusion.
- Le JWT est conservé dans `localStorage` dans cette version. L'application est conçue pour une utilisation locale et ne doit pas être exposée directement à Internet.
- HTTPS, limitation des essais de connexion, sessions adaptées à la production, migrations de base, chiffrement au repos, politique de conservation et audit de sécurité restent à prévoir avant déploiement public.
- Les originaux peuvent contenir des informations sensibles. La base, les images et les vidéos d'enquête doivent rester dans `backend/private_data/`, avec des sauvegardes locales protégées.

## Étapes de développement recommandées

1. Tester les scénarios photo, vidéo, texte, preuves, conclusion et rapport avec des données synthétiques.
2. Valider les sources institutionnelles et leur pertinence éditoriale avec l'équipe malgache.
3. Planifier une mise à niveau React Router distincte, lire les avis npm et vérifier les parcours de navigation avant fusion.
4. Concevoir les protections de production avant tout hébergement accessible à l'extérieur.
