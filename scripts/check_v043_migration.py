"""Exercise the V0.4.3 migration twice on a copied SQLite database."""
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
live = root / 'backend/private_data/checker.db'
snapshots = sorted(live.parent.glob(live.name + '.pre-v043-*.bak'))
source = snapshots[0] if snapshots else live
directory = Path(tempfile.mkdtemp(prefix='checker_ko_v043_'))
target = directory / 'checker.db'
shutil.copy2(source, target)
os.environ['CHECKER_DATA_DIR'] = str(directory)
os.environ['DATABASE_URL'] = 'sqlite:///' + target.as_posix()
sys.path.insert(0, str(root / 'backend'))
from app.core import init_db

tables = ('users', 'verification_cases', 'evidence', 'verdicts', 'media_assets', 'source_directory', 'audit_events')
with sqlite3.connect(target) as connection:
    existing = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    before = {name: [row[0] for row in connection.execute(f'SELECT id FROM {name} ORDER BY id')] for name in tables if name in existing}
    old_sources = connection.execute('SELECT id FROM source_directory WHERE demo_only=1').fetchall()
init_db()
init_db()
with sqlite3.connect(target) as connection:
    after = {name: [row[0] for row in connection.execute(f'SELECT id FROM {name} ORDER BY id')] for name in before}
    active = connection.execute('SELECT source_key FROM source_directory WHERE archived=0 ORDER BY source_key').fetchall()
    archived = connection.execute('SELECT id FROM source_directory WHERE demo_only=1 AND archived=1').fetchall()
    fk_errors = list(connection.execute('PRAGMA foreign_key_check'))
for name in before:
    if name != 'source_directory':
        assert before[name] == after[name], name
assert {item[0] for item in active} == {'bngrc', 'men', 'instat', 'metfp', 'dgm'}, active
assert archived == old_sources, (archived, old_sources)
assert len(after['source_directory']) == len(before['source_directory']) + 5
assert not fk_errors, fk_errors
print('Migration sur copie OK; historique conservé; 5 sources actives; archives fictives:', len(archived))
print('Copie temporaire:', target)
