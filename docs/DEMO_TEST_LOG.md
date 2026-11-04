# Journal de validation de la demo locale

## PASS

- Base SQLite dediee creee sous `backend/private_data/demo/checker_demo.db`; aucun changement sur Render ou sur une base partagee.
- Initialisation executee deux fois sans doublon : les six dossiers du seed sont stables. Trois dossiers `[TEST]` supplementaires ont ete crees par le smoke test des formulaires; la base locale contient maintenant neuf dossiers, six preuves, deux conclusions, deux videos (dont une generee par le smoke test), une actualite fictive, 14 fiches institutionnelles plus une fiche `[TEST]`, trois publications documentaires et trois valeurs statistiques fictives.
- Connexion HTTP du compte journaliste local et reponses 200 pour `/health`, `/sources`, `/statistics`, `/cases` et `/news`.
- Creation HTTP d'un dossier texte, import de la photo de demonstration, import du MP4 synthetique et generation de ses images-cles.
- La fiche RSS conserve son titre, son URL, sa source et sa date. L'etat de provenance est `to_verify`; la piece liee n'a aucune evaluation. Le verdict de demonstration existant est explicitement `[TEST]`.
- Route de rapport disponible (HTTP 200).
- Pytest : 34 passed, 1 skipped.
- `npm run i18n:check`: OK, 646 cles coherentes.
- `npm run check`: OK.
- `npm run build`: OK.
- Frontend Vite (HTTP 200) et proxy API Vite (HTTP 200).

## FAIL corrige

- Le test du catalogue attendait cinq fiches apres son extension; il verifie maintenant le catalogue entier.
- Le test de statistique fictive utilisait une region invalide; il utilise une region reelle.
- L'option de secteur `autre` est ajoutee au filtre de statistiques pour consulter clairement les donnees fictives.

## NON TESTE

- Parcours visuel automatise et capture Chrome : Chrome a ete lance sur l'URL locale et la page repond; le test interactif et la capture n'ont pas abouti dans cette session. Les serveurs restent demarres pour le test manuel local.
- Actualites RSS externes en direct : la collecte depend des flux reseau et de leurs disponibilites; seul l'article `[TEST]` local a ete controle ici.
- Connexion ou insertion de donnees sur Render : volontairement non effectuee.
