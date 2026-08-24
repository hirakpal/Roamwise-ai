import sys
from pathlib import Path

# Ensure project root is in the path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from dotenv import load_dotenv
from core.llm import LLMClient
from core.context_manager import ContextManager
from app.ui import render_sidebar, render_chat_history, handle_user_input

load_dotenv()

st.set_page_config(
    page_title="The Worldly Companion",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 The Worldly Companion")
st.caption("Travel planning with structured memory & token-efficient context")

# Initialize session state
if "llm" not in st.session_state:
    st.session_state.llm = LLMClient(model="gpt-4o-mini")

if "cm" not in st.session_state:
    st.session_state.cm = ContextManager(
        llm_client=st.session_state.llm,
        max_recent_turns=5,
        summary_threshold=2800
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    render_sidebar(st.session_state.cm)

# Main chat area
render_chat_history()
handle_user_input(st.session_state.cm, st.session_state.llm)
