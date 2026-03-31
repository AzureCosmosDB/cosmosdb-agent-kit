# iteration-002-python - Python Gaming Leaderboard

## Metadata
- **Date**: 2026-03-31
- **Language/SDK**: Python
- **Agent**: GitHub Copilot (automated iteration)
- **Tester**: Automated CI
- **Run Type**: Normal run (skills loaded)

## Skills Verification

**Were skills loaded before building?** Yes (via issue prompt referencing AGENTS.md)

## Cosmos DB Patterns Detected

| Pattern | Status | Related Rule |
|---------|--------|--------------|
| Singleton CosmosClient | Detected | `sdk-singleton-client` |
| Direct connection mode | Not detected | `sdk-connection-mode` |
| Gateway connection mode | Not detected | `sdk-connection-mode` |
| Partition key configured | Detected | `partition-high-cardinality` |
| Bulk operations | Not detected | `sdk-bulk-operations` |
| ETag optimistic concurrency | Detected | `sdk-etag-concurrency` |
| Point reads (by ID + partition key) | Detected | `query-avoid-scans` |
| Cross-partition queries | Detected | `query-avoid-cross-partition` |
| Custom indexing policy | Detected | `index-exclude-unused` |
| Throughput configuration | Not detected | `throughput-provision-rus` |
| Change feed usage | Not detected | `pattern-change-feed` |
| Diagnostics/logging | Not detected | `sdk-diagnostics` |

## Test Results

**Pass rate: 63.8%** (60/94 tests passed (63.8%))

| Status | Count |
|--------|-------|
| Passed | 60 |
| Failed | 33 |
| Errors | 0 |
| Skipped | 1 |

### Failures

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_returns_200**
  > AssertionError: GET /api/leaderboards/global should return 200, got 500
assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_returns_array**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_entries_have_required_fields**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_sorted_descending**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_ranks_sequential**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_top_player_is_highest_scorer**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_respects_top_parameter**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_returns_200**
  > AssertionError: GET /api/leaderboards/regional/US should return 200, got 500
assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_only_contains_region_players**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_sorted_descending**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_entries_have_required_fields**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_returns_200**
  > AssertionError: GET /api/players/player-001/rank should return 200, got 500
assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_has_required_fields**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_correct_for_top_player**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_neighbors_is_array**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_neighbors_have_required_fields**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestContainerDesign::test_has_multiple_containers_or_synthetic_keys**
  > Failed: Only one container with a simple partition key. Leaderboard systems need different access patterns: player lookup (by playerId) and ranking queries (by leaderboard scope). Use multiple contain

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestContainerDesign::test_leaderboard_container_uses_synthetic_key**
  > Failed: Leaderboard container 'leaderboard' uses /playerId as partition key. This makes top-N ranking queries cross-partition (expensive). Use a synthetic key like /leaderboardKey = 'global_weekly' so

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_schema_version**
  > Failed: No documents have a schema version field. (Rule: model-schema-versioning)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_negative_value_returns_4xx**
  > AssertionError: Negative score should return 4xx, got 201. Scores should be positive integers per the contract.
assert 400 <= 201
 +  where 201 = <Response [201]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDuplicateHandling::test_create_duplicate_player_does_not_return_500**
  > AssertionError: Duplicate player creation returned 500 — server crashed. Expected 409 Conflict or idempotent 200/201. Response: Internal Server Error
assert 500 != 500
 +  where 500 = <Response [500]>

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDataTypeCorrectness::test_leaderboard_entry_types**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_score_reflected_in_leaderboard**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_regional_filter_matches_stored_region**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_player_rank_score_matches_leaderboard**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_empty_region_leaderboard**
  > AssertionError: Empty region leaderboard should return 200, got 500. Must return empty array for regions with no players.
assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_leaderboard_no_duplicate_players**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_top_parameter_one**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestRapidOperations::test_concurrent_score_submissions_all_counted**
  > AssertionError: After 15 concurrent submissions, totalGames should be 15, got 1. Lost 14 updates. This is the classic read-modify-write race condition — use ETags/optimistic concurrency to prevent los

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestLeaderboardTiebreaking::test_tied_scores_sorted_by_display_name_ascending**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestLeaderboardTiebreaking::test_tied_scores_have_sequential_ranks**
  > assert 500 == 200
 +  where 500 = <Response [500]>.status_code

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_updated_region_reflected_in_regional_leaderboard**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_deleted_player_removed_from_leaderboard**
  > requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

## Source Files

Source code archived in `source-code.zip` (8 files).

## Build & Startup Signals

- **Build**: PASS
- **Startup**: PASS

## Results by Category

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| api_contract | 29 | 16 | 0 |
| build_startup | 2 | 0 | 0 |
| cosmos_infrastructure | 9 | 3 | 1 |
| data_integrity | 5 | 0 | 0 |
| robustness | 17 | 14 | 0 |

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| API Conformance | 5/10 | 63.8% pass rate; 3 infrastructure failures |
| **Overall** | **5/10** | **60/94 tests passed (63.8%)** |
