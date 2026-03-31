# Batch Test Results: Gaming Leaderboard

## Metadata
- **Date**: 2026-03-31
- **Scenario**: gaming-leaderboard
- **Language**: python
- **Skills loaded**: Yes (skills loaded)
- **Iterations**: 5
- **Batch issue**: #80
- **Child PRs**: 86,87,90,88,89

## Aggregate Summary

| Metric | Mean | Std Dev | Min | Max | Range |
|--------|------|---------|-----|-----|-------|
| Pass Rate | 55.5% | 18.6% | 22.3% | 63.8% | 41.5% |
| Score (1-10) | 4.2 | 1.8 | 1 | 5 | 4 |

## Per-Iteration Results

| Run | Build | Startup | Passed | Total | Pass Rate | Score |
|-----|-------|---------|--------|-------|-----------|-------|
| 1 | PASS | PASS | 21 | 94 | 22.3% | 1/10 |
| 2 | PASS | PASS | 60 | 94 | 63.8% | 5/10 |
| 3 | PASS | PASS | 60 | 94 | 63.8% | 5/10 |
| 4 | PASS | PASS | 60 | 94 | 63.8% | 5/10 |
| 5 | PASS | PASS | 60 | 94 | 63.8% | 5/10 |

## Category Breakdown

| Category | Mean | Std Dev | Min | Max |
|----------|------|---------|-----|-----|
| API Contract | 55.1% | 18.4% | 22.2% | 64.4% |
| Build & Startup | 100.0% | 0.0% | 100.0% | 100.0% |
| Cosmos Infrastructure | 63.1% | 22.7% | 23.1% | 76.9% |
| Data Integrity | 96.0% | 8.9% | 80.0% | 100.0% |
| Robustness | 46.4% | 18.7% | 12.9% | 54.8% |

## Test Consistency Analysis

- **Always pass**: 22 tests (23%)
- **Always fail**: 30 tests (31%)
- **Flaky** (stochastic): 44 tests (46%)

### Consistent Passes (22 tests)

- `build_startup::app_startup`
- `build_startup::build_compilation`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestCreatePlayer::test_create_player_response_has_required_fields`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestCreatePlayer::test_create_player_returns_201`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestCreatePlayer::test_create_player_returns_correct_data`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestCreatePlayer::test_new_player_has_zero_stats`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestDeletePlayer::test_delete_nonexistent_player_returns_404`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayer::test_get_nonexistent_player_returns_404`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_for_nonexistent_player_returns_404`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestHealth::test_health_returns_200`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_nonexistent_player_rank_returns_404`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_nonexistent_player_returns_404`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestLeaderboardIndexing::test_has_composite_indexes`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestLeaderboardIndexing::test_has_custom_indexing_policy`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestThroughputConfiguration::test_throughput_is_configured`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_data_integrity.TestDataPersistence::test_database_is_created`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_data_integrity.TestIndexingPolicy::test_containers_have_indexing_policy`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_data_integrity.TestPartitionKeyDesign::test_containers_have_partition_keys`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_data_integrity.TestPartitionKeyDesign::test_no_container_uses_id_as_sole_partition_key`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_create_player_empty_body_returns_4xx`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_create_player_missing_required_fields_returns_4xx`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_created_player_fully_retrievable`

### Consistent Failures (30 tests)

These tests failed in EVERY iteration — likely indicates a real gap (missing rule, contract misunderstanding, or SDK issue).

- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_entries_have_required_fields`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_ranks_sequential`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_respects_top_parameter`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_returns_200`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_returns_array`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_sorted_descending`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGlobalLeaderboard::test_global_leaderboard_top_player_is_highest_scorer`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_correct_for_top_player`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_has_required_fields`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_neighbors_have_required_fields`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_neighbors_is_array`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestPlayerRank::test_player_rank_returns_200`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_entries_have_required_fields`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_only_contains_region_players`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_returns_200`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestRegionalLeaderboard::test_regional_leaderboard_sorted_descending`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_schema_version`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDataTypeCorrectness::test_leaderboard_entry_types`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_empty_region_leaderboard`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_leaderboard_no_duplicate_players`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_top_parameter_one`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_negative_value_returns_4xx`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestLeaderboardTiebreaking::test_tied_scores_have_sequential_ranks`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestLeaderboardTiebreaking::test_tied_scores_sorted_by_display_name_ascending`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestRapidOperations::test_concurrent_score_submissions_all_counted`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_deleted_player_removed_from_leaderboard`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_updated_region_reflected_in_regional_leaderboard`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_player_rank_score_matches_leaderboard`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_regional_filter_matches_stored_region`
- `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestWriteReadConsistency::test_score_reflected_in_leaderboard`

### Flaky Tests (44 tests)

These tests passed in some iterations but failed in others — indicates LLM stochasticity rather than a systematic gap.

| Test | Pass Rate | Outcomes |
|------|-----------|----------|
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestDeletePlayer::test_delete_player_returns_204` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestDeletePlayer::test_deleted_player_returns_404_on_get` | 40.0% | error, passed, passed, failed, failed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayer::test_get_existing_player` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayer::test_get_player_has_required_fields` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayer::test_get_player_stats_updated_after_scores` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_contains_all_player_scores` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_entries_have_required_fields` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_only_shows_own_scores` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_ordered_by_most_recent_first` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_respects_limit` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_returns_200` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestGetPlayerScores::test_score_history_returns_array` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestSubmitScore::test_submit_score_response_has_required_fields` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestSubmitScore::test_submit_score_returns_201` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestSubmitScore::test_submit_score_returns_correct_data` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_preserves_stats` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_reflects_new_display_name` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_response_has_required_fields` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_api_contract.TestUpdatePlayer::test_update_player_returns_200` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestContainerDesign::test_has_multiple_containers_or_synthetic_keys` | 60.0% | failed, failed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestContainerDesign::test_leaderboard_container_uses_synthetic_key` | 0.0% | failed, failed, skipped, skipped, skipped |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestContainerDesign::test_player_container_uses_player_id_key` | 60.0% | skipped, skipped, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_leaderboard_entries_denormalized` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_player_stats_stored_correctly` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_synthetic_partition_key_value_format` | 20.0% | error, passed, skipped, skipped, skipped |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_type_discriminator` | 60.0% | error, passed, failed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestPlayerScoreSerialization::test_etag_present_on_player_documents` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_cosmos_infrastructure.TestPlayerScoreSerialization::test_scores_stored_as_numbers` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_data_integrity.TestDataPersistence::test_player_document_exists_in_cosmos` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_average_score_mathematically_correct` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_best_score_is_maximum` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_new_score_updates_stats` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_player_with_single_score_stats` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestComputedFieldAccuracy::test_total_games_count_correct` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDataTypeCorrectness::test_player_stats_types` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDataTypeCorrectness::test_score_submission_returns_correct_types` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestDuplicateHandling::test_create_duplicate_player_does_not_return_500` | 60.0% | passed, failed, failed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_top_parameter_zero_returns_empty` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestEdgeCases::test_zero_score_submission` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_for_nonexistent_player_returns_4xx` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_missing_player_id_returns_4xx` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestInvalidInput::test_submit_score_missing_score_returns_4xx` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestRapidOperations::test_rapid_score_submissions_all_counted` | 80.0% | error, passed, passed, passed, passed |
| `testing-v2.scenarios.gaming-leaderboard.tests.test_robustness.TestUpdateDeleteConsistency::test_deleted_player_scores_not_in_history` | 40.0% | error, passed, passed, failed, failed |

## Statistical Assessment

**Insufficient confidence** (σ ≥ 15%): Very high variance — results are dominated by LLM stochasticity. More iterations or scenario simplification needed.
