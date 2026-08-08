import streamlit as st
import requests

API_URL = "http://localhost:8000"
API_KEY = None

st.set_page_config(page_title="AI API Hub", layout="wide")
st.title("AI API Hub")

with st.sidebar:
    st.header("Configuration")
    API_KEY = st.text_input("API Key", type="password")
    endpoint = st.selectbox("Endpoint", ["Chat", "RAG (Ask)", "RAG (Ingest)", "Extract", "Agent"])

if endpoint == "Chat":
    message = st.text_area("Message")
    system_prompt = st.text_input("System prompt", "You are a helpful assistant.")
    if st.button("Send") and API_KEY:
        resp = requests.post(f"{API_URL}/chat", json={"message": message, "system_prompt": system_prompt}, headers={"x-api-key": API_KEY})
        st.markdown(resp.json()["reply"])

elif endpoint == "RAG (Ingest)":
    text = st.text_area("Document text")
    doc_id = st.text_input("Document ID")
    if st.button("Ingest") and API_KEY:
        resp = requests.post(f"{API_URL}/rag/ingest", json={"text": text, "document_id": doc_id}, headers={"x-api-key": API_KEY})
        st.json(resp.json())

elif endpoint == "RAG (Ask)":
    question = st.text_input("Question")
    top_k = st.slider("Top K", 1, 10, 3)
    if st.button("Ask") and API_KEY:
        resp = requests.post(f"{API_URL}/rag", json={"question": question, "top_k": top_k}, headers={"x-api-key": API_KEY})
        data = resp.json()
        st.markdown(data["answer"])
        with st.expander("Sources"):
            for s in data["sources"]:
                st.caption(s[:200])

elif endpoint == "Extract":
    text = st.text_area("Text to extract from")
    fields = st.text_input("Fields (e.g. name, age, city)")
    if st.button("Extract") and API_KEY:
        resp = requests.post(f"{API_URL}/extract", json={"text": text, "fields": fields}, headers={"x-api-key": API_KEY})
        st.json(resp.json()["result"])

elif endpoint == "Agent":
    question = st.text_input("Research question")
    if st.button("Research") and API_KEY:
        with st.spinner("Agent researching..."):
            resp = requests.post(f"{API_URL}/agent", json={"question": question}, headers={"x-api-key": API_KEY})
        data = resp.json()
        st.markdown(data["answer"])
        with st.expander("Sources"):
            for s in data["sources"]:
                st.caption(s[:200])