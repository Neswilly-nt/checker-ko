"""Administrative commands; user provisioning is intentionally off the HTTP API."""
from __future__ import annotations
import argparse
from getpass import getpass
import re
import sys
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

def main()->int:
    parser=argparse.ArgumentParser(prog='checker-ko-admin')
    sub=parser.add_subparsers(dest='command',required=True)
    create=sub.add_parser('create-user',help='Créer un compte sans exposer le mot de passe à la ligne de commande')
    create.add_argument('--email',required=True)
    create.add_argument('--name',required=True)
    create.add_argument('--role',choices=('journalist','editor'),required=True)
    args=parser.parse_args()
    if args.command=='create-user': return create_user(args.email,args.name,args.role)
    return 2

if __name__=='__main__':
    raise SystemExit(main())
