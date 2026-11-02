# Essais responsive v0.4.3

La correction cible le slogan de la barre latérale (`white-space: nowrap`), ainsi que la grille des filtres et les noms longs de l'annuaire. Les règles ajoutent `min-width: 0`, un retour à la ligne local et une grille adaptée aux écrans étroits. Aucun `overflow-x: hidden` global n'a été ajouté.

À mesurer dans Chrome pour chaque page (`/dashboard`, `/verifier`, `/sources`, `/dossiers/4`) :

```js
({ largeurPage: document.documentElement.scrollWidth, largeurVisible: window.innerWidth,
   debordement: document.documentElement.scrollWidth > window.innerWidth })
```

Tailles demandées : 1920×1080, 1366×768, 1280×720, 1024×768, 768×1024, 390×844, 360×800. Zooms demandés : 80 %, 100 %, 125 %, 150 %.

`scripts/smoke-v043.py` a testé `/dashboard`, `/verifier`, `/sources` et `/dossiers/4` dans Chrome headless, avec une copie isolée des dossiers historiques : 112 mesures, zéro débordement horizontal global et zéro slogan débordant à largeur de bureau. Le script vérifie aussi que la page demandée est rendue, que l'annuaire affiche cinq institutions et que CK-004 est ouvert. Chaque zoom est représenté par une largeur CSS calculée (`largeur physique / zoom`) via CDP. Ce contrôle n'est pas un test du bouton de zoom natif de Chrome. La vérification visuelle manuelle des superpositions, des champs et de la navigation mobile reste à faire sur un poste de rédaction.

Le flux annuaire → carnet a aussi été vérifié dans Chrome sur la copie isolée : clic sur « Ajouter à ma vérification » et confirmation d'ajout au dossier CK-004.
