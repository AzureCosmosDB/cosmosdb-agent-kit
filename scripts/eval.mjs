import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { discoverEvals } from '@microsoft/vally';

const { evals, errors } = await discoverEvals([fileURLToPath(new URL('../evals/', import.meta.url))]);
if (errors.length > 0) {
    throw new Error(errors.map(({ path, reason }) => `${path}: ${reason}`).join('\n'));
}
if (evals.length === 0) {
    throw new Error('No Vally evaluation specs found under evals/.');
}

// The Vally eval command accepts individual files, not directories or globs.
const require = createRequire(import.meta.url);
const result = spawnSync(process.execPath, [
    require.resolve('@microsoft/vally-cli/dist/index.js'),
    'eval',
    ...evals.flatMap(({ filePath }) => ['--eval-spec', filePath]),
    ...process.argv.slice(2),
], { stdio: 'inherit', env: process.env });
if (result.error) {
    throw result.error;
}
if (result.signal) {
    throw new Error(`Vally terminated by signal ${result.signal}.`);
}
process.exitCode = result.status ?? 1;
