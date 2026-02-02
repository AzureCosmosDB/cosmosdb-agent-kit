# Cosmos DB Agent Kit Testing Framework

This framework provides a structured approach for iteratively testing and improving the Cosmos DB Agent Kit skills.

---

## 🚀 QUICK START: Run a Test Iteration

**Copy and paste this prompt into a NEW chat session:**

```
I want to test the {scenario-name} scenario using {language}.

Read testing/README.md for complete instructions on running test iterations.
```

**Replace:**
- `{scenario-name}` with: `ecommerce-order-api`, `iot-device-telemetry`, `gaming-leaderboard`, `ai-chat-rag`, or `multitenant-saas`
- `{language}` with: `dotnet`, `java`, `python`, `nodejs`, `go`, or `rust`

**Examples:**
```
I want to test the ecommerce-order-api scenario using dotnet.
Read testing/README.md for complete instructions on running test iterations.
```

```
I want to test the ai-chat-rag scenario using python.
Read testing/README.md for complete instructions on running test iterations.
```

---

## 🤖 AGENT INSTRUCTIONS (Detailed)

**If you're an AI agent running a test iteration, follow these steps carefully:**

### ⚠️ CRITICAL: Load Skills FIRST

**Before building any application, you MUST load the Cosmos DB skills into your context.**

#### Option A: Read the AGENTS.md file directly (RECOMMENDED)
```
Read the file: skills/cosmosdb-best-practices/AGENTS.md
```
This file contains all 52+ rules. Read it completely before starting the iteration.

#### Option B: Reference the skill folder
If your agent supports workspace skills/instructions:
- **GitHub Copilot**: The `AGENTS.md` file in the workspace should auto-load
- **Cursor**: Add `skills/cosmosdb-best-practices/` to your context
- **Claude**: Use the file attachment or read the AGENTS.md file

#### Option C: Explicit instruction
Start your session with:
```
Before building this application, read and follow all rules in 
skills/cosmosdb-best-practices/AGENTS.md. Apply these Cosmos DB 
best practices throughout the implementation.
```

**Verify skills are loaded** by asking: "What are the Cosmos DB SDK best practices for connection mode?" 
If the agent mentions "Direct mode" and "singleton client", the skills are loaded.

---

### Running an Existing Scenario

1. **⚠️ LOAD THE SKILLS FIRST** (see above - this is mandatory!)

2. **List available scenarios:**
   ```
   testing/scenarios/
   ├── ecommerce-order-api/    ← E-commerce order management
   ├── iot-device-telemetry/   ← IoT time-series data
   ├── gaming-leaderboard/     ← Real-time leaderboards
   ├── ai-chat-rag/            ← AI chat with vector search
   └── multitenant-saas/       ← Multi-tenant SaaS app
   ```

3. **Check which iterations exist** by looking at `scenarios/<name>/iterations/`

4. **Read the SCENARIO.md** to understand requirements and get the prompt

5. **Create a new iteration folder:**
   ```
   scenarios/<name>/iterations/iteration-{NNN}-{language}/
   ```
   Where `{NNN}` is the next number and `{language}` is: `dotnet`, `java`, `python`, `nodejs`, `go`, or `rust`

6. **Build the app** using the prompt from SCENARIO.md (with skills loaded!)

7. **Test the app** - actually run it and verify endpoints work

8. **Document findings** in `ITERATION.md` inside the iteration folder

9. **Clean up the iteration folder** ⚠️ IMPORTANT:
   - Create `source-code.zip` containing ONLY source files (*.cs, *.java, *.py, etc. - NO bin/, obj/, target/, node_modules/, or DLL files)
   - **DELETE all source code files and folders after zipping**
   - **Final iteration folder should contain ONLY 2 files:**
     - `ITERATION.md` (documentation)
     - `source-code.zip` (source archive)

### Adding a New Scenario

1. **⚠️ LOAD THE SKILLS FIRST** (see above)
2. Copy `scenarios/_scenario-template.md` to `scenarios/<new-name>/SCENARIO.md`
3. Fill in the requirements, language suitability, and prompts
4. Create `scenarios/<new-name>/iterations/` folder
5. Run first iteration following steps above

---

## Purpose

The goal is to evaluate how well AI agents can build Cosmos DB applications using this skill kit, identify gaps, update the skills, and measure improvement over subsequent iterations.

## Supported Languages

| Language | SDK | Package | Typical Use Cases |
|----------|-----|---------|-------------------|
| **.NET** | Microsoft.Azure.Cosmos | `dotnet add package Microsoft.Azure.Cosmos` | Enterprise APIs, web apps |
| **Java** | azure-cosmos | Maven: `com.azure:azure-cosmos` | Enterprise, Spring Boot |
| **Python** | azure-cosmos | `pip install azure-cosmos` | AI/ML, data science, APIs |
| **Node.js** | @azure/cosmos | `npm install @azure/cosmos` | Serverless, web apps |
| **Go** | azcosmos | `go get github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos` | Cloud-native, microservices |
| **Rust** | azure_data_cosmos | `cargo add azure_data_cosmos` | Systems, high-performance |

