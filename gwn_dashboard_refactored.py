"""
GWN Dashboard - Grundwasserneubildung Analyse
Refactored mit modernem Layout und verbesserter UX
EIGENSTÄNDIGE VERSION - Keine externen Code-Abhängigkeiten
"""

from __future__ import annotations

import logging
import glob
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime, date
from urllib.request import urlretrieve

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import geopandas as gpd
from pyproj import Transformer
from scipy.stats import linregress, kendalltau
from sklearn import linear_model
import plotly.express as px

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
# DATENVERARBEITUNGS-FUNKTIONEN (von gwn_dashboard_24062026_v3.py kopiert)
# ============================================================================

@st.cache_data
def load_gwk_mapping(mapping_csv: str) -> pd.DataFrame:
    """Lädt GWK-Mapping aus CSV - erwartet Format: id,name,desc"""
    
    # CSV einlesen mit KOMMA als Trennzeichen
    df = pd.read_csv(mapping_csv, sep=",", encoding="utf-8")
    
    # Strikt prüfen: desc muss existieren
    if "desc" not in df.columns:
        raise KeyError(
            f"Spalte 'desc' nicht in CSV gefunden!\n"
            f"Verfügbare Spalten: {df.columns.tolist()}\n"
            f"Erwartetes Format: id,name,desc"
        )
    
    # GWK_ID aus 'desc' Spalte erstellen
    df["GWK_ID"] = df["desc"].astype(str).str.strip()
    
    # ID-Spalte prüfen
    if "id" not in df.columns:
        raise KeyError(
            f"Spalte 'id' nicht in CSV gefunden!\n"
            f"Verfügbare Spalten: {df.columns.tolist()}\n"
            f"Erwartetes Format: id,name,desc"
        )
    
    return df[["id", "GWK_ID"]]
    

def find_parameter_csv(base_dir: Path, parameter: str) -> Optional[Path]:
    """Findet CSV-Datei für Parameter"""
    folder_glob = str(base_dir / f"{parameter}_*_all_month")
    folders = glob.glob(folder_glob)
    if not folders:
        return None
    folder = Path(sorted(folders)[0])
    csv_path = folder / f"{folder.name}.csv"
    return csv_path if csv_path.exists() else None


@st.cache_data
def load_monthly_csv(csv_path: Path) -> pd.DataFrame:
    """Lädt monatliche CSV-Datei"""
    df = pd.read_csv(csv_path, sep=",", encoding="utf-8")
    df.columns = df.columns.str.strip()
    
    # Datum parsen
    if "month" in df.columns and "year" in df.columns:
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    
    return df


def monthly_to_yearly_sum(df_monthly: pd.DataFrame, value_name: str) -> pd.DataFrame:
    """Aggregiert monatliche Daten zu Jahressummen"""
    return (
        df_monthly.groupby(["id", "year"], as_index=False)["value"]
        .sum()
        .rename(columns={"value": value_name})
    )


@st.cache_data
def compute_gwn_yearly(base_dir: Path) -> pd.DataFrame:
    """Berechnet jährliche GWN aus rg1 + rg2"""
    rg1_csv = find_parameter_csv(base_dir, "rg1")
    rg2_csv = find_parameter_csv(base_dir, "rg2")
    
    if rg1_csv is None or rg2_csv is None:
        raise FileNotFoundError("rg1 oder rg2 CSV nicht gefunden")
    
    df_rg1 = load_monthly_csv(rg1_csv)
    df_rg2 = load_monthly_csv(rg2_csv)
    
    rg1_yearly = monthly_to_yearly_sum(df_rg1, "rg1_mm_a")
    rg2_yearly = monthly_to_yearly_sum(df_rg2, "rg2_mm_a")
    
    # Merge
    df_gwn = pd.merge(rg1_yearly, rg2_yearly, on=["id", "year"], how="outer")
    df_gwn["gwn_mm_a"] = df_gwn["rg1_mm_a"].fillna(0) + df_gwn["rg2_mm_a"].fillna(0)
    
    return df_gwn[["id", "year", "gwn_mm_a"]]


@st.cache_data
def compute_parameter_yearly(base_dir: Path, parameter: str) -> pd.DataFrame:
    """Berechnet jährliche Werte für Parameter (P, ETp)"""
    csv_path = find_parameter_csv(base_dir, parameter)
    
    if csv_path is None:
        raise FileNotFoundError(f"{parameter} CSV nicht gefunden")
    
    df = load_monthly_csv(csv_path)
    return monthly_to_yearly_sum(df, "value")


