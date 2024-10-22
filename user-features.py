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
def get_user_details(api_url, token, user_email):
    response = requests.get(
        f"{api_url}/users/{user_email}",
        headers=get_headers(token)
    )
    return response.json()


def add_user_feature(api_url, token, user_email, feature_name):
    response = requests.post(
        f"{api_url}/users/{user_email}/features",
        headers=get_headers(token),
        json={"feature": feature_name}
    )
    return response.json()


def get_features_list(api_url, token):
    response = requests.get(
        f"{api_url}/features?type=admin",
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

features_list = get_features_list(api_url, token)
feature_names = [feature["name"] for feature in features_list]

feature_name = st.selectbox(
    "Which feature do you want to apply?",
    feature_names
)

if 'user_list' not in st.session_state:
    st.session_state.user_list = []

# Create a text input field
user_to_add = st.text_input("Add user to grant: ", value="")

# Add a button to submit the text input
if st.button("Add to List"):
    # Append the text input value to the list when the button is clicked
    if user_to_add:
        user_details = get_user_details(api_url, token, user_to_add)
        if user_details["id"]:
            st.session_state.user_list.append(user_to_add)
            st.success(f"'{user_details}' added to the list.")

# Display the list of inputs
st.write("List of users to apply this feature to:")
st.write(st.session_state.user_list)

if st.button(f"Grant the feature {feature_name} to the listed users"):
    for user_email in st.session_state.user_list:
        add_user_feature(api_url, token, user_email, feature_name)
        st.success(f"{user_email} has been granted {feature_name}")

for user_email in st.session_state.user_list:
    user_details = get_user_details(api_url, token, user_email)
    st.write(user_details)
