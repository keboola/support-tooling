import streamlit as st
import requests
from urllib.parse import quote

st.set_page_config(page_title="Keboola User Management", page_icon="🧹", layout="centered")

st.title("Keboola User Management")
st.subheader("Manage API Tokens")

# ---- Stack config (host -> label) ----
STACKS = [
    ("connection.keboola.com", "AWS us-east-1"),
    ("connection.eu-central-1.keboola.com", "AWS eu-central-1"),
    ("connection.north-europe.azure.keboola.com", "Azure North Europe"),
    ("connection.us-east4.gcp.keboola.com", "GCP US East4"),
    ("connection.europe-west3.gcp.keboola.com", "GCP Europe West3"),
]

st.write(
    "Provide a **Manage API** token for each stack you want to target. "
    "Leave any stack blank to skip it."
)

# Token inputs (masked)
tokens = {}
for host, label in STACKS:
    tokens[host] = st.text_input(
        label=f"{label}",
        key=host,
        type="password",
        help=f"[Open token settings](https://{host}/admin/account/access-tokens)",
    )

st.markdown("---")

# ---- User email / ID input ----
user_email = st.text_input("User Email", placeholder="user@example.com").strip()

# ---- Styling: make primary buttons red ----
st.markdown(
    """
    <style>
      button[kind="primary"] { background-color: #dc2626 !important; }
      button[kind="primary"]:hover { background-color: #b91c1c !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Helpers ----
def headers_for(token: str):
    # Per your curl: include Content-Type and the manage token header.
    return {
        "X-KBC-ManageApiToken": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def parse_response(resp: requests.Response):
    ct = (resp.headers.get("Content-Type") or "").lower()
    try:
        return resp.json() if "application/json" in ct else resp.text
    except ValueError:
        return resp.text

def api_call(host: str, token: str, method: str, path: str, timeout=30):
    url = f"https://{host}{path}"
    try:
        resp = requests.request(method=method, url=url, headers=headers_for(token), timeout=timeout)
        return {
            "ok": resp.ok,
            "status_code": resp.status_code,
            "body": parse_response(resp),
            "url": url,
            "method": method,
            "endpoint_path": path,
        }
    except requests.RequestException as e:
        return {"ok": False, "status_code": None, "error": str(e), "url": url, "method": method, "endpoint_path": path}

def get_user_details(host: str, token: str, user_id_or_email: str):
    encoded = quote(user_id_or_email, safe="")
    return api_call(host, token, "GET", f"/manage/users/{encoded}")

def delete_user(host: str, token: str, user_id_or_email: str):
    encoded = quote(user_id_or_email, safe="")
    return api_call(host, token, "DELETE", f"/manage/users/{encoded}")

def selected_stacks():
    return [(label, host, tokens[host]) for (host, label) in STACKS if tokens.get(host)]

# ---- Session-state buckets for per-stack results ----
for host, _ in STACKS:
    st.session_state.setdefault(f"user_detail_{host}", None)
    st.session_state.setdefault(f"delete_result_{host}", None)

# ---- Main UI / Logic ----
if not user_email:
    st.info("Enter a **User Email** to continue.")
else:
    selected = selected_stacks()
    if not selected:
        st.info("Provide at least one **Manage API token** to query stacks.")
    else:
        # ---------- USER DETAILS ----------
        st.markdown("### User Details\nFetched per stack using the provided Manage API tokens.")
        with st.spinner("Fetching user details across selected stacks..."):
            for label, host, token in selected:
                st.session_state[f"user_detail_{host}"] = get_user_details(host, token, user_email)

        for label, host, _ in selected:
            res = st.session_state.get(f"user_detail_{host}")
            with st.container(border=True):
                st.write(f"**{label}** ({host}) — User Detail")
                if res is None:
                    st.warning("No response captured.")
                elif res.get("ok"):
                    st.success(f"OK (HTTP {res['status_code']}) via {res.get('method')} {res.get('url')}")
                    st.caption(f"Endpoint: `{res.get('endpoint_path', 'n/a')}`")
                    st.json(res.get("body"))
                else:
                    code = res.get("status_code")
                    err = res.get("error")
                    st.error(f"Failed{'' if code is None else f' (HTTP {code})'}")
                    st.caption(f"Tried {res.get('method')} {res.get('url')}")
                    if err:
                        st.code(err)
                    else:
                        st.json(res.get("body"))

        st.markdown("---")

        # ---------- INDIVIDUAL DELETE BUTTONS ----------
        st.markdown("### Remove User From Stacks")
        st.caption(
            "Click a button below to remove the user from a specific stack. "
            "The response for that stack will be shown immediately next to it."
        )

        for label, host, token in selected:
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button(
                    f"Delete on {label}",
                    key=f"delete_{host}",
                    type="primary",
                    use_container_width=True,
                    help=f"DELETE /manage/users/{{user}} on {label}",
                ):
                    with st.spinner(f"Deleting {user_email} on {label}..."):
                        st.session_state[f"delete_result_{host}"] = delete_user(host, token, user_email)

            with col2:
                res = st.session_state.get(f"delete_result_{host}")
                with st.container(border=True):
                    st.write(f"**{label}** ({host}) — Deletion Result")
                    if not res:
                        st.caption("No deletion attempted yet.")
                    else:
                        if res.get("ok"):
                            st.success(f"Success (HTTP {res['status_code']}) via {res.get('method')} {res.get('url')}")
                            st.caption(f"Endpoint: `{res.get('endpoint_path', 'n/a')}`")
                            st.json(res.get("body"))
                        else:
                            code = res.get("status_code")
                            err = res.get("error")
                            st.error(f"Failed{'' if code is None else f' (HTTP {code})'}")
                            st.caption(f"Tried {res.get('method')} {res.get('url')}")
                            if err:
                                st.code(err)
                            else:
                                st.json(res.get("body"))
