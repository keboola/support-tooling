import streamlit as st
import requests
from urllib.parse import urlparse

import kbc.kbcapi_scripts


STACK_OPTIONS = [
    "eu-central-1.keboola.com",
    "keboola.com",
    "north-europe.azure.keboola.com",
    "europe-west2.gcp.keboola.com",
    "europe-west3.gcp.keboola.com",
    "us-east4.gcp.keboola.com",
    "Other (manual entry)",
]


def _clean_stack_value(raw_stack: str) -> str:
    if not raw_stack:
        return ""
    stack_value = raw_stack.strip()
    if not stack_value:
        return ""
    if stack_value.startswith("http"):
        parsed = urlparse(stack_value)
        host = parsed.netloc or parsed.path
    else:
        host = stack_value
    host = host.strip('/')
    if host.startswith("connection."):
        host = host.replace("connection.", "", 1)
    return host


def _http_error_details(error: requests.HTTPError) -> str:
    status_code = getattr(error.response, 'status_code', 'N/A')
    detail = ''
    if getattr(error, 'response', None) is not None:
        try:
            payload = error.response.json()
            if isinstance(payload, dict):
                detail = payload.get('message') or payload.get('error') or str(payload)
            else:
                detail = str(payload)
        except ValueError:
            detail = error.response.text
    if not detail:
        detail = str(error)
    return f"{status_code}: {detail}"


def _format_organization_option(organization: dict) -> str:
    name = organization.get('name') or 'Unnamed organization'
    org_id = organization.get('id', 'N/A')
    return f"{name} ({org_id})"


def _format_project_option(project: dict) -> str:
    name = project.get('name') or 'Unnamed project'
    project_id = project.get('id', 'N/A')
    return f"{name} ({project_id})"


def display_content():
    # 1. Token Management Section
    stack_selection = st.selectbox("Stack", STACK_OPTIONS, key='pgm_stack')
    if stack_selection == "Other (manual entry)":
        raw_stack = st.text_input("Enter custom stack URL", key='pgm_custom_stack')
    else:
        raw_stack = stack_selection

    stack = _clean_stack_value(raw_stack)

    if stack:
        st.markdown(f"[Go get token](https://connection.{stack}/admin/account/access-tokens)", unsafe_allow_html=True)

    manage_token = st.text_input("Manage Token", type="password", key='pgm_manage_token')

    if not stack:
        st.warning("Please select or enter the stack first.")
        return

    if not manage_token:
        st.warning("Please fill in the Manage Token first.")
        return

    st.divider()

    # 2. Project/Organization Selection Section
    scope = st.radio("Apply to", ["Single project", "Organization projects"], key='pgm_scope')

    if scope == "Single project":
        selected_project, project_id = _render_single_project_selection(stack, manage_token)
        if not selected_project:
            return
        target_projects = None
    else:
        selected_organization, target_projects = _render_organization_selection(stack, manage_token)
        if not selected_organization:
            return
        project_id = None
        selected_project = None

    st.divider()

    # 3. Feature Selection Section
    operation = st.selectbox('Operation', ['ADD', 'REMOVE'], key='pgm_operation')

    try:
        features = kbc.kbcapi_scripts.list_features(stack, manage_token)
    except requests.HTTPError as error:
        st.error(f"Unable to load available features: {_http_error_details(error)}")
        return
    except requests.RequestException as error:
        st.error(f"Unable to load available features: {error}")
        return

    feature_names = [feature.get('name', '') for feature in features if feature.get('name', '')]
    selected_feature = None
    if feature_names:
        selected_feature = st.selectbox("Feature", feature_names, key='pgm_feature')
    else:
        st.info("No features retrieved from the API; please enter a custom feature name.")

    custom_feature_input = st.text_input("Or add a custom feature", key='pgm_custom_feature')
    custom_feature = custom_feature_input.strip()

    final_feature = custom_feature or (selected_feature or "")

    if final_feature:
        st.caption(f"Feature to {operation.lower()}: `{final_feature}`")
    else:
        st.caption("Select an existing feature or provide a custom one to continue.")

    st.divider()

    # 4. Application Section
    if scope == "Single project":
        _render_single_project_actions(stack, manage_token, operation, final_feature, project_id, selected_project)
    else:
        _render_organization_actions(stack, manage_token, operation, final_feature, target_projects)


def _render_single_project_selection(stack: str, manage_token: str) -> tuple:
    """Renders project selection UI and returns (selected_project, project_id)"""
    project_id = st.text_input("Project ID", key='pgm_project_id')

    if not project_id:
        st.info("Please enter the Project ID to continue.")
        return None, None

    try:
        selected_project = kbc.kbcapi_scripts.get_project_detail(stack, manage_token, project_id)
    except requests.HTTPError as error:
        st.error(f"Unable to load project `{project_id}`: {_http_error_details(error)}")
        return None, None
    except requests.RequestException as error:
        st.error(f"Unable to load project `{project_id}`: {error}")
        return None, None

    st.markdown(f"**Selected project name**: **`{selected_project['name']}`**")
    organization = selected_project.get('organization', {})
    st.markdown(f"**Organization name**: **`{organization.get('name', 'N/A')}`**")

    if st.button("Get project features", type="primary", key='pgm_get_features'):
        try:
            result = kbc.kbcapi_scripts.list_project_features(stack, manage_token, project_id)
        except requests.HTTPError as error:
            st.error(f"Unable to fetch project features: {_http_error_details(error)}")
        except requests.RequestException as error:
            st.error(f"Unable to fetch project features: {error}")
        else:
            st.json(result)

    return selected_project, project_id


