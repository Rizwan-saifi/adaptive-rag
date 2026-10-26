"""
Home page for Streamlit authentication interface.
"""

import logging

import streamlit as st

from utils.api_client import create_user, login_user, get_api_token

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

st.set_page_config(page_title="LangGraph Chat - Login")

st.title("🔐 Welcome to LangGraph Assistant")

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
    else:
        if mode == "Create Account":
            success = create_user(username, password, api_token)
            if success:
                st.success("User created. Please log in.")
            else:
                st.error("User creation failed.")
        else:
            response = login_user(username, password, api_token)
            if response and response.get("jwt"):
                st.session_state["jwt_token"] = response["jwt"]
                st.session_state["username"] = username
                st.switch_page("pages/Chat.py")
            else:
                st.error("Login failed. Downstream API error: Received empty JWT token.")
