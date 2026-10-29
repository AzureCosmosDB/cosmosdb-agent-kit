import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { stripVTControlCharacters } from 'node:util';
import { failedTrials, summarizeStimuli, verifyRetry } from './eval-retry.mjs';

function compact(value, limit = 500) {
    const text = stripVTControlCharacters(String(value)).replace(/\s+/g, ' ').trim();
    return text.length > limit ? `${text.slice(0, limit - 3)}...` : text;
}

function cell(value) {
    return compact(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\|/g, '&#124;').replace(/([\\`*_[\]])/g, '\\$1');
}

const matches = (trial, failure) => trial.evalFilePath === failure.evalFilePath
    && trial.stimulus === failure.stimulus;

function environment(trial) {
    const metadata = trial.trajectory?.metadata;
    const skills = metadata?.skillsLoaded;
    return [
        skills?.length ? [...skills].sort().join(', ') : 'No loaded skills recorded',
        metadata?.executor ?? 'executor unknown',
        trial.model ?? metadata?.model ?? 'model unknown',
        trial.variant ?? 'default',
    ].join(' / ');
}

function failureDetail(trial) {
    if (trial.error) return { graders: '-', message: trial.error };
    if (trial.status !== 'success') {
        return { graders: '-', message: trial.skipReason ?? `Trial ${trial.status}.` };
    }
    if (!trial.gradeResult) return { graders: '-', message: 'No grade result was produced.' };
    const grade = trial.gradeResult;
    const failed = (grade.details ?? []).filter((detail) => detail.status === 'error' || !detail.passed);
    return {
        graders: failed.map((detail) => detail.configuredName ?? detail.graderType ?? detail.name).join(', ') || 'aggregate',
        message: failed.map((detail) => detail.evidence || `${detail.name} failed.`).join('; ')
            || grade.evidence || `Score ${grade.score} did not meet the evaluation threshold.`,
    };
}

/** Extract a useful crash message without dumping progress output or a stack trace. */
export function extractLogError(log) {
    const lines = stripVTControlCharacters(log).split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    const errors = lines.filter((line) => /(?:\b[\w]*Error:|::error::|##\[error\])/i.test(line)
        && !/Process completed with exit code/.test(line));
    return errors.length ? compact(errors.at(-1)) : undefined;
}

export function findStepUrl(jobs, jobName = 'Run live evaluations', stepName = 'Run Vally') {
    const job = jobs.find((entry) => entry.name === jobName);
    const step = job?.steps?.find((entry) => entry.name === stepName);
    return job?.html_url && step ? `${job.html_url}#step:${step.number}:1` : undefined;
}

export function findTestUrl(evalFilePath, stimulus, { workspace, sourceRootUrl } = {}) {
    if (!workspace || !sourceRootUrl) return undefined;
    const file = relative(workspace, evalFilePath);
    if (!file || isAbsolute(file) || file === '..' || file.startsWith(`..${sep}`)) {
        console.warn(`Cannot link test outside the repository: ${evalFilePath}`);
        return undefined;
    }
    const url = `${sourceRootUrl}/${file.split(sep).map((part) => encodeURIComponent(part)
        .replace(/[!'()*]/g, (character) => `%${character.charCodeAt(0).toString(16).toUpperCase()}`)).join('/')}`;
    if (!existsSync(evalFilePath)) {
        console.warn(`Test source is unavailable; linking to the spec without a line: ${evalFilePath}`);
        return url;
    }
    const names = new Set([stimulus, JSON.stringify(stimulus), `'${stimulus.replace(/'/g, "''")}'`]);
    const lines = readFileSync(evalFilePath, 'utf8').split(/\r?\n/);
    const matches = lines.flatMap((line, index) => {
        const name = line.match(/^\s*-\s+name:\s*(.*?)\s*$/)?.[1];
        return names.has(name) ? [index + 1] : [];
    });
    if (matches.length !== 1) {
        console.warn(`Cannot locate a unique test definition for ${stimulus}; linking to the spec: ${evalFilePath}`);
        return url;
    }
    return `${url}#L${matches[0]}`;
}

/** Failures only; successful and recovered stimuli remain counts, not table rows. */
export function renderSummary(attempts, { stepUrl, runUrl, log = '', outcome, testUrl = () => undefined } = {}) {
    const first = attempts[0] ?? { status: 1, records: [] };
    const retryRuns = attempts.slice(1);
    const initial = summarizeStimuli(first.records);
    const failures = initial.filter((entry) => !entry.passed);
    const { recovered, stillFailing } = verifyRetry(failures, retryRuns);
    const lines = [
        '## Vally evaluation results',
        '',
        `**${stillFailing.length} failed | ${initial.length - failures.length} passed first attempt | ${recovered.length} recovered after retry**`,
        '',
    ];
    const link = stepUrl ? `[Run Vally](${stepUrl})` : runUrl ? `[Workflow run](${runUrl})` : 'Run Vally';
    const executionErrors = new Set();
    for (const [index, attempt] of attempts.entries()) {
        if (attempt.error) executionErrors.add(`${index ? 'Retry' : 'First attempt'}: ${attempt.error}`);
        for (const record of attempt.records) {
            if (record.type !== 'run-summary') continue;
            for (const entry of record.evals ?? []) {
                if (entry.error) executionErrors.add(`${index ? 'Retry' : 'First attempt'}: ${entry.name}: ${entry.error}`);
            }
        }
        if (!attempt.error && attempt.records.at(-1)?.type !== 'run-summary') {
            executionErrors.add(`${index ? 'Retry' : 'First attempt'} did not produce a completed run summary (exit ${attempt.status}). ${extractLogError(log) ?? ''}`);
        }
    }
    if (!attempts.length || (!executionErrors.size
        && ((outcome === 'failure' && !stillFailing.length) || (first.status !== 0 && !failures.length)))) {
        executionErrors.add(extractLogError(log) ?? 'Evaluation process failed without a retryable result; see the pipeline step.');
    }
    for (const error of executionErrors) lines.push(`- **Error:** ${cell(error)} - ${link}`);
    if (executionErrors.size) lines.push('');

    const groups = new Map();
    for (const failure of stillFailing) {
        const retry = retryRuns.findLast((run) => run.records.some((trial) => matches(trial, failure)));
        const latestFailures = retry ? failedTrials(retry.records).filter((trial) => matches(trial, failure)) : [];
        const trials = latestFailures.length ? latestFailures
            : failedTrials(first.records).filter((trial) => matches(trial, failure));
        let note = '';
        if (retryRuns.length && !retry) note = 'Retry produced no matching result. ';
        else if (retry && !latestFailures.length) {
            note = `Retry did not confirm recovery (exit ${retry.status}, ${retry.records.at(-1)?.type === 'run-summary' ? 'complete' : 'incomplete'}); first failure: `;
        }
        for (const trial of trials) {
            const key = environment(trial);
            const rows = groups.get(key) ?? new Map();
            const detail = failureDetail(trial);
            const rowKey = JSON.stringify([trial.evalFilePath, trial.stimulus]);
            const row = rows.get(rowKey) ?? { evalFilePath: trial.evalFilePath, stimulus: trial.stimulus, graders: new Set(), messages: new Set(), attempt: latestFailures.length ? 'Retry' : 'First' };
            row.graders.add(detail.graders);
            row.messages.add(compact(note + detail.message));
            rows.set(rowKey, row);
            groups.set(key, rows);
        }
    }
    for (const [group, rows] of [...groups].sort(([a], [b]) => a.localeCompare(b))) {
        lines.push(`### ${cell(group)}`, '', '| Failed stimulus | Attempt | Failed graders | Error | Step |',
            '|---|---|---|---|---|');
        for (const row of [...rows.values()].sort((a, b) => a.stimulus.localeCompare(b.stimulus))) {
            const url = testUrl(row.evalFilePath, row.stimulus);
            const stimulus = url ? `[${cell(row.stimulus)}](${url})` : cell(row.stimulus);
            lines.push(`| ${stimulus} | ${row.attempt} | ${cell([...row.graders].join(', '))} | ${cell([...row.messages].join('; '))} | ${link} |`);
        }
        lines.push('');
    }
    if (!stillFailing.length && !executionErrors.size) lines.push('No unresolved evaluation failures.', '');
    lines.push('Only unresolved failures are listed. Full reports, all grader details, and trajectories are in the results artifact.', '');
    return lines.join('\n');
}

export function readAttempts(outputDir) {
    const manifest = join(outputDir, 'eval-attempts.json');
    if (!existsSync(manifest)) return [];
    return JSON.parse(readFileSync(manifest, 'utf8')).map((attempt) => ({
        status: attempt.status,
        error: attempt.error,
        records: attempt.files.flatMap((file) => readFileSync(join(outputDir, file), 'utf8')
            .split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line))),
    }));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    const outputDir = resolve(process.argv[2] ?? 'results');
    const logPath = process.env.VALLY_LOG;
    const jobsPath = process.env.VALLY_JOBS;
    const jobs = jobsPath ? JSON.parse(readFileSync(jobsPath, 'utf8')).flatMap((page) => page.jobs) : [];
    const stepUrl = findStepUrl(jobs);
    if (jobsPath && !stepUrl) console.warn('::warning::Could not locate the Run Vally step; linking to the workflow run instead.');
    const { GITHUB_SERVER_URL, GITHUB_REPOSITORY, GITHUB_SHA, GITHUB_WORKSPACE } = process.env;
    const sourceRootUrl = GITHUB_SERVER_URL && GITHUB_REPOSITORY && GITHUB_SHA
        ? `${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/blob/${GITHUB_SHA}` : undefined;
    const markdown = renderSummary(readAttempts(outputDir), {
        stepUrl,
        runUrl: process.env.VALLY_RUN_URL,
        outcome: process.env.VALLY_OUTCOME,
        log: logPath && existsSync(logPath) ? readFileSync(logPath, 'utf8') : '',
        testUrl: (file, stimulus) => findTestUrl(file, stimulus, { workspace: GITHUB_WORKSPACE, sourceRootUrl }),
    });
    mkdirSync(outputDir, { recursive: true });
    writeFileSync(join(outputDir, 'eval-summary.md'), markdown);
    if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, markdown);
    else console.log(markdown);
}
