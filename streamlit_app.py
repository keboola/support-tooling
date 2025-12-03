import base64
import json
import os
import typing

import streamlit as st

import kbc.kbcapi_scripts
from tabs import encryptor, projectmgr, ddmonitoring

image_path = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Keboola Admin Tools", page_icon=image_path + "/static/keboola.png",
                   layout="centered"
                   )

logo_image = image_path + "/static/keboola_logo.png"
logo_html = f'<div style="display: flex; justify-content: flex-end;"><img src="data:image/png;base64,{base64.b64encode(open(logo_image, "rb").read()).decode()}" style="width: 150px; margin-left: -10px;"></div>'
st.markdown(f"{logo_html}", unsafe_allow_html=True)

st.title('Keboola Admin Tools 👩🏻‍🔬')


def render_responses(consumer_responses: dict, type: str = 'json'):
    if consumer_responses:
        with st.container(border=False):
            for i, (stack, response) in enumerate(consumer_responses.items()):
                if response['status'] == "success":
                    color = "green"
                else:
                    color = "red"
                with st.expander(f":{color}[{stack}]", expanded=False):
                    if response['status'] == "success":
                        if type == 'json':
                            st.json(response['response'], expanded=True)
                        else:
                            st.dataframe(response['response'], use_container_width=True, )
                    else:
                        st.error(response['response'])


def _perform_consumer_operation(stack_tokens: dict,
                                operation: typing.Literal['GET', 'CREATE', 'PATCH'],
                                **params) -> dict:
    if operation == 'GET':
        method = kbc.kbcapi_scripts.get_oauth_consumers
    elif operation == 'LIST':
        method = kbc.kbcapi_scripts.list_oauth_consumers
    elif operation == 'CREATE':
        method = kbc.kbcapi_scripts.create_oauth_consumer
    elif operation == 'PATCH':
        method = kbc.kbcapi_scripts.patch_oauth_consumer
    else:
        raise ValueError(f"Invalid operation: {operation}")

    consumer_responses = {}
    for stack, token in stack_tokens.items():
        try:
            response = method(stack, token, **params)
            consumer_responses[stack] = {"status": "success", "response": response}
        except Exception as e:
            json_response = {}
            try:
                json_response = e.response.json()
            except Exception:
                pass
            consumer_responses[stack] = {"status": "error", "response": f'{str(e)}  {json_response}'}

    if operation in ['GET', 'LIST']:
        st.session_state[f'{operation}_consumer_responses'] = consumer_responses

    return consumer_responses


def display_main_content():
    # streamlit text element to input formatted JSON data
    default_value = {
        "eu-central-1.keboola.com": "TOKEN",
        "keboola.com": "TOKEN",
        "europe-west2.gcp.keboola.com": "TOKEN",
        "europe-west3.gcp.keboola.com": "TOKEN",
        "us-east4.gcp.keboola.com": "TOKEN",
        "north-europe.azure.keboola.com": "TOKEN"
    }
    placeholder = json.dumps(default_value, indent=2)
    stack_tokens = st.text_area("Stack OAuth tokens", value=placeholder, height=200, help="Enter JSON data")
    stack_tokens_json = json.loads(stack_tokens)
    if not stack_tokens:
        st.warning("To continue, please enter your Stack Tokens.")
        return

    st.divider()
    st.subheader("Inspect OAuth Consumer setup")

    st.divider()
    consumer_list = st.session_state.get('LIST_consumer_responses') or {}
    if st.button("List Existing Consumers", type="primary"):
        consumer_list = _perform_consumer_operation(stack_tokens_json, 'LIST')

    render_responses(consumer_list, type='table')

    st.divider()

    component_id = st.text_input('Enter the Component ID', help="e.g. kds-team.ex-hubspot")

    consumer_responses = st.session_state.get('GET_consumer_responses') or {}
    if st.button("List Consumer Details", type="primary"):
        consumer_responses = _perform_consumer_operation(stack_tokens_json, 'GET', component_id=component_id)
    render_responses(consumer_responses)
    enabled_stacks = [stack for stack, response in consumer_responses.items() if response['status'] == 'success']

    st.divider()
    st.subheader("Update OAuth Consumer")

    selected_stacks = st.multiselect(
        'Select stacks',
        list(stack_tokens_json.keys()), [])

    operation = st.selectbox('Operation', ['CREATE', 'PATCH'])

    consumer_payload = st.text_area("Consumer Parameters", placeholder={}, height=300, help="Enter JSON data")

    if consumer_payload:

        try:
            payload_json = json.loads(consumer_payload)
        except json.JSONDecodeError:
            st.error("The payload is not a valid JSON.")
            return

        if not payload_json:
            st.error("Please provide the payload.")
            return

        if operation == 'PATCH' and payload_json and not 'app_secret' in payload_json:
            st.error("Please provide the app_secret in the payload, "
                     "otherwise it will be rewritten with invalid value on PATCH")
            return

        if st.button("EXECUTE", type="primary"):
            filtered_stack_tokens = {stack: stack_tokens_json[stack] for stack in selected_stacks}
            consumer_responses = _perform_consumer_operation(filtered_stack_tokens, operation, payload=payload_json,
                                                             component_id=component_id)
            render_responses(consumer_responses)

    st.divider()
    st.subheader("Update Developer Portal")

    if not (consumer_responses and component_id):
        st.warning("Please fill in the Component ID and list the consumer details first.")
        return

    with st.container(border=True):
        st.markdown("#### Login")
        email = st.text_input("Username",
                              help="Enter the Service Account Username") or st.session_state.get('dev_portal_email')
        password = st.text_input("Password", type="password",
                                 help="Enter the Service Account Password") or st.session_state.get(
            'dev_portal_password')
        st.session_state['dev_portal_email'] = email
        st.session_state['dev_portal_password'] = password

        if st.button("Login", type="primary"):
            response = kbc.kbcapi_scripts.developer_portal_login(email, password)
            if response.get('token'):
                st.session_state['dev_portal_access_token'] = response['token']
                st.success("Login successful")
            else:
                st.error(response)

    st.info("This updates the stack permissions and will add any of the stacks where the consumer is registered")
    if st.button("Update stack permissions", type="primary",
                 help="This updates the stack permissions "
                      "and will add any of the stacks where the consumer is registered"):
        vendor, app = component_id.split('.')

        resp = kbc.kbcapi_scripts.developer_portal_patch_app_permissions(st.session_state['dev_portal_access_token'],
                                                                         vendor,
                                                                         component_id, enabled_stacks)
        st.success('Permissions updated successfully')
        st.json(resp['permissions'])

    st.divider()
    st.subheader("Did you set redirect URLs?")
    st.markdown("Make sure you set all the redirect URLs in the respective app registration.")
    if st.button("Show redirect URLs", type="primary"):
        stack_urls = []
        for stack in enabled_stacks:
            stack_urls.append(f"https://oauth.{stack}/authorize/{component_id}/callback")

        st.dataframe({"urls": stack_urls}, use_container_width=True, column_config={
            "urls": st.column_config.TextColumn(
                "Redirect URLs",
                disabled=True)
        })


def main():
    tab1, tab2, tab3, tab4 = st.tabs(["OAuth Manager", "Encryption API", "Project Features", "DD Monitoring"])
    with tab1:
        display_main_content()

    with tab2:
        encryptor.display_content()

    with tab3:
        projectmgr.display_content()

    with tab4:
        ddmonitoring.display_content()

    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
