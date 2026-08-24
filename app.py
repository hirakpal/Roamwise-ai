import streamlit as st
from llm import LLMClient
from context_manager import ContextManager
from prompt import SYSTEM_PROMPT
from state import TripState
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="The Worldly Companion", page_icon="🌍", layout="wide")

st.title("🌍 The Worldly Companion")
st.caption("Travel planning with structured memory & token-efficient context")

# Initialize
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

# Sidebar - Trip State
with st.sidebar:
    st.header("🧭 Trip State")
    ts = st.session_state.cm.trip_state

    st.markdown(f"**Readiness:** `{ts.readiness}`")
    st.markdown(f"**Destination:** {ts.destination or '—'}")
    st.markdown(f"**Travelers:** {ts.travelers or '—'}")
    st.markdown(f"**Duration:** {ts.duration or '—'}")
    st.markdown(f"**Dates:** {ts.dates or '—'}")
    st.markdown(f"**Budget:** {ts.budget or '—'}")
    st.markdown(f"**Hotel:** {ts.hotel_preference or '—'}")

    if ts.preferences:
        st.markdown("**Preferences:**")
        for p in ts.preferences:
            st.markdown(f"- {p}")

    if ts.constraints:
        st.markdown("**Constraints:**")
        for c in ts.constraints:
            st.markdown(f"- {c}")

    st.divider()
    st.subheader("📊 Token Usage")
    st.metric("Prompt Tokens", st.session_state.cm.total_prompt_tokens)
    st.metric("Completion Tokens", st.session_state.cm.total_completion_tokens)

    if st.button("Reset Conversation"):
        st.session_state.cm = ContextManager(
            llm_client=st.session_state.llm,
            max_recent_turns=5,
            summary_threshold=2800
        )
        st.session_state.messages = []
        st.rerun()

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Tell me about the trip you're thinking of..."):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.cm.add_message("user", prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            messages = st.session_state.cm.build_messages(SYSTEM_PROMPT)
            response, p_tokens, c_tokens = st.session_state.llm.chat(messages)
            st.markdown(response)

    st.session_state.cm.add_assistant_message(response, p_tokens, c_tokens)
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Update Trip State
    st.session_state.cm.update_trip_state(max_turns_for_extraction=3)

    # Summarize if needed
    if st.session_state.cm.should_summarize():
        st.session_state.cm.summarize_older_history()

    st.rerun()
