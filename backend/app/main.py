"""REST API for Checker-ko. Start: uvicorn app.main:app --reload"""
from __future__ import annotations
import json
import os
import shutil
import hashlib
import subprocess
import tempfile
from uuid import uuid4
from io import BytesIO
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from PIL import Image, ImageOps
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .core import (Analysis, Case, Video, DirectorySource, Evidence, SourceAssessment, SourceAssessmentHistory, Media, User, Verdict, NewsItem, NewsSource, NewsSync, SessionLocal,
    now, init_db, DEMO_USERS, make_token, get_user, verify_password, store_media, media_path, media_view,
    evidence_view, assessment_view, verdict_view, audit, valid_url, MAX_BYTES, c2pa_analyze, user_view, IMAGES_DIR, BASE_DIR, APP_ENV, tool_path)
from .regions import REGIONS, NATIONAL, UNKNOWN, normalize_region
from .news import sync_source
from .statistical_catalog import PUBLICATIONS, publication_view

app=FastAPI(title='Checker-ko API',description='Assistance à la vérification journalistique — aucune décision de vérité automatique.',version='0.7.0')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],allow_credentials=False,allow_methods=['*'],allow_headers=['*'])

@app.on_event('startup')
def startup(): init_db()

def db_session():
    with SessionLocal() as db: yield db

def current_user(authorization:str|None=Header(default=None),db:Session=Depends(db_session)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401,'Authentification requise')
    return get_user(db,authorization.removeprefix('Bearer '))

def get_case(case_id:int,db:Session,user:User):
    item=db.get(Case,case_id)
    if not item: raise HTTPException(404,'Dossier introuvable')
    if item.owner_id != user.id and not (user.role=='editor' and item.status in ('review_requested','reviewed','changes_requested')):
        raise HTTPException(403,'Vous n’avez pas accès à ce dossier')
    return item

def only_owner(item:Case,user:User):
    if item.owner_id!=user.id: raise HTTPException(403,'Action réservée au propriétaire')

class LoginIn(BaseModel):
    email: str
    password: str

class EvidenceIn(BaseModel):
    title: str = Field(min_length=2,max_length=250)
    url: str|None = None
    date_of_source: str|None = Field(default=None,max_length=30)
    note: str = Field(default='',max_length=5000)
    relation_type: Literal['appuie','contredit','contexte']
    archived_media_id: int|None = None

AssessmentStatus = Literal['oui','non','a_verifier','non_applicable']
class AssessmentIn(BaseModel):
    source_identity_status: AssessmentStatus|None = None
    subject_expertise_status: AssessmentStatus|None = None
    verifiable_evidence_status: AssessmentStatus|None = None
    primary_source_status: AssessmentStatus|None = None
    date_verified_status: AssessmentStatus|None = None
    original_document_status: AssessmentStatus|None = None
    independent_corroboration_status: AssessmentStatus|None = None
    interests_disclosure_status: AssessmentStatus|None = None
    contradictions_status: AssessmentStatus|None = None
    evidence_relevance: Literal['directe','indirecte','non_etablie']|None = None
    assessment_note: str = Field(default='',max_length=5000)
    justification: str = Field(default='',max_length=2000)

class VerdictIn(BaseModel):
    verdict: Literal['Confirmé','Faux','Trompeur','Non déterminé']
    reasoning: str = Field(min_length=12,max_length=8000)

class ReviewIn(BaseModel):
    decision: Literal['approved','changes_requested']
    note: str = Field(default='',max_length=3000)

class DirectoryIn(BaseModel):
    organization:str=Field(min_length=3,max_length=180)
    sector:str=Field(min_length=3,max_length=80)
    description:str=Field(min_length=3,max_length=500)
    website_url:str|None=None
    geographic_scope:str|None=None
    acronym:str|None=Field(default=None,max_length=40)
    organization_type:str|None=Field(default=None,max_length=80)
    region:str|None=Field(default=None,max_length=80)
    reference_url:str|None=None
    contact_email:str|None=Field(default=None,max_length=250)
    contact_phone:str|None=Field(default=None,max_length=80)
    verification_status:Literal['verifiees','partiellement_verifiees','a_actualiser']='a_actualiser'

