import streamlit as st

import kbc.kbcapi_scripts


def display_content():
    stack = st.selectbox("Stack", ["eu-central-1.keboola.com",
                                   "keboola.com",
                                   "north-europe.azure.keboola.com",
                                   "europe-west2.gcp.keboola.com",
                                   "europe-west3.gcp.keboola.com",
                                   "us-east4.gcp.keboola.com"])
    project_id = st.text_input("Project ID")
    component_id = st.text_input("Component ID")
    config_id = st.text_input("Config ID")

    st.divider()
    st.empty()

    data = st.text_area("String to encrpyt")

    if not (project_id or component_id or config_id):
        st.warning("Please fill in the Project ID, Component ID or Config ID first.")
        st.stop()

    if data and st.button("Encrypt", type="primary"):
        result = kbc.kbcapi_scripts.encrypt(data, component_id, project_id, config_id, stack)

        st.success("Encrypted successfully")
        st.code(result, language="Python")
