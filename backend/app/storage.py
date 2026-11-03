"""Private file storage adapters for local development and Supabase Storage."""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
from urllib.parse import quote
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException

DATA_DIR = Path(os.environ.get('CHECKER_DATA_DIR', Path(__file__).resolve().parents[1] / 'private_data')).expanduser().resolve()
BACKEND = os.environ.get('CHECKER_STORAGE_BACKEND', 'local').strip().lower()
BUCKET = os.environ.get('CHECKER_SUPABASE_STORAGE_BUCKET', 'checker-private').strip()


class StorageError(RuntimeError):
    pass


def _key(value: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or '..' in path.parts or '\\' in value:
        raise StorageError('Invalid private storage key')
    return value.lstrip('/')


def _local_path(key: str) -> Path:
    key = _key(key)
    # Preserve existing SQLite records that stored only the generated filename.
    if '/' not in key:
        key = f'images/{key}'
    root = DATA_DIR.resolve()
    target = (root / key).resolve()
    if root not in target.parents:
        raise StorageError('Private storage path escaped its root')
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _supabase_settings() -> tuple[str, str]:
    base = os.environ.get('CHECKER_SUPABASE_URL', '').rstrip('/')
    service_key = os.environ.get('CHECKER_SUPABASE_SERVICE_ROLE_KEY', '')
    parsed = urlsplit(base)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or not service_key or not BUCKET:
        raise StorageError('Supabase Storage configuration is incomplete')
    return base, service_key


def put(key: str, data: bytes, content_type: str) -> None:
    key = _key(key)
    if BACKEND == 'local':
        _local_path(key).write_bytes(data)
        return
    if BACKEND != 'supabase':
        raise StorageError('CHECKER_STORAGE_BACKEND must be local or supabase')
    base, secret = _supabase_settings()
    url = f'{base}/storage/v1/object/{quote(BUCKET, safe="")}/{quote(key, safe="/")}'
    try:
        response = httpx.post(url, content=data, headers={
            'Authorization': f'Bearer {secret}', 'apikey': secret,
            'Content-Type': content_type, 'x-upsert': 'false',
        }, timeout=30)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise StorageError('Supabase Storage upload failed') from exc


def read(key: str) -> bytes:
    key = _key(key)
    if BACKEND == 'local':
        try:
            return _local_path(key).read_bytes()
        except OSError as exc:
            raise HTTPException(404, 'Média introuvable') from exc
    if BACKEND != 'supabase':
        raise StorageError('CHECKER_STORAGE_BACKEND must be local or supabase')
    base, secret = _supabase_settings()
    url = f'{base}/storage/v1/object/{quote(BUCKET, safe="")}/{quote(key, safe="/")}'
    try:
        response = httpx.get(url, headers={'Authorization': f'Bearer {secret}', 'apikey': secret}, timeout=30)
        if response.status_code == 404:
            raise HTTPException(404, 'Média introuvable')
        response.raise_for_status()
        return response.content
    except httpx.HTTPError as exc:
        raise StorageError('Supabase Storage download failed') from exc


def delete(key: str) -> None:
    key = _key(key)
    if BACKEND == 'local':
        _local_path(key).unlink(missing_ok=True)
        return
    if BACKEND != 'supabase':
        raise StorageError('CHECKER_STORAGE_BACKEND must be local or supabase')
    base, secret = _supabase_settings()
    url = f'{base}/storage/v1/object/{quote(BUCKET, safe="")}'
    try:
        response = httpx.delete(url, json={'prefixes': [key]}, headers={
            'Authorization': f'Bearer {secret}', 'apikey': secret,
        }, timeout=30)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise StorageError('Supabase Storage deletion failed') from exc


@contextmanager
def materialize(key: str):
    """Yield a local path for tools such as Pillow, FFmpeg, and c2patool."""
    if BACKEND == 'local':
        yield _local_path(key)
        return
    suffix = Path(key).suffix
    tmp = NamedTemporaryFile(prefix='checker-ko-', suffix=suffix, delete=False)
    path = Path(tmp.name)
    try:
        with tmp:
            tmp.write(read(key))
        yield path
    finally:
        path.unlink(missing_ok=True)


def ensure_configured() -> None:
    if BACKEND not in ('local', 'supabase'):
        raise RuntimeError('CHECKER_STORAGE_BACKEND must be local or supabase')
    if BACKEND == 'supabase':
        try:
            base, secret = _supabase_settings()
            response = httpx.get(f'{base}/storage/v1/bucket/{quote(BUCKET, safe="")}', headers={
                'Authorization': f'Bearer {secret}', 'apikey': secret,
            }, timeout=15)
            response.raise_for_status()
            if response.json().get('public') is not False:
                raise StorageError('The configured Supabase Storage bucket must be private')
        except httpx.HTTPError as exc:
            raise RuntimeError('Supabase Storage bucket could not be verified; create a private bucket first') from exc
        except StorageError as exc:
            raise RuntimeError(str(exc)) from exc
