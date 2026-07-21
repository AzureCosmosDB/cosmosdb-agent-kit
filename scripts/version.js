// Bumps version across all manifest files
// Usage: node scripts/version.js <new-version>
// Example: node scripts/version.js 1.1.0

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');

const newVersion = process.argv[2];

if (!newVersion || !/^\d+\.\d+\.\d+$/.test(newVersion)) {
    console.error('Usage: node scripts/version.js <semver>');
    console.error('Example: node scripts/version.js 1.1.0');
    process.exit(1);
}

function updateJsonFile(filePath) {
    if (!fs.existsSync(filePath)) return false;
    const content = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const oldVersion = content.version;
    content.version = newVersion;
    fs.writeFileSync(filePath, JSON.stringify(content, null, 2) + '\n');
    console.log('  ' + path.relative(ROOT, filePath) + ': ' + oldVersion + ' -> ' + newVersion);
    return true;
}

function updateYamlVersion(filePath) {
    if (!fs.existsSync(filePath)) return false;
    let content = fs.readFileSync(filePath, 'utf8');
    const oldContent = content;
    content = content.replace(/^version:\s*.+$/m, 'version: ' + newVersion);
    if (content === oldContent) return false;
    fs.writeFileSync(filePath, content);
    console.log('  ' + path.relative(ROOT, filePath) + ': -> ' + newVersion);
    return true;
}

console.log('\nBumping version to ' + newVersion + '\n');

// Root manifests
updateJsonFile(path.join(ROOT, 'package.json'));
updateJsonFile(path.join(ROOT, 'plugin.json'));
updateJsonFile(path.join(ROOT, 'gemini-extension.json'));
updateJsonFile(path.join(ROOT, '.claude-plugin', 'plugin.json'));
updateJsonFile(path.join(ROOT, '.codex-plugin', 'plugin.json'));
updateJsonFile(path.join(ROOT, '.cursor-plugin', 'plugin.json'));
updateJsonFile(path.join(ROOT, '.kimi-plugin', 'plugin.json'));
updateYamlVersion(path.join(ROOT, 'apm.yml'));

// Skill metadata files
const skillsDir = path.join(ROOT, 'skills');
if (fs.existsSync(skillsDir)) {
    for (const skill of fs.readdirSync(skillsDir)) {
        const metadataPath = path.join(skillsDir, skill, 'metadata.json');
        updateJsonFile(metadataPath);
    }
}

console.log('\nDone. To release:\n');
console.log('  git add -A');
console.log('  git commit -m "chore: release v' + newVersion + '"');
console.log('  git tag v' + newVersion);
console.log('  git push origin main --tags');
console.log('');
