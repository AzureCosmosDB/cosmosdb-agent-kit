import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import { basename, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import {
    computeMetrics,
    createDefaultGraderRegistry,
    gradeTrajectory,
    loadEvalSpec,
    resolveGradePass,
} from '@microsoft/vally';

const root = new URL('./', import.meta.url);
const specFiles = (await readdir(root, { recursive: true }))
    .filter((file) => basename(file) === 'eval.yaml')
    .map((file) => join(fileURLToPath(root), file)).sort();
const specs = await Promise.all(specFiles.map(async (file) => ({
    spec: await loadEvalSpec(file),
    source: await readFile(file, 'utf8'),
})));
const rules = (await readdir(new URL('../../skills/cosmosdb-best-practices/rules/', root)))
    .filter((name) => name.endsWith('.md') && !name.startsWith('_'))
    .map((name) => name.slice(0, -3)).sort();
const stimuli = specs.flatMap(({ spec }) => spec.stimuli);
const legacyScenarios = {
    'basic-usage-001': 'partition-high-cardinality',
    'edge-case-001': 'query-avoid-cross-partition',
    'indexing-composite-005': 'index-composite',
    'model-embed-vs-reference-004': 'model-embed-related',
    'model-ttl-expiration': 'model-ttl-expiration',
    'query-optimization-003': 'query-point-reads',
    'sdk-emulator-ssl-java-linux': 'sdk-emulator-ssl',
    'sdk-go-partition-key-metadata': 'sdk-go-partition-key-metadata',
    'sdk-singleton-client-002': 'sdk-singleton-client',
    'security-private-endpoint-dns': 'security-private-endpoint-dns',
    'should-not-trigger-001': 'should-not-trigger',
    'throughput-autoscale-006': 'throughput-autoscale',
    'vector-index-type-013': 'vector-index-type',
};
const skill = { type: 'skill_activation', data: { name: 'cosmosdb-best-practices' } };
const completed = { type: 'turn_end', data: { turnId: 'offline-turn' } };
const failure = { type: 'error', data: { message: 'Synthetic executor failure' } };

test('exactly one evaluation covers every rule', () => {
    assert.deepEqual(stimuli.filter((stimulus) => stimulus.tags.rule)
        .map((stimulus) => stimulus.tags.rule).sort(), rules);
    assert.equal(new Set(stimuli.map((stimulus) => stimulus.name)).size, stimuli.length);
    assert.equal(stimuli.filter((stimulus) => !stimulus.tags.rule).length, 1);
    assert.equal(stimuli.find((stimulus) => !stimulus.tags.rule).name, 'should-not-trigger');
});

test('every legacy scenario maps to exactly one migrated case', () => {
    const migrated = stimuli.filter((stimulus) => stimulus.tags.legacy);
    assert.equal(migrated.length, Object.keys(legacyScenarios).length);
    assert.deepEqual(Object.fromEntries(migrated.map((stimulus) =>
        [stimulus.tags.legacy, stimulus.name])), legacyScenarios);
});

test('cases stay short, commented, and meaningfully graded', () => {
    for (const { spec, source } of specs) {
        assert.equal(spec.scoring.threshold, 1);
        assert.equal(spec.defaults.executor, 'copilot-sdk');
        assert.equal(spec.defaults.runs, 1);
        const comments = [...source.matchAll(/^\s*# ([^\r\n]+)\r?\n\s*- name: ([\w-]+)/gm)];
        assert.deepEqual(comments.map((match) => match[2]), spec.stimuli.map((stimulus) => stimulus.name));
        for (const [, comment] of comments) {
            assert.ok(comment.trim().split(/\s+/).length <= 6, comment);
        }
        for (const stimulus of spec.stimuli) {
            assert.ok(stimulus.prompt.trim().length > 0, stimulus.name);
            // Preserve the original vector decision matrix and its regression details.
            const maxWords = stimulus.tags.legacy === 'vector-index-type-013' ? 180 : 65;
            assert.ok(stimulus.prompt.trim().split(/\s+/).length <= maxWords, stimulus.name);
            assert.ok(stimulus.rubric.length > 0, stimulus.name);
            for (const criterion of stimulus.rubric) {
                assert.ok(criterion.length > 40, stimulus.name);
            }
            assert.deepEqual(stimulus.graders.map((grader) => grader.type),
                ['completed', 'skill-invocation', 'prompt', 'output-matches']);
            assert.equal(stimulus.graders[2].config.scoring, 'binary');
            assert.equal(stimulus.graders[2].config.threshold, 1);
            assert.deepEqual(stimulus.graders[1].config,
                stimulus.tags.rule
                    ? { required: ['cosmosdb-best-practices'] }
                    : { disallowed: ['cosmosdb-best-practices'] });
            if (stimulus.tags.rule) {
                assert.equal(stimulus.name, stimulus.tags.rule);
                assert.equal(stimulus.tags.category, stimulus.name.split('-')[0]);
            }
        }
    }
});

// A fake judge verifies verdict wiring, not the quality of live model judgments.
async function grade(spec, stimulus, { events, output = 'Synthetic answer.', verdict = 1 }) {
    const trajectory = {
        id: 'offline-grader-test',
        stimulus,
        output,
        events,
        metrics: computeMetrics(events),
        workDir: import.meta.dirname,
        metadata: { model: 'offline', executor: 'test', sessionID: 'test' },
    };
    const registry = createDefaultGraderRegistry({
        supportsWorkspaceDelivery: true,
        async judge(options) {
            assert.ok(options.userMessage.includes(stimulus.prompt));
            for (const criterion of stimulus.rubric) {
                assert.ok(options.userMessage.includes(criterion));
            }
            assert.equal(options.model, spec.defaults.judge_model);
            assert.ok(options.workspace.evidenceFiles.length > 0);
            return {
                args: {
                    rubric_scores: stimulus.rubric.map((criterion) =>
                        ({ criterion, score: verdict, reasoning: 'Synthetic verdict.' })),
                    overall_score: verdict,
                    overall_reasoning: 'Synthetic verdict.',
                },
                latencyMs: 0,
                remindersUsed: 0,
            };
        },
        async shutdown() {},
    });
    const result = await gradeTrajectory(trajectory, stimulus.graders, {
        registry,
        stimulus,
        judgeModel: spec.defaults.judge_model,
        weights: spec.scoring.weights,
    });
    assert.notEqual(result.status, 'error', result.evidence);
    return resolveGradePass(result, spec.scoring.threshold);
}

for (const { spec } of specs) {
    for (const stimulus of spec.stimuli) {
        const negative = stimulus.name === 'should-not-trigger';
        const events = negative ? [completed] : [skill, completed];

        test(`${stimulus.name}: accepts a passing verdict with correct activation`, async () => {
            assert.equal(await grade(spec, stimulus, { events }), true);
        });
        test(`${stimulus.name}: rejects an incorrect answer despite activation`, async () => {
            assert.equal(await grade(spec, stimulus, { events, verdict: 0 }), false);
        });
        test(`${stimulus.name}: rejects empty output despite a passing judge`, async () => {
            assert.equal(await grade(spec, stimulus, { events, output: ' \n' }), false);
        });
        test(`${stimulus.name}: rejects incorrect activation`, async () => {
            const wrongEvents = negative ? [skill, completed] : [completed];
            assert.equal(await grade(spec, stimulus, { events: wrongEvents }), false);
        });
        test(`${stimulus.name}: rejects execution errors`, async () => {
            assert.equal(await grade(spec, stimulus, { events: [...events, failure] }), false);
        });
    }
}
