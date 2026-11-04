"""Prepare a separate, local-only Checker-ko newsroom showcase database."""
from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import sqlite3
import sys
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageOps

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / 'private_data' / 'showcase'
DB = DATA / 'checker_showcase.db'
MARKER = DATA / '.checker-ko-showcase-data'
MEDIA_ROOT = DATA / 'storage'
ASSET = BACKEND / 'demo_assets' / 'showcase' / 'madagascar-saririaky.jpg'
NASA_SOURCE = 'https://science.nasa.gov/earth/earth-observatory/moon-like-madagascar/'

parser = argparse.ArgumentParser(description='Prépare une base locale indépendante pour la démonstration Checker-ko.')
parser.add_argument('--reset', action='store_true', help='Reconstruit uniquement la base locale Showcase protégée par son marqueur.')
args = parser.parse_args()

if DATA.is_symlink() or (DATA.exists() and any(DATA.iterdir()) and not MARKER.is_file()):
    raise SystemExit(f'Préparation refusée : dossier existant sans marqueur dédié ({DATA}).')
DATA.mkdir(parents=True, exist_ok=True)
if args.reset:
    if not MARKER.is_file() or MARKER.read_text(encoding='utf-8') != 'Checker-ko local showcase database and media.\n':
        raise SystemExit('Réinitialisation refusée : marqueur local manquant.')
    for target in (DB, Path(str(DB) + '-wal'), Path(str(DB) + '-shm')):
        if target.is_symlink():
            raise SystemExit(f'Réinitialisation refusée sur un lien symbolique : {target}')
        if target.is_file(): target.unlink()
    if MEDIA_ROOT.is_symlink(): raise SystemExit('Réinitialisation refusée sur le stockage symbolique.')
    if MEDIA_ROOT.is_dir(): shutil.rmtree(MEDIA_ROOT)
MARKER.write_text('Checker-ko local showcase database and media.\n', encoding='utf-8')

os.environ.update({
    'APP_ENV': 'development', 'CHECKER_DEMO_MODE': 'true',
    'CHECKER_DEMO_LOCAL_CATALOG': 'true', 'CHECKER_SECRET': secrets.token_urlsafe(48),
    'CHECKER_STORAGE_BACKEND': 'local', 'CHECKER_DATA_DIR': str(MEDIA_ROOT),
    'DATABASE_URL': 'sqlite:///' + DB.as_posix(),
})
sys.path.insert(0, str(BACKEND))

from app import storage  # noqa: E402
from app.core import (  # noqa: E402
    Case, Evidence, NewsItem, NewsSource, SessionLocal, User, DEMO_USERS,
    init_db, store_media,
)


def migrate_local_demo_email() -> None:
    """Rename only the known demo account in the isolated local showcase DB."""
    if not DB.is_file():
        return
    with sqlite3.connect(DB) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'users' not in tables:
            return
        old, new = 'journaliste@checker.local', 'journaliste@checker.mg'
        existing = {row[0] for row in connection.execute('SELECT email FROM users WHERE email IN (?, ?)', (old, new))}
        if old in existing and new in existing:
            raise SystemExit(f'Migration locale refusée : les deux adresses {old} et {new} existent déjà.')
        if old in existing:
            connection.execute('UPDATE users SET email=? WHERE email=?', (new, old))
        connection.commit()


