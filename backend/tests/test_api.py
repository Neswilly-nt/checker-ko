from pathlib import Path
from io import BytesIO
from uuid import uuid4
from PIL import Image
from app.core import c2pa_analyze, inspect_image, MAX_BYTES
from app.core import SessionLocal, Case
from app.core import NewsItem, NewsSource
from app.news import parse_feed, sync_source

ASSETS=Path(__file__).parents[1]/'demo_assets'

def test_health(client):
    response=client.get('/api/health')
    assert response.status_code==200
    assert response.json()['mode']=='development'
    assert isinstance(response.json()['c2patool_installed'],bool)

def test_auth(client,journalist):
    assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',headers={'X-Checker-CSRF':'1'},json={'email':'journaliste@checker.local','password':'wrong'}).status_code==401
    assert client.get('/api/auth/me',headers=journalist).json()['role']=='journalist'

def test_demo_account_cannot_login_in_production(client,monkeypatch):
    monkeypatch.setattr('app.main.APP_ENV','production')
    response=client.post('/api/auth/login',headers={'X-Checker-CSRF':'1','Origin':'http://localhost:5173'},json={'email':'journaliste@checker.local','password':'Journaliste2026!'})
    assert response.status_code==401

def test_demo_seed_requires_explicit_guard(monkeypatch):
    from app.cli import seed_demo
    monkeypatch.setenv('APP_ENV','development')
    monkeypatch.delenv('CHECKER_DEMO_SEED',raising=False)
    assert seed_demo()==2

def test_import_valid(client,journalist,upload_case):
    data=client.get('/api/cases/'+str(upload_case),headers=journalist).json()
    listed=client.get('/api/cases',headers=journalist).json()
    assert next(item for item in listed['items'] if item['id']==upload_case)['content_type']=='photo'
    assert listed['total']>=listed['concluded']
    assert data['media']['sha256'] and len(data['media']['sha256'])==64
    assert data['media']['mime_type']=='image/jpeg'
    assert data['media']['width']==750
    assert data['claim_text']=='Légende non vérifiée'
    preview=client.get('/api/media/'+str(data['media']['id'])+'/preview',headers=journalist)
    assert preview.status_code==200 and preview.headers['content-type']=='image/jpeg'

def test_import_fake_and_oversized(client,journalist):
    fake=client.post('/api/media/upload',headers=journalist,files={'file':('malware.jpg',b'not a picture','image/jpeg')})
    assert fake.status_code==415
    large=client.post('/api/media/upload',headers=journalist,files={'file':('large.jpg',b'B'*(MAX_BYTES+1),'image/jpeg')})
    assert large.status_code==413

def test_import_actual_format_not_extension(client,journalist):
    b=BytesIO();Image.new('RGB',(12,12),'white').save(b,format='PNG')
    r=client.post('/api/media/upload',headers=journalist,files={'file':('claimed.jpg',b.getvalue(),'image/jpeg')})
    assert r.status_code==201
    media=client.get('/api/cases/'+str(r.json()['id']),headers=journalist).json()['media']
    assert media['mime_type']=='image/png'

def test_phash_matches_and_different_image(client,journalist,upload_case):
    results=client.get(f'/api/cases/{upload_case}/matches',headers=journalist).json()['items']
    assert any('passerelle' in v['title'] and v['distance']<=5 for v in results)
    another=client.post('/api/media/upload',headers=journalist,files={'file':('difference.png',(ASSETS/'image_sans_correspondance.png').read_bytes(),'image/png')})
    assert another.status_code==201
    different=client.get('/api/cases/'+str(another.json()['id'])+'/matches',headers=journalist).json()['items']
    assert not any('passerelle' in v['title'] for v in different)

def test_c2pa_unavailable_never_means_absent(monkeypatch):
    monkeypatch.setenv('C2PATOOL_PATH','C:/missing/c2patool.exe')
    monkeypatch.setattr('app.core.shutil.which', lambda _:None)
    monkeypatch.setattr('app.core.tool_path',lambda *_:None)
    tool,status,claim,warnings=c2pa_analyze('/unused/path.jpg')
    assert (tool,status)==('outil_non_installe','indisponible')
    assert claim['signature']=='non_evaluee'
    assert warnings

