import os
import time
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="RAG—PDF QA", page_icon="📄", layout="wide")

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []

st.title("📄 RAG — PDF Question Answering")

with st.sidebar:
    st.header("Settings")
    API_BASE = st.text_input("FastAPI base URL", value=API_BASE, help="e.g., http://localhost:8000")
    top_k = st.number_input("Top-K passages", value=5, min_value=1, max_value=20, step=1)
    st.markdown("---")
    
    # Health check
    try:
        health = requests.get(f"{API_BASE}/health", timeout=2).json()
        st.success(f"✅ API Connected")
        st.caption(f"Version: {health.get('version', 'unknown')}")
    except:
        st.error("❌ API Disconnected")
    
    st.markdown("---")
    st.caption("Tip: run with `streamlit run app.py`")

# -------- Upload panel --------
st.subheader("1) Upload PDFs")
up = st.file_uploader("Choose a PDF", type=["pdf"])
col_u1, col_u2 = st.columns([1, 2])

def poll_task(api_base: str, task_id: str, timeout_s=30, interval_s=1.0):
    """Poll /task/{task_id} endpoint"""
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
    if st.button("Upload", type="primary"):
        if up is None:
            st.warning("Select a PDF first.")
        else:
            files = {"file": (up.name, up.getvalue(), "application/pdf")}
            try:
                with st.spinner(f"Uploading {up.name}..."):
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
                    st.success(f"✅ Uploaded: {up.name}")
                    st.info(f"Task ID: {doc['task_id']}")
            except requests.HTTPError as e:
                st.error(f"Upload failed: {e.response.text if e.response else e}")
            except Exception as e:
                st.error(f"Upload failed: {e}")

with col_u2:
    if st.button("🔄 Check Ingestion Status"):
        if not st.session_state.uploaded_docs:
            st.info("No documents uploaded yet.")
        else:
            with st.spinner("Checking status..."):
                updated = []
                for d in st.session_state.uploaded_docs:
                    if not d.get("task_id"):
                        updated.append(d)
                        continue
                    try:
                        status = poll_task(API_BASE, d["task_id"], timeout_s=2, interval_s=0.5)
                        state = status.get("state", "UNKNOWN")
                        d["status"] = state
                        
                        # Add result info if available
                        if state == "SUCCESS" and "result" in status:
                            result = status["result"]
                            if isinstance(result, dict):
                                d["chunks"] = result.get("chunks", "?")
                        elif state == "FAILURE":
                            d["error"] = str(status.get("error", "Unknown error"))
                    except Exception as e:
                        d["status"] = f"ERROR: {e}"
                    updated.append(d)
                st.session_state.uploaded_docs = updated
            st.success("Status updated!")

if st.session_state.uploaded_docs:
    st.write("**Uploaded Documents**")
    
    # Display table
    display_docs = []
    for d in st.session_state.uploaded_docs:
        display_docs.append({
            "Filename": d["filename"],
            "Status": d["status"],
            "Chunks": d.get("chunks", "-"),
            "Document ID": d["document_id"][:8] + "..." if d.get("document_id") else "N/A",
        })
    
    st.dataframe(display_docs, use_container_width=True)
    
    # Clear button
    if st.button("Clear History"):
        st.session_state.uploaded_docs = []
        st.rerun()

st.markdown("---")

# -------- Query panel --------
st.subheader("2) Ask a Question")

question = st.text_area(
    "Your question", 
    placeholder="e.g., What is the main topic of the document?",
    height=100
)

c1, c2 = st.columns([1, 3])
with c1:
    ask = st.button("🔍 Search", type="primary")

if ask:
    if not question.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        try:
            with st.spinner("Searching documents..."):
                # FIXED: Use GET request with query parameters (matching backend)
                params = {"q": question, "top_k": int(top_k)}
                r = requests.get(f"{API_BASE}/query", params=params, timeout=60)
                r.raise_for_status()
                data = r.json()
            
            # FIXED: Use correct response field names
            results = data.get("results", [])
            query_text = data.get("query", question)
            
            if not results:
                st.warning("No results found. Make sure documents are uploaded and processed.")
            else:
                st.success(f"✅ Found {len(results)} relevant passages")
                
                # Display results
                st.markdown("### 📑 Top Results")
                
                for i, result in enumerate(results, 1):
                    # FIXED: Use correct field names from backend
                    similarity = result.get("similarity", 0)
                    content = result.get("content", "")
                    doc_id = result.get("document_id", "unknown")
                    chunk_id = result.get("chunk_id", "unknown")
                    filename = result.get("document_filename", "Unknown")
                    
                    # Color code by similarity
                    if similarity > 0.7:
                        emoji = "🟢"
                    elif similarity > 0.5:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"
                    
                    with st.expander(
                        f"{emoji} Result #{i} — Score: {similarity:.3f} — {filename}",
                        expanded=(i == 1)  # Expand first result
                    ):
                        st.markdown(f"**Similarity Score:** {similarity:.3f}")
                        st.markdown(f"**Source:** {filename}")
                        st.markdown(f"**Document ID:** `{doc_id[:16]}...`")
                        st.markdown("---")
                        st.markdown("**Content:**")
                        st.write(content)
                
                # Optional: Show combined context
                with st.expander("📄 View Combined Context"):
                    combined = "\n\n".join([
                        f"[Passage {i+1}] (score: {r.get('similarity', 0):.3f})\n{r.get('content', '')}"
                        for i, r in enumerate(results)
                    ])
                    st.text_area("Combined Context", combined, height=400)
                
        except requests.HTTPError as e:
            st.error(f"❌ HTTP Error: {e}")
            if e.response is not None:
                st.code(e.response.text)
        except Exception as e:
            st.error(f"❌ Request failed: {e}")

# Footer
st.markdown("---")
st.caption(f"Connected to: {API_BASE}")