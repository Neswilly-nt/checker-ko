"""Create repeatable, TEST-labelled scenarios in a dedicated local SQLite database.

This script never connects to PostgreSQL/Supabase and never deletes existing rows.
It generates a short synthetic MP4 with FFmpeg and uses the repository's demo photo.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / '.demo-test-data'
DB = DATA / 'checker-test.sqlite3'

# Set these before importing the application modules: their engines are built at import.
os.environ['APP_ENV'] = 'development'
os.environ['CHECKER_DEMO_MODE'] = 'true'
os.environ['CHECKER_SECRET'] = 'TEST-only-local-secret-do-not-use'
os.environ['CHECKER_STORAGE_BACKEND'] = 'local'
os.environ['CHECKER_DATA_DIR'] = str(DATA / 'storage')
os.environ['DATABASE_URL'] = 'sqlite:///' + DB.as_posix()
sys.path.insert(0, str(BACKEND))

from app.core import (  # noqa: E402
    Case, DirectorySource, Evidence, NewsItem, NewsSource, SessionLocal,
    User, Verdict, Video, hash_password, init_db, store_media,
)
from app import storage  # noqa: E402

TEST_PREFIX = '[TEST] '
TEST_EMAIL = 'checker.test.scenarios@example.test'
VIDEO_KEY = 'videos/test-scenario-clip.mp4'
VIDEO_CLAIM = TEST_PREFIX + 'Une séquence synthétique montre une place publique fictive.'
PHOTO_CLAIM = TEST_PREFIX + 'Cette image de démonstration montre un pont fictif.'
TEXT_CLAIM = TEST_PREFIX + 'La bibliothèque fictive ouvrirait tous les dimanches.'
NEWS_CLAIM = TEST_PREFIX + 'Un article RSS fictif annonce une fermeture temporaire.'
TEST_DATE = datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)


def find_or_create_case(db, user_id: int, claim: str, **fields) -> Case:
    case = db.query(Case).filter_by(owner_id=user_id, claim_text=claim).first()
    if case:
        return case
    case = Case(owner_id=user_id, claim_text=claim, status='en_cours', **fields)
    db.add(case)
    db.flush()
    return case


def add_test_evidence_and_verdict(db, case: Case, user_id: int) -> None:
    title = TEST_PREFIX + 'Source fictive de démonstration'
    if not db.query(Evidence).filter_by(case_id=case.id, title=title).first():
        db.add(Evidence(case_id=case.id, added_by=user_id, title=title,
            url='https://example.test/test-source', date_of_source='2026-01-15',
            note=TEST_PREFIX + 'Contenu fictif réservé aux essais; à recouper.', relation_type='contexte'))
    if not db.query(Verdict).filter_by(case_id=case.id).first():
        db.add(Verdict(case_id=case.id, author_id=user_id, verdict='Indéterminé',
            reasoning=TEST_PREFIX + 'Exemple non factuel pour tester l’affichage d’une conclusion.'))


def create_test_video() -> bytes:
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg est requis pour générer la séquence MP4 de test.')
    output = DATA / 'test-synthetic.mp4'
    DATA.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
        '-f', 'lavfi', '-i', 'color=c=0x8bd6a8:s=320x180:r=12:d=2',
        '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)],
        capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('Échec de création MP4: ' + result.stderr[-500:])
    return output.read_bytes()


def main() -> int:
    # The target is constructed here, never accepted from DATABASE_URL or a CLI argument.
    if not str(DB).startswith(str(BACKEND)) or not DB.parent.is_relative_to(BACKEND):
        raise RuntimeError('Chemin de base locale hors du répertoire autorisé.')
    if os.environ['DATABASE_URL'] != 'sqlite:///' + DB.as_posix() or storage.BACKEND != 'local':
        raise RuntimeError('Le seed exige la base SQLite dédiée et le stockage local.')
    DATA.mkdir(parents=True, exist_ok=True)
    init_db()
    video_bytes = create_test_video()
    photo_path = BACKEND / 'demo_assets' / 'variante_pont.jpg'
    if not photo_path.is_file():
        raise RuntimeError(f'Image de démonstration introuvable: {photo_path}')

    with SessionLocal() as db:
        user = db.query(User).filter_by(email=TEST_EMAIL).first()
        if not user:
            user = User(name='Journaliste TEST', email=TEST_EMAIL, role='journalist',
                        password_hash=hash_password('TEST-only-Password-2026!'))
            db.add(user)
            db.flush()

        directory = db.query(DirectorySource).filter_by(organization=TEST_PREFIX + 'Source fictive').first()
        if not directory:
            directory = DirectorySource(organization=TEST_PREFIX + 'Source fictive', sector='autre',
                description=TEST_PREFIX + 'Fiche de test sans organisme réel.', website_url='https://example.test',
                geographic_scope='TEST', demo_only=True, archived=False, verification_status='a_actualiser')
            db.add(directory)

        text_case = find_or_create_case(db, user.id, TEXT_CLAIM, sector='education', region='TEST')
        photo_case = find_or_create_case(db, user.id, PHOTO_CLAIM, sector='autre', region='TEST')
        video_case = find_or_create_case(db, user.id, VIDEO_CLAIM, sector='autre', region='TEST')

        if not photo_case.asset_id:
            media = store_media(db, user.id, photo_path.read_bytes(), 'TEST-variante-pont.jpg')
            photo_case.asset_id = media.id
        if not db.query(Video).filter_by(case_id=video_case.id).first():
            storage.put(VIDEO_KEY, video_bytes, 'video/mp4')
            db.add(Video(case_id=video_case.id, private_path=VIDEO_KEY, original_filename='TEST-sequence.mp4',
                sha256=hashlib.sha256(video_bytes).hexdigest(), size_bytes=len(video_bytes),
                duration_seconds=2.0, width=320, height=180, frame_ids_json='[]'))

        source = db.query(NewsSource).filter_by(key='checker-test-rss').first()
        if not source:
            source = NewsSource(key='checker-test-rss', name=TEST_PREFIX + 'Flux RSS fictif',
                feed_url='https://example.test/test-feed.xml', source_type='rss', sectors_json='["autre"]',
                checked_at='2026-01-15', reuse_terms='TEST uniquement', enabled=False)
            db.add(source)
            db.flush()
        news_case = find_or_create_case(db, user.id, NEWS_CLAIM, original_source_url='https://example.test/test-article', sector='autre', region='TEST')
        article = db.query(NewsItem).filter_by(canonical_id='https://example.test/test-article').first()
        if not article:
            article = NewsItem(source_id=source.id, canonical_id='https://example.test/test-article',
                title=NEWS_CLAIM, original_url='https://example.test/test-article', published_at=TEST_DATE,
                collected_at=TEST_DATE, sector='autre', region='TEST', verification_case_id=news_case.id)
            db.add(article)
        add_test_evidence_and_verdict(db, text_case, user.id)
        add_test_evidence_and_verdict(db, photo_case, user.id)
        add_test_evidence_and_verdict(db, video_case, user.id)
        add_test_evidence_and_verdict(db, news_case, user.id)
        db.commit()
        print(f'Base isolée: {DB}')
        print('Scénarios TEST prêts: texte, photo, vidéo MP4 2 s, article RSS; TEST source, preuves et conclusions.')
        print('Aucune donnée Render/Supabase ciblée; aucun enregistrement existant supprimé.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'Seed local interrompu sans suppression: {exc}', file=sys.stderr)
        raise SystemExit(2)
