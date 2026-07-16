"""Searchable catalogue and detail pages for downloadable scripts."""

from __future__ import annotations

from html import escape
from urllib.parse import quote

import streamlit as st

from gwn_dashboard.domain.script_library import ScriptLibraryItem
from gwn_dashboard.services.script_library_service import ScriptLibraryService


class ScriptLibraryPage:
    """Render the catalogue or one selected publication."""

    def __init__(self, service: ScriptLibraryService) -> None:
        self._service = service

    def render(self) -> None:
        """Render the component or page in Streamlit.
        """
        try:
            catalogue = self._service.load_catalogue()
        except Exception as error:
            st.error(f"Die Script-Bibliothek konnte nicht geladen werden: {error}")
            return

        item_id = self._query_parameter("script")
        if item_id:
            item = self._service.find_by_id(catalogue, item_id)
            if item is None:
                st.warning("Das ausgewählte Werkzeug ist nicht verfügbar.")
                self._back_link()
                return
            self._render_detail(item)
            return

        self._render_catalogue(catalogue)

    def _render_catalogue(
        self,
        catalogue: tuple[ScriptLibraryItem, ...],
    ) -> None:
        st.html(
            """
            <section class="viewer-library-intro">
                <div>
                    <h1>Script-Bibliothek</h1>
                    <p>Geprüfte Werkzeuge für Datenaufbereitung, Analyse und Visualisierung</p>
                </div>
                <span>Python · R · Jupyter</span>
            </section>
            """
        )
        if not catalogue:
            st.info("Derzeit sind keine Werkzeuge in der Script-Bibliothek hinterlegt.")
            return

        query_tag = self._query_parameter("tag")
        valid_tags = self._service.tags(catalogue)
        current_tags = [
            tag
            for tag in st.session_state.get("script_library_tags", [])
            if tag in valid_tags
        ]
        if query_tag in valid_tags:
            applied_tag = st.session_state.get("script_library_applied_query_tag")
            if applied_tag != query_tag:
                current_tags = [query_tag]
                st.session_state["script_library_applied_query_tag"] = query_tag
        st.session_state["script_library_tags"] = current_tags

        with st.container(border=True):
            search = st.text_input(
                "Suche",
                placeholder=(
                    "Titel, Beschreibung, Kategorie, Tag, Dateiformat oder Sprache"
                ),
                key="script_library_search",
            )
            category_column, language_column, type_column = st.columns(3)
            with category_column:
                category = st.selectbox(
                    "Kategorie",
                    options=("Alle Kategorien", *self._service.categories(catalogue)),
                    key="script_library_category",
                )
            with language_column:
                language = st.selectbox(
                    "Sprache",
                    options=("Alle Sprachen", *self._service.languages(catalogue)),
                    key="script_library_language",
                )
            with type_column:
                item_type = st.selectbox(
                    "Bereitstellung",
                    options=("Alle Typen", *self._service.types(catalogue)),
                    key="script_library_type",
                )
            selected_tags = st.multiselect(
                "Tags",
                options=valid_tags,
                key="script_library_tags",
                format_func=lambda value: f"#{value}",
                placeholder="Tags auswählen",
            )

        results = self._service.filter_items(
            catalogue,
            query=search,
            category=category,
            language=language,
            item_type=item_type,
            tags=tuple(selected_tags),
        )
        st.markdown(
            f'<div class="viewer-library-result-count">{len(results)} von '
            f'{len(catalogue)} Werkzeugen</div>',
            unsafe_allow_html=True,
        )

        if not results:
            st.info("Für die gewählten Such- und Filterkriterien wurden keine Werkzeuge gefunden.")
            return

        for row_start in range(0, len(results), 2):
            columns = st.columns(2, gap="medium")
            for column, item in zip(columns, results[row_start : row_start + 2], strict=False):
                with column:
                    self._render_card(item)

    def _render_card(self, item: ScriptLibraryItem) -> None:
        with st.container(border=True):
            st.html(
                f"""
                <article class="viewer-library-card-header">
                    <div>
                        <span class="viewer-library-language">{escape(item.language)}</span>
                        <span class="viewer-library-type">{escape(item.type_label)}</span>
                    </div>
                    <h2>{escape(item.title)}</h2>
                    <p>{escape(item.short_description)}</p>
                </article>
                """
            )
            self._render_tags(item.tags, linked=True)
            st.caption(
                f"{item.category} · Version {item.version} · "
                f"Stand {item.updated.strftime('%d.%m.%Y')}"
            )
            details, download = st.columns([1, 1], gap="small")
            with details:
                item_id = quote(item.item_id, safe="")
                st.markdown(
                    f'<a class="viewer-library-detail-link" '
                    f'href="?view=script-library&script={item_id}" '
                    f'target="_self">Beschreibung und Details</a>',
                    unsafe_allow_html=True,
                )
            with download:
                data, filename, mime_type = self._service.build_download(item)
                st.download_button(
                    "Herunterladen",
                    data=data,
                    file_name=filename,
                    mime=mime_type,
                    key=f"script_library_download_{item.item_id}",
                    use_container_width=True,
                )

    def _render_detail(self, item: ScriptLibraryItem) -> None:
        self._back_link()
        st.html(
            f"""
            <section class="viewer-library-detail-header">
                <div class="viewer-library-detail-labels">
                    <span>{escape(item.language)}</span>
                    <span>{escape(item.type_label)}</span>
                    <span>{escape(item.category)}</span>
                </div>
                <h1>{escape(item.title)}</h1>
                <p>{escape(item.short_description)}</p>
            </section>
            """
        )
        self._render_tags(item.tags, linked=True)

        main, side = st.columns([2.15, 1], gap="medium")
        with main:
            with st.container(border=True):
                st.markdown("### Beschreibung")
                st.write(item.long_description)

                readme = self._service.read_readme(item)
                if readme:
                    st.markdown("### Anwendung")
                    st.markdown(readme)

        with side:
            with st.container(border=True):
                st.markdown("### Technische Angaben")
                self._detail_row("Sprache", item.language)
                self._detail_row("Bereitstellung", item.type_label)
                self._detail_row("Version", item.version)
                self._detail_row("Stand", item.updated.strftime("%d.%m.%Y"))
                self._detail_row("Autor", item.author)
                if item.requires_runtime:
                    self._detail_row("Laufzeit", item.requires_runtime)
                if item.entry_point:
                    self._detail_row("Einstiegspunkt", item.entry_point)
                if item.item_type == "script_package":
                    self._detail_row("Enthaltene Dateien", str(item.file_count))

                self._list_section("Abhängigkeiten", item.dependencies)
                self._list_section("Eingabeformate", item.input_formats)
                self._list_section("Ausgabeformate", item.output_formats)

                data, filename, mime_type = self._service.build_download(item)
                st.download_button(
                    "Werkzeug herunterladen",
                    data=data,
                    file_name=filename,
                    mime=mime_type,
                    key=f"script_library_detail_download_{item.item_id}",
                    use_container_width=True,
                )

    @staticmethod
    def _detail_row(label: str, value: str) -> None:
        st.markdown(
            f'<div class="viewer-library-detail-row"><span>{escape(label)}</span>'
            f'<strong>{escape(value)}</strong></div>',
            unsafe_allow_html=True,
        )

    @staticmethod
    def _list_section(label: str, values: tuple[str, ...]) -> None:
        if not values:
            return
        value_html = "".join(f"<li>{escape(value)}</li>" for value in values)
        st.markdown(
            f'<div class="viewer-library-detail-list"><span>{escape(label)}</span>'
            f'<ul>{value_html}</ul></div>',
            unsafe_allow_html=True,
        )

    @staticmethod
    def _render_tags(tags: tuple[str, ...], *, linked: bool) -> None:
        elements: list[str] = []
        for tag in tags:
            label = f"#{escape(tag)}"
            if linked:
                encoded = quote(tag, safe="")
                elements.append(
                    f'<a href="?view=script-library&tag={encoded}" '
                    f'target="_self">{label}</a>'
                )
            else:
                elements.append(f"<span>{label}</span>")
        st.markdown(
            f'<div class="viewer-library-tags">{"".join(elements)}</div>',
            unsafe_allow_html=True,
        )

    @staticmethod
    def _back_link() -> None:
        st.markdown(
            '<a class="viewer-library-back-link" href="?view=script-library" '
            'target="_self">← Zur Script-Bibliothek</a>',
            unsafe_allow_html=True,
        )

    @staticmethod
    def _query_parameter(name: str) -> str | None:
        value = st.query_params.get(name)
        if isinstance(value, list):
            value = value[0] if value else None
        return str(value) if value else None
