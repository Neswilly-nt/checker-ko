"""Exercise the deny-by-default application-table RLS migration on PostgreSQL."""
import os

from sqlalchemy import create_engine, text

url = os.environ['DATABASE_URL']
engine = create_engine(url, pool_pre_ping=True)
role = 'checker_public_api_test'

with engine.begin() as connection:
    connection.execute(text(f'DROP ROLE IF EXISTS {role}'))
    connection.execute(text(f'CREATE ROLE {role} NOLOGIN'))
    connection.execute(text(f'GRANT USAGE ON SCHEMA public TO {role}'))
    connection.execute(text(f'GRANT SELECT ON public.users TO {role}'))
    connection.execute(text("INSERT INTO public.users (name,email,password_hash,role,created_at) VALUES ('Synthetic RLS Test','rls-test@example.test','not-a-password','journalist',now())"))
    before = connection.execute(text("SELECT count(*) FROM public.users WHERE email='rls-test@example.test'")).scalar_one()
    assert before == 1, f'Expected one fixture row, saw {before}'
    connection.execute(text(f'SET ROLE {role}'))
    after = connection.execute(text("SELECT count(*) FROM public.users WHERE email='rls-test@example.test'")).scalar_one()
    assert after == 0, f'RLS exposed the synthetic fixture to {role}: {after}'
    connection.execute(text('RESET ROLE'))
    connection.execute(text("DELETE FROM public.users WHERE email='rls-test@example.test'"))
    connection.execute(text(f'REVOKE ALL ON public.users FROM {role}'))
    connection.execute(text(f'REVOKE USAGE ON SCHEMA public FROM {role}'))
    connection.execute(text(f'DROP ROLE {role}'))

print('PostgreSQL migrations and deny-by-default RLS check passed.')
