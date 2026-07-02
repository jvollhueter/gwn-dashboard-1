"""
GWN Dashboard - Grundwasserneubildung Analyse
Refactored mit modernem Layout und verbesserter UX
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
import json
from datetime import datetime, date

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

if TYPE_CHECKING:
    import geopandas as gpd

logger = logging.getLogger(__name__)

__version__ = "2.0.0"

# ============================================================================
# CSS & STYLING
# ============================================================================

def _inject_global_css() -> None:
    """Injiziert globales CSS für professionelles Styling."""
    st.markdown(
        """
        <style>
        /* Deploy Button verstecken */
        [data-testid="stDeployButton"],
        [data-testid="stAppDeployButton"] { 
            display: none !important; 
        }
        
        /* Metriken-Cards mit Hintergrund */
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        /* Sidebar Navigation als Link-Liste */
        section[data-testid="stSidebar"] .stRadio > div {
            gap: 0.1rem;
        }
        section[data-testid="stSidebar"] .stRadio label {
            padding: 0.45rem 0.6rem;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: background 0.15s;
        }
        section[data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(31, 119, 180, 0.1);
        }
        section[data-testid="stSidebar"] .stRadio [role="radio"] {
            display: none;
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        
        /* Button Hierarchie */
        .stButton > button[kind="primary"] {
            background-color: #1f77b4;
            border: none;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #1557a0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# IMPORT FUNKTIONEN AUS ORIGINAL
# ============================================================================

from gwn_dashboard_24062026_v3 import (
    # Datenverarbeitung
    load_gwk_mapping,
    compute_gwn_yearly,
    compute_parameter_yearly,
    attach_gwk_id,
    aggregate_to_gwk,
    filter_target_gwk,
    period_stats,
    compute_trend_stats,
    load_all_data,
    
    # Plots
    create_interactive_timeseries,
    create_correlation_plot,
    create_comparison_barplot,
    
    # Messstellen
    load_messstellen_data,
    load_mkz_timeseries,
    compute_mkz_trend,
)


# ============================================================================
# KARTEN-FUNKTIONEN (Original übernommen)
# ============================================================================

def create_gwk_map(gdf, comparison_df, selected_gwk=None):
    """Erstellt interaktive Karte mit GWK und Änderungen (Original-Code)."""
    
    if gdf is None or gdf.empty:
        return None
    
    # Merge mit Vergleichsdaten
    gdf_merged = gdf.merge(comparison_df, on='GWK_ID', how='left')
    
    # Konvertiere zu GeoJSON
    gdf_merged['geometry'] = gdf_merged['geometry'].simplify(tolerance=0.001)
    
    # Zentroide für Beschriftung
    gdf_merged['centroid'] = gdf_merged.geometry.centroid
    gdf_merged['lon'] = gdf_merged.centroid.x
    gdf_merged['lat'] = gdf_merged.centroid.y
    
    # Zentrum berechnen
    center_lat = gdf_merged['lat'].mean()
    center_lon = gdf_merged['lon'].mean()
    
    # Farbskala für delta_abs
    def get_color(delta):
        """Mapping von delta_abs auf Farbe."""
        if pd.isna(delta):
            return 'gray'
        elif delta < -30:
            return 'darkred'
        elif delta < -10:
            return 'red'
        elif delta < 10:
            return 'yellow'
        elif delta < 30:
            return 'lightgreen'
        else:
            return 'darkgreen'
    
    fig = go.Figure()
    
    # Für jedes GWK eine Trace
    for idx, row in gdf_merged.iterrows():
        geom = row['geometry']
        
        if geom.geom_type == 'Polygon':
            coords = list(geom.exterior.coords)
        elif geom.geom_type == 'MultiPolygon':
            # Nimm erstes Polygon
            coords = list(geom.geoms[0].exterior.coords)
        else:
            continue
        
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        color = get_color(row.get('delta_abs'))
        
        # Bestimme ob ausgewählt
        is_selected = (selected_gwk and row['GWK_ID'] == selected_gwk)
        line_width = 3 if is_selected else 0.5
        line_color = 'blue' if is_selected else 'white'
        
        hover_text = (
            f"<b>{row['GWK_ID']}</b><br>"
            f"GWN 1961-90: {row.get('mean_ref', np.nan):.1f} mm/a<br>"
            f"GWN 1991-2020: {row.get('mean_hist', np.nan):.1f} mm/a<br>"
            f"Änderung: {row.get('delta_abs', np.nan):+.1f} mm/a ({row.get('delta_rel_pct', np.nan):+.1f}%)"
        )
        
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            fill='toself',
            fillcolor=color,
            line=dict(width=line_width, color=line_color),
            opacity=0.7 if not is_selected else 0.9,
            name=row['GWK_ID'],
            text=hover_text,
            hoverinfo='text',
            showlegend=False,
        ))
    
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=7
        ),
        title='<b>GWK-Karte: Änderung der Grundwasserneubildung</b>',
        height=600,
        margin={"r":0,"t":40,"l":0,"b":0},
        hovermode='closest'
    )
    
    return fig


# ============================================================================
# MESSSTELLEN-PLOT FUNKTIONEN
# ============================================================================

