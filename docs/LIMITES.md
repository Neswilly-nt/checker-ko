# Limites et contrôles de Checker-ko

## Limites du produit

- REWIND compare les médias accessibles dans l'archive locale. Le pHash est heuristique et ne recherche pas sur Internet.
- La recherche inversée assistée est manuelle; les observations, pas les résultats automatiques des services, sont enregistrées comme preuves.
- C2PA décrit une provenance déclarée; un manifeste ne confirme pas la scène ou sa légende. La confiance de l'émetteur dépend d'une chaîne configurée.
- Les fiches et contacts institutionnels nécessitent une vérification éditoriale pour chaque enquête. L'annuaire ne prouve aucune affirmation.
- Le rapport imprimé vient de la fonction d'impression du navigateur et doit être relu avant diffusion.
- Les fichiers originaux peuvent contenir des informations sensibles. Ils doivent rester dans `CHECKER_DATA_DIR`, derrière un compte système restreint et des sauvegardes protégées.

## État sécurité

Cette branche remplace le stockage frontend du JWT par des sessions cookie révocables, ajoute la protection CSRF/CORS, prépare PostgreSQL avec Alembic, filtre les liens RSS et met à niveau React Router. Ces changements doivent encore passer la suite complète et être validés sur un PostgreSQL de préproduction.

**Le projet n'est pas prêt pour une exposition publique.** HTTPS, configuration du proxy, limites de débit, contrôle des sorties réseau, restauration de sauvegarde, vérification de la CSP sur le site statique et revue manuelle des accès restent des critères bloquants. Voir [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) et [DEPLOYMENT.md](DEPLOYMENT.md).

Les outils FFmpeg, ffprobe et c2patool peuvent être installés localement ou fournis par variables d'environnement; leur présence réelle dépend de l'installation. Les tests de traitement avec outils portables sont ignorés s'ils sont absents.
