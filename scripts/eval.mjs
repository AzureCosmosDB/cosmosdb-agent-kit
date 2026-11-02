import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { discoverEvals } from '@microsoft/vally';
import { planRetry, summarizeStimuli, verifyRetry } from './eval-retry.mjs';

const { evals, errors } = await discoverEvals([fileURLToPath(new URL('../evals/', import.meta.url))]);
if (errors.length > 0) {
    throw new Error(errors.map(({ path, reason }) => `${path}: ${reason}`).join('\n'));
}
if (evals.length === 0) {
    throw new Error('No Vally evaluation specs found under evals/.');
}

// This runner owns --output-dir so each attempt's reports stay separate.
let outputDir = 'results';
const passthrough = [];
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--output-dir') {
        outputDir = args[++i];
    } else if (args[i].startsWith('--output-dir=')) {
        outputDir = args[i].slice('--output-dir='.length);
    } else {
        passthrough.push(args[i]);
    }
}

const require = createRequire(import.meta.url);
const cli = require.resolve('@microsoft/vally-cli/dist/index.js');

const listRuns = (dir) => existsSync(dir) ? new Set(readdirSync(dir)) : new Set();
const attempts = [];

// The Vally eval command accepts individual files, not directories or globs.
function runVally(specs, tags, dir) {
    const before = listRuns(dir);
    const result = spawnSync(process.execPath, [
        cli,
        'eval',
        ...specs.flatMap((spec) => ['--eval-spec', spec]),
        ...tags.flatMap((tag) => ['--tag', tag]),
        '--output-dir', dir,
        ...passthrough,
    ], { stdio: 'inherit', env: process.env });
    const error = result.error ?? (result.signal ? new Error(`Vally terminated by signal ${result.signal}.`) : undefined);
    const files = [...listRuns(dir)].filter((name) => !before.has(name))
        .map((name) => join(dir, name, 'results.jsonl'))
        .filter((file) => existsSync(file));
    attempts.push({
        status: result.status ?? 1,
        ...(error ? { error: error.message } : {}),
        files: files.map((file) => relative(resolve(outputDir), file)),
    });
    mkdirSync(outputDir, { recursive: true });
    writeFileSync(join(outputDir, 'eval-attempts.json'), JSON.stringify(attempts));
    if (error) throw error;
    const records = files.flatMap((file) => readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean)
            .map((line) => JSON.parse(line)));
    return { status: result.status ?? 1, records };
}

const first = runVally(evals.map(({ filePath }) => filePath), [], resolve(outputDir, 'attempt-1'));
if (first.status === 0) {
    process.exit(0);
}

const failures = summarizeStimuli(first.records).filter((entry) => !entry.passed);
const hasSummary = first.records.some((record) => record.type === 'run-summary');
if (!hasSummary || failures.length === 0) {
    // Nothing gradeable to retry (e.g. invalid spec or crash): keep Vally's verdict.
    console.error('Vally failed without retryable stimulus failures; not retrying.');
    process.exit(first.status);
}

// Retry each failed stimulus once. Grading stays strict: a stimulus passes only
// if its retry passes, so consistent failures still fail the run.
console.log(`\nRetrying ${failures.length} failed stimulus/stimuli once: ${failures.map((f) => f.stimulus).join(', ')}\n`);
const retryRuns = planRetry(failures)
    .map(({ specs, tags }) => runVally(specs, tags, resolve(outputDir, 'retry')));
const { recovered, stillFailing } = verifyRetry(failures, retryRuns);

console.log([
    '## Vally retry summary',
    '',
    'Each stimulus that failed the first attempt was retried once with unchanged grading.',
    '',
    '| Stimulus | First attempt | Retry |',
    '|---|---|---|',
    ...stillFailing.map((f) => `| \`${f.stimulus}\` | ❌ | ❌ |`),
    ...recovered.map((f) => `| \`${f.stimulus}\` | ❌ | ✅ flaky |`),
].join('\n'));
process.exitCode = stillFailing.length === 0 ? 0 : 1;
