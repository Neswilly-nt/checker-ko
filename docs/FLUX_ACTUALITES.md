# Flux Actualités

## Source active

| Source | Flux | Type | Secteurs | Vérifié le | Mise à jour observée | Réutilisation |
| --- | --- | --- | --- | --- | --- | --- |
| Madagascar Tribune | `https://www.madagascar-tribune.com/spip.php?page=backend` | RSS | Généraliste ; classé `autre` sans catégorie documentée | 2026-11-03 | Publications récentes dans le flux ; fréquence variable | Consulter les conditions du site de l'éditeur avant toute republication. |
| NewsMada | `https://newsmada.com/feed/` | RSS | Généraliste ; classé `autre` sans catégorie documentée | 2026-11-03 | Publications récentes dans le flux ; fréquence variable | Consulter les conditions du site de l'éditeur avant toute republication. |
| L'Express de Madagascar | `https://www.lexpress.mg/feeds/posts/default?alt=rss` | RSS | Généraliste ; catégorie variable | 2026-11-03 | Publications récentes dans le flux ; fréquence variable | Consulter les conditions du site de l'éditeur avant toute republication. |

Ces trois flux ont été retenus après des requêtes réelles et une lecture réussie par le collecteur. Midi Madagasikara a été désactivé après une réponse HTTP 403 ; ses publications déjà collectées sont conservées. Aucun flux fictif ne remplace une source indisponible.

La première ouverture d'« Actualités » par une personne connectée déclenche la collecte des sources actives. Chaque source est ensuite actualisée au plus une fois toutes les 30 minutes, y compris après un échec. Le responsable de rédaction peut aussi lancer une synchronisation manuelle. Un premier chargement peut prendre quelques secondes selon les médias. Le journal conserve les résultats de chaque tentative.

## Garanties de collecte

- Les URLs sont fixées dans le catalogue applicatif ; aucune URL n'est reçue du navigateur.
- La résolution DNS refuse les adresses privées, locales et link-local ; HTTPS, un délai de 10 secondes, une taille maximale de 1,5 Mo et l'absence de redirection sont imposés.
- Le journal de synchronisation conserve le statut, les compteurs et l'erreur éventuelle.
- Une clé canonique (`guid`, ou URL à défaut) déduplique les publications. La date de publication et la date de collecte restent distinctes.
- La synchronisation manuelle est réservée au responsable de rédaction ; la collecte à l'ouverture est limitée en fréquence. Les exécutions concurrentes sont protégées.

Une actualité est une piste documentaire, jamais un verdict.
