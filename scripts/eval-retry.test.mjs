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
    const { recovered, stillFailing } = verifyRetry(failures, [
        summary(QUERY),
        trial(QUERY, 'query-a'),
        trial(QUERY, 'query-b', { score: 0 }),
        // query-c never ran in the retry (e.g. the filter matched nothing).
        trial(QUERY, 'query-unrelated', { score: 0 }),
    ]);
    assert.deepEqual(recovered.map((f) => f.stimulus), ['query-a']);
    assert.deepEqual(stillFailing.map((f) => f.stimulus), ['query-b', 'query-c']);
});
