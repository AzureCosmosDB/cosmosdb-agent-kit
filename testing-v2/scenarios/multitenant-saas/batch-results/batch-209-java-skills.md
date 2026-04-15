# Batch Test Results: Multitenant Saas

## Metadata
- **Date**: 2026-04-15
- **Scenario**: multitenant-saas
- **Language**: java
- **Skills loaded**: Yes (skills loaded)
- **Iterations**: 5
- **Batch issue**: #209
- **Child PRs**: 215,216,219,217,218
- **Startup failures**: 2/5

## Aggregate Summary

| Metric | Mean | Std Dev | Min | Max | Range |
|--------|------|---------|-----|-----|-------|
| Pass Rate | 60.0% | 54.8% | 0.0% | 100.0% | 100.0% |
| Score (1-10) | 6.4 | 4.9 | 1 | 10 | 9 |

## Per-Iteration Results

| Run | Build | Startup | Passed | Total | Pass Rate | Score |
|-----|-------|---------|--------|-------|-----------|-------|
| 1 | PASS | PASS | 73 | 73 | 100.0% | 10/10 |
| 2 | PASS | FAIL | 0 | 0 | 0.0% | 1/10 |
| 3 | PASS | PASS | 73 | 73 | 100.0% | 10/10 |
| 4 | PASS | FAIL | 0 | 0 | 0.0% | 1/10 |
| 5 | PASS | PASS | 73 | 73 | 100.0% | 10/10 |

## Category Breakdown

| Category | Mean | Std Dev | Min | Max |
|----------|------|---------|-----|-----|
| API Contract | 100.0% | 0.0% | 100.0% | 100.0% |
| Build & Startup | 80.0% | 27.4% | 50.0% | 100.0% |
| Cosmos Infrastructure | 100.0% | 0.0% | 100.0% | 100.0% |
| Data Integrity | 100.0% | 0.0% | 100.0% | 100.0% |

## Test Consistency Analysis

- **Always pass**: 1 tests (1%)
- **Always fail**: 0 tests (0%)
- **Flaky** (stochastic): 74 tests (99%)

### Consistent Passes (1 tests)

- `build_startup::build_compilation`

### Flaky Tests (74 tests)

These tests passed in some iterations but failed in others — indicates LLM stochasticity rather than a systematic gap.

| Test | Pass Rate | Outcomes |
|------|-----------|----------|
| `build_startup::app_startup` | 60.0% | passed, failed, passed, failed, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateProject::test_create_project_response_fields` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateProject::test_create_project_returns_201` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateTask::test_create_task_default_status_is_todo` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateTask::test_create_task_response_fields` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateTask::test_create_task_returns_201` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateTenant::test_create_tenant_generates_unique_ids` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateTenant::test_create_tenant_has_created_at` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateTenant::test_create_tenant_response_fields` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateTenant::test_create_tenant_returns_201` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateUser::test_create_user_generates_unique_ids` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateUser::test_create_user_response_fields` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestCreateUser::test_create_user_returns_201` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestGetProject::test_get_nonexistent_project_returns_404` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestGetProject::test_get_project_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestGetProject::test_get_project_returns_correct_name` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestGetTenant::test_get_nonexistent_tenant_returns_404` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestGetTenant::test_get_tenant_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestGetTenant::test_get_tenant_returns_correct_name` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestHealth::test_health_response_has_status` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestHealth::test_health_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListProjectTasks::test_list_tasks_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListProjectTasks::test_list_tasks_returns_array` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListProjectTasks::test_mobile_app_has_4_seeded_tasks` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListProjectTasks::test_website_redesign_has_3_seeded_tasks` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListProjects::test_acme_has_at_least_2_seeded_projects` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListProjects::test_list_projects_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListProjects::test_startup_has_at_least_1_seeded_project` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListUsers::test_acme_has_at_least_3_seeded_users` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListUsers::test_list_users_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListUsers::test_list_users_returns_array` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestListUsers::test_startup_has_at_least_2_seeded_users` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestQueryTasksByStatus::test_query_blocked_tasks_in_acme` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestQueryTasksByStatus::test_query_by_status_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestQueryTasksByStatus::test_query_done_tasks_in_acme` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestQueryTasksByStatus::test_query_in_progress_tasks_in_acme` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestQueryTasksByStatus::test_query_todo_tasks_in_acme` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantAnalytics::test_acme_analytics_counts` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantAnalytics::test_acme_tasks_by_priority_breakdown` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantAnalytics::test_acme_tasks_by_status_breakdown` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantAnalytics::test_analytics_response_fields` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantAnalytics::test_analytics_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantIsolation::test_analytics_reflect_only_own_tenant` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantIsolation::test_tenant_0_cannot_see_tenant_1_projects` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantIsolation::test_tenant_1_cannot_see_tenant_0_users` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestTenantIsolation::test_tenant_1_tasks_isolated` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestUserTasks::test_alice_has_tasks` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestUserTasks::test_bob_has_tasks_across_projects` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestUserTasks::test_user_tasks_all_belong_to_user` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestUserTasks::test_user_tasks_returns_200` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_api_contract.TestUserTasks::test_user_tasks_returns_array` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestContainerPartitionKeys::test_container_uses_tenant_partition_key` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestContainerPartitionKeys::test_hierarchical_partition_keys` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestContainerPartitionKeys::test_no_id_only_partition_key` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_task_fields_match_api` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_tenant_data_stored_correctly` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_tenant_isolation_in_cosmos` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestCrossBoundaryConsistency::test_user_fields_preserved` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestDocumentStructure::test_schema_version_present` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestDocumentStructure::test_type_discriminator_present` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestEnumSerialization::test_priority_stored_as_string` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestEnumSerialization::test_role_stored_as_string` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestEnumSerialization::test_status_stored_as_string` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestIndexingPolicies::test_composite_index_for_task_queries` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestIndexingPolicies::test_custom_indexing_policy` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestThroughputConfiguration::test_throughput_is_set` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_cosmos_infrastructure.TestTimestampSerialization::test_timestamps_are_iso_strings` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_data_integrity.TestDataPersistence::test_tasks_persisted` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_data_integrity.TestDataPersistence::test_tenants_exist_in_cosmos` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_data_integrity.TestHierarchicalPartitionKeys::test_check_hierarchical_keys` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_data_integrity.TestIndexingPolicy::test_composite_indexes_for_queries` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_data_integrity.TestIndexingPolicy::test_containers_have_indexing_policy` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_data_integrity.TestPartitionKeyDesign::test_no_id_only_partition_key` | 60.0% | passed, missing, passed, missing, passed |
| `testing-v2.scenarios.multitenant-saas.tests.test_data_integrity.TestPartitionKeyDesign::test_partition_key_includes_tenant_id` | 60.0% | passed, missing, passed, missing, passed |

## Statistical Assessment

**Insufficient confidence** (σ ≥ 15%): Very high variance — results are dominated by LLM stochasticity. More iterations or scenario simplification needed.
