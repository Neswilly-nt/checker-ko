"""Tests are isolated from the user's private SQLite database and uploaded files."""
import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

_TMP=Path(tempfile.mkdtemp(prefix='checker_ko_tests_'))
os.environ['CHECKER_DATA_DIR']=str(_TMP)
os.environ['DATABASE_URL']='sqlite:///'+str(_TMP/'test.db')
from app.main import app

@pytest.fixture(scope='session')
def client():
    with TestClient(app) as cli:
        yield cli

@pytest.fixture
def journalist(client):
    resp=client.post('/api/auth/login',json={'email':'journaliste@checker.local','password':'Journaliste2026!'},headers={'X-Checker-CSRF':'1'})
    assert resp.status_code==200
    client.cookies.clear()
    return {'Authorization':'Bearer '+resp.json()['access_token']}

@pytest.fixture
def editor(client):
    resp=client.post('/api/auth/login',json={'email':'redaction@checker.local','password':'Redaction2026!'},headers={'X-Checker-CSRF':'1'})
    assert resp.status_code==200
    client.cookies.clear()
    return {'Authorization':'Bearer '+resp.json()['access_token']}

@pytest.fixture
def upload_case(client,journalist):
    asset=Path(__file__).parents[1]/'demo_assets'/'variante_pont.jpg'
    response=client.post('/api/media/upload',headers=journalist,files={'file':('variante_pont.jpg',asset.read_bytes(),'image/jpeg')},data={'caption':'Légende non vérifiée','sector':'environnement'})
    assert response.status_code==201,response.text
    return response.json()['id']
