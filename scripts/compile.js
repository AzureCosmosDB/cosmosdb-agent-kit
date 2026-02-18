/**
 * Compiles individual rule files into AGENTS.md
 * 
 * Usage: node scripts/compile.js
 */

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const { glob } = require('glob');

const SKILL_DIR = path.join(__dirname, '..', 'skills', 'cosmosdb-best-practices');
const RULES_DIR = path.join(SKILL_DIR, 'rules');
const OUTPUT_FILE = path.join(SKILL_DIR, 'AGENTS.md');

// Section order and metadata
const SECTIONS = [
    { prefix: 'model-', name: 'Data Modeling', number: 1, impact: 'CRITICAL' },
    { prefix: 'partition-', name: 'Partition Key Design', number: 2, impact: 'CRITICAL' },
    { prefix: 'query-', name: 'Query Optimization', number: 3, impact: 'HIGH' },
    { prefix: 'sdk-', name: 'SDK Best Practices', number: 4, impact: 'HIGH' },
    { prefix: 'index-', name: 'Indexing Strategies', number: 5, impact: 'MEDIUM-HIGH' },
    { prefix: 'throughput-', name: 'Throughput & Scaling', number: 6, impact: 'MEDIUM' },
    { prefix: 'global-', name: 'Global Distribution', number: 7, impact: 'MEDIUM' },
    { prefix: 'monitoring-', name: 'Monitoring & Diagnostics', number: 8, impact: 'LOW-MEDIUM' },
    { prefix: 'pattern-', name: 'Design Patterns', number: 9, impact: 'HIGH' }
];

async function compileRules() {
    const metadata = JSON.parse(fs.readFileSync(path.join(SKILL_DIR, 'metadata.json'), 'utf8'));
    
    let output = `# Azure Cosmos DB Best Practices

**Version ${metadata.version}**  
${metadata.organization}  
${metadata.date}

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

${metadata.abstract}

---

## Table of Contents

`;

    // First pass: collect all rules and build TOC
    const allRules = [];
    
    for (const section of SECTIONS) {
        const files = await glob(`${section.prefix}*.md`, { cwd: RULES_DIR });
        const rules = [];
        
        for (const file of files.sort()) {
            const content = fs.readFileSync(path.join(RULES_DIR, file), 'utf8');
            const { data, content: body } = matter(content);
            rules.push({ file, data, body });
        }
        
        allRules.push({ section, rules });
        
        // Add to TOC
        const sectionAnchor = section.name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
        output += `${section.number}. [${section.name}](#${section.number}-${sectionAnchor}) — **${section.impact}**\n`;
        
        rules.forEach((rule, index) => {
            const ruleNumber = `${section.number}.${index + 1}`;
            const ruleAnchor = rule.data.title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
            output += `   - ${ruleNumber} [${rule.data.title}](#${ruleNumber.replace('.', '')}-${ruleAnchor})\n`;
        });
    }

    output += '\n---\n\n';

    // Second pass: write full content
    for (const { section, rules } of allRules) {
        output += `## ${section.number}. ${section.name}\n\n`;
        output += `**Impact: ${section.impact}**\n\n`;
        
        rules.forEach((rule, index) => {
            const ruleNumber = `${section.number}.${index + 1}`;
            output += `### ${ruleNumber} ${rule.data.title}\n\n`;
            output += `**Impact: ${rule.data.impact}** (${rule.data.impactDescription})\n\n`;
            output += rule.body.trim() + '\n\n';
        });

        output += '---\n\n';
    }

    // Add references
    output += `## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
`;

    fs.writeFileSync(OUTPUT_FILE, output);
    console.log(`✓ Compiled ${allRules.reduce((sum, s) => sum + s.rules.length, 0)} rules to AGENTS.md`);
}

compileRules().catch(console.error);
