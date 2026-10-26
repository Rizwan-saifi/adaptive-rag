"""
Home page for Streamlit authentication interface.
"""

import logging

import streamlit as st

from utils.api_client import ApiError, create_user, get_api_token, login_user

# Hide sidebar for cleaner look
hide_sidebar_style = """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",
    filemode="a",
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="DocuMind - Login")

st.title("🧠 Welcome to DocuMind")

# Message left by the chat page, e.g. when the session expired
if notice := st.session_state.pop("notice", None):
    st.warning(notice)

# Step 1: Render login/signup form
with st.form("auth_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    mode = st.radio("Choose action:", ["Login", "Create Account"])
    submit = st.form_submit_button("Submit")

# Step 2: Handle login/account creation
if submit:
    if not username or not password:
        st.error("Username and password required.")
    # Fetch a fresh API token per attempt; issued tokens expire and don't
    # survive a gateway restart.
    elif not (api_token := get_api_token()):
        st.error("Could not reach the auth service. Please try again.")
    elif mode == "Create Account":
        try:
            create_user(username, password, api_token)
            st.success("User created. Please log in.")
        except ApiError as e:
            st.error(f"User creation failed: {e}")
    else:
        try:
            st.session_state["jwt_token"] = login_user(username, password, api_token)
            st.session_state["username"] = username
            st.switch_page("pages/chat.py")
        except ApiError as e:
            st.error(f"Login failed: {e}")
