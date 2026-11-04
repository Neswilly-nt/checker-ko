"""Seed six clearly marked local demo cases into a dedicated SQLite database."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / 'private_data' / 'demo'
DB = DATA / 'checker_demo.db'
MARKER = DATA / '.checker-ko-demo-data'
CREDENTIALS = DATA / 'credentials.json'
TEST_PREFIX = '[TEST] '
FAKE_STATS_KEY = 'demo-fictitious-values'
FAKE_STATS_LABEL = 'DONN\u00c9E FICTIVE \u2014 D\u00c9MONSTRATION'
TEST_EMAIL = 'journaliste.test@checker.local'
EDITOR_EMAIL = 'redaction.test@checker.local'
VIDEO_KEY = 'videos/test-scenario-clip.mp4'
TEST_DATE = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)


def load_demo_credentials() -> dict[str, dict[str, str]]:
    if CREDENTIALS.is_file():
        values = json.loads(CREDENTIALS.read_text(encoding='utf-8'))
        if values.get('journalist', {}).get('email') != TEST_EMAIL or values.get('editor', {}).get('email') != EDITOR_EMAIL:
            raise RuntimeError('Fichier local des comptes de test invalide.')
        return values
    values = {
        'journalist': {'email': TEST_EMAIL, 'password': secrets.token_urlsafe(24)},
        'editor': {'email': EDITOR_EMAIL, 'password': secrets.token_urlsafe(24)},
    }
    CREDENTIALS.write_text(json.dumps(values, ensure_ascii=True, indent=2) + chr(10), encoding='utf-8')
    try:
        CREDENTIALS.chmod(0o600)
    except OSError:
        pass
    return values


def prepare_demo_directory(reset: bool) -> None:
    if DATA.is_symlink():
        raise RuntimeError('Le dossier de demo ne peut pas etre un lien symbolique.')
    if DATA.exists() and any(DATA.iterdir()) and not MARKER.is_file():
        raise RuntimeError(f'Dossier preexistant sans marqueur de demo, refus de toucher: {DATA}')
    DATA.mkdir(parents=True, exist_ok=True)
    if reset:
        if not MARKER.is_file() or MARKER.read_text(encoding='utf-8') != 'Checker-ko local demo database and files.\n':
            raise RuntimeError('Reinitialisation refusee: marqueur local de demo manquant.')
        for target in (DB, Path(str(DB) + '-wal'), Path(str(DB) + '-shm'), DATA / 'test-synthetic.mp4', DATA / 'test-video-frame.png'):
            if target.is_symlink():
                raise RuntimeError(f'Reinitialisation refusee sur un lien: {target}')
            if target.is_file():
                target.unlink()
        storage_dir = DATA / 'storage'
        if storage_dir.is_symlink():
            raise RuntimeError(f'Reinitialisation refusee sur un lien: {storage_dir}')
        if storage_dir.is_dir():
            shutil.rmtree(storage_dir)
    MARKER.write_text('Checker-ko local demo database and files.\n', encoding='utf-8')


parser = argparse.ArgumentParser(description='Initialiser la base de demonstration locale Checker-ko.')
parser.add_argument('--reset', action='store_true', help='R?initialiser uniquement la base et le stockage de demo marqu?s.')
ARGS = parser.parse_args()
prepare_demo_directory(ARGS.reset)

# Set local-only configuration before importing application modules.
os.environ['APP_ENV'] = 'development'
os.environ['CHECKER_DEMO_MODE'] = 'true'
os.environ['CHECKER_DEMO_LOCAL_CATALOG'] = 'true'
os.environ['CHECKER_SECRET'] = secrets.token_urlsafe(48)
os.environ['CHECKER_STORAGE_BACKEND'] = 'local'
os.environ['CHECKER_DATA_DIR'] = str(DATA / 'storage')
os.environ['DATABASE_URL'] = 'sqlite:///' + DB.as_posix()
sys.path.insert(0, str(BACKEND))

from app import storage  # noqa: E402
from app.core import (  # noqa: E402
    Case, DirectorySource, Evidence, NewsItem, NewsSource, SessionLocal,
    StatisticalObservation, User, Verdict, Video, hash_password, init_db, store_media,
)

CASES = {
    'school': TEST_PREFIX + 'Rumeur fictive : les \u00e9coles d\u2019Analamanga seraient ferm\u00e9es demain.',
    'photo': TEST_PREFIX + 'Cette image de demonstration montrerait un pont apres une crue.',
    'video': TEST_PREFIX + 'Cette sequence video synthetique montre une place publique fictive.',
    'news': TEST_PREFIX + 'Un article RSS fictif annonce une fermeture temporaire.',
    'statistics': TEST_PREFIX + 'Une affirmation numerique fictive sur les ecoles doit etre verifiee.',
    'weather': TEST_PREFIX + 'Alerte meteorologique fictive concernant Androy.',
}


def create_test_video() -> tuple[bytes, bytes]:
    configured = os.environ.get('FFMPEG_PATH')
    ffmpeg = configured if configured and Path(configured).is_file() else shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg requis pour fabriquer la video et son image cle synthetiques.')
    output = DATA / 'test-synthetic.mp4'
    frame = DATA / 'test-video-frame.png'
    result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'lavfi', '-i', 'color=c=0x8bd6a8:s=320x180:r=12:d=2',
        '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)],
        capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('Echec de generation MP4: ' + result.stderr[-500:])
    result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(output),
        '-frames:v', '1', str(frame)], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('Echec de generation de image cle: ' + result.stderr[-500:])
    return output.read_bytes(), frame.read_bytes()


def find_or_create_case(db, user_id: int, key: str, sector: str, region: str, source_url: str | None = None) -> Case:
    claim = CASES[key]
    case = db.query(Case).filter_by(owner_id=user_id, claim_text=claim).first()
    if case:
        return case
    case = Case(owner_id=user_id, claim_text=claim, original_source_url=source_url,
                sector=sector, region=region, status='en_cours')
    db.add(case)
    db.flush()
    return case


def add_evidence(db, case: Case, user_id: int, title: str, url: str, note: str) -> None:
    if not db.query(Evidence).filter_by(case_id=case.id, title=title).first():
        db.add(Evidence(case_id=case.id, added_by=user_id, title=title, url=url,
            date_of_source='2026-11-03', note=note, relation_type='contexte'))


def add_test_verdict(db, case: Case, user_id: int) -> None:
    if not db.query(Verdict).filter_by(case_id=case.id).first():
        db.add(Verdict(case_id=case.id, author_id=user_id, verdict='Indetermine',
            reasoning=TEST_PREFIX + 'Conclusion fictive non factuelle pour tester le rapport; aucune affirmation reelle nest evaluee.'))
    case.status = 'concluded'


def add_fake_statistics(db, user_id: int) -> None:
    examples = [
        ('[TEST] Etablissements scolaires fictifs', '247', 'ecoles', 'Analamanga', 'Exemple fictif; aucune page ni source reelle.'),
        ('[TEST] Precipitations fictives', '18', 'mm', 'Androy', 'Exemple fictif; aucune page ni source reelle.'),
        ('[TEST] Acces a leau fictif', '62', '%', 'TEST', 'Exemple fictif; aucune page ni source reelle.'),
    ]
    for indicator, value, unit, region, locator in examples:
        existing = db.query(StatisticalObservation).filter_by(publication_key=FAKE_STATS_KEY, indicator=indicator, year=2026).first()
        if not existing:
            db.add(StatisticalObservation(publication_key=FAKE_STATS_KEY, source_title=FAKE_STATS_LABEL,
                source_url='https://example.test/demo-values-fictitious', indicator=indicator, value=value,
                unit=unit, year=2026, region=region, source_locator=locator, created_by=user_id))


def main() -> int:
    if DB.parent != DATA or not DATA.is_relative_to(BACKEND / 'private_data'):
        raise RuntimeError('Cible SQLite hors du dossier prive local de demo.')
    if os.environ['DATABASE_URL'] != 'sqlite:///' + DB.as_posix() or storage.BACKEND != 'local':
        raise RuntimeError('Le seed exige la base SQLite dediee et le stockage local.')
    credentials = load_demo_credentials()
    init_db()
    photo_path = BACKEND / 'demo_assets' / 'variante_pont.jpg'
    if not photo_path.is_file():
        raise RuntimeError(f'Image de demonstration autoris?e introuvable: {photo_path}')
    video_bytes, frame_bytes = create_test_video()

    with SessionLocal() as db:
        user = db.query(User).filter_by(email=TEST_EMAIL).first()
        if not user:
            user = User(name='Journaliste TEST', email=TEST_EMAIL, role='journalist', password_hash=hash_password(credentials['journalist']['password']))
            db.add(user)
            db.flush()
        editor = db.query(User).filter_by(email=EDITOR_EMAIL).first()
        if not editor:
            editor = User(name='Redaction TEST', email=EDITOR_EMAIL, role='editor', password_hash=hash_password(credentials['editor']['password']))
            db.add(editor)
            db.flush()
        directory = db.query(DirectorySource).filter_by(organization=TEST_PREFIX + 'Source fictive').first()
        if not directory:
            db.add(DirectorySource(organization=TEST_PREFIX + 'Source fictive', acronym='TEST', sector='autre',
                description=TEST_PREFIX + 'Fiche de test sans organisme reel.', website_url='https://example.test',
                geographic_scope='TEST uniquement', demo_only=False, archived=False, verification_status='a_actualiser'))

        school = find_or_create_case(db, user.id, 'school', '?ducation', 'Analamanga')
        photo = find_or_create_case(db, user.id, 'photo', 'autre', 'Analamanga')
        video = find_or_create_case(db, user.id, 'video', 'autre', 'TEST')
        stats = find_or_create_case(db, user.id, 'statistics', '?ducation', 'Analamanga')
        weather = find_or_create_case(db, user.id, 'weather', 'm\u00e9t\u00e9o/catastrophes', 'Androy')

        if not photo.asset_id:
            media = store_media(db, user.id, photo_path.read_bytes(), 'TEST-variante-pont.jpg')
            photo.asset_id = media.id
        if not db.query(Video).filter_by(case_id=video.id).first():
            frame_media = store_media(db, user.id, frame_bytes, 'TEST-video-frame.png')
            storage.put(VIDEO_KEY, video_bytes, 'video/mp4')
            db.add(Video(case_id=video.id, private_path=VIDEO_KEY, original_filename='TEST-sequence.mp4',
                sha256=hashlib.sha256(video_bytes).hexdigest(), size_bytes=len(video_bytes),
                duration_seconds=2.0, width=320, height=180, frame_ids_json=json.dumps([frame_media.id])))

        news_source = db.query(NewsSource).filter_by(key='checker-test-rss').first()
        if not news_source:
            news_source = NewsSource(key='checker-test-rss', name=TEST_PREFIX + 'Flux RSS fictif',
                feed_url='https://example.test/test-feed.xml', source_type='rss', sectors_json='["autre"]',
                checked_at='2026-11-03', reuse_terms='TEST uniquement; ne pas republier.', enabled=False)
            db.add(news_source)
            db.flush()
        news = find_or_create_case(db, user.id, 'news', 'autre', 'TEST', 'https://example.test/test-article')
        article = db.query(NewsItem).filter_by(canonical_id='https://example.test/test-article').first()
        if not article:
            db.add(NewsItem(source_id=news_source.id, canonical_id='https://example.test/test-article',
                title=CASES['news'], original_url='https://example.test/test-article', published_at=TEST_DATE,
                collected_at=TEST_DATE, sector='autre', region='TEST', verification_case_id=news.id))

        add_evidence(db, photo, user.id, TEST_PREFIX + 'Contexte de image synthetique', 'https://example.test/photo-context', TEST_PREFIX + 'Le media est autoris et fictif; ce contexte ne valide pas image.')
        add_evidence(db, video, user.id, TEST_PREFIX + 'Image cle g?n?r?e localement', None, TEST_PREFIX + 'Image cle extraite du MP4 synthetique de deux secondes.')
        add_evidence(db, news, user.id, TEST_PREFIX + 'Publication RSS fictive', 'https://example.test/test-article', TEST_PREFIX + 'Article synthetique; date et source sont des donnees de demonstration.')
        add_evidence(db, news, user.id, TEST_PREFIX + 'Recoupement de demonstration', 'https://example.test/test-corroboration', TEST_PREFIX + 'Seconde reference fictive pour essayer la comparaison; aucune source reelle.')
        add_fake_statistics(db, user.id)
        add_evidence(db, stats, user.id, TEST_PREFIX + 'Observation statistique fictive', 'https://example.test/demo-values-fictitious', FAKE_STATS_LABEL + '. Valeur inventee, sans document officiel ni source reelle.')
        add_evidence(db, weather, user.id, TEST_PREFIX + 'Bulletin meteo fictif', 'https://example.test/test-weather', TEST_PREFIX + 'Aucune alerte reelle; exemple destine  tester le carnet de preuves.')
        add_test_verdict(db, stats, user.id)
        add_test_verdict(db, news, user.id)
        db.commit()
        print(f'Base SQLite locale : {DB}')
        print(f'Compte journaliste de test local : {TEST_EMAIL}')
        print(f'Mot de passe local : {credentials["journalist"]["password"]}')
        print(f'Compte editeur de test local : {EDITOR_EMAIL}')
        print(f'Mot de passe local editeur : {credentials["editor"]["password"]}')
        print('6 dossiers TEST: nouveau, photo avec preuve, video avec image cle, RSS avec 2 references fictives, statistique fictive avec rapport, risque meteo fictif.')
        print('Fiches institutionnelles officielles et publications documentaires sont ajoutees separement avec leur statut de verification.')
        print('Aucune base Render/Supabase ni donnee reelle na ete ciblee.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'Seed local interrompu sans suppression: {exc}', file=sys.stderr)
        raise SystemExit(2)
