from pathlib import Path

import pytest
from fastapi import HTTPException

from app import storage


def test_local_storage_round_trip_and_confined_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'BACKEND', 'local')
    monkeypatch.setattr(storage, 'DATA_DIR', tmp_path)
    key='images/demo.png'
    storage.put(key, b'fictional-image', 'image/png')
    assert storage.read(key)==b'fictional-image'
    with storage.materialize(key) as path:
        assert path.read_bytes()==b'fictional-image'
    storage.delete(key)
    with pytest.raises(HTTPException):
        storage.read(key)
    with pytest.raises(storage.StorageError):
        storage.put('../outside.png', b'x', 'image/png')


def test_supabase_storage_is_private_and_accessed_only_server_side(monkeypatch):
    monkeypatch.setattr(storage, 'BACKEND', 'supabase')
    monkeypatch.setattr(storage, 'BUCKET', 'checker-private')
    monkeypatch.setenv('CHECKER_SUPABASE_URL', 'https://project-ref.supabase.co')
    monkeypatch.setenv('CHECKER_SUPABASE_SERVICE_ROLE_KEY', 'sb_secret_test-only-secret')
    calls=[]

    class Response:
        status_code=200
        content=b'fictional-image'
        def raise_for_status(self): pass
        def json(self): return {'public': False}

    def get(url, **kwargs):
        calls.append(('get',url,kwargs))
        return Response()
    def post(url, **kwargs):
        calls.append(('post',url,kwargs))
        return Response()
    def delete(url, **kwargs):
        calls.append(('delete',url,kwargs))
        return Response()
    monkeypatch.setattr(storage.httpx, 'get', get)
    monkeypatch.setattr(storage.httpx, 'post', post)
    monkeypatch.setattr(storage.httpx, 'delete', delete)

    storage.ensure_configured()
    storage.put('images/fictional.png', b'fictional-image', 'image/png')
    assert storage.read('images/fictional.png')==b'fictional-image'
    with storage.materialize('images/fictional.png') as path:
        assert Path(path).read_bytes()==b'fictional-image'
    assert not Path(path).exists()
    storage.delete('images/fictional.png')
    assert calls[0][0]=='get' and calls[0][2]['headers']=={'apikey':'sb_secret_test-only-secret'}
    assert all('/object/public/' not in call[1] for call in calls)


def test_legacy_supabase_service_role_jwt_is_sent_as_bearer():
    key='eyJlegacy-service-role-test'
    assert storage._supabase_headers(key)=={
        'apikey':key,
        'Authorization':f'Bearer {key}',
    }


def test_supabase_storage_rejects_public_bucket(monkeypatch):
    monkeypatch.setattr(storage, 'BACKEND', 'supabase')
    monkeypatch.setattr(storage, 'BUCKET', 'checker-private')
    monkeypatch.setenv('CHECKER_SUPABASE_URL', 'https://project-ref.supabase.co')
    monkeypatch.setenv('CHECKER_SUPABASE_SERVICE_ROLE_KEY', 'test-only-secret')

    class Response:
        def raise_for_status(self): pass
        def json(self): return {'public': True}

    monkeypatch.setattr(storage.httpx, 'get', lambda *args, **kwargs: Response())
    with pytest.raises(RuntimeError, match='must be private'):
        storage.ensure_configured()
