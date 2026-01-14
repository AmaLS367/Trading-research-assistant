import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');
const docsSource = path.resolve(rootDir, '..', 'docs');

const mode = process.argv[2] || 'dev';
const isBuild = mode === 'build';

const docsTarget = isBuild
  ? path.resolve(rootDir, 'dist', 'docs')
  : path.resolve(rootDir, 'public', 'docs');
const manifestPath = isBuild
  ? path.resolve(rootDir, 'dist', 'docs-manifest.json')
  : path.resolve(rootDir, 'public', 'docs-manifest.json');

function copyDir(src, dest) {
  if (!fs.existsSync(src)) return false;
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
  return true;
}

function getMarkdownFiles(dir, lang, base = '') {
  const files = [];
  if (!fs.existsSync(dir)) return files;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const relPath = base ? `${base}/${entry.name}` : entry.name;
    if (entry.isDirectory()) {
      files.push(...getMarkdownFiles(path.join(dir, entry.name), lang, relPath));
    } else if (entry.name.endsWith('.md')) {
      files.push(`${lang}/${relPath}`);
    }
  }
  return files;
}

console.log(`📚 Preparing docs (mode: ${mode})...`);

if (fs.existsSync(docsTarget)) {
  fs.rmSync(docsTarget, { recursive: true });
}

if (!fs.existsSync(docsSource)) {
  console.log('⚠️  No docs/ folder found. Creating empty manifest.');
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(
    manifestPath,
    JSON.stringify(
      { languages: [], filesByLanguage: {}, generated: new Date().toISOString() },
      null,
      2
    )
  );
  process.exit(0);
}

copyDir(docsSource, docsTarget);

const languages = fs
  .readdirSync(docsSource, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !d.name.startsWith('_'))
  .map((d) => d.name)
  .sort();

const filesByLanguage = {};
for (const lang of languages) {
  const langFiles = getMarkdownFiles(path.join(docsSource, lang), lang);
  filesByLanguage[lang] = langFiles.sort();
}

const manifest = {
  languages,
  filesByLanguage,
  generated: new Date().toISOString(),
};
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

console.log(`✅ Copied docs for languages: ${languages.join(', ')}`);
console.log(
  `✅ Generated manifest with ${Object.values(filesByLanguage).flat().length} files`
);
