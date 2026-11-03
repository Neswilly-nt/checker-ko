"""Administrative commands; user provisioning is intentionally off the HTTP API."""
from __future__ import annotations
import argparse
from getpass import getpass
import re
import sys
import io
import os
from .core import SessionLocal, User, hash_password

def create_user(email:str,name:str,role:str)->int:
    email=email.strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
        print('Adresse e-mail invalide.',file=sys.stderr)
        return 2
    if role not in ('journalist','editor'):
        print('Rôle invalide.',file=sys.stderr)
        return 2
    if not name.strip():
        print('Nom obligatoire.',file=sys.stderr)
        return 2
    password=getpass('Mot de passe (12 caractères minimum) : ')
    confirmation=getpass('Confirmer le mot de passe : ')
    if len(password)<12 or password!=confirmation:
        print('Mot de passe trop court ou confirmation différente.',file=sys.stderr)
        return 2
    with SessionLocal() as db:
        if db.query(User).filter_by(email=email).first():
            print('Cet utilisateur existe déjà.',file=sys.stderr)
            return 2
        db.add(User(name=name.strip()[:150],email=email,role=role,password_hash=hash_password(password)))
        db.commit()
    print(f'Utilisateur créé : {email} ({role}).')
    return 0

def seed_demo()->int:
    """Seed one fictional, isolated demonstration account and case on an empty DB."""
    if os.environ.get('APP_ENV')!='production' or os.environ.get('CHECKER_DEMO_MODE','').lower()!='true' or os.environ.get('CHECKER_DEMO_SEED')!='enabled':
        print('Seed refused: set APP_ENV=production, CHECKER_DEMO_MODE=true, and CHECKER_DEMO_SEED=enabled explicitly.',file=sys.stderr)
        return 2
    from PIL import Image, ImageDraw
    from .core import Case, Evidence, Verdict, store_media
    from . import storage
    if storage.BACKEND!='supabase':
        print('Seed refused: demonstration data must use private Supabase Storage.',file=sys.stderr)
        return 2
    try:
        storage.ensure_configured()
    except RuntimeError as exc:
        print(str(exc),file=sys.stderr)
        return 2
    email='demo.journaliste@example.test'
    password=getpass('Mot de passe de démonstration (12 caractères minimum) : ')
    confirmation=getpass('Confirmer le mot de passe : ')
    if len(password)<12 or password!=confirmation:
        print('Mot de passe trop court ou confirmation différente.',file=sys.stderr)
        return 2
    canvas=Image.new('RGB',(900,560),'#e8f2ef')
    draw=ImageDraw.Draw(canvas)
    draw.rectangle((0,390,900,560),fill='#b9dce0')
    draw.polygon([(0,380),(180,210),(330,380)],fill='#829c78')
    draw.polygon([(430,390),(650,150),(900,390)],fill='#91aa82')
    draw.rectangle((90,300,810,340),fill='#675e52')
    draw.rectangle((90,292,810,301),fill='#d6c9a7')
    for x in (140,280,420,560,700):
        draw.line((x,301,x,390),fill='#544f4a',width=8)
    draw.text((24,22),'ILLUSTRATION FICTIVE - DONNEES DE DEMONSTRATION',fill='#17324d')
    image=io.BytesIO();canvas.save(image,format='PNG')
    with SessionLocal() as db:
        if db.query(User).first() or db.query(Case).first():
            print('Seed refusé : la base doit être vide de comptes et de dossiers.',file=sys.stderr)
            return 2
        user=User(name='Journaliste Démo',email=email,role='journalist',password_hash=hash_password(password))
        db.add(user);db.flush()
        try:
            media=store_media(db,user.id,image.getvalue(),'illustration-fictive.png')
            case=Case(asset_id=media.id,owner_id=user.id,claim_text='Exemple fictif : une passerelle aurait été fermée après une forte pluie.',sector='météo/catastrophes',region='Localité fictive',status='en_cours')
            db.add(case);db.flush()
            db.add(Evidence(case_id=case.id,title='Note de démonstration fictive',note='Document inventé pour montrer la saisie de preuves. Aucune source ni personne réelle.',relation_type='contexte'))
            db.add(Verdict(case_id=case.id,author_id=user.id,verdict='Non déterminé',reasoning='Les éléments de cet exemple sont entièrement fictifs et ne permettent aucune conclusion sur un fait réel.'))
            db.commit()
        except Exception:
            db.rollback()
            if 'media' in locals(): storage.delete(media.private_path)
            raise
    print(f'Données fictives créées. Compte: {email}; dossier #{case.id}.')
    return 0

def main()->int:
    parser=argparse.ArgumentParser(prog='checker-ko-admin')
    sub=parser.add_subparsers(dest='command',required=True)
    create=sub.add_parser('create-user',help='Créer un compte sans exposer le mot de passe à la ligne de commande')
    create.add_argument('--email',required=True)
    create.add_argument('--name',required=True)
    create.add_argument('--role',choices=('journalist','editor'),required=True)
    sub.add_parser('seed-demo',help='Créer un dossier fictif sur une base de démonstration vide (activation explicite requise)')
    args=parser.parse_args()
    if args.command=='create-user': return create_user(args.email,args.name,args.role)
    if args.command=='seed-demo': return seed_demo()
    return 2

if __name__=='__main__':
    raise SystemExit(main())
