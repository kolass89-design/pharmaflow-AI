import * as esbuild from 'esbuild';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(root, 'dist');
fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist, { recursive: true });

const entries = {
  background: 'src/background.ts',
  content: 'src/content.ts',
  scan: 'src/scan.ts',
  popup: 'src/popup.ts',
  options: 'src/options.ts',
};

for (const [name, entry] of Object.entries(entries)) {
  await esbuild.build({
    entryPoints: [path.join(root, entry)],
    outfile: path.join(dist, `${name}.js`),
    bundle: true,
    format: name === 'content' || name === 'scan' ? 'iife' : 'esm',
    target: 'chrome110',
    minify: true,
    logLevel: 'warning',
  });
}

// Copy static assets.
fs.cpSync(path.join(root, 'public'), dist, { recursive: true });

const manifest = JSON.parse(fs.readFileSync(path.join(dist, 'manifest.json'), 'utf8'));
for (const f of ['background.js', 'content.js', 'scan.js', 'popup.js', 'options.js', 'popup.html', 'options.html', 'icons/icon128.png']) {
  if (!fs.existsSync(path.join(dist, f))) throw new Error(`Missing build output: ${f}`);
}
console.log(`Built extension v${manifest.version} -> dist/`);

if (process.argv.includes('--zip')) {
  const AdmZip = (await import('adm-zip')).default;
  const zip = new AdmZip();
  zip.addLocalFolder(dist);
  const out = path.join(root, 'nova-extension.zip');
  zip.writeZip(out);
  console.log(`Packed ${out} (${fs.statSync(out).size} bytes)`);
}
