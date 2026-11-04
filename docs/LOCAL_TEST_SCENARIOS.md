# Scénarios de démonstration locaux

`backend/scripts/seed_local_test_scenarios.py` prépare quatre dossiers explicitement étiquetés `[TEST]` : texte, photo de démonstration déjà présente dans le dépôt, vidéo MP4 synthétique de deux secondes et article RSS fictif. Il ajoute aussi une fiche de source, des éléments de preuve de contexte et des conclusions de test.

Depuis `backend`, dans un environnement Python avec les dépendances backend et FFmpeg installés :

```powershell
python scripts/seed_local_test_scenarios.py
```

Le script utilise toujours `backend/.demo-test-data/checker-test.sqlite3` et `backend/.demo-test-data/storage`. Il force SQLite et le stockage local avant d’importer l’application, n’accepte aucune URL de base en argument, ne supprime aucune ligne et réutilise les objets `[TEST]` lors des exécutions suivantes. Cette base dédiée ne doit pas être remplacée par `DATABASE_URL` de Render, Supabase ou une base d’équipe.

L’existence d’un endpoint public ne révèle pas le moteur ni le backend de stockage configurés dans l’instance Render. Aucune insertion distante n’est prévue par ce script. Vérifier ces services dans le tableau de bord Render/Supabase avant toute opération opérateur distincte.
