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
def ensure_membership(st, api_url, token, user_email, member_checkboxes, nonmember_checkboxes):
    for maintainer_id, checked in member_checkboxes.items():
        if not checked:
            requests.post(
                f"{api_url}/maintainers/{maintainer_id}/users",
                headers=get_headers(token),
                json={"email": user_email}
            )
            st.write(f"removing from maintainer {maintainer_id}")
    for maintainer_id, checked in nonmember_checkboxes.items():
        if checked:
            st.write(f"adding to maintainer {maintainer_id}")
            requests.post(
                f"{api_url}/maintainers/{maintainer_id}/users",
                headers=get_headers(token),
                json={"email": user_email}
            )


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


def get_maintainer_users(api_url, token, maintainer_id):
    response = requests.get(
        f"{api_url}/maintainers/{maintainer_id}/users",
        headers=get_headers(token)
    )
    return response.json()


def get_user_details(api_url, token, user_email):
    response = requests.get(
        f"{api_url}/users/{user_email}",
        headers=get_headers(token)
    )
    return response.json()


def get_maintainers(api_url, token):
    response = requests.get(
        f"{api_url}/maintainers",
        headers=get_headers(token)
    )
    return response.json()

def user_in_maintainer(api_url, token, user_email, maintainer):
    maintainer_users = get_maintainer_users(api_url, token, maintainer['id'])
    for user in maintainer_users:
        if user['email'] == user_email:
            return True
    return False


# Streamlit UI
st.title("Keboola Maintainer Manager")

hostname_suffix = st.selectbox(
    "Which stack? Multitenants only, sorry",
    hostname_suffix_options.keys(),
    format_func=lambda key: hostname_suffix_options[key]
)

api_url = f"https://connection.{hostname_suffix}/manage"

link_to_tokens = f"[Go get token](https://connection.{hostname_suffix}/admin/account/access-tokens)"

st.markdown(link_to_tokens, unsafe_allow_html=True)
token = st.text_input("Keboola Manage Token", type="password")

user_email = st.text_input("Enter User Email")

if user_email:
    st.header(f"Manage Maintainers for user {user_email}")
    user_details = get_user_details(api_url, token, user_email)
    st.write(user_details)

    maintainers = get_maintainers(api_url, token)

    member_maintainers = []
    nonmember_maintainers = []

    for maintainer in maintainers:
        if user_in_maintainer(api_url, token, user_email, maintainer):
            member_maintainers.append(maintainer)
        else:
            nonmember_maintainers.append(maintainer)

    member_checkboxes = {}
    st.subheader(f"{user_email} is a member of:")
    for maintainer in member_maintainers:
        member_checkboxes[maintainer['id']] = st.checkbox(maintainer["name"], True)

    st.subheader(f"{user_email} is NOT a member of:")

    nonmember_checkboxes = {}
    check_all_box = st.checkbox('Check All the below')
    for maintainer in nonmember_maintainers:
        if check_all_box:
            nonmember_checkboxes[maintainer['id']] = st.checkbox(maintainer["name"], True)
        else:
            nonmember_checkboxes[maintainer['id']] = st.checkbox(maintainer["name"])

    if st.button(f"Ensure {user_email} is a member of all selected"):
        ensure_membership(st, api_url, token, user_email, member_checkboxes, nonmember_checkboxes)
