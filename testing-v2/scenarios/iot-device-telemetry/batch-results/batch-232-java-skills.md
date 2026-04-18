# Batch Test Results: Iot Device Telemetry

## Metadata
- **Date**: 2026-04-18
- **Scenario**: iot-device-telemetry
- **Language**: java
- **Skills loaded**: Yes (skills loaded)
- **Iterations**: 5
- **Batch issue**: #232
- **Child PRs**: 238,239,240,241,242
- **Startup failures**: 3/5

## Aggregate Summary

| Metric | Mean | Std Dev | Min | Max | Range |
|--------|------|---------|-----|-----|-------|
| Pass Rate | 22.8% | 38.6% | 0.0% | 89.1% | 89.1% |
| Score (1-10) | 2.2 | 2.7 | 1 | 7 | 6 |

## Per-Iteration Results

| Run | Build | Startup | Passed | Total | Pass Rate | Score |
|-----|-------|---------|--------|-------|-----------|-------|
| 1 | PASS | FAIL | 0 | 0 | 0.0% | 1/10 |
| 2 | PASS | PASS | 82 | 92 | 89.1% | 7/10 |
| 3 | PASS | PASS | 23 | 92 | 25.0% | 1/10 |
| 4 | PASS | FAIL | 0 | 0 | 0.0% | 1/10 |
| 5 | PASS | FAIL | 0 | 0 | 0.0% | 1/10 |

## Category Breakdown

| Category | Mean | Std Dev | Min | Max |
|----------|------|---------|-----|-----|
| API Contract | 58.7% | 58.4% | 17.4% | 100.0% |
| Build & Startup | 70.0% | 27.4% | 50.0% | 100.0% |
| Cosmos Infrastructure | 65.4% | 27.2% | 46.2% | 84.6% |
| Data Integrity | 91.7% | 11.8% | 83.3% | 100.0% |
| Robustness | 42.6% | 39.3% | 14.8% | 70.4% |

## Test Consistency Analysis

- **Always pass**: 1 tests (1%)
- **Always fail**: 7 tests (7%)
- **Flaky** (stochastic): 86 tests (91%)

### Consistent Passes (1 tests)

- `build_startup::build_compilation`

### Consistent Failures (7 tests)

These tests failed in EVERY iteration — likely indicates a real gap (missing rule, contract misunderstanding, or SDK issue).

- `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_schema_version`
- `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestComputedFieldAccuracy::test_stats_humidity_values_correct`
- `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestComputedFieldAccuracy::test_stats_temperature_min_correct`
- `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestEdgeCases::test_latest_reading_is_most_recent`
- `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestInvalidInput::test_ingest_telemetry_empty_body_returns_4xx`
- `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestInvalidInput::test_ingest_telemetry_for_nonexistent_device_returns_4xx`
- `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestInvalidInput::test_ingest_telemetry_missing_device_id_returns_4xx`

### Flaky Tests (86 tests)

These tests passed in some iterations but failed in others — indicates LLM stochasticity rather than a systematic gap.

