"""Checker-ko - persistence, identity and media analysis (local MVP)."""
from __future__ import annotations
import base64
import hashlib
import hmac
import io
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sqlite3
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from urllib.parse import urlsplit
from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import create_engine, ForeignKey, String, DateTime, Integer, Boolean, Text, event, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
import jwt
from .regions import NATIONAL
from .source_catalog import CATALOG, CHECKED_AT
from . import storage

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = Path(os.environ.get('CHECKER_DATA_DIR', str(ROOT / 'private_data'))).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR = BASE_DIR / 'images'
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DB_URL = os.environ.get('DATABASE_URL', f'sqlite:///{(BASE_DIR / "checker.db").as_posix()}')
engine = create_engine(DB_URL, connect_args={'check_same_thread': False} if DB_URL.startswith('sqlite') else {}, pool_pre_ping=True,
                       pool_size=int(os.environ.get('DB_POOL_SIZE','2')), max_overflow=int(os.environ.get('DB_MAX_OVERFLOW','0')) if not DB_URL.startswith('sqlite') else 10,
                       pool_recycle=int(os.environ.get('DB_POOL_RECYCLE_SECONDS','180')))
if DB_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(dbapi_conn, _):
        cur = dbapi_conn.cursor(); cur.execute('PRAGMA foreign_keys=ON'); cur.close()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(250), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(30), default='journalist')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class UserSession(Base):
    __tablename__ = 'user_sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Media(Base):
    __tablename__ = 'media_assets'
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    original_filename: Mapped[str] = mapped_column(String(255))
    private_path: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(40))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    phash: Mapped[str] = mapped_column(String(16))
    video_timestamp_seconds: Mapped[float|None] = mapped_column(nullable=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    exif_json: Mapped[str] = mapped_column(Text, default='{}')
    is_archive: Mapped[bool] = mapped_column(Boolean, default=False)
    archive_title: Mapped[str|None] = mapped_column(String(250), nullable=True)
    archive_source_url: Mapped[str|None] = mapped_column(String(500), nullable=True)
    archive_date: Mapped[str|None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Analysis(Base):
    __tablename__ = 'media_analyses'
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey('media_assets.id'), unique=True)
    tool_status: Mapped[str] = mapped_column(String(40))
    c2pa_status: Mapped[str] = mapped_column(String(40))
    c2pa_claim_json: Mapped[str] = mapped_column(Text, default='{}')
    warnings_json: Mapped[str] = mapped_column(Text, default='[]')
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Case(Base):
    __tablename__ = 'verification_cases'
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int|None] = mapped_column(ForeignKey('media_assets.id'), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    claim_text: Mapped[str] = mapped_column(Text, default='')
    original_source_url: Mapped[str|None] = mapped_column(String(500), nullable=True)
    sector: Mapped[str] = mapped_column(String(80), default='autre')
    region: Mapped[str|None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(60), default='en_cours')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class CaseShare(Base):
    __tablename__ = 'case_shares'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('verification_cases.id'), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    revoked_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)

class Video(Base):
    __tablename__ = 'case_videos'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('verification_cases.id'), unique=True)
    private_path: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[float] = mapped_column()
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    frame_ids_json: Mapped[str] = mapped_column(Text, default='[]')

