"""Landing page following the supplied GWN Viewer reference."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


_ICON_FILES = {
    "maps": "karte.png",
    "diagrams": "liniendiagramm.png",
    "nomograms": "korrelation.png",
    "export": "import-export.png",
}


class LandingPage:
    """Render the full-screen landing page with four working module cards."""

    def __init__(self, background_path: Path) -> None:
        self._background_path = background_path
        self._icon_directory = background_path.parent / "icons"

    def render(self) -> None:
        background = self._encode_image(self._background_path)
        cards = "".join(
            self._card(route, label)
            for route, label in (
                ("maps", "Karten"),
                ("diagrams", "Diagramme"),
                ("nomograms", "Nomogramme"),
                ("export", "Export"),
            )
        )
        # st.html renders raw HTML directly. Unlike st.markdown it cannot turn
        # indented subsequent cards into visible source-code blocks.
        st.html(
            f"""<main class="viewer-landing" style="background-image:linear-gradient(rgba(19,55,24,.22),rgba(21,54,25,.18)),url('data:image/jpeg;base64,{background}')"><section class="viewer-landing-content"><h1>GWN Viewer</h1><p>Daten und Informationen zum Wasserdargebot und zur Grundwasserneubildung in Sachsen</p><div class="viewer-landing-cards">{cards}</div></section><a class="viewer-landing-arrow" href="?view=maps" target="_self" aria-label="Zu den Karten"><span></span><span></span></a></main>"""
        )

    def _card(self, route: str, label: str) -> str:
        icon_path = self._icon_directory / _ICON_FILES[route]
        icon = self._encode_image(icon_path)
        return (
            f'<a class="viewer-landing-card" href="?view={route}" target="_self">'
            f'<span class="viewer-landing-card-icon">'
            f'<img src="data:image/png;base64,{icon}" alt="{label}">'
            f'</span>'
            f'<span class="viewer-landing-card-label">{label}</span>'
            "</a>"
        )

    @staticmethod
    def _encode_image(path: Path) -> str:
        """Return a file as an ASCII base64 string for an HTML data URI."""
        return base64.b64encode(path.read_bytes()).decode("ascii")
