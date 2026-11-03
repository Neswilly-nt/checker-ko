# Checker-ko v0.7.1 — annuaire et observations statistiques

## Répertoire professionnel

La page « Sources » conserve ses deux onglets dans la navigation existante. Le rôle `editor` correspond à l’administration dans cette application : il peut créer et modifier les fiches, archiver puis réactiver une fiche. Une fiche archivée reste dans SQLite et demeure consultable par la rédaction via `include_archived=true`. Les preuves déjà enregistrées dans des dossiers gardent leur propre titre, URL et texte ; aucun endpoint de suppression définitive n’est exposé.

Les contacts publics sont des entrées distinctes rattachées à une fiche. Chaque entrée demande un courriel ou téléphone public, l’URL de la page qui publie ces coordonnées et une date de vérification. Elles peuvent être modifiées par la rédaction, sans suppression destructive. Les données historiques contact_email/contact_phone sont conservées.

## Observations statistiques

Les publications v0.7 restent le catalogue initial. La rédaction peut transcrire une observation à partir de l’une des notices documentées. Une observation contient l’intitulé de l’indicateur, sa valeur et unité, l’année des données, une région optionnelle, et une référence précise de page/table/figure. Le titre et l’URL du document sont copiés dans l’enregistrement pour préserver la provenance si le catalogue évolue. Aucune valeur n’est préchargée ou générée.

Les observations enregistrées s’affichent sous leur publication et peuvent être ajoutées rapidement à un dossier comme élément de contexte, en conservant valeur, périmètre, lien et emplacement dans le document. Une relation « appuie » ou « contredit » n’est jamais appliquée automatiquement.

## Compatibilité et validation

Au démarrage, SQLAlchemy ajoute les tables `directory_contacts` et `statistical_observations` si elles manquent. Les migrations SQLite existantes restent additives. La migration v0.7.1 a été exécutée sur une copie cohérente de la base privée : les 4 dossiers, 3 preuves et 15 fiches ont été conservés, les deux nouvelles tables sont créées et `PRAGMA foreign_key_check` ne signale aucune violation. La base active n’a pas été migrée par ce test.

Les tests API couvrent les permissions rédaction/journaliste, la référence et date obligatoires des contacts, l’archivage/réactivation sans perte des preuves, la persistance des observations et le refus des régions/publications inconnues. Les tests d’évaluation et d’historique des sources v0.6 restent en place.