class ClaimIn(BaseModel):
    claim_text:str=Field(min_length=3,max_length=8000)
    original_source_url:str|None=None
    sector:str=Field(default='autre',max_length=80)
    region:str|None=Field(default=None,max_length=80)

def news_item_view(item, source):
    return {'id':item.id,'title':item.title,'original_url':item.original_url,'published_at':item.published_at,
        'collected_at':item.collected_at,'sector':item.sector,'region':item.region,'source':source.name,
        'source_id':source.id,'verification_case_id':item.verification_case_id}

@app.get('/api/health')
def health():
    return {'status':'ok','c2patool_installed':bool(tool_path('c2patool','C2PATOOL_PATH')),'ffmpeg_installed':bool(tool_path('ffmpeg','FFMPEG_PATH') and tool_path('ffprobe','FFPROBE_PATH')),'mode':APP_ENV}

@app.get('/api/regions')
def regions(user:User=Depends(current_user)):
    return {'items':list(REGIONS),'national':NATIONAL,'unknown':UNKNOWN,'reference_url':'https://www.metfp.gov.mg/cartographie'}

def checked_region(value):
    try:return normalize_region(value)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.post('/api/auth/login')
def login(data:LoginIn,db:Session=Depends(db_session)):
    user=db.query(User).filter_by(email=data.email.lower().strip()).first()
    if APP_ENV == 'production' and user and user.email in {entry[0] for entry in DEMO_USERS}:
        raise HTTPException(401,'Identifiants incorrects')
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,'Identifiants incorrects')
    return {'access_token':make_token(user),'token_type':'bearer','user':user_view(user)}

@app.get('/api/auth/me')
def me(user:User=Depends(current_user)): return user_view(user)

def match_view(media,dist):
    return {'media_id':media.id,'title':media.archive_title or media.original_filename,
        'source_url':media.archive_source_url,'archive_date':media.archive_date,
        'distance':dist,'visual_similarity_index':round((1-dist/64)*100,1),
        'preview_url':f'/api/media/{media.id}/preview','is_demo':media.is_archive,
        'warning':'Indice visuel uniquement ; comparaison à confirmer par une personne.'}

def matches_for_media(db,media,user):
    threshold=int(os.environ.get('PHASH_THRESHOLD','12'))
    threshold=max(0,min(threshold,64))
    # Protect other journalists' private photos; archive is explicitly shared and fictitious.
    other=db.query(Media).filter(Media.id!=media.id,or_(Media.is_archive.is_(True),Media.owner_id==user.id)).all()
    output=[]
    for m in other:
        d=(int(m.phash,16)^int(media.phash,16)).bit_count()
        if d<=threshold:
            output.append(match_view(m,d))
    return sorted(output,key=lambda x:x['distance'])[:15]

def matches_for(db,item,user):
    if item.asset_id is None: return []
    return matches_for_media(db,db.get(Media,item.asset_id),user)

def case_view(db,item,user):
    media=db.get(Media,item.asset_id) if item.asset_id else None
    analysis=db.query(Analysis).filter_by(asset_id=media.id).first() if media else None
    video=db.query(Video).filter_by(case_id=item.id).first()
    evidence=db.query(Evidence).filter_by(case_id=item.id).order_by(Evidence.id.desc()).all()
    assessments={value.evidence_id:value for value in db.query(SourceAssessment).filter_by(case_id=item.id).all()}
    verdicts=db.query(Verdict).filter_by(case_id=item.id).order_by(Verdict.id.desc()).all()
    author=db.get(User,item.owner_id)
    return {'id':item.id,'claim_text':item.claim_text,'original_source_url':item.original_source_url,
        'status':item.status,'sector':item.sector,'region':item.region,'created_at':item.created_at,'updated_at':item.updated_at,
        'owner_id':item.owner_id,'owner_name':author.name,'media':media_view(media,analysis) if media else None,
        'video':{'filename':video.original_filename,'sha256':video.sha256,'size_bytes':video.size_bytes,
                 'duration_seconds':video.duration_seconds,'width':video.width,'height':video.height,
                 'frames':[media_view(db.get(Media,mid)) for mid in json.loads(video.frame_ids_json)]} if video else None,
        'matches':matches_for(db,item,user),'evidence':[evidence_view(e,assessments.get(e.id)) for e in evidence],
        'verdicts':[verdict_view(v,db) for v in verdicts]}