@st.cache_data
def load_gwk_geometries(shapefile_path: str) -> gpd.GeoDataFrame:
    """Lädt GWK-Geometrien aus Shapefile"""
    gdf = gpd.read_file(shapefile_path)
    
    # Koordinatensystem prüfen und ggf. nach WGS84 transformieren
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    
    # Spalte 'desc' als GWK_ID verwenden
    if 'desc' in gdf.columns:
        gdf['GWK_ID'] = gdf['desc'].astype(str).str.strip()
    
    return gdf


def attach_gwk_id(df_id_year: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Hängt GWK_ID an DataFrame"""
    return pd.merge(df_id_year, mapping, on="id", how="left")


def aggregate_to_gwk(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Aggregiert Daten auf GWK-Ebene"""
    return (
        df.dropna(subset=["GWK_ID"])
        .groupby(["GWK_ID", "year"], as_index=False)[value_col]
        .mean()
    )


def filter_target_gwk(df: pd.DataFrame, target_gwk: List[str]) -> pd.DataFrame:
    """Filtert auf Ziel-GWK"""
    return df[df["GWK_ID"].isin(target_gwk)].copy()


def period_stats(df: pd.DataFrame, value_col: str, start: int, end: int) -> pd.DataFrame:
    """Berechnet Statistiken für Periode"""
    sub = df[(df["year"] >= start) & (df["year"] <= end)].copy()
    rows = []
    for gwk, g in sub.groupby("GWK_ID"):
        rows.append({
            "GWK_ID": gwk,
            "mean": g[value_col].mean(),
            "std": g[value_col].std(),
            "n_years": len(g)
        })
    return pd.DataFrame(rows)


def compute_trend_stats(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Berechnet Trendstatistiken für jedes GWK"""
    rows = []
    for gwk, g in df.groupby("GWK_ID"):
        x = g["year"].values
        y = g[value_col].values
        
        n = len(g)
        mean_val = y.mean()
        std_val = y.std()
        
        # Lineare Regression
        lr = linregress(x, y)
        
        # Kendall-Tau
        kt = kendalltau(x, y)
        
        rows.append({
            "GWK_ID": gwk,
            "n_years": n,
            "mean": mean_val,
            "std": std_val,
            "lr_slope": lr.slope,
            "lr_intercept": lr.intercept,
            "lr_rvalue": lr.rvalue,
            "lr_pvalue": lr.pvalue,
            "kendall_tau": kt.correlation,
            "kendall_p": kt.pvalue
        })
    
    return pd.DataFrame(rows)


@st.cache_data
def load_all_data(data_base_dir: str, mapping_csv: str, target_gwk: List[str]) -> Dict:
    """Lädt alle Daten (GWN, P, ETp) und berechnet Statistiken"""
    
    base_path = Path(data_base_dir)
    mapping = load_gwk_mapping(mapping_csv)
    
    # GWN berechnen
    df_gwn = compute_gwn_yearly(base_path)
    df_gwn = attach_gwk_id(df_gwn, mapping)
    df_gwn = aggregate_to_gwk(df_gwn, "gwn_mm_a")
    df_gwn = filter_target_gwk(df_gwn, target_gwk)
    
    # Niederschlag
    df_precip = compute_parameter_yearly(base_path, "P")
    df_precip = attach_gwk_id(df_precip, mapping)
    df_precip = aggregate_to_gwk(df_precip, "value")
    df_precip = filter_target_gwk(df_precip, target_gwk)
    
    # ETp
    df_etp = compute_parameter_yearly(base_path, "ETp")
    df_etp = attach_gwk_id(df_etp, mapping)
    df_etp = aggregate_to_gwk(df_etp, "value")
    df_etp = filter_target_gwk(df_etp, target_gwk)
    
    # Periodenvergleich
    ref_start, ref_end = 1961, 1990
    hist_start, hist_end = 1991, 2020
    
    stats_ref = period_stats(df_gwn, "gwn_mm_a", ref_start, ref_end)
    stats_hist = period_stats(df_gwn, "gwn_mm_a", hist_start, hist_end)
    
    comparison = pd.merge(
        stats_ref.rename(columns={"mean": "mean_ref", "std": "std_ref", "n_years": "n_years_ref"}),
        stats_hist.rename(columns={"mean": "mean_hist", "std": "std_hist", "n_years": "n_years_hist"}),
        on="GWK_ID",
        how="outer"
    )
    
    comparison["delta_abs"] = comparison["mean_hist"] - comparison["mean_ref"]
    comparison["delta_rel_pct"] = (comparison["delta_abs"] / comparison["mean_ref"]) * 100
    
    # Trendstatistik
    trend = compute_trend_stats(df_gwn, "gwn_mm_a")
    
    return {
        "gwn": df_gwn,
        "precip": df_precip,
        "etp": df_etp,
        "comparison": comparison,
        "trend": trend
    }


# ============================================================================
# PLOT-FUNKTIONEN (von gwn_dashboard_24062026_v3.py kopiert)
# ============================================================================

def create_interactive_timeseries(df_gwn, df_precip, df_etp, gwk, show_precip=True, show_etp=True):
    """Erstellt interaktiven Zeitreihenplot mit Plotly"""
    
    # Daten filtern
    gwn_data = df_gwn[df_gwn['GWK_ID'] == gwk].sort_values('year')
    precip_data = df_precip[df_precip['GWK_ID'] == gwk].sort_values('year')
    etp_data = df_etp[df_etp['GWK_ID'] == gwk].sort_values('year')
    
    # Perioden
    ref_start, ref_end = 1961, 1990
    hist_start, hist_end = 1991, 2020
    
    # Mittelwerte berechnen
    gwn_ref = gwn_data[(gwn_data['year'] >= ref_start) & (gwn_data['year'] <= ref_end)]['gwn_mm_a'].mean()
    gwn_hist = gwn_data[(gwn_data['year'] >= hist_start) & (gwn_data['year'] <= hist_end)]['gwn_mm_a'].mean()
    
    # Subplot erstellen
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1,
        subplot_titles=(f'<b>Grundwasserneubildung - {gwk}</b>', '<b>Niederschlag & ETp</b>' if show_precip or show_etp else ''),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    # GWN-Linie
    fig.add_trace(
        go.Scatter(
            x=gwn_data['year'],
            y=gwn_data['gwn_mm_a'],
            mode='lines+markers',
            name='GWN',
            line=dict(color='steelblue', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Jahr:</b> %{x}<br><b>GWN:</b> %{y:.1f} mm/a<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Referenzperioden-Mittelwert
    fig.add_hline(
        y=gwn_ref,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Ø 1961-1990: {gwn_ref:.1f} mm/a",
        annotation_position="left",
        row=1, col=1
    )
    
    # Historische Periode Mittelwert
    fig.add_hline(
        y=gwn_hist,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Ø 1991-2020: {gwn_hist:.1f} mm/a",
        annotation_position="right",
        row=1, col=1
    )
    
    # Niederschlag
    if show_precip and not precip_data.empty:
        fig.add_trace(
            go.Bar(
                x=precip_data['year'],
                y=precip_data['value'],
                name='Niederschlag',
                marker_color='darkblue',
                opacity=0.6,
                hovertemplate='<b>Jahr:</b> %{x}<br><b>P:</b> %{y:.1f} mm/a<extra></extra>'
            ),
            row=2, col=1
        )
    
    # ETp
    if show_etp and not etp_data.empty:
        fig.add_trace(
            go.Bar(
                x=etp_data['year'],
                y=etp_data['value'],
                name='ETp',
                marker_color='orangered',
                opacity=0.6,
                hovertemplate='<b>Jahr:</b> %{x}<br><b>ETp:</b> %{y:.1f} mm/a<extra></extra>'
            ),
            row=2, col=1
        )
    
    # Layout
    fig.update_xaxes(title_text="Jahr", row=2, col=1)
    fig.update_yaxes(title_text="GWN [mm/a]", row=1, col=1)
    fig.update_yaxes(title_text="[mm/a]", row=2, col=1)
    
    fig.update_layout(
        height=700,
        hovermode='x unified',
        template='plotly_white',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_correlation_plot(df_gwn, df_precip, gwk):
    """Erstellt Korrelationsplot GWN vs. Niederschlag"""
    
    gwn_data = df_gwn[df_gwn['GWK_ID'] == gwk][['year', 'gwn_mm_a']]
    precip_data = df_precip[df_precip['GWK_ID'] == gwk][['year', 'value']]
    
    merged = pd.merge(gwn_data, precip_data, on='year', suffixes=('_gwn', '_p'))
    
    if merged.empty:
        return None
    
    # Regression
    x = merged['value'].values
    y = merged['gwn_mm_a'].values
    lr = linregress(x, y)
    
    # Plot
    fig = go.Figure()
    
    # Scatter
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        name='Datenpunkte',
        marker=dict(size=8, color='steelblue'),
        hovertemplate='<b>P:</b> %{x:.1f} mm/a<br><b>GWN:</b> %{y:.1f} mm/a<extra></extra>'
    ))
    
    # Regressionslinie
    x_line = np.array([x.min(), x.max()])
    y_line = lr.slope * x_line + lr.intercept
    
    fig.add_trace(go.Scatter(
        x=x_line,
        y=y_line,
        mode='lines',
        name='Regression',
        line=dict(color='red', dash='dash'),
        hovertemplate='y = %.2fx + %.2f<extra></extra>' % (lr.slope, lr.intercept)
    ))
    
    # Annotation
    fig.add_annotation(
        x=0.05, y=0.95,
        xref='paper', yref='paper',
        text=f'R² = {lr.rvalue**2:.3f}<br>p = {lr.pvalue:.4f}',
        showarrow=False,
        bgcolor='white',
        bordercolor='black',
        borderwidth=1
    )
    
    fig.update_layout(
        title=f'<b>Korrelation: GWN vs. Niederschlag - {gwk}</b>',
        xaxis_title='Niederschlag [mm/a]',
        yaxis_title='GWN [mm/a]',
        height=500,
        template='plotly_white'
    )
    
    return fig


def create_comparison_barplot(comparison_df):
    """Erstellt Vergleichsbarplot für Periodenänderungen"""
    
    df = comparison_df.sort_values('delta_abs')
    
    colors = ['red' if d < 0 else 'green' for d in df['delta_abs']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['delta_abs'],
        y=df['GWK_ID'],
        orientation='h',
        marker_color=colors,
        hovertemplate='<b>%{y}</b><br>Änderung: %{x:+.1f} mm/a<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Änderung der GWN (1991-2020 vs. 1961-1990)</b>',
        xaxis_title='Änderung [mm/a]',
        yaxis_title='',
        height=max(400, len(df) * 20),
        template='plotly_white'
    )
    
    return fig


def create_gwk_map(gdf, comparison_df, selected_gwk=None):
    """Erstellt interaktive Karte mit GWK und Änderungen"""
    
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
# MESSSTELLEN-FUNKTIONEN (von gwn_dashboard_24062026_v3.py kopiert)
# ============================================================================

from urllib.request import urlretrieve
from pyproj import Transformer
from sklearn import linear_model
import datetime

@st.cache_data
def cacheorload(filename: str, cache_dir: str = "./cache") -> None:
    """Lädt Datei von NIWIS, falls nicht lokal vorhanden"""
    os.makedirs(cache_dir, exist_ok=True)
    filepath = os.path.join(cache_dir, filename)
    if not os.path.isfile(filepath):
        url = "https://www.umwelt.sachsen.de/umwelt/infosysteme/niwis/weitere/"
        try:
            urlretrieve(url + filename, filepath)
        except Exception as e:
            st.error(f"Download fehlgeschlagen: {filename}\n{e}")
    return


@st.cache_data
def load_messstellen_data(cache_dir: str = "./cache") -> pd.DataFrame:
    """Lädt Messstellenübersicht mit GWK-Zuordnung"""
    
    # Übersicht laden
    cacheorload('Export_MKZ_Uebersicht.csv', cache_dir)
    messstellen = pd.read_csv(
        os.path.join(cache_dir, 'Export_MKZ_Uebersicht.csv'),
        sep=';',
        thousands='.',
        decimal=','
    )
    
    # GWK-Mapping laden (lokal, muss im Repo liegen)
    mkz_gwk_path = Path(__file__).parent / "data" / "MKZ_GWK.csv"
    
    if mkz_gwk_path.exists():
        mess_gwk = pd.read_csv(
            mkz_gwk_path, 
            sep=';', 
            quotechar='"', 
            decimal=',',
            dtype={'MKZ': str}
        )
        mess_gwk = mess_gwk.fillna("na")
        # Sicherstellen, dass MKZ-Spalte in beiden DataFrames als String vorliegt
        messstellen['MKZ'] = messstellen['MKZ'].astype(str)
        mess_gwk['MKZ'] = mess_gwk['MKZ'].astype(str)
        # Merge: left join, um alle Messstellen zu behalten
        messstellen = messstellen.merge(mess_gwk, on="MKZ", how="left", suffixes=('', '_gwk'))
    else:
        st.warning(f"⚠️ MKZ_GWK.csv nicht gefunden unter {mkz_gwk_path}")
        messstellen['GWK'] = "unbekannt"
        messstellen['GWK25'] = "unbekannt"
    
    # Datums-Spalten konvertieren
    if 'Erstes_Messdatum' in messstellen.columns:
        messstellen['Erstes_Messdatum'] = pd.to_datetime(messstellen['Erstes_Messdatum'], format='%Y-%m-%d', errors='coerce')
    if 'Letztes_Messdatum' in messstellen.columns:
        messstellen['Letztes_Messdatum'] = pd.to_datetime(messstellen['Letztes_Messdatum'], format='%Y-%m-%d', errors='coerce')
    
    # GRIMM-STRELE konvertieren (falls aus MKZ_GWK.csv vorhanden)
    if 'GRIMM-STRELE' in messstellen.columns:
        messstellen['GRIMM-STRELE'] = pd.to_numeric(messstellen['GRIMM-STRELE'], errors='coerce')
    
    # Koordinatentransformation ETRS89 → WGS84
    if 'RW_ETRS89' in messstellen.columns and 'HW_ETRS89' in messstellen.columns:
        transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326")
        lat, lon = transformer.transform(messstellen.RW_ETRS89.values, messstellen.HW_ETRS89.values)
        messstellen['lat'] = lat
        messstellen['lon'] = lon
    else:
        messstellen['lat'] = None
        messstellen['lon'] = None
    
    return messstellen


@st.cache_data
def load_mkz_timeseries(mkz: str, cache_dir: str = "./cache") -> pd.DataFrame:
    """Lädt Zeitreihe für eine MKZ"""
    
    cacheorload(f"ExportSN_GWS-Rohdaten_{mkz}.csv", cache_dir)
    
    df = pd.read_csv(
        os.path.join(cache_dir, f'ExportSN_GWS-Rohdaten_{mkz}.csv'),
        sep=';',
        thousands='.',
        decimal=','
    )
    
    df['MESSZEITPUNKT'] = pd.to_datetime(df['MESSZEITPUNKT'], format='%Y-%m-%d', errors='coerce')
    df['WERT_UNTER_GELAENDE'] = df['WERT_UNTER_GELAENDE'].astype('Float64')
    df['MKZ'] = df['MKZ'].astype('string')
    
    return df


def compute_mkz_trend(mkz: str, trend_ab: datetime.date, trend_bis: datetime.date, cache_dir: str = "./cache") -> dict:
    """Berechnet Trend für eine MKZ nach Grimm-Strele"""
    
    try:
        df = load_mkz_timeseries(mkz, cache_dir)
        
        df = df.set_index('MESSZEITPUNKT')
        df = df.loc[:, "WERT_UNTER_GELAENDE"]
        df = df.resample('MS').mean()
        df = df.dropna()
        
        df = df.loc[(df.index >= pd.to_datetime(trend_ab)) & (df.index <= pd.to_datetime(trend_bis))]
        
        if df.shape[0] <= 1:
            return {"error": "Zu wenige Daten"}
        
        x = (df.index - df.index[0]).days.values.reshape(-1, 1) / 365.0
        y = df.values
        
        model = linear_model.LinearRegression().fit(x, y)
        
        slope = -model.coef_[0]  # negativ weil "Anstieg unter Gelände" = Absinken
        spanne = y.max() - y.min()
        grimm_strele = slope / spanne * 100.0 if spanne > 0.01 else np.nan
        
        return {
            "MKZ": mkz,
            "Anstieg [cm/a]": slope,
            "Spanne [cm]": spanne,
            "Grimm-Strele [%/a]": grimm_strele,
            "Anzahl Werte": len(y),
            "Trend": "fallend" if grimm_strele < -1 else ("steigend" if grimm_strele > 1 else "stabil")
        }
    
    except Exception as e:
        return {"error": str(e)}
# ============================================================================
# HELPER FUNCTIONS
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
    st.subheader("💧 Grundwasser-Messstellen im GWK")
    
    # Cache-Verzeichnis für Messstellen
    cache_dir = st.text_input(
        "Cache-Verzeichnis:",
        value="./cache",
        help="Lokaler Ordner für NIWIS-Downloads",
        key="cache_dir_ts"
    )
    
    try:
        messstellen = load_messstellen_data(cache_dir=cache_dir)
        messstellen_gwk = messstellen[messstellen['GWK25'] == selected_gwk]
        
        if len(messstellen_gwk) == 0:
            st.info(f"ℹ️ Keine Messstellen für {selected_gwk} verfügbar.")
        else:
            st.success(f"✅ {len(messstellen_gwk)} Messstellen gefunden für {selected_gwk}")
            
            # MKZ MULTISELECT
            available_mkz = sorted(messstellen_gwk['MKZ'].tolist())
            
            selected_mkz_list = st.multiselect(
                "Wähle Messstellen aus (Mehrfachauswahl):",
                options=available_mkz,
                default=available_mkz[:min(5, len(available_mkz))],
                help="Mehrfachauswahl mit Strg/Cmd + Klick",
                key="mkz_select_ts"
            )
            
            # Zeitreihen für ausgewählte Messstellen plotten
            for mkz in selected_mkz_list:
                fig_mkz = create_messstellen_plot(
                    mkz=mkz,
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