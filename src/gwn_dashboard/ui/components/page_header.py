"""Reusable page heading for analysis modules."""

from html import escape

import streamlit as st


class PageHeader:
    """Render a compact module heading consistent with the viewer layout."""

    def render(self, title: str, description: str | None = None) -> None:
        """Render the component or page in Streamlit.
        
        Args:
            title: Value of type ``str``.
            description: Value of type ``str | None``.
        """
        safe_title = escape(title)
        description_html = ""
        if description:
            description_html = (
                f'<p class="viewer-page-description">{escape(description)}</p>'
            )
        st.markdown(
            f"""
            <div class="viewer-page-header">
                <h2>{safe_title}</h2>
                {description_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
