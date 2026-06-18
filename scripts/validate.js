/**
 * Validates rule files have correct frontmatter
 * 
 * Usage: node scripts/validate.js [skill-name]
 * 
 * If skill-name is provided, only that skill is validated.
 * If omitted, all skills in skills/ are validated.
 */

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const { glob } = require('glob');

const SKILLS_ROOT = path.join(__dirname, '..', 'skills');

const VALID_IMPACTS = ['CRITICAL', 'HIGH', 'MEDIUM-HIGH', 'MEDIUM', 'LOW-MEDIUM', 'LOW'];

function normalizeTags(tags) {
    if (Array.isArray(tags)) {
        return tags
            .map(tag => String(tag).trim())
            .filter(Boolean);
    }

    if (typeof tags === 'string') {
        return tags
            .split(',')
            .map(tag => tag.trim())
            .filter(Boolean);
    }

    return null;
}

async function validateRules() {
    const specificSkill = process.argv[2];
    let skills;

    if (specificSkill) {
        const skillDir = path.join(SKILLS_ROOT, specificSkill, 'rules');
        if (!fs.existsSync(skillDir)) {
            console.error(`✗ Skill not found or has no rules: ${specificSkill}`);
            process.exit(1);
        }
        skills = [{ name: specificSkill, rulesDir: skillDir }];
    } else {
        skills = fs.readdirSync(SKILLS_ROOT)
            .filter(name => {
                const rulesDir = path.join(SKILLS_ROOT, name, 'rules');
                return fs.existsSync(rulesDir) && fs.statSync(path.join(SKILLS_ROOT, name)).isDirectory();
            })
            .map(name => ({ name, rulesDir: path.join(SKILLS_ROOT, name, 'rules') }));
    }

    let totalErrors = 0;
    let totalValidated = 0;

    for (const skill of skills) {
        const RULES_DIR = skill.rulesDir;
        const files = await glob('*.md', { cwd: RULES_DIR });
        let errors = 0;
        let validated = 0;

    for (const file of files) {
        // Skip template and sections
        if (file.startsWith('_')) continue;

        const filepath = path.join(RULES_DIR, file);
        const content = fs.readFileSync(filepath, 'utf8');
        const { data, content: body } = matter(content);

        const fileErrors = [];

        // Check required frontmatter
        if (!data.title) fileErrors.push('Missing title');
        if (!data.impact) fileErrors.push('Missing impact');
        else if (!VALID_IMPACTS.includes(data.impact)) {
            fileErrors.push(`Invalid impact "${data.impact}". Must be one of: ${VALID_IMPACTS.join(', ')}`);
        }
        if (!data.impactDescription) fileErrors.push('Missing impactDescription');
        const tags = normalizeTags(data.tags);
        if (!tags || tags.length === 0) fileErrors.push('Missing or invalid tags');

        // Check content has Incorrect and Correct sections
        if (!body.includes('**Incorrect')) {
            fileErrors.push('Missing **Incorrect** section');
        }
        if (!body.includes('**Correct')) {
            fileErrors.push('Missing **Correct** section');
        }

        // Check content has code blocks
        if (!body.includes('```')) {
            fileErrors.push('Missing code examples');
        }

        if (fileErrors.length > 0) {
            console.error(`✗ [${skill.name}] ${file}:`);
            fileErrors.forEach(e => console.error(`  - ${e}`));
            errors += fileErrors.length;
        } else {
            validated++;
        }
    }

        console.log(`✓ [${skill.name}] ${validated} rules validated`);
        totalErrors += errors;
        totalValidated += validated;
    }

    console.log(`\n${totalValidated} rules validated successfully across ${skills.length} skill(s)`);
    if (totalErrors > 0) {
        console.error(`${totalErrors} errors found`);
        process.exit(1);
    }
}

validateRules().catch(console.error);
