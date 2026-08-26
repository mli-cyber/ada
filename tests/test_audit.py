from __future__ import annotations

from ada.config import AdaConfig
from ada.platform.audit import AuditEvent, read_events, record_event


def test_append_and_read_audit_events(phase0_config: AdaConfig) -> None:
    event = AuditEvent(
        user="tester@example.test",
        action="CREATE",
        entity_type="document",
        entity_id="doc-1",
        source="test",
        new_value={"status": "REGISTERED"},
    )
    record_event(event, phase0_config)
    record_event(
        AuditEvent(
            user="tester@example.test",
            action="UPDATE",
            entity_type="document",
            entity_id="doc-1",
            source="test",
            previous_value={"status": "REGISTERED"},
            new_value={"status": "REVIEWED"},
        ),
        phase0_config,
    )
    events = read_events(phase0_config)
    assert [item.action for item in events] == ["CREATE", "UPDATE"]
    assert events[0].new_value == {"status": "REGISTERED"}
