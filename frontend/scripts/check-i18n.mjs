import { readFile, readdir } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

const locales = ['fr', 'mg', 'en'];
const sourceRoot = fileURLToPath(new URL('../src/', import.meta.url));
const dictionaries = new Map();
for (const locale of locales) {
  const dictionary = JSON.parse(await readFile(new URL(`../src/locales/${locale}.json`, import.meta.url), 'utf8'));
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
  for (const key of expected) {
    const placeholders = value => [...value.matchAll(/{{\s*([\w.-]+)\s*}}/g)].map(match => match[1]).sort().join('|');
    if (placeholders(dictionaries.get('fr')[key]) !== placeholders(dictionaries.get(locale)[key])) {
      throw new Error(`${locale}.${key}: placeholder mismatch`);
    }
  }
}

const files = [];
async function walk(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) await walk(path);
    else if (/\.tsx$/.test(entry.name)) files.push(path);
  }
}
await walk(sourceRoot);

const frenchValues = new Set(Object.values(dictionaries.get('fr')).map(value => value.trim()));
const allowlisted = new Set([
  'Checker-ko', 'Google Lens', 'TinEye', 'Facebook', 'TikTok', 'WhatsApp', 'Instagram', 'YouTube', 'X', 'Autre',
  'journaliste@checker.local', 'redaction@checker.local', 'CK-', 's', 's.',
  'good', 'neutral', 'alert', 'status', 'active', 'selected', 'text', 'password', 'MP4',
  'image/jpeg,image/png,image/webp', 'video/mp4',
]);
const uncovered = new Map();
const referencedKeys = new Set();
for (const path of files) {
  const text = await readFile(path, 'utf8');
  const source = ts.createSourceFile(path, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const addCandidate = (candidate, line) => {
    const value = candidate.replace(/\s+/g, ' ').trim();
    if (value && /\p{L}/u.test(value) && !frenchValues.has(value) && !allowlisted.has(value)) {
      const key = `${relative(sourceRoot, path)}:${line}: ${value}`;
      uncovered.set(key, value);
    }
  };
  const inspectVisibleExpression = expression => {
    if (ts.isStringLiteral(expression) || ts.isNoSubstitutionTemplateLiteral(expression)) {
      addCandidate(expression.text, source.getLineAndCharacterOfPosition(expression.getStart(source)).line + 1);
    } else if (ts.isConditionalExpression(expression)) {
      inspectVisibleExpression(expression.whenTrue);
      inspectVisibleExpression(expression.whenFalse);
    } else if (ts.isTemplateExpression(expression)) {
      for (const span of expression.templateSpans) inspectVisibleExpression(span.literal);
    } else if (ts.isBinaryExpression(expression) && expression.operatorToken.kind === ts.SyntaxKind.PlusToken) {
      inspectVisibleExpression(expression.left);
      inspectVisibleExpression(expression.right);
    }
  };
  const visit = node => {
    if (ts.isJsxText(node)) addCandidate(node.getText(source), source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1);
    if (ts.isJsxAttribute(node) && ['aria-label', 'title', 'placeholder', 'alt'].includes(node.name.getText(source)) && node.initializer && ts.isStringLiteral(node.initializer)) {
      addCandidate(node.initializer.text, source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1);
    }
    if (ts.isJsxExpression(node) && node.expression) inspectVisibleExpression(node.expression);
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression)) {
      const name = node.expression.text;
      const messageIndex = name === 'action' ? 1 : ['setError', 'setNotice', 'onSaved'].includes(name) ? 0 : -1;
      if (messageIndex >= 0 && node.arguments[messageIndex]) {
        const inspectMessage = expression => {
          if (ts.isStringLiteral(expression) || ts.isNoSubstitutionTemplateLiteral(expression)) {
            if (expression.text) addCandidate(expression.text, source.getLineAndCharacterOfPosition(expression.getStart(source)).line + 1);
          } else if (ts.isConditionalExpression(expression)) {
            inspectMessage(expression.whenTrue);
            inspectMessage(expression.whenFalse);
          } else if (ts.isTemplateExpression(expression)) {
            addCandidate(expression.getText(source), source.getLineAndCharacterOfPosition(expression.getStart(source)).line + 1);
          }
        };
        inspectMessage(node.arguments[messageIndex]);
      }
    }
    if (ts.isCallExpression(node) && node.expression.getText(source) === 't' && node.arguments.length && ts.isStringLiteral(node.arguments[0])) referencedKeys.add(node.arguments[0].text);
    ts.forEachChild(node, visit);
  };
  visit(source);
}

const unknownKeys = [...referencedKeys].filter(key => !expected.has(key));
if (unknownKeys.length || uncovered.size) {
  if (unknownKeys.length) console.error(`Unknown translation keys: ${unknownKeys.join(', ')}`);
  if (uncovered.size) console.error(`Unmapped interface text (${uncovered.size}):\n${[...uncovered.keys()].join('\n')}`);
  process.exit(1);
}
console.log(`i18n OK: ${expected.size} matching keys; JSX labels and accessible text are mapped or explicitly allowlisted.`);
