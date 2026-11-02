"""Référentiel géographique commun, vérifié sur la cartographie du METFP."""
REGIONS = (
    'Alaotra-Mangoro', 'Ambatosoa', "Amoron'i Mania", 'Analamanga',
    'Analanjirofo', 'Androy', 'Anosy', 'Atsimo-Andrefana',
    'Atsimo-Atsinanana', 'Atsinanana', 'Betsiboka', 'Boeny',
    'Bongolava', 'Diana', 'Fitovinany', 'Haute Matsiatra',
    'Ihorombe', 'Itasy', 'Melaky', 'Menabe', 'Sava', 'Sofia',
    'Vakinankaratra', 'Vatovavy',
)
NATIONAL = 'National / Tout Madagascar'
UNKNOWN = 'Région non déterminée'

def normalize_region(value: str | None) -> str | None:
    if value is None or not value.strip() or value.strip() == UNKNOWN:
        return None
    candidate = value.strip()
    if candidate == NATIONAL:
        return NATIONAL
    for region in REGIONS:
        if candidate.casefold() == region.casefold():
            return region
    raise ValueError('Région non reconnue dans le référentiel malgache')
