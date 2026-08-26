"""Phase 0 file intake: store and register uploads without parsing."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ada.config import AdaConfig
from ada.platform.identity import current_principal
from ada.platform.intake import ingest_file, list_documents

st.set_page_config(page_title="Ada - File Import", page_icon="A", layout="wide")
st.title("File Import / Review")
st.caption("Phase 0 intake subset")
st.info(
    "This foundation path stores the original file, registers metadata, and writes an audit "
    "event. It does not parse or map records. Parsing and schema mapping arrive in Phase 5."
)

config = AdaConfig.from_env()
principal = current_principal(config)

uploaded = st.file_uploader(
    "Choose a file",
    type=["xlsx", "xls", "csv", "txt", "pdf", "doc", "docx"],
)
left, right = st.columns(2)
classification = left.selectbox("Classification", ["public", "internal", "restricted"])
pii_level = right.selectbox("PII level", ["public", "internal", "sensitive"])

if st.button("Store and register", disabled=uploaded is None):
    assert uploaded is not None
    try:
        document_id = ingest_file(
            uploaded.getvalue(),
            filename=uploaded.name,
            classification=classification,
            pii_level=pii_level,
            config=config,
            principal=principal,
        )
        st.success(f"Registered document `{document_id}`.")
    except Exception as exc:
        st.error(f"Intake failed: {exc}")

st.subheader("Registered files")
documents = list_documents(config)
if documents:
    st.dataframe(
        [
            {
                "document_id": item.document_id,
                "filename": item.filename,
                "classification": item.classification,
                "pii_level": item.pii_level,
                "uploaded_by": item.uploaded_by,
                "upload_date": item.upload_date,
                "status": item.status,
            }
            for item in documents
        ],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.caption("No files registered yet.")
