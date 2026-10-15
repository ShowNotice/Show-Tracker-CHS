// Sanity checks for worker.js, run on pull requests (check-worker.yml) and again
// before every deploy (deploy-worker.yml):
// 1. No duplicate top-level function declarations. PRs #3/#4 once committed
//    esbuild-bundled output over the hand-written source, so every function was
//    declared twice; JS lets the later copy silently win, and `node --check` and
//    `wrangler deploy --dry-run` both pass such a file.
// 2. DIGEST_CRON in worker.js matches the cron in wrangler.toml. worker.js only sends
//    the digest when a fire's scheduledTime matches its own DIGEST_CRON, so changing
//    the schedule in one place alone would silently stop every digest.
// (Syntax is checked separately with `node --check worker.js`.)
const fs = require('fs');
let failed = false;

const src = fs.readFileSync('worker.js', 'utf8');
const names = [...src.matchAll(/^(?:async function|function) ([A-Za-z_$][\w$]*)/gm)].map(m => m[1]);
const seen = new Set();
const dupes = new Set();
for (const n of names) { if (seen.has(n)) dupes.add(n); seen.add(n); }
if (dupes.size) {
  console.error('Duplicate top-level function declaration(s):', [...dupes].join(', '));
  failed = true;
}

const code = src.match(/const DIGEST_CRON = '([^']+)'/);
const toml = fs.readFileSync('wrangler.toml', 'utf8').match(/^crons\s*=\s*\[\s*"([^"]+)"\s*\]/m);
if (!code || !toml || code[1] !== toml[1]) {
  console.error('DIGEST_CRON (' + (code && code[1]) + ') does not match wrangler.toml crons (' + (toml && toml[1]) + ')');
  failed = true;
}

if (failed) process.exit(1);
console.log('worker.js checks passed (' + names.length + ' top-level functions, DIGEST_CRON ' + code[1] + ').');
