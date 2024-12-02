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


def get_deleted_projects(api_url, token):
    response = requests.get(
        f"{api_url}/deleted-projects",
        headers=get_headers(token),
        params={"limit": "1000"}
    )
    return response.json()


def get_deleted_project(api_url, token, deleted_project_id):
    response = requests.get(
        f"{api_url}/deleted_projects/{deleted_project_id}",
        headers=get_headers(token)
    )
    return response.json()


def restore_deleted_project(api_url, token, deleted_project_id, new_expiration_days=0):
    response = requests.delete(
        f"{api_url}/deleted-projects/{deleted_project_id}",
        headers=get_headers(token),
        json={"expirationDays": new_expiration_days}
    )
    return response


def get_project(api_url, token, project_id):
    response = requests.get(
        f"{api_url}/projects/{project_id}",
        headers=get_headers(token)
    )
    return response.json()


# Streamlit UI
st.title("Keboola User Features Manager")

hostname_suffix = st.selectbox(
    "Which stack? Multitenants only, sorry",
    hostname_suffix_options.keys(),
    format_func=lambda key: hostname_suffix_options[key]
)

api_url = f"https://connection.{hostname_suffix}/manage"

link_to_tokens = f"[Go get token](https://connection.{hostname_suffix}/admin/account/access-tokens)"

st.markdown(link_to_tokens, unsafe_allow_html=True)
token = st.text_input("Keboola Manage Token", type="password")

deleted_projects = get_deleted_projects(api_url, token)

options = {}
for deleted_project in deleted_projects:
    options[deleted_project['id']] = f"{deleted_project['organization']['name']} : {deleted_project['id']} - {deleted_project['name']}"


selected_project = st.selectbox(
    "Select by ID",
    options=list(options.keys()),
    format_func=lambda x: options[x]
)

if selected_project:
    expiration_days = st.text_input("Days until expiration (0 = no expiry):", 0)
    undelete_project = st.button(f"Restore Selected Deleted Project {selected_project} ?")
    deleted_project = get_deleted_project(api_url, token, selected_project)
    if undelete_project:
        result = restore_deleted_project(api_url, token, selected_project)
        project = get_project(api_url, token, selected_project)
        st.subheader(f"The project was restored")
        st.write(project)

# Select box with name as the searchable value but still returns the ID
# name_options = {item['id']: item['name'] for item in json_data}  # ID to Name mapping
# selected_by_name = st.selectbox("Select by Name", options=list(name_options.keys()), format_func=lambda x: name_options[x])
