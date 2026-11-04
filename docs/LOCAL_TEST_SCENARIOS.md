# Scenarios de demonstration locaux

`backend/scripts/seed_local_test_scenarios.py` prepare une base SQLite isolee sous `backend/private_data/demo/checker_demo.db` et les medias sous `backend/private_data/demo/storage`. Il cree six dossiers explicitement marques `[TEST]` : une affirmation textuelle, une photo autorisee du depot, une video MP4 synthetique de deux secondes, un article RSS fictif, une observation statistique fictive, et un bulletin meteo fictif. Les sources et publications officielles restent separees des valeurs inventees.

Prerequis : environnement virtuel backend installe et FFmpeg/ffprobe disponibles. Depuis le dossier `backend` :

```powershell
.venv\Scripts\python.exe scripts\seed_local_test_scenarios.py
```

Le script force `APP_ENV=development`, le mode demo, une option locale de catalogue, SQLite dedie et stockage local avant import de lapplication. Les executions suivantes reutilisent les enregistrements `[TEST]`. Pour reconstruire la base, utiliser `--reset` uniquement si le marqueur `.checker-ko-demo-data` est present; le script ne touche quaux fichiers exacts de la base et du stockage dedies. Ne passez jamais lURL de Render, Supabase ou dune base dequipe a ce script.

Les comptes de test locaux sont generes dans le fichier ignore `backend/private_data/demo/credentials.json`; le script affiche les identifiants au moment de sa premiere execution. Ne pas reutiliser ces identifiants hors de lapplication locale.

Le contenu fictif utilise le domaine reserve `example.test`; il ne doit pas etre cite comme une information reelle. Les publications institutionnelles sont des liens documentaires verifiables, indiquees comme partiellement verifiees lorsquun contact ou une ressource na pas ete controle.