def main() -> None:
    if not ASSET.is_file(): raise SystemExit(f'Photographie NASA absente : {ASSET}')
    if storage.BACKEND != 'local': raise SystemExit('Ce script exige le stockage local.')
    migrate_local_demo_email()
    init_db()
    with SessionLocal() as db:
        journalist = db.query(User).filter_by(email=DEMO_USERS[0][0]).one()

        # The normal RSS endpoints currently fail from this environment. Keep the
        # curated press references visible, while disabling collection to avoid
        # fabricated error banners or claiming an RSS sync happened.
        for source in db.query(NewsSource).all(): source.enabled = False
        publishers = [
            ('lexpress-press', "L’Express de Madagascar", 'https://www.lexpress.mg/', 'press'),
            ('moov-press', 'Moov Madagascar', 'https://new.moov.mg/actualites/', 'press'),
        ]
        source_rows = {}
        for key, name, landing, kind in publishers:
            row = db.query(NewsSource).filter_by(key=key).first()
            if not row:
                row = NewsSource(key=key, name=name, feed_url=landing, source_type=kind,
                    sectors_json='["autre"]', checked_at='2026-11-04',
                    reuse_terms='Références et titres affichés avec lien vers le média éditeur; consulter ses conditions.', enabled=False)
                db.add(row); db.flush()
            else:
                row.name=name;row.feed_url=landing;row.source_type=kind;row.enabled=False
            source_rows[key] = row

        news = [
            (source_rows['lexpress-press'], 'LOI DE FINANCES 2027 - Deux élections inscrites dans le budget',
             'https://www.lexpress.mg/2026/11/loi-de-finances-2027-deux-elections.html', datetime(2026,11,3,2,55,tzinfo=timezone.utc), 'économie'),
            (source_rows['lexpress-press'], 'ANTSIRANANA - La crise de l’eau s’intensifie',
             'https://www.lexpress.mg/2026/11/antsiranana-la-crise-de-leau-sintensifie.html', datetime(2026,11,3,2,50,tzinfo=timezone.utc), 'eau'),
            (source_rows['moov-press'], 'Bourse de RFI : Deux journalistes malgaches récompensés',
             'https://new.moov.mg/actualite/123627-bourse-de-rfi-deux-journalistes-malgaches-recompenses', datetime(2026,11,3,16,57,tzinfo=timezone.utc), 'autre'),
        ]
        for source, title, url, published, sector in news:
            item = db.query(NewsItem).filter_by(canonical_id=url).first()
            if not item:
                item = db.query(NewsItem).filter_by(title=title).first()
            if item:
                item.canonical_id=url;item.original_url=url;item.source_id=source.id
                item.published_at=published;item.sector=sector
            else:
                db.add(NewsItem(source_id=source.id, canonical_id=url, title=title,
                    original_url=url, published_at=published, sector=sector, region=None))

        photo_claim = 'La photographie NASA montre le massif de Saririaky, dans le sud de Madagascar.'
        photo_case = db.query(Case).filter_by(owner_id=journalist.id, claim_text=photo_claim).first()
        if not photo_case:
            photo_case = Case(owner_id=journalist.id, claim_text=photo_claim,
                original_source_url=NASA_SOURCE, sector='environnement', region=None, status='en_cours')
            db.add(photo_case); db.flush()
        if not photo_case.asset_id:
            with Image.open(ASSET) as source_image:
                source_image = ImageOps.exif_transpose(source_image)
                exif = source_image.info.get('exif')
                source_image.thumbnail((5000,5000))
                prepared = BytesIO()
                options = {'quality':94,'optimize':True}
                if exif: options['exif'] = exif
                source_image.convert('RGB').save(prepared,format='JPEG',**options)
            media = store_media(db, journalist.id, prepared.getvalue(), 'NASA-ISS075-E-85249-Saririaky-working-copy.jpg')
            photo_case.asset_id = media.id
        if not db.query(Evidence).filter_by(case_id=photo_case.id, url=NASA_SOURCE).first():
            db.add(Evidence(case_id=photo_case.id, added_by=journalist.id,
                title='NASA Earth Observatory — « Moon-Like Madagascar »', url=NASA_SOURCE,
                date_of_source='2026-10-05',
                note='Publication primaire qui décrit le cliché ISS075-E-85249, acquis le 28 août 2026. Source de provenance; elle ne constitue pas une validation indépendante.',
                relation_type='contexte'))

        db.commit()
        print(f'Base locale indépendante : {DB}')
        print(f'Compte journaliste : {DEMO_USERS[0][0]} / {DEMO_USERS[0][3]}')
        print(f'Compte rédaction : {DEMO_USERS[1][0]} / {DEMO_USERS[1][3]}')
        print(f'Dossiers photo/article préparés; {db.query(NewsItem).count()} publications de presse liées; {db.query(Evidence).count()} références dans les carnets.')
        print('Aucune conclusion n’est préremplie; aucun flux RSS indisponible n’est présenté comme synchronisé.')


if __name__ == '__main__': main()
