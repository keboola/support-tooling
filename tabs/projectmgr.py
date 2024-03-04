import streamlit as st

import kbc.kbcapi_scripts


def display_content():
    stack = st.selectbox("Stack", ["eu-central-1.keboola.com",
                                   "keboola.com",
                                   "north-europe.azure.keboola.com",
                                   "europe-west2.gcp.keboola.com",
                                   "europe-west3.gcp.keboola.com",
                                   "us-east4.gcp.keboola.com"], key='pgm')

    manage_token = st.text_input("Manage Token", type="password", key='pgmtoken')
    if not manage_token:
        st.warning("Please fill in the Manage Token first.")
        return

    project_id = st.text_input("Project ID", key='pgid')

    st.divider()
    st.empty()

    if not project_id:
        st.warning("Please fill in the Project ID first.")
        return

    if st.button("Get project features", type="primary"):
        result = kbc.kbcapi_scripts.list_project_features(stack, manage_token, project_id)

        st.json(result)

    st.divider()
    st.empty()
    operation = st.selectbox('Operation', ['ADD', 'REMOVE'], key='pgmop')
    if manage_token:
        features = kbc.kbcapi_scripts.list_features(stack, manage_token)
        feature = st.selectbox("Feature", [f['name'] for f in features], key='pgmfeat')

    if st.button("Perform action", type="primary"):
        if operation == 'ADD':
            result = kbc.kbcapi_scripts.add_feature(stack, manage_token, project_id, feature)
        else:
            result = kbc.kbcapi_scripts.remove_feature(stack, manage_token, project_id, feature)

        st.json(result)
