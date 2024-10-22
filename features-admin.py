import streamlit as st
import requests

# Keboola API token (ensure you keep this secure)

hostname_suffix_options = {
    "keboola.com": "AWS us-east-1",
    "eu-central-1.keboola.com": "AWS eu-central-1",
    "north-europe.azure.keboola.com": "Azure North Europe",
    "us-east4.gcp.keboola.com": "GCP US East4",
    "europe-west3.gcp.keboola.com": "GCP Europe West3"
}

def get_headers(token):
    return {
        "X-KBC-ManageApiToken": token,
        "Content-Type": "application/json"
    }


# Helper functions for API interactions
def get_project_features(api_url, token, project_id):
    response = requests.get(
        f"{api_url}/projects/{project_id}/features",
        headers=get_headers(token)
    )
    return response.json()


def add_project_feature(api_url, token, project_id, feature_name):
    response = requests.post(
        f"{api_url}/projects/{project_id}/features",
        headers=get_headers(token),
        json={"feature": feature_name}
    )
    return response.json()


def remove_project_feature(api_url, token, project_id, feature_name):
    response = requests.delete(
        f"{api_url}/projects/{project_id}/features/{feature_name}",
        headers=get_headers(token)
    )
    return response.json()


def get_project_details(api_url, token, project_id):
    response = requests.get(
        f"{api_url}/projects/{project_id}",
        headers=get_headers(token)
    )
    return response.json()

def get_features_list(api_url, token):
    response = requests.get(
        f"{api_url}/features?type=project",
        headers=get_headers(token)
    )
    return response.json()

# Streamlit UI
st.title("Keboola Project Features Manager")

hostname_suffix = st.selectbox(
    "Which stack? Multitenants only, sorry",
    hostname_suffix_options.keys(),
    format_func=lambda key: hostname_suffix_options[key]
)

api_url = f"https://connection.{hostname_suffix}/manage"

link_to_tokens = f"[Go get token](https://connection.{hostname_suffix}/admin/account/access-tokens)"

st.markdown(link_to_tokens, unsafe_allow_html=True)
token = st.text_input("Keboola Manage Token", type="password")

# features_list = get_features_list(api_url, token)

project_id = st.text_input("Enter Project ID")

if project_id:

    st.header(f"Manage Features for Project {project_id}")
    project_details = get_project_details(api_url, token, project_id)
    project_name = project_details["name"]
    st.subheader(f"Project Name: {project_name}")
    st.subheader("Current Features on the project")
    if st.button("Refresh Project Features"):
        project_details = get_project_details(api_url, token, project_id)
    st.write(project_details["features"])

    st.subheader("Add Feature")
    new_feature = st.text_input("Feature Name to Add")
    if st.button("Add Feature"):
        if new_feature:
            result = add_project_feature(api_url, token, project_id, new_feature)
            st.write(result)
        else:
            st.error("Please enter a feature name")

    st.subheader("Remove Feature")
    remove_feature = st.text_input("Feature Name to Remove")
    if st.button("Remove Feature"):
        if remove_feature:
            result = remove_project_feature(api_url, token, project_id, remove_feature)
            st.write("the feature was removed")
        else:
            st.error("Please enter a feature name")
