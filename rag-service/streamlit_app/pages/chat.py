"""
Chat page for the Streamlit application.
"""

import uuid

import streamlit as st

from utils.api_client import (
    ApiError,
    SessionExpired,
    delete_document,
    get_conversation_messages,
    list_conversations,
    list_documents,
    stream_answer,
    upload_document,
)

# Configure page settings
st.set_page_config(
    page_title="DocuMind",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a Bug": None,
        "About": None
    }
)


def logout(notice: str = None):
    """Clear the session and return to the login page, optionally showing a notice there."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    if notice:
        st.session_state["notice"] = notice
    st.switch_page("home.py")


def call_api(func, *args):
    """Call the backend, logging out if the session expired and showing other errors."""
    try:
        return func(*args)
    except SessionExpired as e:
        logout(str(e))
    except ApiError as e:
        st.error(str(e))
    return None


def start_new_chat():
    st.session_state.conversation_id = uuid.uuid4().hex
    st.session_state.chat_history = []


# Check authentication before anything can call the backend
if "jwt_token" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

jwt_token = st.session_state["jwt_token"]
if "conversation_id" not in st.session_state:
    start_new_chat()

# Initialize logout confirmation state
if "show_logout_confirm" not in st.session_state:
    st.session_state.show_logout_confirm = False

# Header with logout button
col1, col2 = st.columns([10, 2])
with col2:
    st.write("")  # Spacer
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state.show_logout_confirm = True

# Logout confirmation dialog
if st.session_state.show_logout_confirm:
    st.warning("Are you sure you want to logout?")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ Yes, logout"):
            logout()
    with col_cancel:
        if st.button("❌ Cancel"):
            st.session_state.show_logout_confirm = False
            st.rerun()

st.title("🧠 DocuMind")

with st.sidebar:
    # Conversations
    st.header("💬 Conversations")
    if st.button("➕ New chat", use_container_width=True):
        start_new_chat()
        st.rerun()

    for conversation in call_api(list_conversations, jwt_token) or []:
        conversation_id = conversation["conversation_id"]
        title = conversation["title"]
        label = title if len(title) <= 40 else title[:37] + "..."
        is_current = conversation_id == st.session_state.conversation_id
        if st.button(label, key=f"conv_{conversation_id}", disabled=is_current, use_container_width=True):
            messages = call_api(get_conversation_messages, conversation_id, jwt_token)
            if messages is not None:
                st.session_state.conversation_id = conversation_id
                st.session_state.chat_history = [
                    ("user" if m["role"] == "human" else "assistant", m["content"]) for m in messages
                ]
                st.rerun()

    # Documents
    st.header("📂 Documents")
    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
        file_description = st.text_input(
            "📄 Describe your document",
            max_chars=300,
            placeholder="E.g. LangGraph tutorial with workflows and code examples"
        )
        if st.form_submit_button("Upload", use_container_width=True):
            if not uploaded_file or not file_description:
                st.warning("Choose a file and describe it before uploading.")
            else:
                with st.spinner(f"Indexing {uploaded_file.name}..."):
                    if call_api(upload_document, uploaded_file, file_description, jwt_token):
                        st.success(f"Uploaded: {uploaded_file.name}")

    for document in call_api(list_documents, jwt_token) or []:
        doc_col, delete_col = st.columns([5, 1])
        doc_col.markdown(f"**{document['filename']}**  \n{document['description']}")
        if delete_col.button("🗑️", key=f"del_{document['doc_id']}", help="Delete this document"):
            call_api(delete_document, document["doc_id"], jwt_token)
            st.rerun()

# Display chat history
for role, text in st.session_state.chat_history:
    st.chat_message(role).write(text)

# Ask a question and stream the answer
if user_input := st.chat_input("Ask a question..."):
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        answer = call_api(
            lambda: st.write_stream(stream_answer(user_input, st.session_state.conversation_id, jwt_token))
        )
    if answer:
        st.session_state.chat_history += [("user", user_input), ("assistant", answer)]
        st.rerun()  # Refresh the conversation list
