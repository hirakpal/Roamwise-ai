import streamlit as st
from core.state import TripState

def render_sidebar(cm):
    """Render the sidebar with Trip State and token usage."""
    ts: TripState = cm.trip_state

    st.header("🧭 Trip State")

    # Readiness badge
    readiness_color = {
        "Discovery": "🔵",
        "Concept Ready": "🟡",
        "Execution Ready": "🟢"
    }
    st.markdown(f"**Readiness:** {readiness_color.get(ts.readiness, '⚪')} `{ts.readiness}`")

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
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Prompt", cm.total_prompt_tokens)
    with col2:
        st.metric("Completion", cm.total_completion_tokens)

    st.divider()

    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.clear()
        st.rerun()