| Test | Pass Rate | Outcomes |
|------|-----------|----------|
| `build_startup::app_startup` | 40.0% | failed, passed, passed, failed, failed |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestBatchIngest::test_batch_ingest_returns_201` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestBatchIngest::test_batch_ingest_returns_count` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeleteDevice::test_delete_device_returns_204` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeleteDevice::test_delete_nonexistent_device_returns_404` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeleteDevice::test_deleted_device_removed_from_location_query` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeleteDevice::test_deleted_device_returns_404_on_get` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeviceStats::test_stats_has_required_fields` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeviceStats::test_stats_humidity_has_min_max_avg` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeviceStats::test_stats_returns_200` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeviceStats::test_stats_temperature_has_min_max_avg` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeviceStats::test_stats_values_are_numeric` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestDeviceStats::test_stats_with_period_parameter` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestGetDevice::test_get_device_has_required_fields` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestGetDevice::test_get_existing_device` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestGetDevice::test_get_nonexistent_device_returns_404` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestGetDevicesByLocation::test_building_a_has_2_devices` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestGetDevicesByLocation::test_location_filter_is_correct` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestGetDevicesByLocation::test_query_by_location_returns_200` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestGetDevicesByLocation::test_query_by_location_returns_array` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestHealth::test_health_returns_200` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestIngestTelemetry::test_ingest_response_has_required_fields` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestIngestTelemetry::test_ingest_returns_201` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestIngestTelemetry::test_ingest_returns_correct_values` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLatestReading::test_latest_reading_has_required_fields` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLatestReading::test_latest_reading_is_for_correct_device` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLatestReading::test_latest_reading_returns_200` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLatestReading::test_nonexistent_device_latest_returns_404` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLocationSummary::test_empty_location_returns_empty_array` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLocationSummary::test_location_summary_contains_correct_devices` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLocationSummary::test_location_summary_has_required_fields` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLocationSummary::test_location_summary_one_entry_per_device` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLocationSummary::test_location_summary_returns_200` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestLocationSummary::test_location_summary_returns_array` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestRegisterDevice::test_register_device_response_has_required_fields` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestRegisterDevice::test_register_device_returns_201` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestRegisterDevice::test_register_device_returns_correct_data` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestTimeRangeQuery::test_empty_time_range_returns_empty` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestTimeRangeQuery::test_time_range_only_contains_correct_device` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestTimeRangeQuery::test_time_range_returns_200` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestTimeRangeQuery::test_time_range_returns_array` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestTimeRangeQuery::test_time_range_returns_readings_for_device` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestUpdateDevice::test_update_device_location_reflected_in_queries` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestUpdateDevice::test_update_device_reflects_new_name` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestUpdateDevice::test_update_device_response_has_required_fields` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestUpdateDevice::test_update_device_returns_200` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_api_contract.TestUpdateDevice::test_update_nonexistent_device_returns_404` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestContainerPartitionKeys::test_device_metadata_separate_from_telemetry` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestContainerPartitionKeys::test_no_default_id_partition_key` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestContainerPartitionKeys::test_telemetry_container_uses_device_partition_key` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_aggregation_values_match_raw_data` | 0.0% | missing, skipped, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_device_metadata_stored_correctly` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_telemetry_stored_with_all_fields` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_type_discriminator` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestTTLConfiguration::test_telemetry_container_has_ttl_option` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestTelemetryIndexing::test_has_custom_indexing_policy` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestTelemetrySerialization::test_sensor_values_stored_as_numbers` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestTelemetrySerialization::test_timestamps_stored_as_iso_strings` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_cosmos_infrastructure.TestThroughputConfiguration::test_throughput_is_configured` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_data_integrity.TestDataPersistence::test_containers_exist_in_cosmos` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_data_integrity.TestDataPersistence::test_database_is_created` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_data_integrity.TestIndexingPolicy::test_containers_have_indexing_policy` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_data_integrity.TestPartitionKeyDesign::test_containers_have_partition_keys` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_data_integrity.TestPartitionKeyDesign::test_no_container_uses_id_as_sole_partition_key` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_data_integrity.TestTTLConfiguration::test_at_least_one_container_has_ttl` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestComputedFieldAccuracy::test_stats_temperature_avg_correct` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestComputedFieldAccuracy::test_stats_temperature_max_correct` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestComputedFieldAccuracy::test_stats_values_are_consistent` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestConcurrentIngestion::test_concurrent_ingestion_all_persisted` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestDataIsolation::test_location_query_filters_correctly` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestDataIsolation::test_time_range_only_returns_correct_device` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestDataTypeCorrectness::test_device_field_types` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestDataTypeCorrectness::test_stats_values_are_numeric` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestDataTypeCorrectness::test_telemetry_values_are_numbers` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestDuplicateHandling::test_register_duplicate_device_does_not_return_500` | 40.0% | missing, passed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestEdgeCases::test_batch_ingest_count_matches_input` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestEdgeCases::test_empty_location_returns_empty_array` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestEdgeCases::test_future_time_range_returns_empty` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestEdgeCases::test_stats_for_device_with_single_reading` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestInvalidInput::test_register_device_empty_body_returns_4xx` | 20.0% | missing, failed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestInvalidInput::test_register_device_missing_device_id_returns_4xx` | 20.0% | missing, failed, passed, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestUpdateDeleteConsistency::test_deleted_device_telemetry_returns_404` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestUpdateDeleteConsistency::test_updated_device_preserves_telemetry` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestWriteReadConsistency::test_device_appears_in_location_query` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestWriteReadConsistency::test_ingested_reading_appears_in_latest` | 20.0% | missing, passed, error, missing, missing |
| `testing-v2.scenarios.iot-device-telemetry.tests.test_robustness.TestWriteReadConsistency::test_registered_device_retrievable_by_get` | 40.0% | missing, passed, passed, missing, missing |

## Statistical Assessment

**Insufficient confidence** (σ ≥ 15%): Very high variance — results are dominated by LLM stochasticity. More iterations or scenario simplification needed.
