import { readFile } from 'node:fs/promises';

const locales = ['fr', 'mg', 'en'];
const dictionaries = new Map();
for (const locale of locales) {
  const path = new URL(`../src/locales/${locale}.json`, import.meta.url);
  const dictionary = JSON.parse(await readFile(path, 'utf8'));
  const empty = Object.entries(dictionary).filter(([, value]) => typeof value !== 'string' || !value.trim());
  if (empty.length) throw new Error(`${locale}: empty or invalid values: ${empty.map(([key]) => key).join(', ')}`);
  dictionaries.set(locale, dictionary);
}
const expected = new Set(Object.keys(dictionaries.get('fr')));
for (const locale of locales.slice(1)) {
  const actual = new Set(Object.keys(dictionaries.get(locale)));
  const missing = [...expected].filter(key => !actual.has(key));
  const extra = [...actual].filter(key => !expected.has(key));
  if (missing.length || extra.length) throw new Error(`${locale}: missing [${missing.join(', ')}], extra [${extra.join(', ')}]`);
}
console.log(`i18n resources OK: ${expected.size} matching keys in ${locales.join(', ')}.`);