## Directory Structure

```
testing/
├── README.md                    # This file (agent instructions)
├── IMPROVEMENTS-LOG.md          # Track all skill improvements
├── scenarios/
│   ├── _scenario-template.md    # Template for new scenarios
│   ├── _iteration-template.md   # Template for iteration docs
│   └── <scenario-name>/
│       ├── SCENARIO.md          # Requirements & prompts (DO NOT MODIFY)
│       └── iterations/
│           ├── iteration-001-dotnet/
│           │   ├── ITERATION.md      # Findings doc (KEEP)
│           │   └── source-code.zip   # Archived source (KEEP)
│           ├── iteration-001-python/
│           └── iteration-002-dotnet/
```

## The Iteration Loop

```
┌─────────────────────────────────────────────────────────────────┐
│  0. LOAD SKILLS: Read skills/cosmosdb-best-practices/AGENTS.md │
│     ⚠️ This step is MANDATORY - do not skip!                   │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Read SCENARIO.md for requirements and prompt               │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Create iteration folder: iteration-{N}-{lang}/             │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Build the app following the prompt                         │
│     • Apply Cosmos DB best practices FROM THE LOADED SKILLS    │
│     • Reference specific rules as you implement                │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. TEST THE APP                                               │
│     • Run it locally (with Cosmos DB Emulator)                 │
│     • Call all endpoints                                       │
│     • Verify data is persisted in Cosmos DB                    │
│     • Note any bugs or issues                                  │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Document findings in ITERATION.md                          │
│     • Bugs found                                               │
│     • Best practice gaps                                       │
│     • Score (1-10)                                             │
│     • Lessons learned (see Feedback Loop below!)               │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. ⚠️ CREATE NEW RULES (if gaps found)                        │
│     • If you discovered missing guidance, CREATE the rule NOW │
│     • Add rule to skills/cosmosdb-best-practices/rules/        │
│     • Run `npm run build` to regenerate AGENTS.md              │
│     • See "Continuous Improvement" section for details         │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. ⚠️ UPDATE IMPROVEMENTS-LOG.md (MANDATORY)                  │
│     • Add entry at TOP of Improvements section                │
│     • Include: scenario, iteration, issues, new rules created │
│     • Document lessons learned and files modified             │
│     • See IMPROVEMENTS-LOG.md format section for template     │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. Clean up iteration folder ⚠️ CRITICAL                      │
│     • Zip ONLY source files: *.cs, *.java, *.py, etc.         │
│     • DO NOT include: bin/, obj/, target/, node_modules/,     │
│       DLLs, .class files, or any build artifacts              │
│     • DELETE all source code after creating source-code.zip   │
│     • FINAL STATE: Only ITERATION.md + source-code.zip remain │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Continuous Improvement: The Feedback Loop

**⚠️ CRITICAL: Create new rules AND update IMPROVEMENTS-LOG.md DURING the iteration, not after!**

When you discover missing guidance or encounter issues that aren't covered by existing rules, **CREATE THE NEW RULE IMMEDIATELY** as part of your iteration work, and **UPDATE THE IMPROVEMENTS LOG** to track the improvement. This ensures the skill kit is continuously improved and documented.

### When to Create a New Rule (DO THIS DURING STEP 6)

Create a new rule if you encounter ANY of these situations:

1. **Build failures** due to missing configuration guidance
2. **Runtime errors** that could have been prevented with documentation
3. **SDK-specific quirks** not covered in existing rules
4. **Framework version requirements** (Java, Spring Boot, .NET, etc.)
5. **Workarounds discovered** through trial and error
6. **Performance issues** solved by specific patterns
7. **Configuration challenges** (emulator, SSL, environment setup)

**Rule of thumb**: If you had to search Stack Overflow or official docs to solve it, **create a rule for it**.

### Step-by-Step: Creating a New Rule During Your Iteration

### Step-by-Step: Creating a New Rule AND Updating the Log

#### 1. Identify the Gap

As you work through the iteration, note when you encounter:
- Bugs encountered - Were there patterns that caused issues?
- Workarounds discovered - Did you find solutions not documented in the rules?
- SDK-specific quirks - Did the SDK behave unexpectedly?
- Configuration challenges - Were there setup issues (emulator, SSL, env vars)?
- Missing guidance - What questions came up that the rules didn't answer?

#### 2. Check Existing Rules

#### 2. Check Existing Rules

Before creating a new rule, verify it doesn't already exist:

```
skills/cosmosdb-best-practices/rules/
├── model-*.md       # Data modeling rules
├── partition-*.md   # Partition key rules
├── query-*.md       # Query optimization rules
├── sdk-*.md         # SDK best practices
├── index-*.md       # Indexing strategies
├── throughput-*.md  # Throughput & scaling
├── global-*.md      # Global distribution
├── monitoring-*.md  # Monitoring & diagnostics
└── pattern-*.md     # Design patterns
```

Use grep/search to check: `grep -r "Spring Boot" skills/cosmosdb-best-practices/rules/`

#### 3. Create the New Rule File

If you identify a gap, **create a new rule file immediately** following this template:

```markdown
---
title: Short description of the rule
impact: CRITICAL | HIGH | MEDIUM | LOW
impactDescription: brief explanation of impact
tags: category, sdk, relevant, keywords
---