def create_messstellen_plot(mkz: str, gwk_id: str, cache_dir: str = "./cache"):
    """Erstellt Ganglinie für Messstelle mit GWK-Kontext."""
    
    try:
        # Zeitreihe laden
        df = load_mkz_timeseries(mkz=mkz, cache_dir=cache_dir)
        
        if df is None or df.empty:
            return None
        
        # WICHTIG: Die Spalte heißt 'MESSZEITPUNKT', nicht 'Datum'
        # Und der Wert ist 'WERT_UNTER_GELAENDE', nicht 'Wert'
        
        # Plot erstellen
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['MESSZEITPUNKT'],  # ← KORRIGIERT (war: 'Datum')
            y=df['WERT_UNTER_GELAENDE'],  # ← KORRIGIERT (war: 'Wert')
            mode='lines',
            name=f'GW-Stand {mkz}',
            line=dict(color='steelblue', width=2),
            hovertemplate='<b>Datum:</b> %{x}<br><b>GW-Stand:</b> %{y:.2f} cm u. Gelände<extra></extra>'
        ))
        
        # Mittelwert
        mean_val = df['WERT_UNTER_GELAENDE'].mean()  # ← KORRIGIERT
        fig.add_hline(
            y=mean_val,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Ø {mean_val:.2f} cm",
            annotation_position="right"
        )
        
        fig.update_layout(
            title=f"<b>Ganglinie Messstelle {mkz}</b> (GWK: {gwk_id})",
            xaxis_title="Datum",
            yaxis_title="Grundwasserstand [cm unter Gelände]",
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        # Y-Achse umkehren (je tiefer, desto niedriger der Wasserstand)
        fig.update_yaxes(autorange="reversed")
        
        return fig
    
    except Exception as e:
        logger.exception(f"Messstellen-Plot failed for {mkz}")
        st.error(f"Fehler beim Erstellen des Plots für {mkz}: {e}")
        return None


@st.cache_data
def load_gwk_geometries(shapefile_path: str):
    """Lädt GWK-Geometrien aus Shapefile"""
    try:
        gdf = gpd.read_file(shapefile_path)
        
        # Koordinatensystem prüfen und ggf. nach WGS84 transformieren
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        
        # Spalte 'desc' als GWK_ID verwenden
        if 'desc' in gdf.columns:
            gdf['GWK_ID'] = gdf['desc'].astype(str).str.strip()
        
        return gdf
    except Exception as e:
        st.error(f"Fehler beim Laden der Shapefile: {e}")
        return None


def get_messstellen_for_gwk(gwk_id: str, messstellen_df: pd.DataFrame) -> list[str]:
    """Findet Messstellen für ein GWK."""
    
    if messstellen_df is None or messstellen_df.empty:
        return []
    
    # Filter nach GWK25 (NICHT GWK_ID!)
    if 'GWK25' in messstellen_df.columns:
        mkz_list = messstellen_df[messstellen_df['GWK25'] == gwk_id]['MKZ'].dropna().unique().tolist()
    elif 'GWK' in messstellen_df.columns:
        # Fallback auf GWK-Spalte
        mkz_list = messstellen_df[messstellen_df['GWK'] == gwk_id]['MKZ'].dropna().unique().tolist()
    else:
        # Fallback: Name-Matching
        mkz_list = messstellen_df['MKZ'].dropna().unique().tolist()
        # Filtere nach Präfix (z.B. "DESN_EL" in MKZ-Namen)
        prefix = gwk_id.split('-')[0] if '-' in gwk_id else gwk_id[:8]
        mkz_list = [mkz for mkz in mkz_list if prefix in str(mkz)]
    
    return mkz_list[:10]  # Max 10 Messstellen


# ============================================================================
# DEMO DATA & HELPERS
# ============================================================================

def _load_demo_gwk() -> list[str]:
    """Lädt 4 Demo-GWK für schnelle Tests."""
    return [
        "DESN_EL-2-1",
        "DESN_NE-3",
        "DESN_SAL-GW-060",
        "DESN_SE-1-1-1",
    ]


def _show_workflow_step(current: int, total: int = 6) -> None:
    """Zeigt Workflow-Progress-Indicator."""
    steps = ["🔧 Setup", "📊 Daten laden", "📈 Zeitreihen", "🔄 Korrelation", "📋 Statistik", "🗺️ Karte"]
    steps_display = "  →  ".join(
        f"**{s}**" if i == current else s
        for i, s in enumerate(steps)
    )
    st.caption(f"Workflow: {steps_display}")
    st.progress(current / (total - 1))


def _demo_data_cta() -> bool:
    """Zeigt 'Demo-Daten laden' Button in Empty States."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(
            "💡 **Tipp:** Die Demo-Daten umfassen 4 GWK mit vollständigen "
            "Zeitreihen (1961-2023) für GWN, Niederschlag und ETp — "
            "perfekt zum Erkunden aller Dashboard-Features."
        )
    with col2:
        if st.button("📦 Demo-Daten laden", use_container_width=True, key=f"demo_{id(st)}"):
            return True
    return False


# ============================================================================
# PAGE: HOME / ÜBERSICHT
# ============================================================================

def page_home() -> None:
    """Startseite mit Übersicht und Quick Actions."""
    
    st.title("💧 GWN Analyse Dashboard")
    st.markdown(
        """
        **Interaktive Analyse der Grundwasserneubildung** (GWN) mit Fokus auf 
        Klimawandel-Effekte und räumliche Trends in Sachsen.
        
        ### Features
        - 📊 **Zeitreihenanalyse** — GWN, Niederschlag, Evapotranspiration
        - 🔄 **Korrelationsanalyse** — GWN vs. Niederschlag mit Regressionen
        - 📋 **Periodenvergleich** — 1961-1990 vs. 1991-2020
        - 📈 **Trendstatistik** — Lineare Regression + Kendall-Tau
        - 🗺️ **Räumliche Darstellung** — Interaktive GWK-Karten
        - 💧 **Messstellen-Integration** — Grundwasserstände mit Grimm-Strele
        """
    )
    
    # Quick Metrics wenn Daten geladen
    if "data" in st.session_state:
        data = st.session_state["data"]
        n_gwk = len(data["gwn"]["GWK_ID"].unique())
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📍 GWK Geladen", str(n_gwk))
        
        avg_gwn = data["comparison"]["mean_hist"].mean()
        col2.metric("⌀ GWN 1991-2020", f"{avg_gwn:.1f} mm/a")
        
        delta = data["comparison"]["delta_abs"].mean()
        col3.metric("⌀ Änderung", f"{delta:+.1f} mm/a", 
                   delta_color="inverse")
        
        n_decreasing = (data["comparison"]["delta_abs"] < 0).sum()
        col4.metric("GWK mit Rückgang", f"{n_decreasing}/{n_gwk}")
        
        st.success(f"✅ Daten für {n_gwk} GWK erfolgreich geladen")
    
    st.divider()
    
    # Quick Start Cards
    st.subheader("🚀 Quick Start")
    st.caption("Wählen Sie einen Einstiegspunkt:")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**Schritt 1 — Konfiguration**")
        st.caption("GWK auswählen, Datenpfade prüfen, Daten laden")
        if st.button("⚙️ Zur Konfiguration →", use_container_width=True, key="qs_config"):
            st.session_state["_nav_pending"] = "⚙️ Konfiguration"
            st.rerun()
    
    with c2:
        st.markdown("**Schritt 2 — Zeitreihen**")
        st.caption("GWN, Niederschlag, ETp über Zeit visualisieren")
        if st.button("📈 Zu Zeitreihen →", use_container_width=True, key="qs_ts"):
            st.session_state["_nav_pending"] = "📈 Zeitreihen"
            st.rerun()
    
    with c3:
        st.markdown("**Schritt 3 — Statistik**")
        st.caption("Periodenvergleich, Trends, Export")
        if st.button("📊 Zur Statistik →", use_container_width=True, key="qs_stat"):
            st.session_state["_nav_pending"] = "📊 Statistiken"
            st.rerun()
    
    st.divider()
    
    # Analytical Showcase
    st.subheader("📐 Analytische Features")
    
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("**💧 Messstellen-Analyse**")
        st.caption("Grundwasserstände, Ganglinien, Grimm-Strele Trends")
        if st.button("Zu Messstellen →", key="cta_mkz", use_container_width=True):
            st.session_state["_nav_pending"] = "💧 Messstellen"
            st.rerun()
    
    with a2:
        st.markdown("**🗺️ Räumliche Analyse**")
        st.caption("GWK-Karten mit Änderungen, interaktive Choropleth")
        if st.button("Zur Karte →", key="cta_map", use_container_width=True):
            st.session_state["_nav_pending"] = "🗺️ Karte"
            st.rerun()
    
    with a3:
        st.markdown("**🔄 Korrelationen**")
        st.caption("GWN vs. Niederschlag, Scatter-Plots mit Regression")
        if st.button("Zu Korrelation →", key="cta_corr", use_container_width=True):
            st.session_state["_nav_pending"] = "🔄 Korrelation"
            st.rerun()
    
    st.divider()
    st.caption(
        "💡 **Hinweis:** Alle Plots sind interaktiv (Zoom, Pan, Hover). "
        "Nutzen Sie das Kamera-Icon zum Download als PNG."
    )


# ============================================================================
# PAGE: KONFIGURATION
# ============================================================================

def page_configuration() -> None:
    """Datenpfade, GWK-Auswahl, Daten laden."""
    
    st.title("⚙️ Konfiguration")
    st.markdown("Konfigurieren Sie Datenpfade und wählen Sie GWK für die Analyse.")
    
    _show_workflow_step(0)
    st.markdown("")
    
    # ── Datenpfade ──
    with st.expander("📁 Datenpfade", expanded=True):
        BASE_PATH = Path(__file__).parent / "data" / "kalib_beo_ERA5"
        
        data_base_dir = st.text_input(
            "Basis-Datenordner:",
            value=str(BASE_PATH),
            help="Ordner mit rg1_*, rg2_*, P_*, ETp_* Unterordnern"
        )
        
        default_mapping = str(Path(data_base_dir) / "GWK_2025" / "GWK_2025.csv")
        mapping_csv = st.text_input(
            "GWK Mapping CSV:",
            value=default_mapping,
            help="CSV mit Spalten: id, desc (GWK_ID)"
        )
        
        default_shapefile = str(Path(data_base_dir) / "GWK_2025" / "GWK_2025.shp")
        shapefile_path = st.text_input(
            "Shapefile (optional):",
            value=default_shapefile,
            help="Für räumliche Darstellung"
        )
    
    # ── GWK laden ──
    try:
        with st.spinner("🔄 Lade GWK-Mapping..."):
            mapping = load_gwk_mapping(mapping_csv)
            all_gwk = sorted(mapping["GWK_ID"].unique())
        
        st.success(f"✅ {len(all_gwk)} GWK im Mapping gefunden")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden des Mappings:\n\n```\n{e}\n```")
        st.stop()
    
    st.divider()
    
    # ── GWK Auswahl ──
    st.subheader("🎯 GWK Auswahl")
    
    selection_mode = st.radio(
        "Auswahlmodus:",
        ["Demo (4 GWK)", "Eigene Auswahl", "Alle GWK"],
        horizontal=True,
    )
    
    if selection_mode == "Demo (4 GWK)":
        demo_gwk = _load_demo_gwk()
        target_gwk = [g for g in demo_gwk if g in all_gwk]
        
        if not target_gwk:
            st.warning("⚠️ Keine Demo-GWK im Mapping gefunden. Nutzen Sie 'Eigene Auswahl'.")
            target_gwk = all_gwk[:4]
        
        st.info(f"📋 Verwende {len(target_gwk)} Demo-GWK")
        with st.expander("Ausgewählte Demo-GWK", expanded=False):
            for gwk in target_gwk:
                st.text(f"• {gwk}")
    
    elif selection_mode == "Eigene Auswahl":
        default_selection = [g for g in _load_demo_gwk() if g in all_gwk]
        if not default_selection:
            default_selection = all_gwk[:2]
        
        target_gwk = st.multiselect(
            "GWK auswählen (Mehrfachauswahl):",
            options=all_gwk,
            default=default_selection,
            help="Strg/Cmd + Klick für Mehrfachauswahl"
        )
        
        if not target_gwk:
            st.warning("⚠️ Bitte mindestens 1 GWK auswählen")
    
    else:  # Alle GWK
        target_gwk = all_gwk
        st.info(f"📋 Verwende alle {len(target_gwk)} verfügbaren GWK")
        
        if len(target_gwk) > 50:
            st.warning(
                f"⚠️ **Performance-Hinweis:** {len(target_gwk)} GWK können lange "
                "Ladezeiten verursachen. Erwägen Sie die Auswahl einer Teilmenge."
            )
    
    # ── Daten laden ──
    st.divider()
    
    if not target_gwk:
        st.warning("Bitte mindestens 1 GWK auswählen, um fortzufahren.")
        return
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Bereit zum Laden:** {len(target_gwk)} GWK")
        st.caption(
            "Dies berechnet jährliche GWN (rg1 + rg2), aggregiert auf GWK-Ebene, "
            "und lädt Niederschlag + ETp."
        )
    
    with col2:
        load_btn = st.button(
            "🚀 Daten laden",
            type="primary",
            use_container_width=True,
        )
    
    if load_btn:
        with st.spinner(f"🔄 Lade und verarbeite Daten für {len(target_gwk)} GWK..."):
            try:
                data = load_all_data(
                    data_base_dir=data_base_dir,
                    mapping_csv=mapping_csv,
                    target_gwk=target_gwk,
                )
                
                # In Session State speichern
                st.session_state["data"] = data
                st.session_state["target_gwk"] = target_gwk
                st.session_state["data_base_dir"] = data_base_dir
                st.session_state["shapefile_path"] = shapefile_path
                
                st.success(f"✅ Daten erfolgreich geladen für {len(target_gwk)} GWK!")
                
                # Zusammenfassung
                col1, col2, col3 = st.columns(3)
                col1.metric("GWN Datenpunkte", len(data["gwn"]))
                col2.metric("Niederschlag Punkte", len(data["precip"]))
                col3.metric("ETp Punkte", len(data["etp"]))
                
                st.info("➡️ Navigieren Sie zu **📈 Zeitreihen** oder **📊 Statistiken** für die Analyse")
                
            except Exception as e:
                st.error(f"❌ Fehler beim Laden:\n\n```python\n{e}\n```")
                logger.exception("Data loading failed")


# ============================================================================
# PAGE: ZEITREIHEN (mit Messstellen)
# ============================================================================

def page_timeseries() -> None:
    """Interaktive Zeitreihen-Plots mit Messstellen."""
    
    st.title("📈 Zeitreihen-Analyse")
    st.markdown("Visualisieren Sie GWN, Niederschlag, ETp und Grundwasserstände über Zeit.")
    
    _show_workflow_step(2)
    st.markdown("")
    
    # Daten prüfen
    if "data" not in st.session_state:
        st.info("📊 Keine Daten geladen. Gehen Sie zuerst zur **Konfiguration**.")
        if _demo_data_cta():
            st.session_state["_nav_pending"] = "⚙️ Konfiguration"
            st.rerun()
        return
    
    data = st.session_state["data"]
    target_gwk = st.session_state.get("target_gwk", [])
    
    st.success(f"✅ Daten für {len(target_gwk)} GWK verfügbar")
    
    # ── GWK Auswahl ──
    st.subheader("🎯 GWK für Detailansicht")
    
    available_gwk = sorted(data["gwn"]["GWK_ID"].unique())
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search = st.text_input(
            "🔍 GWK suchen:",
            placeholder="z.B. DESN_EL",
            help="Filtert die Dropdown-Liste"
        )
    
    filtered = [g for g in available_gwk if search.upper() in g.upper()] if search else available_gwk
    
    if not filtered:
        st.warning(f"Keine GWK gefunden für Suche: '{search}'")
        return
    
    with col2:
        st.caption(f"{len(filtered)} GWK verfügbar")
    
    selected_gwk = st.selectbox(
        "GWK auswählen:",
        filtered,
        index=0,
        label_visibility="collapsed"
    )
    
    # ── Plot Optionen ──
    st.divider()
    
    col1, col2 = st.columns(2)
    show_precip = col1.checkbox("📊 Niederschlag anzeigen", value=True)
    show_etp = col2.checkbox("🌡️ ETp anzeigen", value=True)
    
    # ── Metriken ──
    gwk_comparison = data["comparison"][data["comparison"]["GWK_ID"] == selected_gwk]
    
    if not gwk_comparison.empty:
        st.subheader(f"Kennzahlen: {selected_gwk}")
        
        row = gwk_comparison.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "GWN 1961-1990",
            f"{row['mean_ref']:.1f} mm/a",
            help="Referenzperiode"
        )
        
        col2.metric(
            "GWN 1991-2020",
            f"{row['mean_hist']:.1f} mm/a",
            help="Historische Periode"
        )
        
        delta = row["delta_abs"]
        col3.metric(
            "Absolute Änderung",
            f"{delta:+.1f} mm/a",
            delta=f"{delta:+.1f}",
            delta_color="inverse"
        )
        
        delta_pct = row["delta_rel_pct"]
        col4.metric(
            "Relative Änderung",
            f"{delta_pct:+.1f} %",
            delta=f"{delta_pct:+.1f}%",
            delta_color="inverse"
        )
    
    st.divider()
    
    # ── GWN Plot ──
    try:
        fig = create_interactive_timeseries(
            df_gwn=data["gwn"],
            df_precip=data["precip"],
            df_etp=data["etp"],
            gwk=selected_gwk,
            show_precip=show_precip,
            show_etp=show_etp,
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Fehler beim Erstellen des Plots:\n\n```\n{e}\n```")
        logger.exception("Timeseries plot failed")
    
    # ── Messstellen-Sektion ──
    st.divider()
    st.subheader("💧 Grundwasser-Messstellen")
    
    with st.expander("ℹ️ Messstellen-Daten", expanded=False):
        st.markdown(
            """
            **Hinweis:** Messstellen-Daten werden von NIWIS (Niedrigwasser-Informationssystem Sachsen) 
            nachgeladen. Der erste Aufruf kann 1-2 Minuten dauern.
            
            Die Daten werden lokal gecacht für schnelleren Zugriff.
            """
        )
    
    cache_dir = st.text_input(
        "Cache-Verzeichnis:",
        value="./cache",
        help="Lokaler Ordner für NIWIS-Downloads",
        key="cache_dir_ts"
    )
    
    if st.button("🔄 Messstellen für GWK laden", type="primary"):
        with st.spinner(f"Lade Messstellen für {selected_gwk}..."):
            try:
                # Alle Messstellen laden
                messstellen = load_messstellen_data(cache_dir=cache_dir)
                
                # Messstellen für GWK filtern
                mkz_list = get_messstellen_for_gwk(selected_gwk, messstellen)
                
                if not mkz_list:
                    st.warning(f"⚠️ Keine Messstellen für {selected_gwk} gefunden")
                else:
                    st.success(f"✅ {len(mkz_list)} Messstellen gefunden")
                    
                    # Messstelle auswählen
                    selected_mkz = st.selectbox(
                        "Messstelle auswählen:",
                        mkz_list,
                        key="mkz_select_ts"
                    )
                    
                    # Ganglinie plotten
                    fig_mkz = create_messstellen_plot(
                        mkz=selected_mkz,
                        gwk_id=selected_gwk,
                        cache_dir=cache_dir
                    )
                    
                    if fig_mkz:
                        st.plotly_chart(fig_mkz, use_container_width=True)
                        
                        # Trend-Optionen
                        with st.expander("📐 Trend berechnen (Grimm-Strele)"):
                            col1, col2 = st.columns(2)
                            trend_start = col1.date_input(
                                "Trend von:",
                                value=pd.to_datetime("2000-01-01"),
                                key="trend_start_ts"
                            )
                            trend_end = col2.date_input(
                                "Trend bis:",
                                value=pd.to_datetime("2023-12-31"),
                                key="trend_end_ts"
                            )
                            
                            if st.button("Trend berechnen", key="calc_trend_ts"):
                                with st.spinner("Berechne Trend..."):
                                    result = compute_mkz_trend(
                                        mkz=selected_mkz,
                                        trend_ab=trend_start,
                                        trend_bis=trend_end,
                                        cache_dir=cache_dir,
                                    )
                                    
                                    if "error" in result:
                                        st.error(f"Fehler: {result['error']}")
                                    else:
                                        col1, col2, col3 = st.columns(3)
                                        col1.metric("Anstieg", f"{result['Anstieg [cm/a]']:.2f} cm/a")
                                        col2.metric("Grimm-Strele", f"{result['Grimm-Strele [%/a]']:.2f} %/a")
                                        col3.metric("Trend", result["Trend"])
                                        
                                        st.info(
                                            f"**Anzahl Werte:** {result['Anzahl Werte']}\n\n"
                                            f"**Spanne:** {result['Spanne [cm]']:.1f} cm"
                                        )
                    else:
                        st.warning("Keine Zeitreihe für diese Messstelle verfügbar")
            
            except Exception as e:
                st.error(f"❌ Fehler beim Laden der Messstellen:\n\n```\n{e}\n```")
                logger.exception("Messstellen loading failed")


# ============================================================================
# PAGE: KORRELATION
# ============================================================================

def page_correlation() -> None:
    """GWN vs. Niederschlag Korrelation."""
    
    st.title("🔄 Korrelations-Analyse")
    st.markdown("Analysieren Sie den Zusammenhang zwischen GWN und Niederschlag.")
    
    _show_workflow_step(3)
    st.markdown("")
    
    if "data" not in st.session_state:
        st.info("📊 Keine Daten geladen. Gehen Sie zuerst zur **Konfiguration**.")
        if _demo_data_cta():
            st.session_state["_nav_pending"] = "⚙️ Konfiguration"
            st.rerun()
        return
    
    data = st.session_state["data"]
    available_gwk = sorted(data["gwn"]["GWK_ID"].unique())
    
    selected_gwk = st.selectbox("GWK auswählen:", available_gwk, index=0)
    
    st.divider()
    
    try:
        fig = create_correlation_plot(
            df_gwn=data["gwn"],
            df_precip=data["precip"],
            gwk=selected_gwk,
        )
        
        if fig is None:
            st.warning("⚠️ Keine Daten für Korrelation verfügbar")
        else:
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(
                "💡 **Interpretation:**\n"
                "- **R² > 0.7:** Starke Korrelation\n"
                "- **R² 0.4-0.7:** Moderate Korrelation\n"
                "- **R² < 0.4:** Schwache Korrelation\n"
                "- **p < 0.05:** Statistisch signifikant"
            )
    
    except Exception as e:
        st.error(f"❌ Fehler:\n\n```\n{e}\n```")
        logger.exception("Correlation plot failed")


# ============================================================================
# PAGE: STATISTIKEN
# ============================================================================

def page_statistics() -> None:
    """Periodenvergleich, Trendanalyse, Export."""
    
    st.title("📊 Statistiken & Vergleich")
    st.markdown("Periodenvergleich (1961-1990 vs. 1991-2020) und Trendanalyse.")
    
    _show_workflow_step(4)
    st.markdown("")
    
    if "data" not in st.session_state:
        st.info("📊 Keine Daten geladen. Gehen Sie zuerst zur **Konfiguration**.")
        if _demo_data_cta():
            st.session_state["_nav_pending"] = "⚙️ Konfiguration"
            st.rerun()
        return
    
    data = st.session_state["data"]
    target_gwk = st.session_state.get("target_gwk", [])
    
    # ── Zusammenfassung ──
    st.subheader(f"📋 Übersicht: {len(target_gwk)} GWK")
    
    col1, col2, col3, col4 = st.columns(4)
    
    avg_ref = data["comparison"]["mean_ref"].mean()
    col1.metric("⌀ GWN 1961-1990", f"{avg_ref:.1f} mm/a")
    
    avg_hist = data["comparison"]["mean_hist"].mean()
    col2.metric("⌀ GWN 1991-2020", f"{avg_hist:.1f} mm/a")
    
    avg_delta = data["comparison"]["delta_abs"].mean()
    col3.metric(
        "⌀ Änderung",
        f"{avg_delta:+.1f} mm/a",
        delta=f"{avg_delta:+.1f}",
        delta_color="inverse"
    )
    
    n_dec = (data["comparison"]["delta_abs"] < 0).sum()
    col4.metric("GWK mit Rückgang", f"{n_dec} / {len(target_gwk)}")
    
    st.divider()
    
    # ── Tabs ──
    tab_comparison, tab_trends, tab_export = st.tabs([
        "📊 Periodenvergleich",
        "📈 Trendanalyse",
        "💾 Daten-Export"
    ])
    
    with tab_comparison:
        st.subheader("Vergleich 1961-1990 vs. 1991-2020")
        
        try:
            fig = create_comparison_barplot(data["comparison"])
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Plot-Fehler: {e}")
        
        st.markdown("### Detailtabelle")
        
        display_cols = [
            "GWK_ID",
            "mean_ref", "mean_hist",
            "delta_abs", "delta_rel_pct",
            "n_years_ref", "n_years_hist"
        ]
        
        display_df = data["comparison"][display_cols].copy()
        display_df = display_df.rename(columns={
            "mean_ref": "GWN 1961-90 [mm/a]",
            "mean_hist": "GWN 1991-2020 [mm/a]",
            "delta_abs": "Δ absolut [mm/a]",
            "delta_rel_pct": "Δ relativ [%]",
            "n_years_ref": "Jahre Ref.",
            "n_years_hist": "Jahre Hist."
        })
        
        st.dataframe(
            display_df.style.format({
                "GWN 1961-90 [mm/a]": "{:.1f}",
                "GWN 1991-2020 [mm/a]": "{:.1f}",
                "Δ absolut [mm/a]": "{:+.1f}",
                "Δ relativ [%]": "{:+.1f}",
            }),
            use_container_width=True,
            height=400,
        )
    
    with tab_trends:
        st.subheader("Lineare Regression & Kendall-Tau")
        
        st.markdown("### Trendstatistik")
        
        display_cols_trend = [
            "GWK_ID",
            "n_years", "mean", "std",
            "lr_slope", "lr_pvalue", "lr_rvalue",
            "kendall_tau", "kendall_p"
        ]
        
        trend_df = data["trend"][display_cols_trend].copy()
        trend_df = trend_df.rename(columns={
            "n_years": "Jahre",
            "mean": "⌀ GWN [mm/a]",
            "std": "σ [mm/a]",
            "lr_slope": "Slope [mm/a²]",
            "lr_pvalue": "p-value (LR)",
            "lr_rvalue": "R",
            "kendall_tau": "τ (Kendall)",
            "kendall_p": "p-value (τ)"
        })
        
        st.dataframe(
            trend_df.style.format({
                "⌀ GWN [mm/a]": "{:.1f}",
                "σ [mm/a]": "{:.1f}",
                "Slope [mm/a²]": "{:.4f}",
                "p-value (LR)": "{:.4f}",
                "R": "{:.3f}",
                "τ (Kendall)": "{:.3f}",
                "p-value (τ)": "{:.4f}",
            }),
            use_container_width=True,
            height=400,
        )
        
        st.info(
            "**Interpretation:**\n"
            "- **Slope < 0:** Abnehmende GWN\n"
            "- **p-value < 0.05:** Statistisch signifikant\n"
            "- **Kendall τ < -0.3:** Deutlich fallender Trend"
        )
    
    with tab_export:
        st.subheader("📥 Daten exportieren")
        
        st.markdown("### CSV Downloads")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_comp = data["comparison"].to_csv(index=False, sep=";", decimal=",")
            st.download_button(
                "📄 Vergleichstabelle (CSV)",
                data=csv_comp,
                file_name=f"gwn_vergleich_{len(target_gwk)}_gwk.csv",
                mime="text/csv",
                use_container_width=True,
            )
        
        with col2:
            csv_trend = data["trend"].to_csv(index=False, sep=";", decimal=",")
            st.download_button(
                "📄 Trendanalyse (CSV)",
                data=csv_trend,
                file_name=f"gwn_trends_{len(target_gwk)}_gwk.csv",
                mime="text/csv",
                use_container_width=True,
            )
        
        csv_gwn = data["gwn"].to_csv(index=False, sep=";", decimal=",")
        st.download_button(
            "📄 GWN Zeitreihen (CSV)",
            data=csv_gwn,
            file_name=f"gwn_zeitreihen_{len(target_gwk)}_gwk.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ============================================================================
# PAGE: KARTE
# ============================================================================

def page_map() -> None:
    """Räumliche Darstellung der GWK."""
    
    st.title("🗺️ Räumliche Analyse")
    st.markdown("Interaktive Karte der GWK mit Änderungen der GWN.")
    
    _show_workflow_step(5)
    st.markdown("")
    
    if "data" not in st.session_state:
        st.info("📊 Keine Daten geladen. Gehen Sie zuerst zur **Konfiguration**.")
        if _demo_data_cta():
            st.session_state["_nav_pending"] = "⚙️ Konfiguration"
            st.rerun()
        return
    
    data = st.session_state["data"]
    shapefile_path = st.session_state.get("shapefile_path")
    
    # Shapefile laden
    try:
        import geopandas as gpd
        
        if shapefile_path and Path(shapefile_path).exists():
            with st.spinner("🗺️ Lade Geometrien..."):
                gdf = load_gwk_geometries(shapefile_path)  # ← GEÄNDERT
            
            if gdf is not None and not gdf.empty:
                st.success(f"✅ {len(gdf)} Geometrien geladen")
            else:
                st.warning("⚠️ Keine Geometrien im Shapefile gefunden")
                return
        else:
            st.warning("⚠️ Shapefile nicht gefunden. Karte nicht verfügbar.")
            st.info(f"Erwarteter Pfad: `{shapefile_path}`")
            return
    
    except ImportError:
        st.error("❌ `geopandas` nicht installiert. Führe aus: `pip install geopandas`")
        return
    except Exception as e:
        st.error(f"❌ Fehler beim Laden des Shapefiles:\n\n```\n{e}\n```")
        return
    
    # ── GWK Auswahl für Highlight ──
    st.subheader("🎯 GWK hervorheben (optional)")
    
    available_gwk = sorted(data["gwn"]["GWK_ID"].unique())
    selected_gwk = st.selectbox(
        "GWK zum Hervorheben:",
        ["Kein Highlight"] + available_gwk,
        index=0,
    )
    
    highlight_gwk = None if selected_gwk == "Kein Highlight" else selected_gwk
    
    st.divider()
    
    # ── Karte ──
    try:
        fig = create_gwk_map(
            gdf=gdf,
            comparison_df=data["comparison"],
            selected_gwk=highlight_gwk,
        )
        
        if fig is None:
            st.warning("Karte konnte nicht erstellt werden")
        else:
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(
                "**Legende:**\n"
                "- 🟢 **Grün:** GWN-Zunahme (> +10 mm/a)\n"
                "- 🟡 **Gelb:** Keine signifikante Änderung (-10 bis +10 mm/a)\n"
                "- 🔴 **Rot:** GWN-Rückgang (< -10 mm/a)\n"
                "- Hover für Details zu jedem GWK"
            )
    
    except Exception as e:
        st.error(f"❌ Fehler beim Erstellen der Karte:\n\n```\n{e}\n```")
        logger.exception("Map creation failed")


# ============================================================================
# PAGE: MESSSTELLEN
# ============================================================================

def page_stations() -> None:
    """Messstellen-Analyse mit Grundwasserständen."""
    
    st.title("💧 Messstellen-Analyse")
    st.markdown("Grundwasserstände und Grimm-Strele Trendanalyse.")
    
    st.info(
        "⚠️ **Hinweis:** Messstellen-Daten werden von NIWIS nachgeladen. "
        "Erster Aufruf kann 1-2 Minuten dauern (Caching aktiv)."
    )
    
    cache_dir = st.text_input(
        "Cache-Verzeichnis:",
        value="./cache",
        help="Lokaler Ordner für NIWIS-Downloads"
    )
    
    if not st.button("📊 Messstellen laden", type="primary"):
        return
    
    with st.spinner("🔄 Lade Messstellen-Übersicht von NIWIS..."):
        try:
            messstellen = load_messstellen_data(cache_dir=cache_dir)
            
            st.success(f"✅ {len(messstellen)} Messstellen geladen")
            
            st.dataframe(
                messstellen.head(50),
                use_container_width=True,
                height=400,
            )
            
            # Trend-Berechnung
            st.divider()
            st.subheader("🔍 Trend für einzelne MKZ")
            
            mkz_list = messstellen["MKZ"].dropna().unique()
            selected_mkz = st.selectbox("MKZ auswählen:", mkz_list[:100])
            
            col1, col2 = st.columns(2)
            trend_start = col1.date_input("Trend von:", value=pd.to_datetime("2000-01-01"))
            trend_end = col2.date_input("Trend bis:", value=pd.to_datetime("2023-12-31"))
            
            if st.button("📐 Trend berechnen"):
                with st.spinner(f"Berechne Trend für {selected_mkz}..."):
                    result = compute_mkz_trend(
                        mkz=selected_mkz,
                        trend_ab=trend_start,
                        trend_bis=trend_end,
                        cache_dir=cache_dir,
                    )
                    
                    if "error" in result:
                        st.error(f"Fehler: {result['error']}")
                    else:
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Anstieg", f"{result['Anstieg [cm/a]']:.2f} cm/a")
                        col2.metric("Grimm-Strele", f"{result['Grimm-Strele [%/a]']:.2f} %/a")
                        col3.metric("Trend", result["Trend"])
                        
                        st.info(
                            f"**Anzahl Werte:** {result['Anzahl Werte']}\n\n"
                            f"**Spanne:** {result['Spanne [cm]']:.1f} cm"
                        )
        
        except Exception as e:
            st.error(f"❌ Fehler:\n\n```\n{e}\n```")
            logger.exception("Messstellen loading failed")


# ============================================================================
# MAIN APP
# ============================================================================

_PAGES: dict[str, tuple[str, callable]] = {
    "home": ("🏠 Home", page_home),
    "config": ("⚙️ Konfiguration", page_configuration),
    "timeseries": ("📈 Zeitreihen", page_timeseries),
    "correlation": ("🔄 Korrelation", page_correlation),
    "statistics": ("📊 Statistiken", page_statistics),
    "map": ("🗺️ Karte", page_map),
    "stations": ("💧 Messstellen", page_stations),
}


def main() -> None:
    """Haupteinstiegspunkt der Streamlit-App."""
    
    st.set_page_config(
        page_title="GWN Dashboard",
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="auto",
    )
    
    _inject_global_css()
    
    # ── Sidebar Navigation ──
    page_labels = [label for label, _ in _PAGES.values()]
    
    st.sidebar.markdown("## 💧 GWN Dashboard")
    st.sidebar.markdown("---")
    
    # Pending navigation anwenden
    if "_nav_pending" in st.session_state:
        st.session_state["current_page"] = st.session_state.pop("_nav_pending")
    elif "current_page" not in st.session_state:
        st.session_state["current_page"] = page_labels[0]
    
    selected_label = st.sidebar.radio(
        "Navigate",
        page_labels,
        key="current_page",
        label_visibility="collapsed",
    )
    
    # Map label → key
    label_to_key = {label: key for key, (label, _) in _PAGES.items()}
    selected_key = label_to_key[selected_label]
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"GWN Dashboard v{__version__}")
    
    # Session State Info
    if "data" in st.session_state:
        n = len(st.session_state.get("target_gwk", []))
        st.sidebar.success(f"📦 {n} GWK geladen")
    
    # ── Render Page ──
    _, page_func = _PAGES[selected_key]
    page_func()


if __name__ == "__main__":
    main()