def test_c2pa_no_manifest_when_tool_replies(monkeypatch):
    monkeypatch.setenv('C2PATOOL_PATH',str(Path(__file__).parents[2]/'tools/media/c2patool/c2patool/c2patool.exe'))
    class Result:
        returncode=0
        stdout='{"manifests":{},"active_manifest":null}'
        stderr=''
    monkeypatch.setattr('app.core.shutil.which', lambda _:'/local/c2patool')
    monkeypatch.setattr('app.core.subprocess.run', lambda *a,**k:Result())
    tool,status,claim,warnings=c2pa_analyze('/unused/path.jpg')
    assert (tool,status)==('disponible','absent')

def test_evidence_verdict_report(client,journalist,upload_case):
    matches=client.get(f'/api/cases/{upload_case}/matches',headers=journalist).json()['items']
    match=next(item for item in matches if item['is_demo'])
    evidence=client.post(f'/api/cases/{upload_case}/evidence',headers=journalist,json={'title':'Archive fictive','relation_type':'contexte','note':'Image ressemblante, à confirmer','archived_media_id':match['media_id']})
    assert evidence.status_code==201
    edit=client.put(f'/api/cases/{upload_case}/evidence/{evidence.json()["id"]}',headers=journalist,json={'title':'Archive illustrée','relation_type':'contexte','note':'Réemploi possible, examen humain requis','archived_media_id':match['media_id']})
    assert edit.status_code==200
    bad=client.post(f'/api/cases/{upload_case}/verdict',headers=journalist,json={'verdict':'Trompeur','reasoning':'trop court'})
    assert bad.status_code==422
    good=client.post(f'/api/cases/{upload_case}/verdict',headers=journalist,json={'verdict':'Trompeur','reasoning':'Une archive visuellement similaire a été retrouvée ; il faut confirmer le contexte.'})
    assert good.status_code==201
    report=client.get(f'/api/cases/{upload_case}/report',headers=journalist)
    assert report.status_code==200
    assert report.json()['verdicts'][0]['author_name']=='Journaliste Démo'
    assert report.json()['evidence'][0]['title']=='Archive illustrée'
    assert report.json()['visibility']=='private'

def test_source_assessment_history_summary_and_permissions(client,journalist,editor,upload_case):
    evidence=client.post(f'/api/cases/{upload_case}/evidence',headers=journalist,json={'title':'Document primaire','relation_type':'appuie','note':'Statistique à recouper'}).json()
    payload={'source_identity_status':'oui','subject_expertise_status':'oui','verifiable_evidence_status':'oui','primary_source_status':'oui','evidence_relevance':'directe','assessment_note':'Document accessible, périmètre à vérifier.'}
    created=client.post(f'/api/cases/{upload_case}/evidence/{evidence["id"]}/assessment',headers=journalist,json=payload)
    assert created.status_code==201 and created.json()['assessment_summary']=='elements_solides'
    payload['contradictions_status']='oui';payload['justification']='Une contradiction a été documentée.'
    updated=client.patch(f'/api/cases/{upload_case}/evidence/{evidence["id"]}/assessment',headers=journalist,json=payload)
    assert updated.status_code==200 and updated.json()['assessment_summary']=='points_de_vigilance'
    history=client.get(f'/api/cases/{upload_case}/evidence/{evidence["id"]}/assessment/history',headers=journalist).json()['items']
    assert len(history)==2 and history[0]['justification']
    summary=client.get(f'/api/cases/{upload_case}/assessments/summary',headers=journalist).json()
    assert summary['favorable'][0]['assessment']['assessment_summary']=='points_de_vigilance'
    assert client.post(f'/api/cases/{upload_case}/evidence/{evidence["id"]}/assessment',headers=editor,json=payload).status_code==403

