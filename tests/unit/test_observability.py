import logging

from apps.api.core.observability import (
    matter_id_cv,
    redact_event_dict,
    request_id_cv,
    setup_standard_logging_context,
)


def test_structured_log_redaction_removes_secrets_and_document_content() -> None:
    event = redact_event_dict(
        None,
        None,
        {
            "authorization": "Bearer top-secret-token",
            "database": "postgresql+psycopg://user:password@db/mesa_law",
            "evidence_text": "privileged client document content",
            "nested": {"api_key": "mesa-api-key", "status": "ok"},
        },
    )

    assert event["authorization"] == "[REDACTED]"
    assert event["evidence_text"] == "[REDACTED]"
    assert event["nested"] == {"api_key": "[REDACTED]", "status": "ok"}
    assert "password" not in event["database"]


def test_stdlib_logging_includes_correlation_without_leaking_secret() -> None:
    setup_standard_logging_context()
    request_token = request_id_cv.set("request-123")
    matter_token = matter_id_cv.set("matter-456")
    try:
        record = logging.getLogger("test.observability").makeRecord(
            "test.observability",
            logging.INFO,
            __file__,
            1,
            "authorization=Bearer top-secret-token",
            (),
            None,
        )
        message = record.getMessage()
        assert "request_id=request-123" in message
        assert "matter_id=matter-456" in message
        assert "top-secret-token" not in message
        assert "[REDACTED]" in message
    finally:
        matter_id_cv.reset(matter_token)
        request_id_cv.reset(request_token)
