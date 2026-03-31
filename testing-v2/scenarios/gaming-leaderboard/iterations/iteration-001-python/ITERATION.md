# iteration-001-python - Python Gaming Leaderboard

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

**Pass rate: 22.3%** (21/94 tests passed (22.3%))

| Status | Count |
|--------|-------|
| Passed | 21 |
| Failed | 2 |
| Errors | 70 |
| Skipped | 1 |

### Failures

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayer::test_get_existing_player**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayer::test_get_player_has_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayer::test_get_player_stats_updated_after_scores**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestSubmitScore::test_submit_score_returns_201**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestSubmitScore::test_submit_score_response_has_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestSubmitScore::test_submit_score_returns_correct_data**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_returns_200**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_returns_array**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_entries_have_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_sorted_descending**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_ranks_sequential**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_top_player_is_highest_scorer**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_respects_top_parameter**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_returns_200**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_only_contains_region_players**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_sorted_descending**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_entries_have_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_returns_200**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_has_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_correct_for_top_player**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_neighbors_is_array**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_neighbors_have_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_returns_200**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_returns_array**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_entries_have_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_contains_all_player_scores**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_ordered_by_most_recent_first**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_respects_limit**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_only_shows_own_scores**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_returns_200**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_response_has_required_fields**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_reflects_new_display_name**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_preserves_stats**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestDeletePlayer::test_delete_player_returns_204**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestDeletePlayer::test_deleted_player_returns_404_on_get**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestContainerDesign::test_has_multiple_containers_or_synthetic_keys**
  > Failed: Only one container with a simple partition key. Leaderboard systems need different access patterns: player lookup (by playerId) and ranking queries (by leaderboard scope). Use multiple contain

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestContainerDesign::test_leaderboard_container_uses_synthetic_key**
  > Failed: Leaderboard container 'leaderboard' uses /playerId as partition key. This makes top-N ranking queries cross-partition (expensive). Use a synthetic key like /leaderboardKey = 'global_weekly' so

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestPlayerScoreSerialization::test_scores_stored_as_numbers**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestPlayerScoreSerialization::test_etag_present_on_player_documents**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_type_discriminator**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_schema_version**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_player_stats_stored_correctly**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_leaderboard_entries_denormalized**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_synthetic_partition_key_value_format**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_data_integrity.TestDataPersistence::test_player_document_exists_in_cosmos**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_missing_player_id_returns_4xx**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_missing_score_returns_4xx**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_negative_value_returns_4xx**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_for_nonexistent_player_returns_4xx**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_average_score_mathematically_correct**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_total_games_count_correct**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_best_score_is_maximum**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_player_with_single_score_stats**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_new_score_updates_stats**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDataTypeCorrectness::test_player_stats_types**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDataTypeCorrectness::test_leaderboard_entry_types**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDataTypeCorrectness::test_score_submission_returns_correct_types**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_score_reflected_in_leaderboard**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_regional_filter_matches_stored_region**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_player_rank_score_matches_leaderboard**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_empty_region_leaderboard**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_leaderboard_no_duplicate_players**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_top_parameter_zero_returns_empty**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_top_parameter_one**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_zero_score_submission**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestRapidOperations::test_rapid_score_submissions_all_counted**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestRapidOperations::test_concurrent_score_submissions_all_counted**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestLeaderboardTiebreaking::test_tied_scores_sorted_by_display_name_ascending**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestLeaderboardTiebreaking::test_tied_scores_have_sequential_ranks**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_updated_region_reflected_in_regional_leaderboard**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_deleted_player_removed_from_leaderboard**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

- **testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_deleted_player_scores_not_in_history**
  > failed on setup with "AssertionError: Failed to submit score for player-001: 500 Internal Server Error
assert 500 == 201
 +  where 500 = <Response [500]>.status_code"

## Source Files

Source code archived in `source-code.zip` (6 files).

## Build & Startup Signals

- **Build**: PASS
- **Startup**: PASS

## Results by Category

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| api_contract | 10 | 35 | 0 |
| build_startup | 2 | 0 | 0 |
| cosmos_infrastructure | 3 | 9 | 1 |
| data_integrity | 4 | 1 | 0 |
| robustness | 4 | 27 | 0 |

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| API Conformance | 1/10 | 22.3% pass rate; 9 infrastructure failures |
| **Overall** | **1/10** | **21/94 tests passed (22.3%)** |