def test_access_control(client,journalist,editor,upload_case):
    item=client.get(f'/api/cases/{upload_case}',headers=journalist).json()
    assert client.get(f'/api/cases/{upload_case}',headers=editor).status_code==403
    assert client.get(f'/api/media/{item["media"]["id"]}/preview',headers=editor).status_code==403
    assert client.get(f'/api/cases/{upload_case}/report',headers=editor).status_code==403
    assert client.post(f'/api/cases/{upload_case}/verdict',headers=editor,json={'verdict':'Faux','reasoning':'Cette justification n’est pas autorisée'}).status_code==403

def test_private_case_media_and_report_are_isolated_between_journalists(client,journalist,upload_case):
    from app.core import SessionLocal,User,hash_password
    with SessionLocal() as db:
        db.add(User(name='Autre journaliste',email='other-journalist@example.test',role='journalist',password_hash=hash_password('Autre mot de passe fort 2026!')))
        db.commit()
    login=client.post('/api/auth/login',headers={'X-Checker-CSRF':'1'},json={'email':'other-journalist@example.test','password':'Autre mot de passe fort 2026!'})
    assert login.status_code==200
    client.cookies.clear()
    other={'Authorization':'Bearer '+login.json()['access_token']}
    item=client.get(f'/api/cases/{upload_case}',headers=journalist).json()
    assert client.get(f'/api/cases/{upload_case}',headers=other).status_code==403
    assert client.get(f'/api/media/{item["media"]["id"]}/preview',headers=other).status_code==403
    assert client.get(f'/api/cases/{upload_case}/report',headers=other).status_code==403

