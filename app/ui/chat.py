import streamlit as st
from core.prompt import SYSTEM_PROMPT

def render_chat_history():
    """Display the conversation history."""
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def handle_user_input(cm, llm):
    """Handle new user input and generate assistant response."""
    if prompt := st.chat_input("Tell me about the trip you're thinking of..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        cm.add_message("user", prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                messages = cm.build_messages(SYSTEM_PROMPT)
                response, p_tokens, c_tokens = llm.chat(messages)
                st.markdown(response)

        cm.add_assistant_message(response, p_tokens, c_tokens)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Update structured state
        cm.update_trip_state(max_turns_for_extraction=3)

        # Summarize if needed
        if cm.should_summarize():
            cm.summarize_older_history()

        st.rerun()
