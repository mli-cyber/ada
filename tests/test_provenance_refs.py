from __future__ import annotations

from dataclasses import asdict

import pytest

from ada.provenance.refs import EvidenceRef, ProvenanceRef, SourceRef


def test_reference_contract_round_trip() -> None:
    source = SourceRef("uploaded_document", "doc-1", "sample.pdf")
    evidence = EvidenceRef(source.source_ref_id, "page:1")
    provenance = ProvenanceRef(
        source_ref_id=source.source_ref_id,
        evidence_ref_ids=(evidence.evidence_ref_id,),
        method="manual_upload",
        confidence=0.95,
    )
    assert asdict(provenance)["source_ref_id"] == source.source_ref_id


def test_confidence_validation() -> None:
    with pytest.raises(ValueError):
        ProvenanceRef("source", confidence=1.5)
