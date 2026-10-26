import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const fixtureFiles = [
    'scripts/version.js',
    'scripts/validate-manifests.js',
    'package.json',
    'package-lock.json',
    'plugin.json',
    'gemini-extension.json',
    '.claude-plugin/plugin.json',
    '.codex-plugin/plugin.json',
    '.cursor-plugin/plugin.json',
    '.kimi-plugin/plugin.json',
    'apm.yml',
    'skills/cosmosdb-best-practices/metadata.json',
];

function createFixture(context) {
    const directory = mkdtempSync(join(tmpdir(), 'cosmosdb-version-'));
    context.after(() => rmSync(directory, { recursive: true, force: true }));
    for (const file of fixtureFiles) {
        const destination = join(directory, file);
        mkdirSync(dirname(destination), { recursive: true });
        cpSync(join(root, file), destination);
    }
    return directory;
}

function runScript(directory, script, ...args) {
    return spawnSync(process.execPath, [join(directory, 'scripts', script), ...args], {
        cwd: directory,
        encoding: 'utf8',
    });
}

function readJson(directory, file) {
    return JSON.parse(readFileSync(join(directory, file), 'utf8'));
}

test('version bump aligns manifests and both lockfile versions without changing dependencies', (context) => {
    const directory = createFixture(context);
    const expectedLock = readJson(directory, 'package-lock.json');
    const nextVersion = '9.8.7';
    const result = runScript(directory, 'version.js', nextVersion);
    assert.equal(result.status, 0, result.stderr);

    expectedLock.version = nextVersion;
    expectedLock.packages[''].version = nextVersion;
    assert.deepEqual(readJson(directory, 'package-lock.json'), expectedLock);
    assert.equal(readJson(directory, 'package.json').version, nextVersion);
    assert.equal(readJson(directory, 'skills/cosmosdb-best-practices/metadata.json').version, nextVersion);

    const validation = runScript(directory, 'validate-manifests.js');
    assert.equal(validation.status, 0, validation.stderr);
});

const invalidLockfiles = [
    ['stale top-level version', (lock) => { lock.version = '0.0.0'; }, /Version mismatch in package-lock\.json: /],
    ['stale root-package version', (lock) => { lock.packages[''].version = '0.0.0'; }, /Version mismatch in package-lock\.json packages\[""\]/],
    ['both versions stale', (lock) => { lock.version = lock.packages[''].version = '0.0.0'; }, /Version mismatch in package-lock\.json: /],
    ['missing top-level version', (lock) => { delete lock.version; }, /No "version" field in package-lock\.json/],
    ['missing root-package version', (lock) => { delete lock.packages[''].version; }, /No .*version.* field in package-lock\.json/],
    ['missing root package', (lock) => { delete lock.packages['']; }, /No .*version.* field in package-lock\.json/],
];

for (const [name, mutate, expectedError] of invalidLockfiles) {
    test(`manifest validation rejects a lockfile with ${name}`, (context) => {
        const directory = createFixture(context);
        const lock = readJson(directory, 'package-lock.json');
        mutate(lock);
        writeFileSync(join(directory, 'package-lock.json'), JSON.stringify(lock));
        const result = runScript(directory, 'validate-manifests.js');
        assert.equal(result.status, 1, result.stderr);
        assert.match(result.stderr, expectedError);
    });
}

test('manifest validation rejects a missing lockfile', (context) => {
    const directory = createFixture(context);
    rmSync(join(directory, 'package-lock.json'));
    const result = runScript(directory, 'validate-manifests.js');
    assert.equal(result.status, 1, result.stderr);
    assert.match(result.stderr, /Missing manifest: package-lock\.json/);
});

test('manifest validation rejects malformed lockfile JSON', (context) => {
    const directory = createFixture(context);
    writeFileSync(join(directory, 'package-lock.json'), '{');
    const result = runScript(directory, 'validate-manifests.js');
    assert.equal(result.status, 1, result.stderr);
    assert.match(result.stderr, /Invalid JSON in package-lock\.json/);
});

test('invalid versions leave all manifests unchanged', (context) => {
    const directory = createFixture(context);
    const originals = fixtureFiles.map((file) => readFileSync(join(directory, file), 'utf8'));
    const result = runScript(directory, 'version.js', 'not-a-version');
    assert.equal(result.status, 1, result.stderr);
    fixtureFiles.forEach((file, index) => {
        assert.equal(readFileSync(join(directory, file), 'utf8'), originals[index], file);
    });
});