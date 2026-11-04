"""Références publiques et observations sourcées, avec leur périmètre."""

CHECKED_AT = '2026-11-04'

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

# These four values are transcribed from the official source documents below.
# Keep the table/page locator with every figure so journalists can recheck scope.
CURATED_OBSERVATIONS = {
    'rgph3-tome1': [
        {
            'id': -1, 'publication_key': 'rgph3-tome1',
            'source_title': 'Résultats globaux du RGPH-3 de 2018 de Madagascar - Tome 1',
            'source_url': 'https://www.instat.mg/documents/upload/main/INSTAT_RGPH3-Definitif-ResultatsGlogaux-Tome1_17-2021.pdf',
            'indicator': 'Population résidente des ménages ordinaires recensée',
            'value': '25 674 196', 'unit': 'habitants', 'year': 2018, 'region': 'Madagascar',
            'source_locator': 'p. 11, Tableau 1, ligne MADAGASCAR, colonne Ensemble; hors ménages collectifs et population flottante.',
            'created_at': CHECKED_AT,
        },
        {
            'id': -2, 'publication_key': 'rgph3-tome1',
            'source_title': 'Résultats globaux du RGPH-3 de 2018 de Madagascar - Tome 1',
            'source_url': 'https://www.instat.mg/documents/upload/main/INSTAT_RGPH3-Definitif-ResultatsGlogaux-Tome1_17-2021.pdf',
            'indicator': 'Part des femmes dans la population résidente des ménages ordinaires',
            'value': '50,7', 'unit': '%', 'year': 2018, 'region': 'Madagascar',
            'source_locator': 'p. 11, Tableau 1, ligne MADAGASCAR, colonne % par sexe / Femmes.',
            'created_at': CHECKED_AT,
        },
    ],
    'education-yearbook-2023-2024': [
        {
            'id': -3, 'publication_key': 'education-yearbook-2023-2024',
            'source_title': 'Annuaire statistique scolaire 2023-2024',
            'source_url': 'https://www.education.gov.mg/wp-content/uploads/2024/04/MEN-ANNUAIRE-STATISTIQUE-_SCOLAIRE_2023_2024.pdf',
            'indicator': 'Effectif des élèves des écoles primaires publiques et privées',
            'value': '5 293 936', 'unit': 'élèves', 'year': 2024, 'region': 'Madagascar',
            'source_locator': 'Annuaire 2023-2024, tableau EFFECTIFS DES ÉLÈVES PAR ÂGE, PAR SECTION ET PAR GENRE DES PRIMAIRES PUBLICS ET PRIVÉS, ligne ENSEMBLE, colonne TOTAL.',
            'created_at': CHECKED_AT,
        },
        {
            'id': -4, 'publication_key': 'education-yearbook-2023-2024',
            'source_title': 'Annuaire statistique scolaire 2023-2024',
            'source_url': 'https://www.education.gov.mg/wp-content/uploads/2024/04/MEN-ANNUAIRE-STATISTIQUE-_SCOLAIRE_2023_2024.pdf',
            'indicator': 'Effectif des élèves des collèges publics et privés',
            'value': '1 264 347', 'unit': 'élèves', 'year': 2024, 'region': 'Madagascar',
            'source_locator': 'Annuaire 2023-2024, tableau EFFECTIFS DES ÉLÈVES PAR ÂGE, PAR SECTION ET PAR GENRE DES COLLÈGES PUBLICS ET PRIVÉS, ligne ENSEMBLE, colonne TOTAL.',
            'created_at': CHECKED_AT,
        },
    ],
}


def publication_view(item):
    return {**item, 'last_link_check': CHECKED_AT, 'observations': list(CURATED_OBSERVATIONS.get(item['key'], []))}