def test_cookie_session_is_http_only_and_csrf_protected(client,monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    from app.core import SessionLocal,User,UserSession,Audit,hash_password
    email=f'private-session-{uuid4().hex}@example.test'
    with SessionLocal() as db:
        db.add(User(name='Journaliste privé',email=email,role='journalist',password_hash=hash_password('Secret de test 2026!')))
        db.commit()
    monkeypatch.setattr(main,'APP_ENV','production')
    monkeypatch.setattr(main,'CORS_ORIGINS',['https://testserver'])
    browser=TestClient(main.app,base_url='https://testserver')
    login=browser.post('/api/auth/login',headers={'X-Checker-CSRF':'1','Origin':'https://testserver'},json={'email':email,'password':'Secret de test 2026!'})
    assert login.status_code==200 and 'access_token' not in login.json()
    cookie=login.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'secure' in cookie and 'samesite=lax' in cookie
    assert browser.get('/api/auth/me').status_code==200
    assert browser.post('/api/cases',json={'claim_text':'Une affirmation privée','sector':'autre'}).status_code==403
    assert browser.post('/api/cases',headers={'X-Checker-CSRF':'1','Origin':'https://attacker.example'},json={'claim_text':'Une affirmation privée','sector':'autre'}).status_code==403
    assert browser.post('/api/cases',headers={'X-Checker-CSRF':'1'},json={'claim_text':'Une affirmation privée','sector':'autre'}).status_code==403
    assert browser.post('/api/cases',headers={'X-Checker-CSRF':'1','Origin':'https://testserver'},json={'claim_text':'Une affirmation privée','sector':'autre'}).status_code==201
    assert browser.post('/api/auth/logout',headers={'X-Checker-CSRF':'1','Origin':'https://testserver'}).status_code==200
    assert browser.get('/api/auth/me').status_code==401
    with SessionLocal() as db:
        test_user=db.query(User).filter_by(email=email).first()
        if test_user:
            db.query(UserSession).filter_by(user_id=test_user.id).delete()
            db.query(Audit).filter_by(actor_id=test_user.id).delete()
            db.query(Case).filter_by(owner_id=test_user.id).delete()
            db.delete(test_user)
            db.commit()

def test_review_optional_and_by_other_user(client,journalist,editor,upload_case):
    pre=client.post(f'/api/cases/{upload_case}/request-review',headers=journalist)
    assert pre.status_code==422
    verdict=client.post(f'/api/cases/{upload_case}/verdict',headers=journalist,json={'verdict':'Non déterminé','reasoning':'Les documents disponibles ne suffisent pas à conclure.'})
    assert verdict.status_code==201
    assert client.post(f'/api/cases/{upload_case}/request-review',headers=journalist).status_code==200
    listed=client.get('/api/cases',headers=journalist).json()
    assert listed['concluded']>=1
    assert client.post(f'/api/cases/{upload_case}/review',headers=journalist,json={'decision':'approved'}).status_code==403
    assert client.get(f'/api/cases/{upload_case}',headers=editor).status_code==200
    assert client.post(f'/api/cases/{upload_case}/review',headers=editor,json={'decision':'approved'}).status_code==200
    report=client.get(f'/api/cases/{upload_case}/report',headers=journalist).json()
    assert report['verdicts'][0]['reviewer_name']=='Responsable Rédaction'

def test_directory_and_unverified_demo_labels(client,journalist,editor):
    values=client.get('/api/sources',headers=journalist).json()['items']
    assert len(values)==5
    assert all(not x['demo_only'] and not x['archived'] for x in values)
    assert {x['acronym'] for x in values}=={'BNGRC','MEN','INSTAT','METFP','DGM'}
    assert all(x['website_url'] and x['reference_url'] for x in values)
    assert client.get('/api/sources?include_archived=true',headers=journalist).status_code==403
    assert len(client.get('/api/sources?sector=éducation',headers=journalist).json()['items'])==2
    assert len(client.get('/api/sources?region=National%20%2F%20Tout%20Madagascar',headers=journalist).json()['items'])==5
    assert len(client.get('/api/sources?organization_type=ministère',headers=journalist).json()['items'])==2
    assert client.get('/api/sources/1',headers=journalist).status_code==200
    assert client.post('/api/sources',headers=journalist,json={'organization':'Organisme local','sector':'santé','description':'Un service public à examiner'}).status_code==403
    created=client.post('/api/sources',headers=editor,json={'organization':'Organisme local','sector':'santé','description':'Un service public à examiner'})
    assert created.status_code==201
    assert client.get(f"/api/sources/{created.json()['id']}",headers=editor).json()['verification_status']=='a_actualiser'

def test_statistical_catalog_has_documented_publications_without_fabricated_observations(client,journalist):
    response=client.get('/api/statistics',headers=journalist)
    assert response.status_code==200
    items=response.json()['items']
    assert {item['key'] for item in items}=={'health-yearbook-2024','education-yearbook-2023-2024','rgph3-tome1'}
    assert all(item['url'].startswith('https://') and item['observations']==[] for item in items)
    assert response.json()['observation_count']==0
    assert len(client.get('/api/statistics?sector=sant%C3%A9',headers=journalist).json()['items'])==1
    assert len(client.get('/api/statistics?q=RGPH',headers=journalist).json()['items'])==1

def test_public_contacts_are_traceable_and_directory_archiving_preserves_case_evidence(client,journalist,editor):
    payload={'organization':'Organisme de test','sector':'santé','description':'Fiche synthétique de test',
        'reference_url':'https://example.org/contact-directory','verification_status':'partiellement_verifiees','last_checked_at':'2026-11-03'}
    assert client.post('/api/sources',headers=journalist,json=payload).status_code==403
    assert client.post('/api/sources',headers=editor,json={**payload,'reference_url':None,'last_checked_at':None}).status_code==422
    source=client.post('/api/sources',headers=editor,json=payload)
    assert source.status_code==201,source.text
    source_id=source.json()['id']
    contact={'name':'Contact de test','role':'Accueil','email':'contact@example.test','phone':None,
        'reference_url':'https://example.org/contact-directory','verified_at':'2026-11-03'}
    assert client.post(f'/api/sources/{source_id}/contacts',headers=journalist,json=contact).status_code==403
    assert client.post(f'/api/sources/{source_id}/contacts',headers=editor,json={**contact,'reference_url':None}).status_code==422
    assert client.post(f'/api/sources/{source_id}/contacts',headers=editor,json={**contact,'email':None,'phone':None}).status_code==422
    created=client.post(f'/api/sources/{source_id}/contacts',headers=editor,json=contact)
    assert created.status_code==201,created.text
    assert created.json()['reference_url']==contact['reference_url'] and created.json()['verified_at']==contact['verified_at']
    edited=client.put(f"/api/sources/{source_id}/contacts/{created.json()['id']}",headers=editor,json={**contact,'role':'Standard téléphonique'})
    assert edited.status_code==200 and edited.json()['role']=='Standard téléphonique'
    case=client.post('/api/cases',headers=journalist,json={'claim_text':'Source de test à conserver','sector':'santé'}).json()
    evidence=client.post(f"/api/cases/{case['id']}/evidence",headers=journalist,json={'title':'Fiche organisme','url':payload['reference_url'],'note':'Référence conservée dans le dossier.','relation_type':'contexte'})
    assert evidence.status_code==201
    assert client.patch(f'/api/sources/{source_id}/archive',headers=journalist,json={'archived':True}).status_code==403
    archived=client.patch(f'/api/sources/{source_id}/archive',headers=editor,json={'archived':True})
    assert archived.status_code==200 and archived.json()['archived'] is True
    assert client.get(f'/api/sources/{source_id}',headers=journalist).status_code==404
    assert source_id in {item['id'] for item in client.get('/api/sources?include_archived=true',headers=editor).json()['items']}
    assert client.get(f"/api/cases/{case['id']}",headers=journalist).json()['evidence'][0]['url']==payload['reference_url']
    restored=client.patch(f'/api/sources/{source_id}/archive',headers=editor,json={'archived':False})
    assert restored.status_code==200 and client.get(f'/api/sources/{source_id}',headers=journalist).status_code==200

def test_statistical_observations_require_editor_and_keep_document_provenance(client,journalist,editor):
    payload={'publication_key':'health-yearbook-2024','indicator':'Indicateur de test','value':'12.5','unit':'pour 100 000',
        'year':2023,'region':'Analamanga','source_locator':'p. 12, tableau 2'}
    assert client.post('/api/statistics/observations',headers=journalist,json=payload).status_code==403
    assert client.post('/api/statistics/observations',headers=editor,json={**payload,'publication_key':'invented'}).status_code==422
    assert client.post('/api/statistics/observations',headers=editor,json={**payload,'value':'NaN'}).status_code==422
    created=client.post('/api/statistics/observations',headers=editor,json=payload)
    assert created.status_code==201,created.text
    response=client.get('/api/statistics?q=Indicateur%20de%20test',headers=journalist)
    assert response.status_code==200 and response.json()['observation_count']==1
    observation=response.json()['items'][0]['observations'][0]
    assert observation['value']=='12.5' and observation['year']==2023 and observation['region']=='Analamanga'
    assert observation['source_locator']==payload['source_locator']
    assert observation['source_url'].startswith('https://www.instat.mg/')
    assert client.post('/api/statistics/observations',headers=editor,json={**payload,'region':'Région inventée'}).status_code==422

def test_regions_and_case_validation(client,journalist):
    regions=client.get('/api/regions',headers=journalist)
    assert regions.status_code==200 and len(regions.json()['items'])==24
    assert 'Ambatosoa' in regions.json()['items']
    good=client.post('/api/cases',headers=journalist,json={'claim_text':'Observation à examiner','sector':'autre','region':'Ambatosoa'})
    assert good.status_code==201,good.text
    assert client.get(f"/api/cases/{good.json()['id']}",headers=journalist).json()['region']=='Ambatosoa'
    bad=client.post('/api/cases',headers=journalist,json={'claim_text':'Observation à examiner','sector':'autre','region':'Région inventée'})
    assert bad.status_code==422

def test_text_case_without_image_and_existing_case_preserved(client,journalist,upload_case):
    before=client.get(f'/api/cases/{upload_case}',headers=journalist).json()
    response=client.post('/api/cases',headers=journalist,json={'claim_text':'Une affirmation à examiner','original_source_url':'https://example.org/article','sector':'santé'})
    assert response.status_code==201,response.text
    item=client.get(f'/api/cases/{response.json()["id"]}',headers=journalist).json()
    listed=client.get('/api/cases',headers=journalist).json()['items']
    assert next(row for row in listed if row['id']==item['id'])['content_type']=='texte'
    assert item['media'] is None and item['claim_text']=='Une affirmation à examiner'
    assert item['original_source_url']=='https://example.org/article'
    assert client.get(f'/api/cases/{upload_case}',headers=journalist).json()['media']['sha256']==before['media']['sha256']
    evidence=client.post(f'/api/cases/{item["id"]}/evidence',headers=journalist,json={'title':'Document','relation_type':'contexte','note':'À vérifier'})
    assert evidence.status_code==201
    verdict=client.post(f'/api/cases/{item["id"]}/verdict',headers=journalist,json={'verdict':'Non déterminé','reasoning':'Les sources restent insuffisantes.'})
    assert verdict.status_code==201

def test_news_feed_parse_deduplication_and_case_creation(client,journalist,editor,monkeypatch):
    feed=b'''<?xml version="1.0"?><rss><channel><item><guid>news-unique</guid><title>Publication a examiner</title><link>https://example.org/article</link><pubDate>Mon, 03 Nov 2026 10:00:00 GMT</pubDate><category>Sante</category></item></channel></rss>'''
    class Response:
        status_code=200
        def __enter__(self): return self
        def __exit__(self,*_): return False
        def iter_bytes(self): yield feed
    class Client:
        def __init__(self,**_): pass
        def __enter__(self): return self
        def __exit__(self,*_): return False
        def stream(self,*_): return Response()
    monkeypatch.setattr('app.news.socket.getaddrinfo',lambda *_args,**_kwargs:[(None,None,None,None,('8.8.8.8',443))])
    monkeypatch.setattr('app.news.httpx.Client',Client)
    with SessionLocal() as db:
        source=db.query(NewsSource).filter_by(key='madagascar-tribune').first()
        first=sync_source(db,source); second=sync_source(db,source)
        assert first.status=='success' and first.inserted_count==1
        assert second.inserted_count==0
    listed=client.get('/api/news?sector=autre',headers=journalist)
    assert listed.status_code==200 and any(x['title']=='Publication a examiner' for x in listed.json()['items'])
    assert client.get('/api/news?source_id=',headers=journalist).status_code==200
    assert client.get('/api/news?source_id=pas-un-id',headers=journalist).status_code==422
    article=next(x for x in listed.json()['items'] if x['title']=='Publication a examiner')
    assert client.post('/api/news/sync',headers=journalist).status_code==403
    created=client.post(f"/api/news/{article['id']}/verify",headers=journalist)
    assert created.status_code==201
    duplicate=client.post(f"/api/news/{article['id']}/verify",headers=journalist)
    assert duplicate.json()['id']==created.json()['id']
    item=client.get(f"/api/cases/{created.json()['id']}",headers=journalist).json()
    assert item['claim_text']=='Publication a examiner' and item['original_source_url']=='https://example.org/article'

def test_news_invalid_feed_and_unknown_dates():
    assert parse_feed(b'<rss><channel><item><title>Sans lien</title></item></channel></rss>')==[]
    parsed=parse_feed(b'<rss><channel><item><guid>x</guid><title>Sans date</title><link>https://example.org/x</link></item></channel></rss>')
    assert parsed[0]['published_at'] is None

def test_news_rejects_script_links_and_xml_entities():
    import pytest
    from defusedxml.common import DefusedXmlException
    from app.news import _safe_feed_url
    assert parse_feed(b'<rss><channel><item><guid>x</guid><title>Unsafe</title><link>javascript:alert(1)</link></item></channel></rss>')==[]
    with pytest.raises(ValueError): _safe_feed_url('https://127.0.0.1/feed.xml')
    with pytest.raises(ValueError): _safe_feed_url('https://attacker.example/feed.xml')
    with pytest.raises(ValueError): _safe_feed_url('https://www.madagascar-tribune.com:8443/feed.xml')
    with pytest.raises(DefusedXmlException):
        parse_feed(b'<!DOCTYPE x [<!ENTITY boom "expanded">]><rss><channel><item><title>&boom;</title></item></channel></rss>')

def test_video_missing_ffmpeg(client,journalist,monkeypatch):
    monkeypatch.setenv('FFMPEG_PATH','C:/missing/ffmpeg.exe')
    monkeypatch.setenv('FFPROBE_PATH','C:/missing/ffprobe.exe')
    monkeypatch.setattr('app.main.shutil.which',lambda name:None if name in ('ffmpeg','ffprobe') else None)
    monkeypatch.setattr('app.main.tool_path',lambda *_:None)
    response=client.post('/api/video/upload',headers=journalist,files={'file':('clip.mp4',b'\0\0\0\x18ftypisom','video/mp4')})
    assert response.status_code==503
    assert 'FFmpeg' in response.json()['detail']

def test_video_invalid_container(client,journalist,monkeypatch):
    monkeypatch.setattr('app.main.shutil.which',lambda name:'C:/fake/'+name)
    response=client.post('/api/video/upload',headers=journalist,files={'file':('clip.mp4',b'not a real mp4','video/mp4')})
    assert response.status_code==415

def test_video_extracts_three_frames_and_matches(client,journalist,upload_case,monkeypatch):
    import json
    from app import main
    jpeg=(ASSETS/'variante_pont.jpg').read_bytes()
    class Result:
        returncode=0
        def __init__(self,stdout): self.stdout=stdout
    def run(args,**_kwargs):
        if 'ffprobe' in args[0]: return Result(json.dumps({'format':{'duration':'12.0'},'streams':[{'codec_type':'video','width':640,'height':360}]}))
        return Result(jpeg)
    monkeypatch.setattr(main.shutil,'which',lambda name:'ffprobe' if name=='ffprobe' else 'ffmpeg' if name=='ffmpeg' else None)
    monkeypatch.setattr(main.subprocess,'run',run)
    response=client.post('/api/video/upload',headers=journalist,files={'file':('clip.mp4',b'\0\0\0\x18ftypisom'+b'0'*100,'video/mp4')},data={'caption':'Vidéo à examiner'})
    assert response.status_code==201,response.text
    item=client.get(f'/api/cases/{response.json()["id"]}',headers=journalist).json()
    assert item['video']['duration_seconds']==12
    assert len(item['video']['frames'])==3
    assert [frame['video_timestamp_seconds'] for frame in item['video']['frames']]==[3.0,6.0,9.0]
    assert item['video']['sha256']
    first,second=item['video']['frames'][:2]
    comparison=client.get(f"/api/cases/{item['id']}/compare?left_media_id={first['id']}&right_media_id={second['id']}",headers=journalist)
    assert comparison.status_code==200 and comparison.json()['phash_hamming_distance']==0
    assert 'ne démontre' in comparison.json()['interpretation']
    saved=client.post(f"/api/cases/{item['id']}/evidence",headers=journalist,json={'title':'Image-clé à 3 s','note':'Image extraite de la vidéo, contexte à examiner.','relation_type':'contexte','media_id':first['id']})
    assert saved.status_code==201 and saved.json()['media_id']==first['id']
    cross_case=client.post(f"/api/cases/{item['id']}/evidence",headers=journalist,json={'title':'Autre image','note':'Cette image appartient à un autre dossier.', 'relation_type':'contexte','media_id':client.get(f"/api/cases/{upload_case}",headers=journalist).json()['media']['id']})
    assert cross_case.status_code==403
    assert client.get(f"/api/cases/{item['id']}",headers=journalist).json()['evidence'][0]['media_id']==first['id']
    for frame in item['video']['frames']:
        matches=client.get(f'/api/cases/{item["id"]}/frames/{frame["id"]}/matches',headers=journalist)
        assert matches.status_code==200
        assert any('passerelle' in match['title'] for match in matches.json()['items'])

def test_social_publication_provenance_is_optional_and_owner_only(client,journalist,editor,upload_case):
    case_id=upload_case
    created=client.post(f'/api/cases/{case_id}/social-posts',headers=journalist,json={
        'platform':'TikTok','original_url':'https://www.tiktok.com/@example/video/123',
        'declared_account':'@example','published_at':'2026-01-12T10:30','capture_date':'2026-01-10',
        'observation':'La date affichée ne confirme pas la date de captation.'})
    assert created.status_code==201
    post=client.get(f'/api/cases/{case_id}',headers=journalist).json()['social_posts'][0]
    assert post['published_at']=='2026-01-12T10:30' and post['capture_date']=='2026-01-10'
    forbidden=client.post(f'/api/cases/{case_id}/social-posts',headers=editor,json={
        'platform':'Facebook','original_url':'https://facebook.com/example'})
    assert forbidden.status_code==403

def test_real_mp4_and_c2pa_tools(client,journalist,monkeypatch,tmp_path):
    from pathlib import Path
    from app.core import c2pa_analyze
    root=Path(__file__).resolve().parents[2]
    media=root/'tools'/'media'
    ffmpeg=media/'ffmpeg'/'ffmpeg-9.0.2-essentials_build'/'bin'
    c2pa=media/'c2patool'/'c2patool'/'c2patool.exe'
    sample=media/'test-v043.mp4'
    if not all(p.is_file() for p in (ffmpeg/'ffmpeg.exe',ffmpeg/'ffprobe.exe',c2pa,sample)):
        import pytest
        pytest.skip('Outils médias portables absents')
    monkeypatch.setenv('FFMPEG_PATH',str(ffmpeg/'ffmpeg.exe'))
    monkeypatch.setenv('FFPROBE_PATH',str(ffmpeg/'ffprobe.exe'))
    monkeypatch.setenv('C2PATOOL_PATH',str(c2pa))
    result=client.post('/api/video/upload',headers=journalist,
        files={'file':('test-v043.mp4',sample.read_bytes(),'video/mp4')},
        data={'caption':'Vidéo synthétique de contrôle','region':'Ambatosoa'})
    assert result.status_code==201,result.text
    item=client.get(f"/api/cases/{result.json()['id']}",headers=journalist).json()
    listed=client.get('/api/cases',headers=journalist).json()['items']
    assert next(row for row in listed if row['id']==item['id'])['content_type']=='video'
    assert item['region']=='Ambatosoa' and item['video']['width']==320 and item['video']['height']==180
    assert 3.9<=item['video']['duration_seconds']<=4.1
    assert len(item['video']['frames'])==3
    assert all(frame['preview_url'] and frame['sha256'] for frame in item['video']['frames'])
    for frame in item['video']['frames']:
        preview=client.get(frame['preview_url'],headers=journalist)
        assert preview.status_code==200 and preview.headers['content-type']=='image/jpeg'
        matches=client.get(f"/api/cases/{item['id']}/frames/{frame['id']}/matches",headers=journalist)
        assert matches.status_code==200
    invalid=client.post('/api/video/upload',headers=journalist,files={'file':('broken.mp4',b'not mp4','video/mp4')})
    assert invalid.status_code==415
    assert c2pa_analyze(ASSETS/'variante_pont.jpg')[1]=='absent'
    assert c2pa_analyze(media/'c2patool'/'c2patool'/'sample'/'C.jpg')[1]=='present'
    assert c2pa_analyze(media/'c2patool-invalid-test.jpg')[1]=='non_fiable'
    unsupported=tmp_path/'unsupported-v043.txt'
    unsupported.write_text('not an image',encoding='utf-8')
    assert c2pa_analyze(unsupported)[1]=='erreur'