class SocialPost(Base):
    __tablename__ = 'case_social_posts'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('verification_cases.id'), index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    platform: Mapped[str] = mapped_column(String(30))
    original_url: Mapped[str] = mapped_column(String(2000))
    declared_account: Mapped[str|None] = mapped_column(String(250), nullable=True)
    published_at: Mapped[str|None] = mapped_column(String(80), nullable=True)
    capture_date: Mapped[str|None] = mapped_column(String(80), nullable=True)
    observation: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Evidence(Base):
    __tablename__ = 'evidence'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('verification_cases.id'))
    added_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    url: Mapped[str|None] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(250))
    date_of_source: Mapped[str|None] = mapped_column(String(30), nullable=True)
    note: Mapped[str] = mapped_column(Text, default='')
    relation_type: Mapped[str] = mapped_column(String(20))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_media_id: Mapped[int|None] = mapped_column(ForeignKey('media_assets.id'), nullable=True)
    media_id: Mapped[int|None] = mapped_column(ForeignKey('media_assets.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class SourceAssessment(Base):
    """Human, case-specific documentation of a source and its evidentiary scope."""
    __tablename__ = 'source_assessments'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('verification_cases.id'), index=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey('evidence.id'), unique=True, index=True)
    evaluator_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    source_identity_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    subject_expertise_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    verifiable_evidence_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    primary_source_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    date_verified_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    original_document_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    independent_corroboration_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    interests_disclosure_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    contradictions_status: Mapped[str|None] = mapped_column(String(20), nullable=True)
    evidence_relevance: Mapped[str|None] = mapped_column(String(30), nullable=True)
    assessment_summary: Mapped[str] = mapped_column(String(50), default='evaluation_incomplete')
    assessment_note: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class SourceAssessmentHistory(Base):
    __tablename__ = 'source_assessment_history'
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey('source_assessments.id'), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    change_kind: Mapped[str] = mapped_column(String(20))
    snapshot_json: Mapped[str] = mapped_column(Text)
    justification: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Verdict(Base):
    __tablename__ = 'verdicts'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('verification_cases.id'))
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    verdict: Mapped[str] = mapped_column(String(30))
    reasoning: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='author_validated')
    reviewer_id: Mapped[int|None] = mapped_column(ForeignKey('users.id'), nullable=True)
    reviewed_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class DirectorySource(Base):
    __tablename__ = 'source_directory'
    id: Mapped[int] = mapped_column(primary_key=True)
    organization: Mapped[str] = mapped_column(String(180))
    sector: Mapped[str] = mapped_column(String(80))
    website_url: Mapped[str|None] = mapped_column(String(500), nullable=True)
    description: Mapped[str] = mapped_column(String(500))
    geographic_scope: Mapped[str|None] = mapped_column(String(80), nullable=True)
    last_checked_at: Mapped[str|None] = mapped_column(String(30), nullable=True)
    demo_only: Mapped[bool] = mapped_column(Boolean, default=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    source_key: Mapped[str|None] = mapped_column(String(60), nullable=True)
    acronym: Mapped[str|None] = mapped_column(String(40), nullable=True)
    organization_type: Mapped[str|None] = mapped_column(String(80), nullable=True)
    region: Mapped[str|None] = mapped_column(String(80), nullable=True)
    reference_url: Mapped[str|None] = mapped_column(String(500), nullable=True)
    resources_json: Mapped[str] = mapped_column(Text, default='[]')
    contact_email: Mapped[str|None] = mapped_column(String(250), nullable=True)
    contact_phone: Mapped[str|None] = mapped_column(String(80), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(40), default='a_actualiser')

class DirectoryContact(Base):
    """Public professional contacts with an explicit verification reference."""
    __tablename__ = 'directory_contacts'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('source_directory.id'), index=True)
    name: Mapped[str] = mapped_column(String(180), default='')
    role: Mapped[str] = mapped_column(String(180), default='')
    email: Mapped[str|None] = mapped_column(String(250), nullable=True)
    phone: Mapped[str|None] = mapped_column(String(80), nullable=True)
    reference_url: Mapped[str] = mapped_column(String(500))
    verified_at: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class StatisticalObservation(Base):
    """Persisted indicator, with publication snapshot and exact document locator."""
    __tablename__ = 'statistical_observations'
    id: Mapped[int] = mapped_column(primary_key=True)
    publication_key: Mapped[str] = mapped_column(String(80), index=True)
    source_title: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str] = mapped_column(String(500))
    indicator: Mapped[str] = mapped_column(String(250))
    value: Mapped[str] = mapped_column(String(40))
    unit: Mapped[str] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer, index=True)
    region: Mapped[str|None] = mapped_column(String(80), nullable=True)
    source_locator: Mapped[str] = mapped_column(String(300))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

Index('ix_stat_obs_publication_year_region', StatisticalObservation.publication_key, StatisticalObservation.year, StatisticalObservation.region)

class Audit(Base):
    __tablename__ = 'audit_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    case_id: Mapped[int] = mapped_column(ForeignKey('verification_cases.id'))
    action: Mapped[str] = mapped_column(String(90))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    details_json: Mapped[str] = mapped_column(Text, default='{}')

