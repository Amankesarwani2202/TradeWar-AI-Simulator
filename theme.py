import streamlit as st


def current_theme_type():
    """Return the active Streamlit theme type.

    Prefer the configured Streamlit theme because it is the authoritative value
    for this app. Some Streamlit versions expose st.context.theme.type
    inconsistently when a custom theme is configured.
    """
    try:
        configured = st.get_option("theme.base")
        if configured in ("dark", "light"):
            return configured
    except Exception:
        pass
    try:
        theme_type = st.context.theme.type
        if theme_type in ("dark", "light"):
            return theme