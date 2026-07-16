"""Landing pages for the platform and its subject areas."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from html import escape
from pathlib import Path

import streamlit as st


@dataclass(frozen=True)
class LandingCard:
    """One navigable card on a landing page."""

    route: str
    label: str
    icon_filename: str


class CardLandingPage:
    """Render a full-screen landing page with navigable cards."""

    def __init__(
        self,
        background_path: Path,
        title: str,
        subtitle: str,
        cards: tuple[LandingCard, ...],
        arrow_route: str | None = None,
        compact_title: bool = False,
    ) -> None:
        self._background_path = background_path
        self._icon_directory = background_path.parent / "icons"
        self._title = title
        self._subtitle = subtitle
        self._cards = cards
        self._arrow_route = arrow_route
        self._compact_title = compact_title

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        background = self._encode_image(self._background_path)
        cards = "".join(self._card(card) for card in self._cards)
        card_count = len(self._cards)
        title_class = " viewer-landing-title-compact" if self._compact_title else ""
        arrow = self._arrow_html()
        st.html(
            f"""<main class="viewer-landing" style="background-image:linear-gradient(rgba(19,55,24,.22),rgba(21,54,25,.18)),url('data:image/jpeg;base64,{background}')"><section class="viewer-landing-content"><h1 class="{title_class.strip()}">{escape(self._title)}</h1><p>{escape(self._subtitle)}</p><div class="viewer-landing-cards viewer-landing-cards-{card_count}">{cards}</div></section>{arrow}</main>"""
        )

    def _card(self, card: LandingCard) -> str:
        icon_path = self._icon_directory / card.icon_filename
        icon = self._encode_image(icon_path)
        route = escape(card.route)
        label = escape(card.label)
        return (
            f'<a class="viewer-landing-card" href="?view={route}" target="_self">'
            f'<span class="viewer-landing-card-icon">'
            f'<img src="data:image/png;base64,{icon}" alt="{label}">'
            f'</span>'
            f'<span class="viewer-landing-card-label">{label}</span>'
            "</a>"
        )

    def _arrow_html(self) -> str:
        if self._arrow_route is None:
            return ""
        route = escape(self._arrow_route)
        return (
            f'<a class="viewer-landing-arrow" href="?view={route}" '
            'target="_self" aria-label="Zum ersten Bereich">'
            "<span></span><span></span></a>"
        )

    @staticmethod
    def _encode_image(path: Path) -> str:
        """Return a file as an ASCII base64 string for an HTML data URI."""
        return base64.b64encode(path.read_bytes()).decode("ascii")


class PlatformLandingPage(CardLandingPage):
    """Render the central platform landing page."""

    def __init__(self, background_path: Path) -> None:
        super().__init__(
            background_path=background_path,
            title="Plattform für Datenaufbereitung und  &#8209;visualisierung",
            subtitle=(
                "Zentrale Arbeitsbereiche für Datenvisualisierung und "
                "Datenaufbereitung im Referat 43"
            ),
            cards=(
                LandingCard(
                    "groundwater-data",
                    "Grundwasserdaten",
                    "grundwasser.png",
                ),
                LandingCard(
                    "meteorological-data",
                    "Meteorologische Daten",
                    "wetter.png",
                ),
                LandingCard(
                    "script-library",
                    "Script-Bibliothek",
                    "bibliothek.png",
                ),
            ),
            arrow_route="groundwater-data",
            compact_title=True,
        )


class GroundwaterDataLandingPage(CardLandingPage):
    """Render the groundwater data landing page."""

    def __init__(self, background_path: Path) -> None:
        super().__init__(
            background_path=background_path,
            title="Grundwasserdaten",
            subtitle=(
                "Datenvisualisierung und Aufbereitung für "
                "Grundwasserquantität und Grundwasserqualität"
            ),
            cards=(
                LandingCard(
                    "groundwater-quantity",
                    "Grundwasserquantität",
                    "messbecher.png",
                ),
                LandingCard(
                    "groundwater-quality",
                    "Grundwasserqualität",
                    "labor-ausstattung.png",
                ),
            ),
            arrow_route="groundwater-quantity",
        )


class LandingPage(CardLandingPage):
    """Render the groundwater quantity landing page."""

    def __init__(self, background_path: Path) -> None:
        super().__init__(
            background_path=background_path,
            title="GWN Viewer",
            subtitle=(
                "Daten und Informationen zum Wasserdargebot und zur "
                "Grundwasserneubildung in Sachsen"
            ),
            cards=(
                LandingCard("maps", "Karten", "karte.png"),
                LandingCard("diagrams", "Diagramme", "liniendiagramm.png"),
                LandingCard("nomograms", "Nomogramme", "korrelation.png"),
                LandingCard("export", "Export", "import-export.png"),
            ),
            arrow_route="maps",
        )


class PlaceholderLandingPage:
    """Render a subject-area page without configured content modules."""

    def __init__(
        self,
        background_path: Path,
        title: str,
        subtitle: str,
        icon_filename: str,
    ) -> None:
        self._background_path = background_path
        self._icon_directory = background_path.parent / "icons"
        self._title = title
        self._subtitle = subtitle
        self._icon_filename = icon_filename

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        background = CardLandingPage._encode_image(self._background_path)
        icon = CardLandingPage._encode_image(
            self._icon_directory / self._icon_filename
        )
        st.html(
            f"""<main class="viewer-landing" style="background-image:linear-gradient(rgba(19,55,24,.22),rgba(21,54,25,.18)),url('data:image/jpeg;base64,{background}')"><section class="viewer-landing-content viewer-placeholder-content"><h1>{escape(self._title)}</h1><p>{escape(self._subtitle)}</p><div class="viewer-placeholder-panel"><img src="data:image/png;base64,{icon}" alt="{escape(self._title)}"><div><strong>{escape(self._title)}</strong><span>Für diesen Bereich sind derzeit noch keine Inhalte hinterlegt.</span></div></div></section></main>"""
        )