## Rule Title

Brief description of the problem this rule addresses.

**Problem:**
\`\`\`language
// Code showing the problem
\`\`\`

**Solution:**
\`\`\`language
// Code showing the correct approach
\`\`\`

**Key Points:**
- Important takeaway 1
- Important takeaway 2

Reference: [Link to official docs](url)
```

**Example filename**: `skills/cosmosdb-best-practices/rules/sdk-java-spring-boot-versions.md`

#### 4. Choose the Right Category/Prefix

| Prefix | Category | When to Use |
|--------|----------|-------------|
| `model-` | Data Modeling | Document structure, embedding vs referencing |
| `partition-` | Partition Key Design | Partition key selection, distribution |
| `query-` | Query Optimization | Query patterns, filtering, pagination |
| `sdk-` | SDK Best Practices | Client configuration, connection, retries |
| `index-` | Indexing Strategies | Index policies, composite indexes |
| `throughput-` | Throughput & Scaling | RU provisioning, autoscale |
| `global-` | Global Distribution | Multi-region, consistency |
| `monitoring-` | Monitoring & Diagnostics | Logging, metrics, alerts |
| `pattern-` | Design Patterns | Architecture patterns (e.g., Change Feed) |

#### 5. Regenerate AGENTS.md

**⚠️ CRITICAL**: After creating the new rule file, you MUST regenerate AGENTS.md:

```bash
cd c:\cosmos\gen-ai\skills\cosmosdb-agent-kit
npm run build
```

This compiles all individual rule files into the master `AGENTS.md` file that agents load.

#### 6. ⚠️ Update IMPROVEMENTS-LOG.md (MANDATORY)

**AFTER creating new rules, you MUST update the improvements log.** This is how we track the evolution of the skill kit over time.

Add an entry at the **TOP** of the "Improvements" section in `testing/IMPROVEMENTS-LOG.md`:

```markdown
#### YYYY-MM-DD: Iteration NNN - Scenario Name (Language / Framework)

- **Scenario**: scenario-name
- **Iteration**: NNN-language
- **Result**: ✅ SUCCESSFUL or ❌ FAILED
- **Score**: N/10
- **Key Achievement**: Brief summary of what was accomplished/discovered

**Critical Discovery** (if applicable):
- What major gap was found
- Impact of the gap
- How it was resolved

**New Rules Created** (if any):
1. **rule-filename.md** (IMPACT_LEVEL)
   - Brief description of what the rule covers
   - Why it was needed

**Issues Encountered & Resolved**:
1. **Issue Name**
   - Problem: What went wrong
   - Error: Specific error message if applicable
   - Solution: How it was fixed
   - Status: ✅ RESOLVED or ⚠️ PARTIAL or ❌ UNRESOLVED

**Test Results**:
- ✅ What worked
- ❌ What failed
- ⚠️ What needs attention

**Lessons Learned**:
- Key takeaway 1
- Key takeaway 2

**FILES MODIFIED**:
- ✅ path/to/new-rule.md - NEW (IMPACT)
- ✅ path/to/updated-file.md - UPDATED
- ✅ AGENTS.md - Recompiled (X total rules)
```

**See existing entries in `testing/IMPROVEMENTS-LOG.md` for full examples.**

**⚠️ IMPORTANT**: Every completed iteration MUST have a corresponding entry in IMPROVEMENTS-LOG.md. This is not optional - it's how we measure and track progress.

#### 7. Verify Your Changes

```markdown
## 2026-01-29 - Iteration 002 (Java)

### New Rules Created
- `sdk-java-spring-boot-versions.md` - **CRITICAL**: Spring Boot version requirements
  - Problem: Spring Boot 3.x requires Java 17+, build fails with Java 11
  - Impact: Prevents immediate build failures for all Java developers
  
### Lessons Learned
- Framework version compatibility is foundational - must be documented
```