@app.get('/api/cases')
def list_cases(q:str='',db:Session=Depends(db_session),user:User=Depends(current_user)):
    stmt=db.query(Case)
    if user.role=='editor': stmt=stmt.filter(or_(Case.owner_id==user.id,Case.status.in_(['review_requested','reviewed','changes_requested'])))
    else: stmt=stmt.filter_by(owner_id=user.id)
    if q: stmt=stmt.filter(Case.claim_text.ilike(f'%{q[:100]}%'))
    total=stmt.count()
    concluded=stmt.filter(Case.id.in_(db.query(Verdict.case_id))).count()
    cases=stmt.order_by(Case.created_at.desc()).limit(100).all()
    video_ids={row[0] for row in db.query(Video.case_id).filter(Video.case_id.in_([c.id for c in cases])).all()} if cases else set()
    return {'items':[{'id':c.id,'claim_text':c.claim_text or 'Image sans affirmation','status':c.status,'sector':c.sector,'region':c.region,'content_type':'video' if c.id in video_ids else 'photo' if c.asset_id else 'texte','created_at':c.created_at,'updated_at':c.updated_at} for c in cases],
        'total':total,'concluded':concluded}

@app.post('/api/media/upload',status_code=201)
async def upload(file:UploadFile=File(...), caption:str=Form(''),source_url:str=Form(''),sector:str=Form('autre'),region:str=Form(''),db:Session=Depends(db_session),user:User=Depends(current_user)):
    valid_url(source_url)
    if len(caption)>8000 or len(sector)>80: raise HTTPException(422,'Données trop longues')
    chunks=await file.read(MAX_BYTES+1)
    if len(chunks)>MAX_BYTES: raise HTTPException(413,'Image de plus de 10 Mo refusée')
    new_path=None
    try:
        media=store_media(db,user.id,chunks,file.filename or 'image')
        new_path=media_path(media)
        item=Case(asset_id=media.id,owner_id=user.id,claim_text=caption.strip(),original_source_url=source_url or None,sector=sector,region=checked_region(region),status='en_cours')
        db.add(item);db.flush()
        audit(db,user.id,item.id,'upload',{'asset_id':media.id})
        db.commit()
        return {'id':item.id,'message':'Dossier et analyse enregistrés','media_id':media.id}
    except Exception:
        db.rollback()
        if new_path is not None: new_path.unlink(missing_ok=True)
        raise

