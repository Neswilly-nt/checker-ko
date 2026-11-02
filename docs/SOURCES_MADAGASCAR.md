# Sources institutionnelles de Madagascar — v0.4.3

Vérification des pages le 2 novembre 2026. Les cinq fiches sont marquées **partiellement vérifiées** : l'identité et le site institutionnel ont été contrôlés, mais les contacts et la disponibilité de chaque document ne le sont pas. Leur présence dans l'annuaire ne prouve aucune affirmation.

| Organisme | Domaine | Site | Page de vérification | Manque |
| --- | --- | --- | --- | --- |
| Bureau National de Gestion des Risques et des Catastrophes (BNGRC) | Météo / catastrophes | https://bngrc.gov.mg/ | https://bngrc.gov.mg/mot-du-directeur-general/ | Contact direct et documents propres à chaque dossier |
| Ministère de l'Éducation nationale (MEN) | Éducation | https://www.education.gov.mg/ | https://www.education.gov.mg/ | Contact direct et documents propres à chaque dossier |
| Institut National de la Statistique (INSTAT) | Économie / statistiques | https://www.instat.mg/ | https://www.instat.mg/qui-sommes-nous/organigramme | Contact direct et données propres à chaque dossier |
| Ministère de l'Enseignement Technique et de la Formation Professionnelle (METFP) | Éducation | https://www.metfp.gov.mg/ | https://www.metfp.gov.mg/ | Contact direct et documents propres à chaque dossier |
| Direction Générale de la Météorologie (DGM) | Météo / catastrophes | https://www.meteomadagascar.mg/ | https://www.meteomadagascar.mg/meteo-madagascar/organisations/ | Contact direct et bulletins propres à chaque dossier |

Le référentiel commun des 24 régions est dans `backend/app/regions.py` et exposé par `GET /api/regions`. Référence : https://www.metfp.gov.mg/cartographie. « National / Tout Madagascar » et « Région non déterminée » sont des choix distincts ; aucune région n'est déduite automatiquement d'un contenu. L'annuaire et la création des dossiers utilisent ce même endpoint.

Les dix anciennes fiches fictives sont conservées avec `archived=1` et `demo_only=1`. Elles sont invisibles dans l'annuaire normal. Seule la rédaction peut les consulter avec `include_archived=true` pour comprendre les dossiers historiques.
