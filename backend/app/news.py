"""Controlled RSS collection. Feed targets are seeded by the application, never supplied by clients."""
from __future__ import annotations
import ipaddress
import socket
from defusedxml import ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
import httpx
from threading import Lock
from sqlalchemy.orm import Session
from .core import NewsItem, NewsSource, NewsSync, now

MAX_FEED_BYTES=1_500_000
TIMEOUT=10.0
SYNC_LOCK=Lock()
ALLOWED_FEED_HOSTS={'www.madagascar-tribune.com','midi-madagasikara.mg'}

def _safe_feed_url(url:str)->str:
    parsed=urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.hostname.lower() not in ALLOWED_FEED_HOSTS or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError('URL de flux non autorisée')
    for result in socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(result[4][0]).is_global:
            raise ValueError('Hôte de flux non public')
    return url

def _safe_article_url(url:str)->str|None:
    try:
        parsed=urlsplit(url)
        if parsed.scheme in ('http','https') and parsed.hostname and parsed.netloc and not parsed.username and not parsed.password and len(url)<=500:
            return url
    except ValueError:
        pass
    return None

def _text(node, names):
    for name in names:
        found=node.find(name)
        if found is not None and found.text: return found.text.strip()
    return ''

def _date(value:str):
    if not value: return None
    try:
        dt=parsedate_to_datetime(value)
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        try: return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(timezone.utc)
        except ValueError: return None

def _sector(category:str)->str:
    value=category.lower()
    for key, sector in [('santé','santé'),('education','éducation'),('éducation','éducation'),('environnement','environnement'),('économie','économie'),('météo','météo/catastrophes'),('catastrophe','météo/catastrophes'),('gouvernement','administration')]:
        if key in value:return sector
    return 'autre'

def parse_feed(content:bytes):
    root=ET.fromstring(content)
    entries=root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
    result=[]
    for entry in entries[:100]:
        title=_text(entry,['title','{http://www.w3.org/2005/Atom}title'])[:500]
        link=_text(entry,['link','{http://www.w3.org/2005/Atom}link'])
        if not link:
            atom_link=entry.find('{http://www.w3.org/2005/Atom}link'); link=(atom_link.get('href','') if atom_link is not None else '')
        guid=_text(entry,['guid','id','{http://www.w3.org/2005/Atom}id']) or link
        safe_link=_safe_article_url(link)
        if title and safe_link and guid:
            category=_text(entry,['category','{http://www.w3.org/2005/Atom}category'])
            result.append({'id':guid[:500],'title':title,'url':safe_link,'published_at':_date(_text(entry,['pubDate','published','updated','{http://www.w3.org/2005/Atom}published'])),'sector':_sector(category)})
    return result

def sync_source(db:Session, source:NewsSource):
    if not SYNC_LOCK.acquire(blocking=False):
        raise RuntimeError('Une collecte est déjà en cours')
    sync=NewsSync(source_id=source.id); db.add(sync); db.commit()
    try:
        url=_safe_feed_url(source.feed_url)
        content=bytearray()
        with httpx.Client(timeout=TIMEOUT,follow_redirects=False,trust_env=False,headers={'User-Agent':'Checker-ko-news-monitoring/0.5'}) as client:
            with client.stream('GET',url) as response:
                if response.status_code != 200: raise ValueError(f'HTTP {response.status_code}')
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content)>MAX_FEED_BYTES: raise ValueError('Flux trop volumineux')
        entries=parse_feed(bytes(content)); sync.fetched_count=len(entries)
        inserted=0
        for entry in entries:
            if db.query(NewsItem).filter_by(canonical_id=entry['id']).first(): continue
            db.add(NewsItem(source_id=source.id,canonical_id=entry['id'],title=entry['title'],original_url=entry['url'],published_at=entry['published_at'],sector=entry['sector'],region=None)); inserted+=1
        sync.inserted_count=inserted; sync.status='success'; sync.completed_at=now(); db.commit()
    except Exception as exc:
        sync.status='error'; sync.error_message=str(exc)[:500]; sync.completed_at=now(); db.commit()
    finally:
        SYNC_LOCK.release()
    return sync
