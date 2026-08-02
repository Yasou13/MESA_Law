"""Database-independent queue schema contract tests."""

from typing import cast

from apps.api.models.queue import Job, JobStatus
from apps.worker.jobs import validate_job_payload
from sqlalchemy import Table


def test_job_statuses_are_explicit_and_terminal_states_are_distinct() -> None:
    assert {state.value for state in JobStatus} == {
        "PENDING",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "DEAD",
    }


def test_idempotency_index_is_unique_and_null_safe() -> None:
    table = cast(Table, Job.__table__)
    index = next(
        item for item in table.indexes if item.name == "uq_legal_jobs_idempotency"
    )
    sql = str(index.dialect_options["postgresql"]["where"])
    assert index.unique is True
    assert [column.name for column in index.columns] == [
        "tenant_id",
        "type",
        "idempotency_key",
    ]
    assert "idempotency_key IS NOT NULL" in sql


def test_poll_mutation_payload_requires_a_matter_scope() -> None:
    payload = validate_job_payload(
        "POLL_MESA_MUTATION",
        {
            "tenant_id": "tenant-1",
            "matter_id": "matter-1",
            "sync_record_id": "sync-1",
        },
    )
    assert payload["matter_id"] == "matter-1"