@app.post('/api/cases',status_code=201)
def create_claim(data:ClaimIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=Case(owner_id=user.id,claim_text=data.claim_text.strip(),original_source_url=valid_url(data.original_source_url),sector=data.sector,region=checked_region(data.region),status='en_cours')
    db.add(item);db.flush();audit(db,user.id,item.id,'claim_created',{'region':data.region});db.commit()
    return {'id':item.id}

@app.get('/api/news')
def list_news(q:str='',sector:str='',region:str='',source_id:str='',order:Literal['newest','oldest']='newest',db:Session=Depends(db_session),user:User=Depends(current_user)):
    stmt=db.query(NewsItem,NewsSource).join(NewsSource,NewsItem.source_id==NewsSource.id)
    if q: stmt=stmt.filter(NewsItem.title.ilike(f'%{q[:100]}%'))
    if sector: stmt=stmt.filter(NewsItem.sector==sector[:80])
    if region: stmt=stmt.filter(NewsItem.region==checked_region(region))
    if source_id:
        try: stmt=stmt.filter(NewsItem.source_id==int(source_id))
        except ValueError as exc: raise HTTPException(422,'Source invalide') from exc
    sort=NewsItem.published_at.asc().nullslast() if order=='oldest' else NewsItem.published_at.desc().nullslast()
    rows=stmt.order_by(sort,NewsItem.collected_at.desc()).limit(200).all()
    sources=db.query(NewsSource).filter_by(enabled=True).order_by(NewsSource.name).all()
    last=db.query(NewsSync).filter_by(status='success').order_by(NewsSync.completed_at.desc()).first()
    latest_errors=db.query(NewsSync).filter_by(status='error').order_by(NewsSync.completed_at.desc()).limit(3).all()
    return {'items':[news_item_view(item,src) for item,src in rows], 'sources':[{'id':s.id,'name':s.name} for s in sources],
        'last_sync_at':last.completed_at if last else None,'errors':[s.error_message for s in latest_errors if s.error_message]}

@app.post('/api/news/sync')
def collect_news(db:Session=Depends(db_session),user:User=Depends(current_user)):
    if user.role!='editor': raise HTTPException(403,'Collecte réservée au responsable de rédaction')
    try:
        results=[sync_source(db,source) for source in db.query(NewsSource).filter_by(enabled=True).all()]
    except RuntimeError as exc: raise HTTPException(409,str(exc)) from exc
    return {'items':[{'source_id':x.source_id,'status':x.status,'inserted_count':x.inserted_count,'error_message':x.error_message} for x in results]}

@app.post('/api/news/{item_id}/verify',status_code=201)
def create_case_from_news(item_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    article=db.get(NewsItem,item_id)
    if not article: raise HTTPException(404,'Publication introuvable')
    if article.verification_case_id:
        case=get_case(article.verification_case_id,db,user)
        return {'id':case.id,'existing':True}
    item=Case(owner_id=user.id,claim_text=article.title,original_source_url=article.original_url,sector=article.sector,region=article.region,status='en_cours')
    db.add(item);db.flush(); article.verification_case_id=item.id
    audit(db,user.id,item.id,'news_case_created',{'news_item_id':article.id,'published_at':article.published_at.isoformat() if article.published_at else None})
    db.commit()
    return {'id':item.id,'existing':False}

VIDEO_MAX_BYTES=int(os.environ.get('VIDEO_MAX_MB','50'))*1024*1024
VIDEO_MAX_SECONDS=int(os.environ.get('VIDEO_MAX_SECONDS','30'))

@app.post('/api/video/upload',status_code=201)
async def upload_video(file:UploadFile=File(...),caption:str=Form(''),source_url:str=Form(''),sector:str=Form('autre'),region:str=Form(''),db:Session=Depends(db_session),user:User=Depends(current_user)):
    ffmpeg,ffprobe=tool_path('ffmpeg','FFMPEG_PATH'),tool_path('ffprobe','FFPROBE_PATH')
    if not ffmpeg or not ffprobe: raise HTTPException(503,'FFmpeg et ffprobe doivent être installés pour examiner une vidéo.')
    valid_url(source_url)
    if len(caption)>8000 or len(sector)>80: raise HTTPException(422,'Données trop longues')
    data=await file.read(VIDEO_MAX_BYTES+1)
    if len(data)>VIDEO_MAX_BYTES: raise HTTPException(413,'Vidéo trop volumineuse')
    if len(data)<12 or data[4:8]!=b'ftyp': raise HTTPException(415,'Fichier MP4 invalide')
    videos_dir=BASE_DIR/'videos';videos_dir.mkdir(exist_ok=True)
    path=videos_dir/(uuid4().hex+'.mp4')
    path.write_bytes(data)
    frame_paths=[]
    try:
        result=subprocess.run([ffprobe,'-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(path)],capture_output=True,text=True,timeout=15,shell=False)
        if result.returncode: raise HTTPException(415,'Vidéo MP4 illisible')
        info=json.loads(result.stdout)
        duration=float(info.get('format',{}).get('duration',0))
        stream=next((s for s in info.get('streams',[]) if s.get('codec_type')=='video'),None)
        if not stream or duration<=0: raise HTTPException(415,'Aucune piste vidéo lisible')
        if duration>VIDEO_MAX_SECONDS: raise HTTPException(413,'Vidéo trop longue')
        width,height=int(stream.get('width',0)),int(stream.get('height',0))
        if width<1 or height<1 or width*height>25_000_000: raise HTTPException(413,'Résolution vidéo excessive')
        frame_ids=[]
        for index in range(3):
            at=max(0.0,min(duration-0.05,duration*(index+1)/4))
            extract=subprocess.run([ffmpeg,'-nostdin','-v','error','-ss',str(at),'-i',str(path),'-frames:v','1','-vf','scale=800:800:force_original_aspect_ratio=decrease','-f','image2pipe','-vcodec','mjpeg','pipe:1'],capture_output=True,timeout=20,shell=False)
            if extract.returncode or not extract.stdout: raise HTTPException(422,'Extraction des images-clés impossible')
            frame=store_media(db,user.id,extract.stdout,f'image-cle-{index+1}.jpg')
            frame_paths.append(media_path(frame));frame_ids.append(frame.id)
        item=Case(asset_id=frame_ids[0],owner_id=user.id,claim_text=caption.strip(),original_source_url=source_url or None,sector=sector,region=checked_region(region),status='en_cours')
        db.add(item);db.flush()
        db.add(Video(case_id=item.id,private_path=path.name,original_filename=Path(file.filename or 'video.mp4').name[:255],sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data),duration_seconds=duration,width=width,height=height,frame_ids_json=json.dumps(frame_ids)))
        audit(db,user.id,item.id,'video_uploaded',{'frame_ids':frame_ids});db.commit()
        return {'id':item.id,'frame_ids':frame_ids}
    except (subprocess.TimeoutExpired,OSError,ValueError,KeyError,json.JSONDecodeError) as exc:
        db.rollback();path.unlink(missing_ok=True)
        for frame_path in frame_paths:frame_path.unlink(missing_ok=True)
        raise HTTPException(422,'Analyse vidéo impossible ou délai dépassé') from exc
    except Exception:
        db.rollback();path.unlink(missing_ok=True)
        for frame_path in frame_paths:frame_path.unlink(missing_ok=True)
        raise

@app.get('/api/cases/{case_id}')
def case_details(case_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    return case_view(db,get_case(case_id,db,user),user)

@app.get('/api/cases/{case_id}/matches')
def matches(case_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    return {'items':matches_for(db,get_case(case_id,db,user),user),'scope':'archives internes Checker-ko et dossiers accessibles uniquement'}

@app.get('/api/cases/{case_id}/frames/{media_id}/matches')
def frame_matches(case_id:int,media_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user)
    video=db.query(Video).filter_by(case_id=item.id).first()
    if not video or media_id not in json.loads(video.frame_ids_json): raise HTTPException(404,'Image-clé introuvable')
    return {'items':matches_for_media(db,db.get(Media,media_id),user)}

@app.post('/api/cases/{case_id}/analyze')
def analyze(case_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user); only_owner(item,user)
    if item.asset_id is None: raise HTTPException(422,'Ce dossier ne contient pas de photo')
    media=db.get(Media,item.asset_id)
    tool,status,claims,warnings=c2pa_analyze(media_path(media))
    record=db.query(Analysis).filter_by(asset_id=media.id).first()
    record.tool_status=tool;record.c2pa_status=status
    record.c2pa_claim_json=json.dumps(claims,ensure_ascii=False);record.warnings_json=json.dumps(warnings,ensure_ascii=False);record.analyzed_at=now()
    audit(db,user.id,item.id,'reanalyzed');db.commit()
    return case_view(db,item,user)

@app.post('/api/cases/{case_id}/evidence',status_code=201)
def add_evidence(case_id:int,data:EvidenceIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user);only_owner(item,user)
    if data.archived_media_id:
        archive=db.get(Media,data.archived_media_id)
        if not archive or not (archive.is_archive or archive.owner_id==user.id): raise HTTPException(403,'Archive inaccessible')
        # A chosen match must actually be a match, preventing arbitrary hidden media linking.
        allowed={m['media_id'] for m in matches_for(db,item,user)}
        video=db.query(Video).filter_by(case_id=item.id).first()
        if video:
            for frame_id in json.loads(video.frame_ids_json):
                allowed.update(m['media_id'] for m in matches_for_media(db,db.get(Media,frame_id),user))
        if archive.id not in allowed: raise HTTPException(422,'Cette archive ne correspond pas au dossier')
    url=valid_url(data.url)
    e=Evidence(case_id=case_id,added_by=user.id,url=url,title=data.title,note=data.note,date_of_source=data.date_of_source,relation_type=data.relation_type,archived_media_id=data.archived_media_id)
    db.add(e);audit(db,user.id,item.id,'evidence_added');item.updated_at=now();db.commit()
    return evidence_view(e)

@app.delete('/api/cases/{case_id}/evidence/{evidence_id}')
def delete_evidence(case_id:int,evidence_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user);only_owner(item,user)
    evidence=db.query(Evidence).filter_by(id=evidence_id,case_id=case_id).first()
    if not evidence: raise HTTPException(404,'Preuve introuvable')
    db.delete(evidence);audit(db,user.id,case_id,'evidence_removed');item.updated_at=now();db.commit()
    return {'ok':True}

@app.put('/api/cases/{case_id}/evidence/{evidence_id}')
def edit_evidence(case_id:int,evidence_id:int,data:EvidenceIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user);only_owner(item,user)
    evidence=db.query(Evidence).filter_by(id=evidence_id,case_id=case_id).first()
    if not evidence: raise HTTPException(404,'Preuve introuvable')
    if data.archived_media_id!=evidence.archived_media_id:
        if data.archived_media_id and data.archived_media_id not in [m['media_id'] for m in matches_for(db,item,user)]: raise HTTPException(422,'Archive non associable')
    evidence.title=data.title;evidence.url=valid_url(data.url);evidence.note=data.note
    evidence.date_of_source=data.date_of_source;evidence.relation_type=data.relation_type;evidence.archived_media_id=data.archived_media_id
    audit(db,user.id,case_id,'evidence_edited');item.updated_at=now();db.commit()
    return evidence_view(evidence)

ASSESSMENT_FIELDS=('source_identity_status','subject_expertise_status','verifiable_evidence_status','primary_source_status','date_verified_status','original_document_status','independent_corroboration_status','interests_disclosure_status','contradictions_status','evidence_relevance')

def descriptive_summary(data:AssessmentIn)->str:
    """Describe documentation only; never infer truth or compute a confidence score."""
    core=(data.source_identity_status,data.subject_expertise_status,data.verifiable_evidence_status)
    if any(value is None for value in core): return 'evaluation_incomplete'
    if data.contradictions_status=='oui' or 'non' in core: return 'points_de_vigilance'
    if all(value=='oui' for value in core) and data.evidence_relevance=='directe': return 'elements_solides'
    return 'source_partiellement_documentee'

def assessment_snapshot(assessment:SourceAssessment):
    return {field:getattr(assessment,field) for field in ASSESSMENT_FIELDS+('assessment_summary','assessment_note')}

@app.get('/api/cases/{case_id}/evidence/{evidence_id}/assessment')
def get_assessment(case_id:int,evidence_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    get_case(case_id,db,user)
    if not db.query(Evidence).filter_by(id=evidence_id,case_id=case_id).first(): raise HTTPException(404,'Preuve introuvable')
    return assessment_view(db.query(SourceAssessment).filter_by(case_id=case_id,evidence_id=evidence_id).first())

@app.post('/api/cases/{case_id}/evidence/{evidence_id}/assessment',status_code=201)
def save_assessment(case_id:int,evidence_id:int,data:AssessmentIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user);only_owner(item,user)
    if not db.query(Evidence).filter_by(id=evidence_id,case_id=case_id).first(): raise HTTPException(404,'Preuve introuvable')
    record=db.query(SourceAssessment).filter_by(case_id=case_id,evidence_id=evidence_id).first()
    is_new=record is None
    if is_new: record=SourceAssessment(case_id=case_id,evidence_id=evidence_id,evaluator_id=user.id)
    for field in ASSESSMENT_FIELDS: setattr(record,field,getattr(data,field))
    record.assessment_note=data.assessment_note.strip();record.assessment_summary=descriptive_summary(data);record.updated_at=now()
    if is_new: db.add(record);db.flush()
    db.add(SourceAssessmentHistory(assessment_id=record.id,author_id=user.id,change_kind='created' if is_new else 'updated',snapshot_json=json.dumps(assessment_snapshot(record),ensure_ascii=False),justification=data.justification.strip()))
    audit(db,user.id,case_id,'source_assessment_created' if is_new else 'source_assessment_updated',{'evidence_id':evidence_id})
    item.updated_at=now();db.commit();return assessment_view(record)

@app.patch('/api/cases/{case_id}/evidence/{evidence_id}/assessment')
def update_assessment(case_id:int,evidence_id:int,data:AssessmentIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    return save_assessment(case_id,evidence_id,data,db,user)

@app.get('/api/cases/{case_id}/evidence/{evidence_id}/assessment/history')
def assessment_history(case_id:int,evidence_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    get_case(case_id,db,user)
    record=db.query(SourceAssessment).filter_by(case_id=case_id,evidence_id=evidence_id).first()
    if not record: return {'items':[]}
    rows=db.query(SourceAssessmentHistory).filter_by(assessment_id=record.id).order_by(SourceAssessmentHistory.id.desc()).all()
    return {'items':[{'id':row.id,'change_kind':row.change_kind,'snapshot':json.loads(row.snapshot_json),'justification':row.justification,'created_at':row.created_at,'author_name':db.get(User,row.author_id).name} for row in rows]}

@app.get('/api/cases/{case_id}/assessments/summary')
def assessments_summary(case_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    get_case(case_id,db,user)
    evidence=db.query(Evidence).filter_by(case_id=case_id).all()
    assessments={x.evidence_id:x for x in db.query(SourceAssessment).filter_by(case_id=case_id).all()}
    def item(e): return evidence_view(e,assessments.get(e.id))
    return {'favorable':[item(e) for e in evidence if e.relation_type=='appuie'], 'contraire':[item(e) for e in evidence if e.relation_type=='contredit'], 'contexte_et_incertitudes':[item(e) for e in evidence if e.relation_type=='contexte' or not assessments.get(e.id) or assessments[e.id].assessment_summary in ('evaluation_incomplete','points_de_vigilance')]}

@app.post('/api/cases/{case_id}/verdict',status_code=201)
def submit_verdict(case_id:int,data:VerdictIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user);only_owner(item,user)
    if len(data.reasoning.strip())<12:raise HTTPException(422,'Une justification de 12 caractères minimum est obligatoire')
    verdict=Verdict(case_id=item.id,author_id=user.id,verdict=data.verdict,reasoning=data.reasoning.strip(),status='author_validated')
    db.add(verdict);item.status='concluded';item.updated_at=now()
    audit(db,user.id,item.id,'human_verdict',{'verdict':data.verdict});db.commit()
    return verdict_view(verdict,db)

@app.post('/api/cases/{case_id}/request-review')
def request_review(case_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user);only_owner(item,user)
    verdict=db.query(Verdict).filter_by(case_id=item.id).order_by(Verdict.id.desc()).first()
    if not verdict: raise HTTPException(422,'Un verdict humain est requis avant relecture')
    verdict.status='pending_review';item.status='review_requested';item.updated_at=now()
    audit(db,user.id,item.id,'review_requested');db.commit()
    return {'status':item.status}

@app.post('/api/cases/{case_id}/review')
def review(case_id:int,data:ReviewIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    if user.role!='editor': raise HTTPException(403,'Réservé au responsable de rédaction')
    item=get_case(case_id,db,user)
    if item.owner_id==user.id:raise HTTPException(403,'La relecture exige un autre compte')
    if item.status!='review_requested':raise HTTPException(422,'Ce dossier ne demande pas de relecture')
    v=db.query(Verdict).filter_by(case_id=item.id).order_by(Verdict.id.desc()).first()
    v.status=data.decision;v.reviewer_id=user.id;v.reviewed_at=now()
    item.status='reviewed' if data.decision=='approved' else 'changes_requested';item.updated_at=now()
    audit(db,user.id,item.id,'review_'+data.decision,{'note':data.note});db.commit()
    return {'status':item.status}

@app.get('/api/cases/{case_id}/report')
def report(case_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    item=get_case(case_id,db,user)
    result=case_view(db,item,user)
    result['disclaimer']='Document rédigé par un journaliste. Les indices C2PA et pHash ne déterminent pas la véracité des faits.'
    result['visibility']='private'
    return result

@app.get('/api/media/{media_id}/preview')
def preview(media_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    media=db.get(Media,media_id)
    if not media: raise HTTPException(404,'Média introuvable')
    if not media.is_archive and media.owner_id!=user.id:
        linked=db.query(Case).filter_by(asset_id=media.id).first()
        if not linked:
            for video in db.query(Video).all():
                if media.id in json.loads(video.frame_ids_json):
                    linked=db.get(Case,video.case_id)
                    break
        if not linked or user.role!='editor' or linked.status not in ('review_requested','reviewed','changes_requested'):
            raise HTTPException(403,'Accès refusé au média')
    with Image.open(media_path(media)) as im:
        im=ImageOps.exif_transpose(im)
        im.thumbnail((1200,800))
        if im.mode not in ('RGB','L'): im=im.convert('RGB')
        buf=BytesIO();im.save(buf,format='JPEG',quality=83)
        buf.seek(0)
    return StreamingResponse(buf,media_type='image/jpeg',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

def source_view(s):
    return {'id':s.id,'organization':s.organization,'acronym':s.acronym,'organization_type':s.organization_type,
        'sector':s.sector,'description':s.description,'website_url':s.website_url,
        'geographic_scope':s.geographic_scope,'region':s.region,'last_checked_at':s.last_checked_at,
        'reference_url':s.reference_url,'resources':json.loads(s.resources_json or '[]'),
        'contact_email':s.contact_email,'contact_phone':s.contact_phone,
        'verification_status':s.verification_status,'demo_only':s.demo_only,'archived':s.archived}

@app.get('/api/sources')
def sources(sector:str='',region:str='',organization_type:str='',q:str='',include_archived:bool=False,db:Session=Depends(db_session),user:User=Depends(current_user)):
    if include_archived and user.role!='editor':raise HTTPException(403,'Archives réservées à la rédaction')
    stmt=db.query(DirectorySource)
    if not include_archived:stmt=stmt.filter_by(archived=False,demo_only=False)
    if sector:stmt=stmt.filter_by(sector=sector)
    if region:stmt=stmt.filter_by(region=checked_region(region))
    if organization_type:stmt=stmt.filter_by(organization_type=organization_type[:80])
    if q:stmt=stmt.filter(DirectorySource.organization.ilike('%'+q[:100]+'%'))
    rows=stmt.order_by(DirectorySource.organization.asc()).limit(200).all()
    return {'items':[source_view(s) for s in rows]}

@app.get('/api/statistics')
def statistical_publications(sector:str='',q:str='',user:User=Depends(current_user)):
    """Publications documentées; les observations restent vides sans données vérifiées."""
    query=q.strip().casefold()[:100]
    items=[publication_view(item) for item in PUBLICATIONS
        if (not sector or item['sector']==sector)
        and (not query or query in ' '.join(str(item.get(k) or '') for k in ('title','producer','sector','description','reference_year')).casefold())]
    return {'items':items,'observation_count':0}

@app.get('/api/sources/{source_id}')
def source_details(source_id:int,db:Session=Depends(db_session),user:User=Depends(current_user)):
    source=db.get(DirectorySource,source_id)
    if not source or (source.archived and user.role!='editor'):raise HTTPException(404,'Source introuvable')
    return source_view(source)

@app.post('/api/sources',status_code=201)
def add_source(data:DirectoryIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    if user.role!='editor':raise HTTPException(403,'Réservé à la rédaction')
    s=DirectorySource(organization=data.organization,acronym=data.acronym,organization_type=data.organization_type,sector=data.sector,description=data.description,website_url=valid_url(data.website_url),geographic_scope=data.geographic_scope,region=checked_region(data.region),reference_url=valid_url(data.reference_url),contact_email=data.contact_email,contact_phone=data.contact_phone,last_checked_at=None,verification_status='a_actualiser',demo_only=False,archived=False)
    db.add(s);db.commit();return {'id':s.id}

@app.put('/api/sources/{source_id}')
def edit_source(source_id:int,data:DirectoryIn,db:Session=Depends(db_session),user:User=Depends(current_user)):
    if user.role!='editor': raise HTTPException(403,'Réservé à la rédaction')
    source=db.get(DirectorySource,source_id)
    if not source: raise HTTPException(404,'Source introuvable')
    source.organization=data.organization;source.sector=data.sector;source.description=data.description
    source.website_url=valid_url(data.website_url);source.geographic_scope=data.geographic_scope
    source.acronym=data.acronym;source.organization_type=data.organization_type;source.region=checked_region(data.region)
    source.reference_url=valid_url(data.reference_url);source.contact_email=data.contact_email;source.contact_phone=data.contact_phone
    source.last_checked_at=None;source.verification_status='a_actualiser';db.commit()
    return {'id':source.id}
