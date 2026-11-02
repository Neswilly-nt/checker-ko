"""Références documentaires publiques; aucune observation chiffrée n'est importée."""

CHECKED_AT = '2026-11-03'

PUBLICATIONS = (
    {
        'key': 'health-yearbook-2024',
        'title': 'MSANP | Annuaire des statistiques du secteur santé de Madagascar - 2024',
        'producer': 'Ministère de la Santé Publique / INSTAT',
        'sector': 'santé',
        'reference_year': '2023',
        'publication_date': '2026-02-04',
        'coverage': 'Madagascar; formations sanitaires publiques et privées',
        'format': 'PDF',
        'url': 'https://www.instat.mg/documents/upload/main/MSANP_AnnuaireStatistiques_2024.pdf',
        'landing_url': 'https://www.instat.mg/p/msanp-annuaire-des-statistiques-du-secteur-sante-de-madagascar-2024',
        'description': 'Annuaire de données sanitaires issues notamment des rapports mensuels d’activité. Les observations portent sur 2023.',
        'accessibility': 'document_accessible',
    },
    {
        'key': 'education-yearbook-2023-2024',
        'title': 'Annuaire statistique scolaire 2023-2024',
        'producer': 'Ministère de l’Éducation Nationale',
        'sector': 'éducation',
        'reference_year': '2023-2024',
        'publication_date': None,
        'coverage': 'Madagascar',
        'format': 'PDF',
        'url': 'https://www.education.gov.mg/wp-content/uploads/2024/04/MEN-ANNUAIRE-STATISTIQUE-_SCOLAIRE_2023_2024.pdf',
        'landing_url': 'https://www.education.gov.mg/ressources/annuaires-statistiques/',
        'description': 'Annuaire scolaire publié par la Direction de la Planification de l’Éducation; présente les statistiques du système éducatif.',
        'accessibility': 'document_accessible',
    },
    {
        'key': 'rgph3-tome1',
        'title': 'Résultats globaux du RGPH-3 de 2018 de Madagascar - Tome 1',
        'producer': 'INSTAT / Cellule Centrale d’Exécution du Recensement',
        'sector': 'démographie',
        'reference_year': '2018',
        'publication_date': '2021',
        'coverage': 'Madagascar selon le découpage et les définitions du RGPH-3',
        'format': 'PDF',
        'url': 'https://www.instat.mg/documents/upload/main/INSTAT_RGPH3-Definitif-ResultatsGlogaux-Tome1_17-2021.pdf',
        'landing_url': 'https://www.instat.mg/index.php/p/resultats-definitifs-du-rgph-3',
        'description': 'Résultats définitifs du troisième Recensement Général de la Population et de l’Habitation; données de 2018.',
        'accessibility': 'document_accessible',
    },
)


def publication_view(item):
    return {**item, 'last_link_check': CHECKED_AT, 'observations': []}
