"""Ticketing scenario-specific behavioural checks (all SDKs).

The generic engine (/verifier/check_*.py) already grades the *event*
aggregate root from the contract. This file grades the *ticket* child
entity and the ticket-lifecycle endpoints the generic engine does not
model:

    POST   /events/{id}/tickets             buy a ticket (201 / 409 dup)
    DELETE /events/{id}/tickets/{ticketId}  cancel (204 / 412 ETag mismatch)

Every assertion is proven against the Cosmos emulator with the verifier's
own client, never trusting the agent's API in isolation. Tickets must be
co-located with their event (partition by eventId) so event-scoped ticket
queries stay single-partition.
"""
from __future__ import annotations

import pytest

from conftest import CHILDREN, emulator_docs_for_id, fmt_path, partition_key_field

TICKET = next((c for c in CHILDREN if c["name"] == "ticket"), None)


def _ticket_body(row: dict) -> dict:
    """Contract seed row minus the path-only parentId."""
    return {k: v for k, v in row.items() if k != "parentId"}


@pytest.fixture(scope="session")
def tickets_container(child_containers):
    assert TICKET is not None, "ticketing contract has no 'ticket' child entity"
    return child_containers["ticket"]


@pytest.fixture(scope="session")
def seeded_tickets(api, seed_roots):
    """Seed tickets through the API once. `seed_roots` guarantees the parent
    events exist first. Idempotent on the declared duplicate status."""
    dup = TICKET["create"].get("duplicate_status")
    ok = {201, 200}
    if dup is not None:
        ok.add(dup)
    for row in TICKET["seed"]:
        path = fmt_path(TICKET["create"]["path"], parentId=row["parentId"])
        r = api.api("POST", path, json=_ticket_body(row))
        assert r.status_code in ok, f"POST {path} -> {r.status_code}: {r.text[:200]}"
    return TICKET["seed"]


class TestTicketPurchase:
    def test_ticket_persisted_in_cosmos(self, seeded_tickets, tickets_container):
        row = TICKET["seed"][0]
        rows = emulator_docs_for_id(tickets_container, row["id"])
        assert rows, (
            f"ticket {row['id']!r} was accepted by the API but is NOT in Cosmos. "
            "Tickets must persist through the Cosmos SDK."
        )

    def test_ticket_fields_match_input(self, seeded_tickets, tickets_container):
        row = TICKET["seed"][0]
        doc = emulator_docs_for_id(tickets_container, row["id"])[0]
        for field in TICKET.get("compare_fields", []):
            assert doc.get(field) == row.get(field), (
                f"ticket {row['id']}: {field!r} stored as {doc.get(field)!r}, "
                f"expected {row.get(field)!r}."
            )

    def test_ticket_references_its_event(self, seeded_tickets, tickets_container):
        row = TICKET["seed"][0]
        doc = emulator_docs_for_id(tickets_container, row["id"])[0]
        pf = TICKET["partition_field"]
        assert doc.get(pf) == row["parentId"], (
            f"ticket {row['id']}: {pf!r} = {doc.get(pf)!r}, expected the owning event id "
            f"{row['parentId']!r}."
        )

    def test_tickets_colocated_with_event(self, seeded_tickets, tickets_container):
        pk = partition_key_field(tickets_container)
        assert pk, "tickets container has no partition key"
        row = TICKET["seed"][0]
        doc = emulator_docs_for_id(tickets_container, row["id"])[0]
        assert doc.get(pk) == row["parentId"], (
            f"tickets are partitioned by /{pk} but ticket {row['id']}'s value is "
            f"{doc.get(pk)!r}, not its event id {row['parentId']!r}. Partition tickets by "
            "eventId so all tickets for an event live in one logical partition."
        )


class TestDuplicateTicket:
    def test_duplicate_ticket_returns_409(self, seeded_tickets, api):
        row = TICKET["seed"][0]
        path = fmt_path(TICKET["create"]["path"], parentId=row["parentId"])
        r = api.api("POST", path, json=_ticket_body(row))
        assert r.status_code == 409, (
            f"Re-buying ticket id {row['id']!r} returned {r.status_code}, expected 409. "
            "Duplicate ticket ids must be rejected atomically."
        )

    def test_duplicate_ticket_no_second_doc(self, seeded_tickets, api, tickets_container):
        row = TICKET["seed"][0]
        path = fmt_path(TICKET["create"]["path"], parentId=row["parentId"])
        api.api("POST", path, json=_ticket_body(row))
        rows = emulator_docs_for_id(tickets_container, row["id"])
        assert len(rows) == 1, (
            f"Expected exactly 1 ticket for id {row['id']!r}, found {len(rows)}."
        )


class TestTicketCancellation:
    """Cancellation uses the ticket's ETag as an optimistic-concurrency
    guard: a stale ETag must be rejected (412) without deleting anything,
    a correct/unconditional cancel must remove the ticket (204)."""

    def _target(self):
        # A dedicated ticket not used by the purchase/duplicate checks.
        return TICKET["seed"][1]

    def test_cancel_with_wrong_etag_returns_412(self, seeded_tickets, api, tickets_container):
        row = self._target()
        path = fmt_path(TICKET["delete"]["path"], parentId=row["parentId"], id=row["id"])
        r = api.api("DELETE", path, headers={"If-Match": '"0000-stale-etag"'})
        assert r.status_code == TICKET["delete"]["etag_mismatch_status"], (
            f"DELETE {path} with a stale If-Match returned {r.status_code}, expected "
            f"{TICKET['delete']['etag_mismatch_status']}. A stale ETag must be rejected."
        )
        # And the ticket must still be there.
        assert emulator_docs_for_id(tickets_container, row["id"]), (
            "A rejected (412) cancel must not delete the ticket."
        )

    def test_cancel_succeeds_and_removes_ticket(self, seeded_tickets, api, tickets_container):
        row = self._target()
        path = fmt_path(TICKET["delete"]["path"], parentId=row["parentId"], id=row["id"])
        r = api.api("DELETE", path)
        assert r.status_code == TICKET["delete"]["success_status"], (
            f"DELETE {path} returned {r.status_code}, expected "
            f"{TICKET['delete']['success_status']}."
        )
        assert emulator_docs_for_id(tickets_container, row["id"]) == [], (
            f"After a successful cancel, ticket {row['id']!r} must be gone from Cosmos."
        )
