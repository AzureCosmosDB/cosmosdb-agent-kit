import assert from 'node:assert/strict';
import { test } from 'node:test';
import { planRetry, summarizeStimuli, verifyRetry } from './eval-retry.mjs';

const QUERY = '/repo/evals/query/eval.yaml';
const ROOT = '/repo/evals/eval.yaml';

const summary = (...evalFilePaths) => ({
    type: 'run-summary',
    evals: evalFilePaths.map((evalFilePath) => ({ evalFilePath, threshold: 1 })),
});
const trial = (evalFilePath, stimulus, { score = 1, status = 'success', rule = stimulus, graded = true } = {}) => ({
    type: 'trial-result',
    evalFilePath,
    stimulus,
    status,
    gradeResult: graded ? { passed: score === 1, score } : undefined,
    trajectory: { stimulus: { tags: rule ? { rule } : {} } },
});

test('a stimulus fails on a partial score, an execution error, or a missing grade', () => {
    const results = summarizeStimuli([
        summary(QUERY),
        trial(QUERY, 'query-a'),
        trial(QUERY, 'query-b', { score: 0.75 }),
        trial(QUERY, 'query-c', { status: 'error' }),
        trial(QUERY, 'query-d', { graded: false }),
    ]);
    assert.deepEqual(results.map(({ stimulus, passed }) => [stimulus, passed]),
        [['query-a', true], ['query-b', false], ['query-c', false], ['query-d', false]]);
});

test('the eval threshold decides a trial, not the raw grader flag', () => {
    const lenient = { type: 'run-summary', evals: [{ evalFilePath: QUERY, threshold: 0.5 }] };
    const [result] = summarizeStimuli([lenient, trial(QUERY, 'query-a', { score: 0.75 })]);
    assert.equal(result.passed, true);
});

test('one failed trial fails a multi-trial stimulus', () => {
    const [result] = summarizeStimuli([
        summary(QUERY),
        trial(QUERY, 'query-a'),
        trial(QUERY, 'query-a', { score: 0 }),
    ]);
    assert.equal(result.passed, false);
});

test('retries target failed rules by tag and rerun untagged specs whole', () => {
    const failures = summarizeStimuli([
        summary(QUERY, ROOT),
        trial(QUERY, 'query-a', { score: 0 }),
        trial(QUERY, 'query-b', { score: 0 }),
        trial(ROOT, 'should-not-trigger', { score: 0, rule: null }),
    ]).filter((entry) => !entry.passed);
    assert.deepEqual(planRetry(failures), [
        { specs: [QUERY], tags: ['rule=query-a,query-b'] },
        { specs: [ROOT], tags: [] },
    ]);
    assert.deepEqual(planRetry([]), []);
});

test('only a passing retry recovers a failure; missing or failed retries do not', () => {
    const failures = summarizeStimuli([
        summary(QUERY),
        trial(QUERY, 'query-a', { score: 0 }),
        trial(QUERY, 'query-b', { score: 0 }),
        trial(QUERY, 'query-c', { score: 0 }),
    ]);
    const { recovered, stillFailing } = verifyRetry(failures, [{ status: 0, records: [
        trial(QUERY, 'query-a'),
        trial(QUERY, 'query-b', { score: 0 }),
        // query-c never ran in the retry (e.g. the filter matched nothing).
        trial(QUERY, 'query-unrelated', { score: 0 }),
        summary(QUERY),
    ] }]);
    assert.deepEqual(recovered.map((f) => f.stimulus), ['query-a']);
    assert.deepEqual(stillFailing.map((f) => f.stimulus), ['query-b', 'query-c']);
});

for (const { name, status, completed } of [
    { name: 'nonzero retry without a run summary', status: 1, completed: false },
    { name: 'nonzero retry with a run summary', status: 1, completed: true },
    { name: 'zero-exit retry without a run summary', status: 0, completed: false },
]) {
    test(`${name} cannot recover a failure from passing records`, () => {
        const failures = summarizeStimuli([trial(QUERY, 'query-a', { score: 0 }), summary(QUERY)]);
        const records = [
            { ...trial(QUERY, 'query-a'), trialIndex: 0, totalTrials: 2 },
            ...(completed ? [
                { ...trial(QUERY, 'query-a'), trialIndex: 1, totalTrials: 2 },
                summary(QUERY),
            ] : []),
        ];
        assert.deepEqual(verifyRetry(failures, [{ status, records }]), {
            recovered: [],
            stillFailing: failures,
        });
    });
}

test('a completed successful retry recovers a multi-trial stimulus only when every trial passes', () => {
    const failures = summarizeStimuli([trial(QUERY, 'query-a', { score: 0 }), summary(QUERY)]);
    for (const score of [0, 1]) {
        const records = [
            { ...trial(QUERY, 'query-a'), trialIndex: 0, totalTrials: 2 },
            { ...trial(QUERY, 'query-a', { score }), trialIndex: 1, totalTrials: 2 },
            summary(QUERY),
        ];
        assert.deepEqual(verifyRetry(failures, [{ status: 0, records }]), {
            recovered: score === 1 ? failures : [],
            stillFailing: score === 1 ? [] : failures,
        });
    }
});

test('a successful retry cannot lend its status or summary to another invocation', () => {
    const failures = summarizeStimuli([
        trial(QUERY, 'query-a', { score: 0 }),
        trial(QUERY, 'query-b', { score: 0 }),
        trial(QUERY, 'query-c', { score: 0 }),
        summary(QUERY),
    ]);
    const { recovered, stillFailing } = verifyRetry(failures, [
        { status: 1, records: [trial(QUERY, 'query-a'), summary(QUERY)] },
        { status: 0, records: [trial(QUERY, 'query-b')] },
        { status: 0, records: [trial(QUERY, 'query-c'), summary(QUERY)] },
    ]);
    assert.deepEqual(recovered.map((f) => f.stimulus), ['query-c']);
    assert.deepEqual(stillFailing.map((f) => f.stimulus), ['query-a', 'query-b']);
});

test('a run summary must be the final retry record', () => {
    const failures = summarizeStimuli([trial(QUERY, 'query-a', { score: 0 }), summary(QUERY)]);
    assert.deepEqual(verifyRetry(failures, [{
        status: 0,
        records: [summary(QUERY), trial(QUERY, 'query-a')],
    }]), { recovered: [], stillFailing: failures });
});

test('missing retry runs leave every failure unrecovered', () => {
    const failures = summarizeStimuli([trial(QUERY, 'query-a', { score: 0 }), summary(QUERY)]);
    assert.deepEqual(verifyRetry(failures, []), { recovered: [], stillFailing: failures });
});