class NewsSource(Base):
    __tablename__ = 'news_sources'
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    feed_url: Mapped[str] = mapped_column(String(500), unique=True)
    source_type: Mapped[str] = mapped_column(String(20), default='rss')
    sectors_json: Mapped[str] = mapped_column(Text, default='[]')
    checked_at: Mapped[str] = mapped_column(String(30))
    reuse_terms: Mapped[str] = mapped_column(Text, default='')
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class NewsItem(Base):
    __tablename__ = 'news_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('news_sources.id'), index=True)
    canonical_id: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    original_url: Mapped[str] = mapped_column(String(500))
    published_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    sector: Mapped[str] = mapped_column(String(80), default='autre')
    region: Mapped[str|None] = mapped_column(String(80), nullable=True)
    verification_case_id: Mapped[int|None] = mapped_column(ForeignKey('verification_cases.id'), unique=True, nullable=True)

class NewsSync(Base):
    __tablename__ = 'news_syncs'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('news_sources.id'))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='running')
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str|None] = mapped_column(String(500), nullable=True)

APP_ENV = os.environ.get('APP_ENV', 'development')
if APP_ENV not in ('development', 'test', 'production'):
    raise RuntimeError('APP_ENV doit valoir development, test ou production')
DEMO_MODE = os.environ.get('CHECKER_DEMO_MODE','').strip().lower()=='true'
LOCAL_DEMO_CATALOG = (DEMO_MODE and APP_ENV == 'development' and DB_URL.startswith('sqlite:')
    and os.environ.get('CHECKER_DEMO_LOCAL_CATALOG','').strip().lower()=='true')
DEMO_USERS = [('journaliste@checker.local', 'Journaliste Démo', 'journalist', 'Journaliste2026!'), ('redaction@checker.local', 'Responsable Rédaction', 'editor', 'Redaction2026!')]

def hash_password(password):
    salt=secrets.token_bytes(16)
    derived=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32)
    return 'scrypt$'+base64.b64encode(salt).decode()+'$'+base64.b64encode(derived).decode()

def verify_password(password, encoded):
    try:
        tag,salt_b64,key_b64=encoded.split('$')
        if tag!='scrypt': return False
        salt=base64.b64decode(salt_b64)
        expected=base64.b64decode(key_b64)
        return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32),expected)
    except (ValueError, TypeError): return False

SECRET = os.environ.get('CHECKER_SECRET', '')
if APP_ENV == 'production' and len(SECRET) < 32:
    raise RuntimeError('CHECKER_SECRET doit être configuré avec au moins 32 caractères en production')
if not SECRET:
    # local demo only, persisted across restarts for stable login; never print or ship it.
    secret_path = BASE_DIR / '.local_secret'
    if secret_path.exists(): SECRET=secret_path.read_text().strip()
    else:
        SECRET=secrets.token_urlsafe(48)
        secret_path.write_text(SECRET)
        try: os.chmod(secret_path,0o600)
        except OSError: pass

def make_token(db,user):
    session_id=uuid4().hex
    issued=now()
    db.query(UserSession).filter(UserSession.expires_at<=issued).delete(synchronize_session=False)
    expires=issued+timedelta(hours=4)
    db.add(UserSession(jti=session_id,user_id=user.id,expires_at=expires))
    db.flush()
    return jwt.encode({'sub':str(user.id),'sid':session_id,'iat':issued,'exp':expires},SECRET,algorithm='HS256')

def get_user(db, token):
    try:
        claims=jwt.decode(token,SECRET,algorithms=['HS256'])
        user=db.get(User,int(claims['sub']))
        if not user: raise ValueError('user')
        session=db.query(UserSession).filter_by(jti=claims['sid'],user_id=user.id,revoked_at=None).first()
        if not session or session.expires_at.replace(tzinfo=timezone.utc)<=now(): raise ValueError('session')
        return user
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401,detail='Session invalide ou expirée')

