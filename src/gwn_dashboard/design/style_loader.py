"""Load the shared Streamlit stylesheet."""

from pathlib import Path


def load_global_styles() -> None:
    """Inject the central stylesheet into the Streamlit application."""

    import streamlit as st

    css_path = Path(__file__).with_name("styles.css")
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
