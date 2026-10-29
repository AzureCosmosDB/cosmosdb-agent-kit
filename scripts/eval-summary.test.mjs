import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { test } from 'node:test';
import matter from 'gray-matter';
import { extractLogError, findStepUrl, findTestUrl, readAttempts, renderSummary } from './eval-summary.mjs';

const EVAL = '/repo/evals/query/eval.yaml';
const STEP = 'https://github.com/owner/repo/actions/runs/10/job/20#step:6:1';
const SOURCE = 'https://github.com/owner/repo/blob/0123456789abcdef';
const summary = (overrides = {}) => ({
    type: 'run-summary',
    evals: [{ name: 'query', evalFilePath: EVAL, threshold: 1, ...overrides }],
});
const trial = (stimulus, { passed = false, evidence = 'Missing partition filter.', ...overrides } = {}) => ({
    type: 'trial-result',
    evalFilePath: EVAL,
    stimulus,
    status: 'success',
    variant: 'main',
    model: 'test-model',
    gradeResult: {
        passed,
        score: passed ? 1 : 0.75,
        evidence: '3/4 graders passed',
        details: [
            { name: 'completed', graderType: 'completed', passed: true, evidence: 'Completed.' },
            { name: 'prompt "Long repeated rubric"', graderType: 'prompt', passed, evidence },
        ],
    },
    trajectory: { metadata: { skillsLoaded: ['cosmosdb-best-practices'], executor: 'copilot-sdk' } },
    ...overrides,
});
const run = (trials, status = 1) => ({ status, records: [...trials, summary()] });

