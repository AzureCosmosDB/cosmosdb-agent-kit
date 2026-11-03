import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import matter from 'gray-matter';

const root = fileURLToPath(new URL('../../', import.meta.url));
const skill = resolve(root, 'skills/cosmosdb-fault-testing');
const read = (path) => readFileSync(resolve(skill, path), 'utf8');
const hash = 'cdc4727bb1ea288f1f65319261cc3780eec29b7d3e7b5b7b251404e2c5f3c25f';

test('bundled upstream bytes match documented SHA-256', () => {
    const bytes = readFileSync(resolve(skill, 'scripts/EnableDisableChaosFault.ps1'));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), hash);
    assert.ok(read('references/script-provenance.md').includes(hash));
    assert.ok(read('references/ppaf.md').includes(hash));
    assert.match(read('LICENSE'), /MIT License/);
});

test('snapshot checkout stays byte-identical with autocrlf enabled', () => {
    const path = 'skills/cosmosdb-fault-testing/scripts/EnableDisableChaosFault.ps1';
    const bytes = readFileSync(resolve(root, path));
    const blob = execFileSync('git', ['hash-object', '-w', '--stdin'], { cwd: root, input: bytes })
        .toString().trim();
    const filtered = execFileSync('git',
        ['-c', 'core.autocrlf=true', 'cat-file', '--filters', `--path=${path}`, blob], { cwd: root });
    assert.equal(createHash('sha256').update(filtered).digest('hex'), hash);
});
test('agent entry point is scenario-based and independent of README', () => {
    const entry = read('SKILL.md');
    assert.equal(matter(entry).data.name, 'cosmosdb-fault-testing');
    assert.ok(entry.split('\n').length < 500);
    assert.match(entry, /references\/ppaf\.md/);
    assert.match(entry, /references\/script-provenance\.md/);
    assert.doesNotMatch(entry, /\]\(README\.md\)/);
    assert.match(entry, /one question at a time/);
    assert.equal(JSON.parse(read('metadata.json')).version,
        JSON.parse(readFileSync(resolve(root, 'package.json'), 'utf8')).version);
});

test('packaged documentation links resolve within the skill', () => {
    const paths = ['SKILL.md', 'README.md',
        ...readdirSync(resolve(skill, 'references')).filter(p => p.endsWith('.md')).map(p => `references/${p}`)];
    for (const path of paths) {
        for (const match of read(path).matchAll(/\]\(([^)#\s]+)(?:#[^)]*)?\)/g)) {
            if (/^https?:/.test(match[1])) continue;
            const target = resolve(dirname(resolve(skill, path)), match[1]);
            assert.ok(target.startsWith(skill + '/'), `${path}: link outside package`);
            assert.ok(readFileSync(target).length, `${path}: missing link ${match[1]}`);
        }
    }
});
