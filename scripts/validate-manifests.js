/**
 * Validates that every vendor plugin manifest is well-formed and version-aligned.
 *
 * Source of truth: the "version" field in root package.json.
 * Every JSON manifest must parse, declare the same version, and point "skills"
 * at an existing directory. apm.yml is checked for a matching top-level version.
 *
 * Usage: node scripts/validate-manifests.js
 * Exits non-zero (with descriptive messages) on any mismatch or parse error.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');

// JSON manifests that must share the package version.
const JSON_MANIFESTS = [
    'package.json',
    'plugin.json',
    'gemini-extension.json',
    path.join('.claude-plugin', 'plugin.json'),
    path.join('.codex-plugin', 'plugin.json'),
    path.join('.cursor-plugin', 'plugin.json'),
    path.join('.kimi-plugin', 'plugin.json'),
];

// YAML manifests checked with a simple top-level version regex (no yaml dep).
const YAML_MANIFESTS = ['apm.yml'];

const errors = [];

function readVersionFromJson(relPath) {
    const abs = path.join(ROOT, relPath);
    if (!fs.existsSync(abs)) {
        errors.push(`Missing manifest: ${relPath}`);
        return null;
    }
    let parsed;
    try {
        parsed = JSON.parse(fs.readFileSync(abs, 'utf8'));
    } catch (err) {
        errors.push(`Invalid JSON in ${relPath}: ${err.message}`);
        return null;
    }
    if (!parsed.version) {
        errors.push(`No "version" field in ${relPath}`);
    }
    // If a manifest declares a skills path, it must exist.
    if (typeof parsed.skills === 'string') {
        const skillsAbs = path.join(ROOT, parsed.skills);
        if (!fs.existsSync(skillsAbs)) {
            errors.push(`${relPath} "skills" path does not exist: ${parsed.skills}`);
        }
    }
    return parsed.version || null;
}

function readVersionFromYaml(relPath) {
    const abs = path.join(ROOT, relPath);
    if (!fs.existsSync(abs)) {
        errors.push(`Missing manifest: ${relPath}`);
        return null;
    }
    const content = fs.readFileSync(abs, 'utf8');
    const match = content.match(/^version:\s*["']?([^"'\r\n]+)["']?\s*$/m);
    if (!match) {
        errors.push(`No top-level "version" found in ${relPath}`);
        return null;
    }
    return match[1].trim();
}

// package.json is the source of truth.
const expected = readVersionFromJson('package.json');
if (!expected) {
    console.error('✗ Cannot determine expected version from package.json');
    console.error(errors.map(e => `  - ${e}`).join('\n'));
    process.exit(1);
}

for (const relPath of JSON_MANIFESTS) {
    if (relPath === 'package.json') continue;
    const version = readVersionFromJson(relPath);
    if (version && version !== expected) {
        errors.push(`Version mismatch in ${relPath}: found ${version}, expected ${expected}`);
    }
}

for (const relPath of YAML_MANIFESTS) {
    const version = readVersionFromYaml(relPath);
    if (version && version !== expected) {
        errors.push(`Version mismatch in ${relPath}: found ${version}, expected ${expected}`);
    }
}

if (errors.length > 0) {
    console.error(`✗ Manifest validation failed (expected version ${expected}):`);
    console.error(errors.map(e => `  - ${e}`).join('\n'));
    console.error('\nRun `npm run version <newVersion>` to bump all manifests atomically.');
    process.exit(1);
}

console.log(`✓ All vendor manifests valid and aligned at version ${expected}`);