test('shows only unresolved failures with inline evidence and a failed-step link', () => {
    const markdown = renderSummary([run([trial('query-pass', { passed: true }), trial('query-fail')])], { stepUrl: STEP });
    assert.match(markdown, /1 failed \| 1 passed first attempt \| 0 recovered after retry/);
    assert.match(markdown, /### cosmosdb-best-practices \/ copilot-sdk \/ test-model \/ main/);
    assert.match(markdown, /\| query-fail \| First \| prompt \| Missing partition filter\./);
    assert.ok(markdown.includes(`[Run Vally](${STEP})`));
    assert.doesNotMatch(markdown, /query-pass|completed|Long repeated rubric|<br>|<details>/);
    assert.equal(markdown.split('\n').filter((line) => line.startsWith('|')).length, 3);
});

test('collapses category tables into one skill/environment group and keeps other environments separate', () => {
    const markdown = renderSummary([run([
        trial('query-b'),
        trial('index-a', { evalFilePath: '/repo/evals/index/eval.yaml' }),
        trial('query-other-model', { model: 'other-model' }),
        trial('query-other-variant', { variant: 'baseline' }),
        trial('query-other-skills', { trajectory: { metadata: { skillsLoaded: ['other-skill'], executor: 'copilot-sdk' } } }),
    ])]);
    assert.equal(markdown.split('\n').filter((line) => line.startsWith('### ')).length, 4);
    assert.ok(markdown.indexOf('| index-a |') < markdown.indexOf('| query-b |'));
});

test('omits recovered rows and uses retry evidence for persistent failures', () => {
    const markdown = renderSummary([
        run([trial('flaky'), trial('persistent')]),
        run([trial('flaky', { passed: true })], 0),
        run([trial('persistent', { evidence: 'Retry still missed the filter.' })]),
    ]);
    assert.match(markdown, /1 failed \| 0 passed first attempt \| 1 recovered after retry/);
    assert.doesNotMatch(markdown, /\| flaky \||Missing partition filter/);
    assert.match(markdown, /\| persistent \| Retry \| prompt \| Retry still missed the filter/);
});

test('a passing record from an unsuccessful retry does not claim recovery', () => {
    const markdown = renderSummary([run([trial('query-fail')]), run([trial('query-fail', { passed: true })])]);
    assert.match(markdown, /1 failed/);
    assert.match(markdown, /Retry did not confirm recovery \(exit 1, complete\); first failure: Missing partition filter/);
});

test('a retry with no matching result is explicit', () => {
    const markdown = renderSummary([run([trial('query-fail')]), run([], 0)]);
    assert.match(markdown, /Retry produced no matching result/);
    assert.match(markdown, /1 failed/);
});

test('multiple failed trials share a row and graders stay on one line', () => {
    const first = trial('query-fail');
    first.gradeResult.details.push({ name: 'output-matches', graderType: 'output-matches', passed: false, evidence: 'Output was empty.' });
    const markdown = renderSummary([run([first, { ...first, trialIndex: 1 }])]);
    assert.equal(markdown.split('\n').filter((line) => line.startsWith('| query-fail |')).length, 1);
    assert.match(markdown, /\| prompt, output-matches \| Missing partition filter\.; Output was empty\./);
});

test('uses the evaluation threshold rather than raw grader flags', () => {
    const markdown = renderSummary([{ status: 0, records: [trial('lenient'), summary({ threshold: 0.5 })] }]);
    assert.match(markdown, /0 failed \| 1 passed first attempt/);
    assert.match(markdown, /No unresolved evaluation failures/);
    assert.doesNotMatch(markdown, /\| lenient \|/);
});

test('reports execution errors, skipped trials, missing grades, and threshold failures without failed child graders', () => {
    const markdown = renderSummary([run([
        trial('error', { status: 'error', error: 'Connection refused.', gradeResult: null, trajectory: null }),
        trial('skip', { status: 'skipped', skipReason: 'Unsupported executor.' }),
        trial('missing', { gradeResult: null }),
        trial('aggregate', { gradeResult: { passed: false, score: 0.5 } }),
    ])]);
    for (const message of ['Connection refused.', 'Unsupported executor.', 'No grade result was produced.', 'Score 0.5 did not meet']) {
        assert.ok(markdown.includes(message));
    }
    assert.match(markdown, /No loaded skills recorded \/ executor unknown/);
});

test('escapes Markdown and HTML and bounds long multiline evidence', () => {
    const markdown = renderSummary([run([trial('a|b', { evidence: '<details>\n[x](bad) | `code` & ' + 'x'.repeat(900) })])]);
    const row = markdown.split('\n').find((line) => line.startsWith('| a'));
    assert.match(row, /a&#124;b/);
    assert.match(row, /&lt;details&gt; \\\[x\\\]\(bad\) &#124; \\`code\\` &amp;/);
    assert.ok(row.length < 650);
    assert.match(row, /\.\.\./);
    assert.doesNotMatch(markdown, /<details>/);
});

test('empty or crashed attempts expose errors rather than claiming success', () => {
    for (const attempts of [[], [{ status: 1, records: [] }]]) {
        const markdown = renderSummary(attempts, { log: '\u001b[31mError: Access denied.\u001b[0m\n at main()\n', stepUrl: STEP });
        assert.match(markdown, /Error: Access denied/);
        assert.ok(markdown.includes(STEP));
        assert.doesNotMatch(markdown, /No unresolved evaluation failures/);
    }
});

test('a terminated retry exposes its process error even when the first attempt had graded failures', () => {
    const markdown = renderSummary([
        run([trial('query-fail')]),
        { status: 1, records: [], error: 'Vally terminated by signal SIGTERM.' },
    ], { stepUrl: STEP, outcome: 'failure' });
    assert.match(markdown, /Retry: Vally terminated by signal SIGTERM/);
    assert.match(markdown, /Retry produced no matching result/);
    assert.match(markdown, /1 failed/);
    assert.ok(markdown.includes(STEP));
});

test('reports eval-level errors and an externally failed step even when trial records passed', () => {
    const markdown = renderSummary([{ status: 1, records: [summary({ error: 'Invalid environment.' })] }]);
    assert.match(markdown, /Invalid environment/);
    assert.doesNotMatch(markdown, /without a retryable result/);
    const external = renderSummary([run([trial('pass', { passed: true })], 0)], {
        outcome: 'failure', log: 'Error: Process shutdown failed.',
    });
    assert.match(external, /Process shutdown failed/);
    assert.doesNotMatch(external, /No unresolved evaluation failures/);
});

test('all-pass and fully recovered runs have no tables', () => {
    for (const attempts of [
        [run([trial('pass', { passed: true })], 0)],
        [run([trial('flaky')]), run([trial('flaky', { passed: true })], 0)],
    ]) {
        const markdown = renderSummary(attempts);
        assert.match(markdown, /No unresolved evaluation failures/);
        assert.doesNotMatch(markdown, /Failed stimulus|\n\|/);
    }
});

test('extracts error messages without generic exit-code noise', () => {
    assert.equal(extractLogError('progress\nTypeError: Invalid input.\n    at main\n##[error]Process completed with exit code 1.'), 'TypeError: Invalid input.');
    assert.equal(extractLogError('All done.'), undefined);
});

test('derives exact step anchors dynamically and falls back explicitly to the run', () => {
    assert.equal(findStepUrl([{ name: 'Run live evaluations', html_url: STEP.split('#')[0], steps: [{ name: 'Run Vally', number: 6 }] }]), STEP);
    assert.equal(findStepUrl([]), undefined);
    const markdown = renderSummary([], { runUrl: 'https://github.com/owner/repo/actions/runs/10' });
    assert.match(markdown, /\[Workflow run\]\(https:\/\/github.com\/owner\/repo\/actions\/runs\/10\)/);
});

test('links failed test names without adding columns or linking passing tests', () => {
    const url = `${SOURCE}/evals/query/eval.yaml#L20`;
    const markdown = renderSummary([run([trial('query-fail'), trial('query-pass', { passed: true })])], {
        testUrl: (file, stimulus) => {
            assert.equal(file, EVAL);
            assert.equal(stimulus, 'query-fail');
            return url;
        },
    });
    assert.ok(markdown.includes(`| [query-fail](${url}) | First |`));
    assert.equal(markdown.split('\n').filter((line) => line.startsWith('|')).length, 3);
});

test('test links use the checked-out path, commit, and exact definition line', () => {
    const dir = mkdtempSync(join(tmpdir(), 'vally-test-link-'));
    try {
        const file = join(dir, 'eval [query](test).yaml');
        writeFileSync(file, [
            'stimuli:',
            '  - name: plain-name',
            '    prompt: Explain this.',
            '  - name: "quoted-name"',
            "  - name: 'single-quoted'",
        ].join('\r\n'));
        for (const [stimulus, line] of [['plain-name', 2], ['quoted-name', 4], ['single-quoted', 5]]) {
            assert.equal(findTestUrl(file, stimulus, { workspace: dir, sourceRootUrl: SOURCE }),
                `${SOURCE}/eval%20%5Bquery%5D%28test%29.yaml#L${line}`);
        }
        assert.equal(findTestUrl(file, 'plain-name'), undefined);
    } finally {
        rmSync(dir, { recursive: true, force: true });
    }
});

test('missing or ambiguous source locations warn and link the spec, never an invented line', (t) => {
    const warn = t.mock.method(console, 'warn', () => {});
    const dir = mkdtempSync(join(tmpdir(), 'vally-test-link-missing-'));
    try {
        const file = join(dir, 'eval.yaml');
        const options = { workspace: dir, sourceRootUrl: SOURCE };
        assert.equal(findTestUrl(file, 'missing', options), `${SOURCE}/eval.yaml`);
        writeFileSync(file, 'stimuli:\n  - name: repeated\n  - name: repeated\n');
        assert.equal(findTestUrl(file, 'missing', options), `${SOURCE}/eval.yaml`);
        assert.equal(findTestUrl(file, 'repeated', options), `${SOURCE}/eval.yaml`);
        assert.equal(findTestUrl(join(dir, '..', 'outside.yaml'), 'missing', options), undefined);
        assert.equal(warn.mock.calls.length, 4);
    } finally {
        rmSync(dir, { recursive: true, force: true });
    }
});

test('the actual interrupt test link points at its definition and nearby rubric', () => {
    const file = resolve('evals/cosmosdb-best-practices/pattern/eval.yaml');
    const url = findTestUrl(file, 'pattern-langgraph-interrupt-human', { workspace: process.cwd(), sourceRootUrl: SOURCE });
    assert.match(url, /\/evals\/cosmosdb-best-practices\/pattern\/eval.yaml#L\d+$/);
    const index = Number(url.split('#L')[1]) - 1;
    const lines = readFileSync(file, 'utf8').split(/\r?\n/);
    assert.equal(lines[index].trim(), '- name: pattern-langgraph-interrupt-human');
    assert.ok(lines.slice(index, index + 8).some((line) => line.includes('resumption restarts the node')));
});

test('the artifact link uses the upload output and is published even after a failed evaluation', () => {
    const source = readFileSync(new URL('../.github/workflows/evals.yml', import.meta.url), 'utf8');
    const workflow = matter(`---\n${source}\n---`).data;
    const steps = workflow.jobs.eval.steps;
    const upload = steps.findIndex((step) => step.id === 'reports');
    const link = steps.findIndex((step) => step.name === 'Link results artifact');
    assert.ok(upload >= 0 && link > upload);
    assert.match(steps[upload].uses, /^actions\/upload-artifact@/);
    assert.equal(steps[link].if, "always() && steps.vally.outcome != 'skipped'");
    assert.equal(steps[link].env.ARTIFACT_URL, '${{ steps.reports.outputs.artifact-url }}');
    assert.match(steps[link].run, /Download full results artifact/);
    assert.match(steps[link].run, /Results artifact unavailable/);
});

test('CLI loads only manifest-listed attempts and writes the artifact and Actions summary', () => {
    const dir = mkdtempSync(join(tmpdir(), 'vally-summary-'));
    try {
        mkdirSync(join(dir, 'attempt-1'));
        const spec = join(dir, 'eval.yaml');
        writeFileSync(spec, 'stimuli:\n  - name: query-fail\n');
        const records = [trial('query-fail', { evalFilePath: spec }), summary({ evalFilePath: spec })];
        writeFileSync(join(dir, 'attempt-1', 'results.jsonl'), records.map((record) => JSON.stringify(record)).join('\n'));
        writeFileSync(join(dir, 'stale.jsonl'), 'not valid JSON');
        writeFileSync(join(dir, 'eval-attempts.json'), JSON.stringify([{ status: 1, files: ['attempt-1/results.jsonl'] }]));
        assert.equal(readAttempts(dir).length, 1);
        const jobs = join(dir, 'jobs.json');
        writeFileSync(jobs, JSON.stringify([{ jobs: [] }, { jobs: [{ name: 'Run live evaluations', html_url: STEP.split('#')[0], steps: [{ name: 'Run Vally', number: 6 }] }] }]));
        const stepSummary = join(dir, 'step-summary.md');
        const result = spawnSync(process.execPath, ['scripts/eval-summary.mjs', dir], {
            encoding: 'utf8',
            env: {
                ...process.env, GITHUB_STEP_SUMMARY: stepSummary, VALLY_JOBS: jobs, VALLY_OUTCOME: 'failure',
                GITHUB_SERVER_URL: 'https://github.com', GITHUB_REPOSITORY: 'owner/repo',
                GITHUB_SHA: '0123456789abcdef', GITHUB_WORKSPACE: dir,
            },
        });
        assert.equal(result.status, 0, result.stderr);
        const markdown = readFileSync(join(dir, 'eval-summary.md'), 'utf8');
        assert.equal(readFileSync(stepSummary, 'utf8'), markdown);
        assert.ok(markdown.includes(STEP));
        assert.match(markdown, /Missing partition filter/);
        assert.ok(markdown.includes(`[query-fail](${SOURCE}/eval.yaml#L2)`));
    } finally {
        rmSync(dir, { recursive: true, force: true });
    }
});

test('a malformed manifest is not silently treated as success', () => {
    const dir = mkdtempSync(join(tmpdir(), 'vally-summary-invalid-'));
    try {
        assert.deepEqual(readAttempts(dir), []);
        writeFileSync(join(dir, 'eval-attempts.json'), '{invalid');
        assert.throws(() => readAttempts(dir), SyntaxError);
    } finally {
        rmSync(dir, { recursive: true, force: true });
    }
});
