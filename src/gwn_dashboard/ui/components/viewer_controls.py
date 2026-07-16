"""Common controls placed in the viewer-style toolbar and side panels."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import streamlit as st

from gwn_dashboard.domain.models import Period, SidebarSelection


class ViewerControls:
    """Maintain the spatial and temporal selection shared by all modules."""

    MODEL_LABEL = "KliWES 3.0 - Simulation - kalib_beo_ERA5"

    def __init__(
        self,
        default_reference_period: Period,
        default_comparison_period: Period,
    ) -> None:
        self._default_reference_period = default_reference_period
        self._default_comparison_period = default_comparison_period

    def render_toolbar(
        self,
        available_groundwater_bodies: Sequence[str],
        minimum_year: int,
        maximum_year: int,
    ) -> SidebarSelection:
        """Render spatial controls and two effective period sliders."""

        available = self._validated_available(available_groundwater_bodies)
        mode_default = st.session_state.get(
            "viewer_selection_mode",
            "Alle Grundwasserkörper",
        )

        col_room, col_model, col_detail = st.columns(
            [1.15, 1.65, 1.65],
            gap="small",
        )
        with col_room:
            mode = st.selectbox(
                "Raumauswahl",
                options=("Alle Grundwasserkörper", "Eigene Auswahl"),
                index=0 if mode_default == "Alle Grundwasserkörper" else 1,
                key="viewer_selection_mode",
            )
        with col_model:
            self.static_field("Modell", self.MODEL_LABEL)

        if mode == "Eigene Auswahl":
            current = st.session_state.get("viewer_selected_ids", available[:3])
            selected_ids = st.multiselect(
                "Grundwasserkörper auswählen",
                options=available,
                default=[value for value in current if value in available],
                key="viewer_selected_ids",
            )
            if not selected_ids:
                st.warning("Bitte mindestens einen Grundwasserkörper auswählen.")
                st.stop()
        else:
            selected_ids = available

        previous_detail = st.session_state.get("viewer_detail_gwk")
        default_index = (
            selected_ids.index(previous_detail)
            if previous_detail in selected_ids
            else 0
        )
        with col_detail:
            detail = st.selectbox(
                "Detail-GWK",
                options=selected_ids,
                index=default_index,
                key="viewer_detail_gwk",
            )

        reference_period, comparison_period = self._render_period_sliders(
            minimum_year,
            maximum_year,
        )
        return self._selection(
            selected_ids,
            detail,
            reference_period,
            comparison_period,
        )

    def current_selection(
        self,
        available_groundwater_bodies: Sequence[str],
        minimum_year: int,
        maximum_year: int,
    ) -> SidebarSelection:
        """Return the current selection without rendering the toolbar."""

        available = self._validated_available(available_groundwater_bodies)
        mode = st.session_state.get(
            "viewer_selection_mode",
            "Alle Grundwasserkörper",
        )
        if mode == "Eigene Auswahl":
            selected = [
                value
                for value in st.session_state.get(
                    "viewer_selected_ids",
                    available[:3],
                )
                if value in available
            ]
            selected_ids = selected or available[:1]
        else:
            selected_ids = available
        detail = st.session_state.get("viewer_detail_gwk")
        if detail not in selected_ids:
            detail = selected_ids[0]

        reference_period, comparison_period = self._periods_from_state(
            minimum_year,
            maximum_year,
        )
        return self._selection(
            selected_ids,
            detail,
            reference_period,
            comparison_period,
        )

    def render_diagram_controls(
        self,
        selection: SidebarSelection,
    ) -> tuple[bool, bool]:
        """Render the original time-series options and selected periods."""

        st.markdown(
            '<div class="viewer-panel-heading">Grundwasserneubildung</div>',
            unsafe_allow_html=True,
        )
        self.static_field("Modell", self.MODEL_LABEL)
        self.static_field("Parameter", "Grundwasserneubildung GWN")
        self.static_field("Raum", selection.selected_groundwater_body)

        st.markdown(
            '<div class="viewer-panel-separator"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="viewer-panel-heading">Meteorologische Vergleichsgrößen</div>',
            unsafe_allow_html=True,
        )
        show_precipitation = st.checkbox(
            "Niederschlag P anzeigen",
            value=bool(
                st.session_state.get("viewer_show_precipitation", True)
            ),
            key="viewer_show_precipitation",
        )
        show_etp = st.checkbox(
            "Potenzielle Evapotranspiration ETp anzeigen",
            value=bool(st.session_state.get("viewer_show_etp", False)),
            key="viewer_show_etp",
        )

        st.markdown(
            '<div class="viewer-panel-separator"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="viewer-panel-heading">Vergleichszeiträume</div>',
            unsafe_allow_html=True,
        )
        self.static_field("Referenz", selection.reference_period.label)
        self.static_field("Vergleich", selection.comparison_period.label)
        self.static_field("Zeitschritt", "Jahr")
        return show_precipitation, show_etp

    def _render_period_sliders(
        self,
        minimum_year: int,
        maximum_year: int,
    ) -> tuple[Period, Period]:
        reference_default, comparison_default = self._default_ranges(
            minimum_year,
            maximum_year,
        )
        self._initialize_period_state(
            "viewer_reference_period",
            reference_default,
            minimum_year,
            maximum_year,
        )
        self._initialize_period_state(
            "viewer_comparison_period",
            comparison_default,
            minimum_year,
            maximum_year,
        )

        reference_column, comparison_column = st.columns(2, gap="small")
        with reference_column:
            reference_range = st.slider(
                "Referenzzeitraum",
                min_value=minimum_year,
                max_value=maximum_year,
                step=1,
                key="viewer_reference_period",
            )
            st.caption(
                f"{reference_range[0]}–{reference_range[1]} "
                f"({reference_range[1] - reference_range[0] + 1} Jahre)"
            )
        with comparison_column:
            comparison_range = st.slider(
                "Vergleichszeitraum",
                min_value=minimum_year,
                max_value=maximum_year,
                step=1,
                key="viewer_comparison_period",
            )
            st.caption(
                f"{comparison_range[0]}–{comparison_range[1]} "
                f"({comparison_range[1] - comparison_range[0] + 1} Jahre)"
            )

        reference_period, comparison_period = self._periods_from_ranges(
            reference_range,
            comparison_range,
        )
        self._validate_selected_periods(reference_period, comparison_period)
        return reference_period, comparison_period

    def _periods_from_state(
        self,
        minimum_year: int,
        maximum_year: int,
    ) -> tuple[Period, Period]:
        reference_default, comparison_default = self._default_ranges(
            minimum_year,
            maximum_year,
        )
        reference_range = self._valid_range_or_default(
            st.session_state.get("viewer_reference_period"),
            reference_default,
            minimum_year,
            maximum_year,
        )
        comparison_range = self._valid_range_or_default(
            st.session_state.get("viewer_comparison_period"),
            comparison_default,
            minimum_year,
            maximum_year,
        )
        reference_period, comparison_period = self._periods_from_ranges(
            reference_range,
            comparison_range,
        )
        try:
            self._validate_selected_periods(
                reference_period,
                comparison_period,
                stop_on_error=False,
            )
        except ValueError:
            reference_period, comparison_period = self._periods_from_ranges(
                reference_default,
                comparison_default,
            )
            st.session_state["viewer_reference_period"] = reference_default
            st.session_state["viewer_comparison_period"] = comparison_default
        return reference_period, comparison_period

    def _default_ranges(
        self,
        minimum_year: int,
        maximum_year: int,
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        if maximum_year - minimum_year + 1 < 4:
            raise ValueError(
                "Für zwei getrennte Vergleichszeiträume werden mindestens vier Jahre benötigt."
            )

        reference = self._clip_period(
            self._default_reference_period,
            minimum_year,
            maximum_year,
        )
        comparison = self._clip_period(
            self._default_comparison_period,
            minimum_year,
            maximum_year,
        )
        if (
            reference[1] - reference[0] + 1 < 2
            or comparison[1] - comparison[0] + 1 < 2
            or reference[1] >= comparison[0]
        ):
            split = minimum_year + (maximum_year - minimum_year + 1) // 2
            reference = (minimum_year, split - 1)
            comparison = (split, maximum_year)
        return reference, comparison

    @staticmethod
    def _clip_period(
        period: Period,
        minimum_year: int,
        maximum_year: int,
    ) -> tuple[int, int]:
        start = min(max(period.start_year, minimum_year), maximum_year)
        end = min(max(period.end_year, minimum_year), maximum_year)
        return min(start, end), max(start, end)

    @staticmethod
    def _initialize_period_state(
        key: str,
        default: tuple[int, int],
        minimum_year: int,
        maximum_year: int,
    ) -> None:
        st.session_state[key] = ViewerControls._valid_range_or_default(
            st.session_state.get(key),
            default,
            minimum_year,
            maximum_year,
        )

    @staticmethod
    def _valid_range_or_default(
        value,
        default: tuple[int, int],
        minimum_year: int,
        maximum_year: int,
    ) -> tuple[int, int]:
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            return default
        start, end = int(value[0]), int(value[1])
        if minimum_year <= start <= end <= maximum_year:
            return start, end
        return default

    @staticmethod
    def _periods_from_ranges(
        reference_range: tuple[int, int],
        comparison_range: tuple[int, int],
    ) -> tuple[Period, Period]:
        reference = Period(
            f"{reference_range[0]}–{reference_range[1]}",
            reference_range[0],
            reference_range[1],
        )
        comparison = Period(
            f"{comparison_range[0]}–{comparison_range[1]}",
            comparison_range[0],
            comparison_range[1],
        )
        return reference, comparison

    @staticmethod
    def _validate_selected_periods(
        reference_period: Period,
        comparison_period: Period,
        *,
        stop_on_error: bool = True,
    ) -> None:
        message: str | None = None
        if reference_period.end_year - reference_period.start_year + 1 < 2:
            message = "Der Referenzzeitraum muss mindestens zwei Jahre umfassen."
        elif comparison_period.end_year - comparison_period.start_year + 1 < 2:
            message = "Der Vergleichszeitraum muss mindestens zwei Jahre umfassen."
        elif reference_period.end_year >= comparison_period.start_year:
            message = (
                "Referenz- und Vergleichszeitraum dürfen sich nicht überschneiden. "
                "Der Referenzzeitraum muss vor dem Vergleichszeitraum liegen."
            )
        if message is None:
            return
        if stop_on_error:
            st.error(message)
            st.stop()
        raise ValueError(message)

    @staticmethod
    def static_field(label: str, value: str) -> None:
        """Render a clearly read-only value instead of a one-option menu."""

        st.html(
            f'<div class="viewer-static-field"><span>{escape(label)}</span>'
            f'<strong>{escape(str(value))}</strong></div>'
        )

    @staticmethod
    def _validated_available(values: Sequence[str]) -> list[str]:
        available = list(values)
        if not available:
            raise ValueError("Keine Grundwasserkörper verfügbar.")
        return available

    @staticmethod
    def _selection(
        selected_ids: Sequence[str],
        detail: str,
        reference_period: Period,
        comparison_period: Period,
    ) -> SidebarSelection:
        return SidebarSelection(
            groundwater_body_ids=tuple(selected_ids),
            selected_groundwater_body=str(detail),
            reference_period=reference_period,
            comparison_period=comparison_period,
            show_precipitation=bool(
                st.session_state.get("viewer_show_precipitation", True)
            ),
            show_evapotranspiration=bool(
                st.session_state.get("viewer_show_etp", False)
            ),
        )
