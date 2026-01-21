/**
 * Validates rule files have correct frontmatter
 * 
 * Usage: node scripts/validate.js
 */

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const { glob } = require('glob');

const RULES_DIR = path.join(__dirname, '..', 'skills', 'cosmosdb-best-practices', 'rules');

const VALID_IMPACTS = ['CRITICAL', 'HIGH', 'MEDIUM-HIGH', 'MEDIUM', 'LOW-MEDIUM', 'LOW'];

async function validateRules() {
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
        if (!data.tags || !Array.isArray(data.tags)) fileErrors.push('Missing or invalid tags array');

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
            console.error(`✗ ${file}:`);
            fileErrors.forEach(e => console.error(`  - ${e}`));
            errors += fileErrors.length;
        } else {
            validated++;
        }
    }

    console.log(`\n${validated} rules validated successfully`);
    if (errors > 0) {
        console.error(`${errors} errors found`);
        process.exit(1);
    }
}

validateRules().catch(console.error);