def _render_organization_selection(stack: str, manage_token: str) -> tuple:
    """Renders organization selection UI and returns (selected_organization, target_projects)"""
    try:
        organizations = kbc.kbcapi_scripts.list_organizations_by_stack(stack, manage_token)
    except requests.HTTPError as error:
        st.error(f"Unable to load organizations: {_http_error_details(error)}")
        return None, None
    except requests.RequestException as error:
        st.error(f"Unable to load organizations: {error}")
        return None, None

    if not organizations:
        st.info("No organizations available for this manage token.")
        return None, None

    selected_organization = st.selectbox(
        "Organization",
        organizations,
        format_func=_format_organization_option,
        key='pgm_organization',
    )
    st.caption("Lists all organizations the user is part of. If authorized with an application token with scope `organizations:read`, all organizations are listed.")

    if not selected_organization:
        st.info("Select an organization to continue.")
        return None, None

    organization_id = selected_organization.get('id')
    if not organization_id:
        st.error("The selected organization is missing an ID.")
        return None, None

    try:
        organization_detail = kbc.kbcapi_scripts.get_organization_by_stack(stack, manage_token, organization_id)
    except requests.HTTPError as error:
        st.error(f"Unable to load organization detail: {_http_error_details(error)}")
        return None, None
    except requests.RequestException as error:
        st.error(f"Unable to load organization detail: {error}")
        return None, None

    projects = organization_detail.get('projects') or []
    if not projects:
        st.info("The selected organization does not have any projects.")
        return selected_organization, []

    project_rows = []
    for project in projects:
        project_rows.append({
            "include": True,
            "name": project.get('name', ''),
            "project_id": project.get('id', ''),
            "type": project.get('type', ''),
        })

    edited_projects = st.data_editor(
        project_rows,
        column_config={
            "include": st.column_config.CheckboxColumn("Include", help="Uncheck to skip this project", default=True),
            "name": st.column_config.TextColumn("Project name", disabled=True),
            "project_id": st.column_config.TextColumn("Project ID", disabled=True),
            "type": st.column_config.TextColumn("Project type", disabled=True),
        },
        hide_index=True,
        key='pgm_project_table',
    )

    included_project_ids = {
        row.get('project_id')
        for row in edited_projects
        if row.get('include') and row.get('project_id')
    }
    target_projects = [project for project in projects if project.get('id') in included_project_ids]

    st.caption(f"{len(target_projects)} project(s) selected for the operation.")

    return selected_organization, target_projects


def _render_single_project_actions(stack: str, manage_token: str, operation: str, final_feature: str, project_id: str, selected_project: dict) -> None:
    """Renders action buttons for single project operations"""
    if st.button("Apply feature change", type="primary", key='pgm_single_apply'):
        if not final_feature:
            st.warning("Please select or enter a feature before performing the action.")
            return

        try:
            if operation == 'ADD':
                result = kbc.kbcapi_scripts.add_feature(stack, manage_token, project_id, final_feature)
                st.success(f"Added feature `{final_feature}` to project `{project_id}`.")
            else:
                result = kbc.kbcapi_scripts.remove_feature(stack, manage_token, project_id, final_feature)
                st.success(f"Removed feature `{final_feature}` from project `{project_id}`.")

            st.json(result)
        except requests.HTTPError as error:
            st.error(f"Operation failed: {_http_error_details(error)}")
            return
        except requests.RequestException as error:
            st.error(f"Operation failed: {error}")
            return


def _render_organization_actions(stack: str, manage_token: str, operation: str, final_feature: str, target_projects: list) -> None:
    """Renders action buttons for organization operations"""
    if st.button("Apply feature change", type="primary", key='pgm_multi_apply'):
        if not final_feature:
            st.warning("Please select or enter a feature before performing the action.")
            return

        if not target_projects:
            st.warning("All projects are excluded; nothing to update.")
            return

        results_container = st.container()
        with results_container:
            for project in target_projects:
                project_id = project.get('id')
                project_label = _format_project_option(project)

                if not project_id:
                    st.error(f"{project_label}: missing project ID, skipping.")
                    continue

                try:
                    if operation == 'ADD':
                        kbc.kbcapi_scripts.add_feature(stack, manage_token, project_id, final_feature)
                        st.success(f"{project_label}: added `{final_feature}`.")
                    else:
                        kbc.kbcapi_scripts.remove_feature(stack, manage_token, project_id, final_feature)
                        st.success(f"{project_label}: removed `{final_feature}`.")
                except requests.HTTPError as error:
                    status_code = getattr(error.response, 'status_code', None)
                    message = _http_error_details(error)
                    if status_code in (400, 404, 409):
                        st.warning(f"{project_label}: skipped ({message}).")
                    else:
                        st.error(f"{project_label}: failed ({message}).")
                except requests.RequestException as error:
                    st.error(f"{project_label}: unexpected error ({error}).")
