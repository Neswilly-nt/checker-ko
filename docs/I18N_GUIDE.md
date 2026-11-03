# Guide i18n Checker-ko

## Langues prises en charge

Les ressources sont des dictionnaires JSON plats dans `frontend/src/locales/` : `fr.json`, `mg.json` et `en.json`. Les clés sont stables et les ressources doivent avoir exactement les mêmes clés. Le français sert de langue par défaut et de secours.

## Utilisation dans React

Les vues sous `I18nProvider` utilisent `useI18n()` :

```tsx
const { t, locale, setLocale, formatDate, errorMessage } = useI18n();
```

`setLocale` conserve le rendu et les champs montés. `formatDate` adapte le format à la langue choisie. `errorMessage` traduit les erreurs HTTP connues et masque les détails bruts pour les autres erreurs.

Pour ajouter une chaîne, ajouter la même clé et une valeur dans les trois JSON, employer `t('section.key')` pour le texte visible, puis lancer `npm run i18n:check`. Les paramètres s'écrivent `{{name}}`.

## Données qui restent originales

Ne pas traduire ou modifier les affirmations, les textes de preuves, les notes, les titres de publications, les noms officiels d'organismes, les noms de régions et les justifications de conclusion. Ces champs sont des données journalistiques. La traduction concerne les commandes et libellés de l'interface.

## Relecture

La traduction malagasy est une base de travail; une personne maîtrisant le malagasy rédactionnel et les usages journalistiques de Madagascar doit la relire avant diffusion. Les noms d'organismes officiels et les régions malgaches doivent rester tels qu'ils sont fournis par les sources de référence.
