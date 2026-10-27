import { resolveGradePass } from '@microsoft/vally';

const keyOf = (evalFilePath, stimulus) => `${evalFilePath}::${stimulus}`;

function thresholds(records) {
    const byEval = new Map();
    for (const record of records) {
        if (record.type !== 'run-summary') continue;
        for (const entry of record.evals ?? []) {
            byEval.set(entry.evalFilePath, entry.threshold);
        }
    }
    return byEval;
}

function trialPassed(trial, threshold) {
    return trial.status === 'success' && trial.gradeResult != null
        && resolveGradePass(trial.gradeResult, threshold);
}

/** Group trial results by stimulus; a stimulus passes only if every trial passes. */
export function summarizeStimuli(records) {
    const threshold = thresholds(records);
    const stimuli = new Map();
    for (const trial of records) {
        if (trial.type !== 'trial-result') continue;
        const key = keyOf(trial.evalFilePath, trial.stimulus);
        const entry = stimuli.get(key) ?? {
            key,
            evalFilePath: trial.evalFilePath,
            stimulus: trial.stimulus,
            rule: trial.trajectory?.stimulus?.tags?.rule,
            passed: true,
        };
        entry.passed &&= trialPassed(trial, threshold.get(trial.evalFilePath));
        stimuli.set(key, entry);
    }
    return [...stimuli.values()];
}

/**
 * Plan a single retry of failed stimuli. Rule-tagged stimuli are selected with
 * one `--tag rule=...` filter; untagged stimuli rerun their whole spec, and only
 * the previously failed stimuli count toward the retry verdict.
 */
export function planRetry(failures) {
    const tagged = failures.filter((failure) => typeof failure.rule === 'string');
    const untagged = failures.filter((failure) => typeof failure.rule !== 'string');
    const invocations = [];
    if (tagged.length > 0) {
        invocations.push({
            specs: [...new Set(tagged.map((failure) => failure.evalFilePath))],
            tags: [`rule=${[...new Set(tagged.map((failure) => failure.rule))].join(',')}`],
        });
    }
    if (untagged.length > 0) {
        invocations.push({
            specs: [...new Set(untagged.map((failure) => failure.evalFilePath))],
            tags: [],
        });
    }
    return invocations;
}

/** Recovery requires a successful, completed retry in which every trial of the stimulus passed. */
export function verifyRetry(failures, retryRuns) {
    const retryRecords = retryRuns
        .filter(({ status, records }) => status === 0 && records.at(-1)?.type === 'run-summary')
        .flatMap(({ records }) => records);
    const retried = new Map(summarizeStimuli(retryRecords).map((entry) => [entry.key, entry]));
    const recovered = [];
    const stillFailing = [];
    for (const failure of failures) {
        (retried.get(failure.key)?.passed ? recovered : stillFailing).push(failure);
    }
    return { recovered, stillFailing };
}
