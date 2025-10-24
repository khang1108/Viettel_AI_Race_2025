import os
import time
import json
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="RAG—PDF QA", page_icon="📄", layout="wide")

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []   # list of {"document_id","filename","task_id","status"}

st.title("📄 RAG — PDF Question Answering")

with st.sidebar:
    st.header("Settings")
    API_BASE = st.text_input("FastAPI base URL", value=API_BASE, help="e.g., http://localhost:8000")
    top_k = st.number_input("Top-K passages", value=6, min_value=1, max_value=50, step=1)
    st.markdown("---")
    st.caption("Tip: you can run this with `streamlit run app.py`")

# -------- Upload panel --------
st.subheader("1) Upload PDFs")
up = st.file_uploader("Choose a PDF", type=["pdf"])
col_u1, col_u2 = st.columns([1, 2])

def poll_task(api_base: str, task_id: str, timeout_s=30, interval_s=1.0):
    """Optional: poll /task/{task_id} if you add that route on the backend."""
    url = f"{api_base}/task/{task_id}"
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                data = r.json()
                state = data.get("state", "")
                if state in {"SUCCESS", "FAILURE", "REVOKED"}:
                    return data
            time.sleep(interval_s)
        except Exception:
            time.sleep(interval_s)
    return {"state": "PENDING"}

with col_u1:
    if st.button("Upload"):
        if up is None:
            st.warning("Select a PDF first.")
        else:
            files = {"file": (up.name, up.getvalue(), "application/pdf")}
            try:
                r = requests.post(f"{API_BASE}/upload", files=files, timeout=120)
                r.raise_for_status()
                payload = r.json()
                doc = {
                    "document_id": payload.get("document_id"),
                    "task_id": payload.get("task_id"),
                    "filename": up.name,
                    "status": "queued",
                }
                st.session_state.uploaded_docs.append(doc)
                st.success(f"Uploaded: {up.name}")
            except Exception as e:
                st.error(f"Upload failed: {e}")

with col_u2:
    if st.button("Check Ingestion Status"):
        updated = []
        for d in st.session_state.uploaded_docs:
            if not d.get("task_id"):
                updated.append(d)
                continue
            try:
                status = poll_task(API_BASE, d["task_id"], timeout_s=5, interval_s=0.5)
                d["status"] = status.get("state", "UNKNOWN")
            except Exception:
                d["status"] = "UNKNOWN"
            updated.append(d)
        st.session_state.uploaded_docs = updated

if st.session_state.uploaded_docs:
    st.write("**Uploaded documents**")
    st.dataframe(
        [{"filename": d["filename"], "document_id": d["document_id"], "task_id": d["task_id"], "status": d["status"]}
         for d in st.session_state.uploaded_docs],
        use_container_width=True
    )

st.markdown("---")

# -------- Query panel --------
st.subheader("2) Ask a question")
question = st.text_area("Your question")

c1, c2 = st.columns([1, 3])
with c1:
    ask = st.button("Ask")

if ask:
    if not question.strip():
        st.warning("Enter a question.")
    else:
        try:
            payload = {"question": question, "top_k": int(top_k)}
            r = requests.post(f"{API_BASE}/query", json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            st.success("Retrieved context")
            # Show synthesized context (if your backend later adds LLM answer, render it here)
            st.markdown("**Context (top passages):**")
            st.code(data.get("context", "")[:5000])  # safety truncate

            st.markdown("**Matches:**")
            matches = data.get("matches", [])
            for i, m in enumerate(matches, 1):
                with st.expander(f"#{i}  — score: {m.get('score', 0):.3f}  — doc: {m.get('document_id')}  — ord: {m.get('ord')}"):
                    st.write(m.get("content", "")[:5000])
        except requests.HTTPError as e:
            st.error(f"HTTP error: {e} — {e.response.text if e.response is not None else ''}")
        except Exception as e:
            st.error(f"Request failed: {e}")
