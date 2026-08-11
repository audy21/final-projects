import streamlit as st
import requests

API_URL = "http://localhost:8001"

st.set_page_config(page_title="API Sandbox Generator", layout="wide")
st.title("API Sandbox Generator")

tab1, tab2 = st.tabs(["Parse Spec", "Sandbox"])

with tab1:
    st.subheader("Paste your OpenAPI spec")
    spec_input = st.text_area("OpenAPI spec (YAML or JSON)", height=300)

    if st.button("Parse") and spec_input:
        resp = requests.post(f"{API_URL}/parse", json={"spec": spec_input})
        data = resp.json()

        if data.get("status") == "parsed":
            st.session_state["endpoints"] = data["endpoints"]
            st.success(f"Parsed {data['total']} endpoints")
        else:
            st.error(data.get("message", "Parse failed"))

with tab2:
    st.subheader("Test endpoints with mock data")

    if "endpoints" not in st.session_state or not st.session_state["endpoints"]:
        st.info("Parse a spec first (Tab 1)")
    else:
        endpoints = st.session_state["endpoints"]
        labels = [f"{e['method']} {e['path']} - {e['summary']}" for e in endpoints]
        selected = st.selectbox("Select endpoint", labels)
        endpoint = endpoints[labels.index(selected)]

        status_code = st.selectbox("Status code", [str(code) for code in endpoint["responses"].keys()])

        if st.button("Generate mock"):
            resp = requests.post(
                f"{API_URL}/generate",
                json={
                    "spec": spec_input,
                    "endpoint_path": endpoint["path"],
                    "method": endpoint["method"].lower(),
                    "status_code": status_code
                }
            )
            data = resp.json()
            if data.get("status") == "generated":
                st.json(data["mock_response"])
            else:
                st.error(data.get("message", "Generation failed"))