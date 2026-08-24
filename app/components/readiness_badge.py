import streamlit as st

def readiness_badge(readiness: str):
    """Render a visual readiness badge."""
    styles = {
        "Discovery": {
            "bg": "#e0f2fe",
            "text": "#0369a1",
            "label": "🔵 Discovery"
        },
        "Concept Ready": {
            "bg": "#fef9c3",
            "text": "#a16207",
            "label": "🟡 Concept Ready"
        },
        "Execution Ready": {
            "bg": "#dcfce7",
            "text": "#15803d",
            "label": "🟢 Execution Ready"
        }
    }

    style = styles.get(readiness, {
        "bg": "#f3f4f6",
        "text": "#374151",
        "label": readiness
    })

    st.markdown(
        f"""
        <div style="
            background-color: {style['bg']};
            color: {style['text']};
            padding: 6px 14px;
            border-radius: 20px;
            display: inline-block;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 12px;
        ">
            {style['label']}
        </div>
        """,
        unsafe_allow_html=True
    )