#### 7. Update Your ITERATION.md

Reference the new rule you created in your iteration documentation:

```markdown
**Proposed Skill Improvements**:

1. ✅ **CREATED: `sdk-java-spring-boot-versions.md`** (CRITICAL)
   - Created during iteration to address build failure
   - Documents Spring Boot 3.x → Java 17+ requirement
   - Prevents similar failures in future iterations
```

### Complete Example: iteration-002-java

This iteration discovered that Spring Boot 3.2.1 requires Java 17+, causing build failures. The agent:

1. **Identified the gap**: Build failed with "wrong version 61.0, should be 55.0"
2. **Checked existing rules**: No rule covered Java/Spring Boot version requirements
3. **Created the rule**: `sdk-java-spring-boot-versions.md` with compatibility matrix
4. **Regenerated AGENTS.md**: Ran `npm run build` to compile the new rule
5. **Updated IMPROVEMENTS-LOG.md**: Documented the new CRITICAL rule
6. **Updated ITERATION.md**: Marked the rule as ✅ CREATED during iteration

**Result**: Future Java iterations will have this guidance available immediately, preventing the same build failure.

---

## 📊 Step 7: Review After Iteration (Summary Only)

| Iteration | Issue Found | Rule Created |
|-----------|-------------|--------------|
| 001-dotnet | Enum queries returned empty | `sdk-serialization-enums.md` |
| 003-java | SSL handshake failures | `sdk-emulator-ssl.md` |
| 003-java | createItem returned null | `sdk-java-content-response.md` |
| 004-python | System env vars overrode .env | `sdk-local-dev-config.md` |
| Multiple | Cross-partition admin queries | `pattern-change-feed-materialized-views.md` |

### Questions to Ask After Each Iteration

1. ❓ **Was there a bug that a rule could have prevented?**
   → Create a new rule with the problem and solution

2. ❓ **Did you discover a workaround not in the docs?**
   → Document it as a rule for future iterations

3. ❓ **Was there SDK-specific behavior that surprised you?**
   → Add to existing SDK rule or create new one

4. ❓ **Did you spend time debugging configuration issues?**
   → Create a rule to save time for future developers

5. ❓ **Did you find a pattern that could benefit other scenarios?**
   → Create a `pattern-*.md` rule

---

## Scoring Guide

| Score | Description |
|-------|-------------|
| 1-3 | Major issues, app doesn't work, significant intervention needed |
| 4-6 | Functional but with notable gaps or bugs |
| 7-8 | Good result with minor issues |
| 9-10 | Excellent, production-quality code |

## Completed Iterations

| Scenario | Language | Iteration | Skills Loaded? | Score | Key Findings |
|----------|----------|-----------|----------------|-------|--------------|
| ecommerce-order-api | .NET | 001 | ❌ NO (baseline) | 6/10 | Enum serialization bug, no pagination |

> **Note**: Iteration 001 was run WITHOUT skills loaded. This serves as a baseline.
> Future iterations should load skills first to test their effectiveness.

## Next Actions

Based on findings, these actions are tracked:

- [x] ✅ Created `sdk-serialization-enums.md` rule (prevents enum query bug)
- [x] ✅ Added section 4.10 to AGENTS.md for enum serialization
- [ ] Investigate why agent didn't apply existing `query-pagination.md` rule
- [ ] Investigate why agent didn't apply existing `monitoring-ru-consumption.md` rule

## Testing Checklist for Agents

When completing an iteration, verify:

### Build & Test
- [ ] **⚠️ Skills were loaded BEFORE building** (read AGENTS.md first!)
- [ ] App compiles/builds without errors
- [ ] App runs locally with Cosmos DB Emulator
- [ ] All CRUD endpoints work
- [ ] Data persists to Cosmos DB
- [ ] Query endpoints return correct data
- [ ] No obvious security issues

### Documentation
- [ ] ITERATION.md documents all findings
- [ ] ITERATION.md notes which skills were applied/not applied
- [ ] ITERATION.md includes "Lessons Learned" section
- [ ] Score assigned with justification

### Feedback Loop (NEW!)
- [ ] **Reviewed lessons learned for potential new rules**
- [ ] **Checked if issues could have been prevented by a rule**
- [ ] **Created new rules for undocumented patterns/issues**
- [ ] **Updated IMPROVEMENTS-LOG.md with new rules**

### Cleanup
- [ ] Source code is zipped to `source-code.zip` (source files ONLY - no bin/, obj/, target/, node_modules/, DLLs, .class files)
- [ ] **All source code files and folders are DELETED after zipping**
- [ ] **Iteration folder contains ONLY 2 files: ITERATION.md and source-code.zip**
- [ ] Build artifacts removed (verify no bin/, obj/, node_modules/, target/ folders remain)
