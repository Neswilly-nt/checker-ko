"""Run manually against a copy of the user's current database; never edit the original."""
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

backend = Path(__file__).resolve().parents[1]
source = backend / 'private_data' / 'checker.db'
directory = Path(tempfile.mkdtemp(prefix='checker_ko_migration_'))
target = directory / 'checker.db'
shutil.copy2(source, target)
os.environ['CHECKER_DATA_DIR'] = str(directory)
os.environ['DATABASE_URL'] = 'sqlite:///' + target.as_posix()
sys.path.insert(0, str(backend))
from app.core import init_db

tables = ('verification_cases', 'evidence', 'verdicts', 'media_assets')
with sqlite3.connect(target) as connection:
    before = {table: connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in tables}
init_db()
with sqlite3.connect(target) as connection:
    after = {table: connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in tables}
    nullable = next(row[3] == 0 for row in connection.execute('PRAGMA table_info(verification_cases)') if row[1] == 'asset_id')
    foreign_key_errors = list(connection.execute('PRAGMA foreign_key_check'))
assert before == after, (before, after)
assert nullable
assert not foreign_key_errors, foreign_key_errors
print('Migration vérifiée sur copie :', before, 'identifiants et liens conservés ; sauvegarde :', directory)
