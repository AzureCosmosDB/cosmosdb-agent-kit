"""IoT (SensorGrid) scenario-specific behavioural checks (all SDKs).

The generic engine (/verifier/check_*.py) grades the *device* aggregate
root from the contract. This file grades the *reading* child entity and
the time-series endpoints the generic engine does not model:

    POST /readings                                   ingest a reading (201)
    GET  /devices/{id}/readings?start=<iso>&end=<iso> time-range query
    GET  /devices/{id}/summary                        aggregate stats

Readings must be co-located with their device (partition by deviceId) so
device+time-range queries stay single-partition — the dominant access
pattern for a write-heavy telemetry store. Every result is cross-checked
against the emulator with the verifier's own client.
"""
from __future__ import annotations

import pytest

from conftest import CHILDREN, emulator_docs_for_id, fmt_path, partition_key_field

READING = next((c for c in CHILDREN if c["name"] == "reading"), None)


def _reading_body(row: dict) -> dict:
    """Contract seed row mapped to the API payload: parentId -> deviceId."""
    body = {k: v for k, v in row.items() if k != "parentId"}
    body["deviceId"] = row["parentId"]
    return body


def _readings_for_device(container, device_id: str) -> list[dict]:
    return list(container.query_items(
        query="SELECT * FROM c WHERE c.deviceId = @d",
        parameters=[{"name": "@d", "value": device_id}],
        enable_cross_partition_query=True,
    ))


@pytest.fixture(scope="session")
def readings_container(child_containers):
    assert READING is not None, "iot contract has no 'reading' child entity"
    return child_containers["reading"]


@pytest.fixture(scope="session")
def seeded_readings(api, seed_roots):
    """Ingest readings through the API once. `seed_roots` guarantees the
    parent devices exist first."""
    for row in READING["seed"]:
        path = READING["create"]["path"]
        r = api.api("POST", path, json=_reading_body(row))
        assert r.status_code in (201, 200), f"POST {path} -> {r.status_code}: {r.text[:200]}"
    return READING["seed"]


class TestReadingIngest:
    def test_reading_persisted_in_cosmos(self, seeded_readings, readings_container):
        row = READING["seed"][0]
        rows = emulator_docs_for_id(readings_container, row["id"])
        assert rows, (
            f"reading {row['id']!r} was accepted by the API but is NOT in Cosmos. "
            "Readings must persist through the Cosmos SDK."
        )

    def test_reading_fields_match_input(self, seeded_readings, readings_container):
        row = READING["seed"][0]
        doc = emulator_docs_for_id(readings_container, row["id"])[0]
        assert doc.get("value") == row["value"], (
            f"reading {row['id']}: value stored as {doc.get('value')!r}, expected {row['value']!r}."
        )
        assert doc.get("unit") == row["unit"], (
            f"reading {row['id']}: unit stored as {doc.get('unit')!r}, expected {row['unit']!r}."
        )
        assert doc.get(READING["partition_field"]) == row["parentId"], (
            f"reading {row['id']}: deviceId stored as "
            f"{doc.get(READING['partition_field'])!r}, expected {row['parentId']!r}."
        )

    def test_readings_colocated_with_device(self, seeded_readings, readings_container):
        pk = partition_key_field(readings_container)
        assert pk, "readings container has no partition key"
        row = READING["seed"][0]
        doc = emulator_docs_for_id(readings_container, row["id"])[0]
        assert doc.get(pk) == row["parentId"], (
            f"readings are partitioned by /{pk} but reading {row['id']}'s value is "
            f"{doc.get(pk)!r}, not its device id {row['parentId']!r}. Partition readings by "
            "deviceId so device+time-range queries stay single-partition."
        )


class TestTimeRangeQuery:
    def test_range_returns_expected_ids(self, seeded_readings, api):
        rq = READING["range_query"]
        tr = READING["time_range"]
        path = fmt_path(tr["path"], parentId=rq["parentId"])
        r = api.api("GET", path, params={tr["start_param"]: rq["start"], tr["end_param"]: rq["end"]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list), f"Expected list, got {type(body).__name__}"
        got = {item["id"] for item in body}
        assert got == set(rq["expected_ids"]), (
            f"GET {path}?{tr['start_param']}={rq['start']}&{tr['end_param']}={rq['end']} "
            f"returned {sorted(got)}, expected {sorted(rq['expected_ids'])}. The endpoint "
            "must return exactly the device's readings whose timestamp is in range."
        )

    def test_range_matches_emulator(self, seeded_readings, api, readings_container):
        rq = READING["range_query"]
        tr = READING["time_range"]
        tf = tr["time_field"]
        emulator_ids = {
            item["id"]
            for item in readings_container.query_items(
                query=(
                    f"SELECT c.id FROM c WHERE c.deviceId = @d "
                    f"AND c.{tf} >= @s AND c.{tf} <= @e"
                ),
                parameters=[
                    {"name": "@d", "value": rq["parentId"]},
                    {"name": "@s", "value": rq["start"]},
                    {"name": "@e", "value": rq["end"]},
                ],
                enable_cross_partition_query=True,
            )
        }
        path = fmt_path(tr["path"], parentId=rq["parentId"])
        r = api.api("GET", path, params={tr["start_param"]: rq["start"], tr["end_param"]: rq["end"]})
        api_ids = {item["id"] for item in r.json()}
        assert api_ids == emulator_ids, (
            f"Time-range API returned {sorted(api_ids)} but the emulator holds "
            f"{sorted(emulator_ids)} for that device+range."
        )


class TestDeviceSummary:
    def test_summary_stats_match_emulator(self, seeded_readings, api, readings_container):
        summ = READING["summary"]
        device_id = READING["range_query"]["parentId"]
        docs = _readings_for_device(readings_container, device_id)
        values = [d["value"] for d in docs]
        assert values, f"no readings persisted for {device_id}; cannot verify summary"

        r = api.api("GET", fmt_path(summ["path"], parentId=device_id))
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, dict), f"summary must be a JSON object, got {type(body).__name__}"

        assert body.get(summ["count_field"]) == len(values), (
            f"summary {summ['count_field']} = {body.get(summ['count_field'])!r}, "
            f"expected {len(values)}."
        )
        assert float(body.get(summ["min_field"])) == pytest.approx(min(values), abs=1e-6), (
            f"summary {summ['min_field']} = {body.get(summ['min_field'])!r}, expected {min(values)}."
        )
        assert float(body.get(summ["max_field"])) == pytest.approx(max(values), abs=1e-6), (
            f"summary {summ['max_field']} = {body.get(summ['max_field'])!r}, expected {max(values)}."
        )
        expected_avg = sum(values) / len(values)
        assert float(body.get(summ["avg_field"])) == pytest.approx(expected_avg, abs=1e-6), (
            f"summary {summ['avg_field']} = {body.get(summ['avg_field'])!r}, expected {expected_avg}."
        )