def revoke_token(db,token):
    if not token:return
    try:
        claims=jwt.decode(token,SECRET,algorithms=['HS256'])
        session=db.query(UserSession).filter_by(jti=claims.get('sid'),revoked_at=None).first()
        if session:
            session.revoked_at=now()
            db.commit()
    except (jwt.PyJWTError,TypeError,KeyError):
        db.rollback()

FORMATS={'JPEG':('image/jpeg','.jpg'), 'PNG':('image/png','.png'), 'WEBP':('image/webp','.webp')}
MAX_BYTES=10*1024*1024
MAX_PIXELS=25_000_000

def phash_for(im):
    """ImageHash pHash if installed; mathematically equivalent 32x32 DCT fallback offline."""
    try:
        import imagehash
        return str(imagehash.phash(im.convert('RGB')))
    except ImportError:
        # Self-contained fallback so the application is testable without pip downloads.
        grey=ImageOps.grayscale(im).resize((32,32),Image.Resampling.LANCZOS)
        pix=list(grey.getdata()); size=32
        # separable 2D DCT, only 8x8 low frequency coefficients necessary
        cos=[ [math.cos((2*x+1)*u*math.pi/(2*size)) for x in range(size)] for u in range(8)]
        rows=[[sum(pix[y*size+x]*cos[u][x] for x in range(size)) for u in range(8)] for y in range(size)]
        result=[[sum(rows[y][u]*cos[v][y] for y in range(size)) for u in range(8)] for v in range(8)]
        values=[result[v][u] for v in range(8) for u in range(8)]
        mid=sorted(values[1:])[len(values[1:])//2]
        value=0
        for coef in values: value=(value<<1) | int(coef>mid)
        return f'{value:016x}'

def inspect_image(data):
    if len(data)>MAX_BYTES: raise HTTPException(413,'Image de plus de 10 Mo refusée')
    if not data: raise HTTPException(400,'Fichier vide')
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt=im.format
            if fmt not in FORMATS: raise HTTPException(415,'JPEG, PNG ou WebP uniquement')
            if im.width*im.height > MAX_PIXELS: raise HTTPException(413,'Dimensions excessives')
            im.verify()
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            width,height=im.size
            photo_hash=phash_for(im)
            safe_exif={}
            exif=im.getexif()
            for tag, label in [(306,'date_modification_declared'),(36867,'date_capture_declared'),(36868,'date_digitized_declared'),(271,'make'),(272,'model')]:
                value=exif.get(tag)
                if value: safe_exif[label]=str(value)[:140]
            # Never expose GPS, serial numbers or EXIF location data.
        mime, ext=FORMATS[fmt]
        return {'mime':mime,'ext':ext,'width':width,'height':height,'phash':photo_hash,'exif':safe_exif,'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
    except HTTPException: raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise HTTPException(415,'Fichier image invalide ou illisible')

def c2pa_analyze(path):
    """Separate manifest presence, signature state and signer trust; no scene authenticity claim."""
    binary=tool_path('c2patool','C2PATOOL_PATH')
    if not binary:
        return ('outil_non_installe','indisponible',{'signature':'non_evaluee','emetteur':'non_evalue'},['c2patool non installé ; impossible de déterminer la présence d’un manifeste.'])
    try:
        result=subprocess.run([binary,str(path)],capture_output=True,text=True,timeout=10,shell=False)
        if result.returncode != 0:
            combined=(result.stderr+' '+result.stdout).lower()
            if 'no manifest' in combined or 'manifest not found' in combined or 'no c2pa' in combined or 'no claim found' in combined:
                return ('disponible','absent',{'signature':'non_applicable','emetteur':'non_applicable'},['Aucun manifeste détecté ; cela ne prouve pas une manipulation.'])
            return ('erreur','erreur',{'signature':'non_evaluee','emetteur':'non_evalue'},['Impossible d’interpréter le diagnostic c2patool.'])
        payload=json.loads(result.stdout)
        if not isinstance(payload,dict): raise ValueError('JSON type')
        manifests=payload.get('manifests') or {}
        active=payload.get('active_manifest')
        validation=payload.get('validation_status') or payload.get('validation_results') or {}
        if not active and not manifests:
            return ('disponible','absent',{'signature':'non_applicable','emetteur':'non_applicable'},['Absence de manifeste ≠ image fausse.'])
        # No claims of trusted signer without a configured trust store.
        errors=[]
        if isinstance(validation,list): errors=validation
        elif isinstance(validation,dict): errors=validation.get('failure') or validation.get('errors') or []
        nested=payload.get('validation_results') or {}
        if isinstance(nested,dict):
            errors=list(errors)+list((nested.get('activeManifest') or {}).get('failure') or [])
        codes={item.get('code','') for item in errors if isinstance(item,dict)}
        untrusted=any(code.startswith('signingCredential.untrusted') for code in codes)
        substantive=[code for code in codes if not code.startswith('signingCredential.untrusted')]
        if substantive:
            return ('disponible','non_fiable',{'signature':'erreurs_de_validation','emetteur':'non_evalue','nb_erreurs':len(substantive)},['Des erreurs de validation sont signalées ; enquête humaine nécessaire.'])
        if untrusted:
            return ('disponible','present',{'signature':'aucune_erreur_cryptographique_signalee','emetteur':'non_approuve','manifest_active':bool(active)},['Certificat de signature non approuvé par le magasin de confiance ; la scène photographiée reste à vérifier.'])
        return ('disponible','present',{'signature':'aucune_erreur_signalee','emetteur':'confiance_non_etablie','manifest_active':bool(active)},['La présence d’un manifeste ne valide pas l’affirmation photographique. La confiance de l’émetteur n’est pas établie.'])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, OSError):
        return ('erreur','erreur',{'signature':'non_evaluee','emetteur':'non_evalue'},['Analyse C2PA indisponible ou réponse illisible.'])

def tool_path(name, variable):
    configured=os.environ.get(variable)
    if configured:
        candidate=Path(configured).expanduser()
        if candidate.is_file(): return str(candidate.resolve())
    portable=ROOT.parent/'tools'/'media'
    if name in ('ffmpeg','ffprobe'):
        for candidate in portable.glob(f'ffmpeg/*/bin/{name}.exe'):
            if candidate.is_file():return str(candidate.resolve())
    elif name=='c2patool':
        candidate=portable/'c2patool'/'c2patool'/'c2patool.exe'
        if candidate.is_file():return str(candidate.resolve())
    return shutil.which(name)

def valid_url(value):
    if value in (None,''): return None
    parsed=urlsplit(value)
    if parsed.scheme not in ('http','https') or not parsed.netloc or parsed.username or parsed.password or len(value)>500:
        raise HTTPException(422,'URL publique http(s) invalide')
    return value

def store_media(db, owner_id, data, filename, is_archive=False, archive_title=None, archive_source_url=None, archive_date=None):
    properties=inspect_image(data)
    key='images/'+uuid4().hex+properties['ext']
    storage.put(key,data,properties['mime'])
    try:
        media=Media(owner_id=owner_id,original_filename=Path(filename).name[:255],private_path=key, mime_type=properties['mime'],size_bytes=properties['size'],sha256=properties['sha256'],phash=properties['phash'],width=properties['width'],height=properties['height'],exif_json=json.dumps(properties['exif']),is_archive=is_archive,archive_title=archive_title,archive_source_url=archive_source_url,archive_date=archive_date)
        db.add(media); db.flush()
        with storage.materialize(key) as path:
            tool,status,claims,warnings=c2pa_analyze(path)
        db.add(Analysis(asset_id=media.id,tool_status=tool,c2pa_status=status,c2pa_claim_json=json.dumps(claims),warnings_json=json.dumps(warnings,ensure_ascii=False)))
        return media
    except Exception:
        storage.delete(key)
        raise

def media_path(media):
    # Filename is generated by the backend and must be confined to private directory.
    path=(IMAGES_DIR/media.private_path).resolve()
    if path.parent!=IMAGES_DIR.resolve(): raise HTTPException(500,'Chemin média invalide')
    return path

def user_view(user): return {'id':user.id,'name':user.name,'email':user.email,'role':user.role}

def media_view(media, analysis=None):
    return {'id':media.id,'filename':media.original_filename,'mime_type':media.mime_type,'size_bytes':media.size_bytes,'sha256':media.sha256,'phash':media.phash,'width':media.width,'height':media.height,'video_timestamp_seconds':media.video_timestamp_seconds,'created_at':media.created_at,'exif':json.loads(media.exif_json),'is_archive':media.is_archive,'preview_url':f'/api/media/{media.id}/preview','analysis': {'tool_status':analysis.tool_status,'c2pa_status':analysis.c2pa_status,'claim':json.loads(analysis.c2pa_claim_json),'warnings':json.loads(analysis.warnings_json),'analyzed_at':analysis.analyzed_at} if analysis else None}

def assessment_view(value):
    if not value: return None
    fields=('source_identity_status','subject_expertise_status','verifiable_evidence_status','primary_source_status','date_verified_status','original_document_status','independent_corroboration_status','interests_disclosure_status','contradictions_status','evidence_relevance','assessment_summary','assessment_note')
    return {'id':value.id, **{field:getattr(value,field) for field in fields}, 'created_at':value.created_at,'updated_at':value.updated_at}

def evidence_view(e, assessment=None): return {'id':e.id,'title':e.title,'url':e.url,'date_of_source':e.date_of_source,'note':e.note,'relation_type':e.relation_type,'archived_media_id':e.archived_media_id,'media_id':e.media_id,'created_at':e.created_at,'assessment':assessment_view(assessment)}

def verdict_view(v, db):
    author=db.get(User,v.author_id)
    reviewer=db.get(User,v.reviewer_id) if v.reviewer_id else None
    return {'id':v.id,'verdict':v.verdict,'reasoning':v.reasoning,'status':v.status,'created_at':v.created_at,'author_name':author.name if author else 'Inconnu','reviewer_name':reviewer.name if reviewer else None,'reviewed_at':v.reviewed_at}

def audit(db, actor, case_id, action, data=None): db.add(Audit(actor_id=actor,case_id=case_id,action=action,details_json=json.dumps(data or {},ensure_ascii=False)))

def init_db():
    if DB_URL.startswith('sqlite'):
        database = engine.url.database
        if database and Path(database).exists():
            with sqlite3.connect(database) as connection:
                columns = [row[1:4] for row in connection.execute('PRAGMA table_info(verification_cases)')]
                if columns and any(name == 'asset_id' and not_null for name, _kind, not_null in columns):
                    # SQLite cannot drop NOT NULL in place. Keep IDs and all linked rows.
                    backup_path = Path(database).with_name(Path(database).name + '.pre-v04-' + now().strftime('%Y%m%d%H%M%S') + '.bak')
                    with sqlite3.connect(backup_path) as backup_connection:
                        connection.backup(backup_connection)
                    connection.execute('PRAGMA foreign_keys=OFF')
                    connection.execute('BEGIN IMMEDIATE')
                    connection.execute('''CREATE TABLE verification_cases_new (
                        id INTEGER PRIMARY KEY, asset_id INTEGER REFERENCES media_assets(id),
                        owner_id INTEGER NOT NULL REFERENCES users(id), claim_text TEXT NOT NULL,
                        original_source_url VARCHAR(500), sector VARCHAR(80) NOT NULL,
                        status VARCHAR(60) NOT NULL, created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL)''')
                    names = 'id, asset_id, owner_id, claim_text, original_source_url, sector, status, created_at, updated_at'
                    connection.execute(f'INSERT INTO verification_cases_new ({names}) SELECT {names} FROM verification_cases')
                    connection.execute('DROP TABLE verification_cases')
                    connection.execute('ALTER TABLE verification_cases_new RENAME TO verification_cases')
                    connection.commit()
                    connection.execute('PRAGMA foreign_keys=ON')
                # Migration additive : aucune enquête ni fiche historique n'est supprimée.
                existing_tables={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                additions={
                    'verification_cases': {'region':'VARCHAR(80)'},
                    'media_assets': {'video_timestamp_seconds':'FLOAT'},
                    'evidence': {'media_id':'INTEGER REFERENCES media_assets(id)'},
                    'source_directory': {
                        'archived':'BOOLEAN NOT NULL DEFAULT 0', 'source_key':'VARCHAR(60)',
                        'acronym':'VARCHAR(40)', 'organization_type':'VARCHAR(80)',
                        'region':'VARCHAR(80)', 'reference_url':'VARCHAR(500)',
                        'resources_json':"TEXT NOT NULL DEFAULT '[]'", 'contact_email':'VARCHAR(250)',
                        'contact_phone':'VARCHAR(80)', 'verification_status':"VARCHAR(40) NOT NULL DEFAULT 'a_actualiser'",
                    },
                    'news_items': {'verification_case_id':'INTEGER'},
                }
                needs_migration=any(table in existing_tables and set(fields)-{row[1] for row in connection.execute(f'PRAGMA table_info({table})')} for table,fields in additions.items())
                if needs_migration:
                    backup_path=Path(database).with_name(Path(database).name+'.pre-v043-'+now().strftime('%Y%m%d%H%M%S')+'.bak')
                    with sqlite3.connect(backup_path) as backup_connection:
                        connection.backup(backup_connection)
                    for table,fields in additions.items():
                        if table not in existing_tables: continue
                        existing={row[1] for row in connection.execute(f'PRAGMA table_info({table})')}
                        for field,kind in fields.items():
                            if field not in existing:
                                connection.execute(f'ALTER TABLE {table} ADD COLUMN {field} {kind}')
                    connection.commit()
    # SQLite remains the zero-configuration local backend. PostgreSQL schemas are
    # managed by Alembic so production startup never creates or alters tables.
    if DB_URL.startswith('sqlite'):
        Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for email,name,role,password in (DEMO_USERS if APP_ENV == 'development' else []):
            if not db.query(User).filter_by(email=email).first():
                db.add(User(name=name,email=email,role=role,password_hash=hash_password(password)))
        # Sources are application-controlled; users cannot submit arbitrary collection URLs.
        feeds=[
            ('madagascar-tribune','Madagascar Tribune','https://www.madagascar-tribune.com/spip.php?page=backend'),
            ('newsmada','NewsMada','https://newsmada.com/feed/'),
            ('lexpress-madagascar',"L’Express de Madagascar",'https://www.lexpress.mg/feeds/posts/default?alt=rss'),
        ]
        old_midi=db.query(NewsSource).filter_by(key='midi-madagasikara').first()
        if old_midi:
            old_midi.enabled=False
        for key,name,feed_url in feeds:
            if not db.query(NewsSource).filter_by(key=key).first():
                db.add(NewsSource(key=key,name=name,feed_url=feed_url,source_type='rss',
                    sectors_json='["autre"]',checked_at='2026-11-03',
                    reuse_terms='Consulter les conditions du site éditeur avant toute republication.',enabled=True))
        db.commit()
        if not DEMO_MODE or LOCAL_DEMO_CATALOG:
            for old in db.query(DirectorySource).filter_by(demo_only=True,archived=False).all():
                old.archived=True
            for entry in CATALOG:
                if db.query(DirectorySource).filter_by(source_key=entry['key']).first(): continue
                if db.query(DirectorySource).filter_by(website_url=entry['website_url'],demo_only=False).first(): continue
                db.add(DirectorySource(organization=entry['organization'],acronym=entry['acronym'],organization_type=entry['kind'],sector=entry['sector'],description=entry['description'],website_url=entry['website_url'],reference_url=entry['reference_url'],resources_json=json.dumps(entry['resources']),geographic_scope='Tout Madagascar',region=NATIONAL,last_checked_at=CHECKED_AT,verification_status='partiellement_verifiees',source_key=entry['key'],demo_only=False,archived=False))
        db.commit()
        # Seed archived photos once, shared by all logged-in journalists for demonstration only.
        if APP_ENV == 'development' and not db.query(Media).filter_by(is_archive=True).first():
            author=db.query(User).filter_by(email=DEMO_USERS[0][0]).first()
            demodir=ROOT/'demo_assets'
            for index,(name,title) in enumerate([('archive_pont.png','ARCHIVE FICTIVE — passerelle et arbres'),('archive_route.png','ARCHIVE FICTIVE — route et collines'),('archive_ecole.png','ARCHIVE FICTIVE — façade scolaire')]):
                p=demodir/name
                if p.exists(): store_media(db,author.id,p.read_bytes(),name,True,title,None,'2026-01-01')
            db.commit()
