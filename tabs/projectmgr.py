import streamlit as st

import kbc.kbcapi_scripts


def display_content():
    stack = st.selectbox("Stack", ["eu-central-1.keboola.com",
                                   "keboola.com",
                                   "north-europe.azure.keboola.com",
                                   "europe-west2.gcp.keboola.com",
                                   "europe-west3.gcp.keboola.com",
                                   "us-east4.gcp.keboola.com",
                                   "Other (manual entry)"], key='pgm')

    if stack == "Other (manual entry)":
        stack = st.text_input("Enter custom stack URL", key='custom_stack')

    manage_token = st.text_input("Manage Token", type="password", key='pgmtoken')
    if not manage_token:
        st.warning("Please fill in the Manage Token first.")
        return

    project_id = st.text_input("Project ID", key='pgid')


    if not project_id:
        st.warning("Please fill in the Project ID first.")
        return

    selected_project = kbc.kbcapi_scripts.get_project_detail(stack, manage_token, project_id)
    st.markdown(f"**Selected project name**: **`{selected_project['name']}`**")
    st.markdown(f"**Organization name**: **`{selected_project['organization']['name']}`**")

    st.divider()
    st.empty()

    if st.button("Get project features", type="primary"):
        result = kbc.kbcapi_scripts.list_project_features(stack, manage_token, project_id)

        st.json(result)

    st.divider()
    st.empty()
    operation = st.selectbox('Operation', ['ADD', 'REMOVE'], key='pgmop')
    if manage_token:
        features = kbc.kbcapi_scripts.list_features(stack, manage_token)
        selected_feature = st.selectbox("Feature", [f['name'] for f in features], key='pgmfeat')
        # Text input for custom feature
        custom_feature = st.text_input("Or add a custom feature", key='pgmcustomfeat')

        # Combine selected feature and custom feature
        if custom_feature:
            final_feature = custom_feature
        else:
            final_feature = selected_feature

        st.write(f"Selected or custom feature: {final_feature}")

        if st.button("Perform action", type="primary"):
            if operation == 'ADD':
                result = kbc.kbcapi_scripts.add_feature(stack, manage_token, project_id, final_feature)
            else:
                result = kbc.kbcapi_scripts.remove_feature(stack, manage_token, project_id, final_feature)

            st.json(result)
