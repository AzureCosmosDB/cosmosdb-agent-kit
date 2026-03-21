# Iteration [NNN] - [Language] [Scenario Name]

## Metadata
- **Date**: YYYY-MM-DD
- **Language/SDK**: [e.g., .NET 8 / Microsoft.Azure.Cosmos 3.57.0]
- **Skill Version**: [Git commit hash or "pre-release"]
- **Agent**: [e.g., GitHub Copilot (Claude Opus 4.5)]
- **Tester**: [Your name or "automated"]

## ⚠️ Skills Verification

**Were skills loaded before building?** ✅ Yes / ❌ No

**How were skills loaded?**
- [ ] Read `skills/cosmosdb-best-practices/AGENTS.md` directly
- [ ] Skills auto-loaded from workspace
- [ ] Explicit instruction to follow skills
- [ ] Other: [describe]

**Verification question asked?** [e.g., "What connection mode should I use?" → Agent said "Direct mode"]

> **Note**: If skills were NOT loaded, this iteration tests baseline agent knowledge, 
> not the skill kit effectiveness. Mark findings accordingly.

## Prompt Used

```
[Copy the exact prompt from SCENARIO.md that was used]
```

## What the Agent Produced

### Data Model
- ✅/❌ [Observation about data model choices]
- ✅/❌ [Embedded vs referenced decisions]
- ⚠️ [Warnings or concerns]

### Container Configuration
- ✅/❌ [Partition key choice]
- ✅/❌ [Indexing policy]
- ❌ [Missing configurations]

### Repository Layer
- ✅/❌ [Query patterns]
- ✅/❌ [Point reads with partition key]
- ❌ [Missing patterns]

### SDK Usage
- ✅/❌ [Singleton client]
- ✅/❌ [Connection mode]
- ❌ [Missing best practices]

## Build Status
- **Initial Build**: ✅ Succeeded / ❌ Failed ([reason])
- **After Fixes**: ✅ Succeeded / ❌ Failed
- **Runtime Test**: ✅ Performed / ❌ Not performed

## Runtime Test Results

### Tests Passed ✅
| Endpoint | Method | Result |
|----------|--------|--------|
| `/api/...` | GET/POST | [Result] |

### Tests Failed ❌
| Endpoint | Method | Issue |
|----------|--------|-------|
| `/api/...` | GET | [What went wrong] |

### Bugs Found 🐛
[Describe any bugs discovered during testing]

## Gaps Identified

### Critical Gaps (functionality issues)
1. [Gap that prevents the app from working correctly]

### Best Practice Gaps (suboptimal but works)
1. [Missing best practice]
2. [Another missing practice]

### Knowledge Gaps (agent didn't know/mention)
1. [Topic the agent didn't address]

## Recommendations for Skill Improvements

### High Priority
1. [Rule to add or update]

### Medium Priority
1. [Rule to add or update]

### Low Priority
1. [Rule to add or update]

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| Data Model | X/10 | [Brief note] |
| Partition Key | X/10 | [Brief note] |
| Indexing | X/10 | [Brief note] |
| SDK Usage | X/10 | [Brief note] |
| Query Patterns | X/10 | [Brief note] |
| **Overall** | **X/10** | [Summary] |

## Next Steps
1. [What should be done before next iteration]
2. [Skills to update]
3. [Tests to add]
