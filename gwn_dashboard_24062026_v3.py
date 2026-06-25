import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import glob
from typing import Optional, List, Dict, Tuple
from scipy.stats import linregress, kendalltau
import geopandas as gpd
import plotly.express as px
import os

# ============================================================================
# KONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="GWN Analyse Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS für besseres Styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# DATENVERARBEITUNGS-FUNKTIONEN
# ============================================================================

@st.cache_data
def load_gwk_mapping(mapping_csv: str) -> pd.DataFrame:
    """Lädt GWK Mapping"""
    m = pd.read_csv(mapping_csv, sep=",", on_bad_lines="skip")
    if "id" not in m.columns or "desc" not in m.columns:
        raise ValueError(f"Mapping CSV must contain 'id' and 'desc'. Columns: {m.columns.tolist()}")
    m = m[["id", "desc"]].copy()
    m["id"] = m["id"].astype(int)
    m["GWK_ID"] = m["desc"].astype(str).str.strip()
    return m[["id", "GWK_ID"]]


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
    """Lädt monatliche Daten"""
    df = pd.read_csv(csv_path)
    required = {"id", "year", "month", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path} missing columns: {sorted(missing)}")
    df = df[["id", "year", "month", "value"]].copy()
    df["id"] = df["id"].astype(int)
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
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
    rg1_path = find_parameter_csv(base_dir, "rg1")
    rg2_path = find_parameter_csv(base_dir, "rg2")
    
    if rg1_path is None or rg2_path is None:
        raise FileNotFoundError(f"rg1/rg2 CSV nicht gefunden in {base_dir}")
    
    df1_m = load_monthly_csv(rg1_path)
    df2_m = load_monthly_csv(rg2_path)
    
    df1_y = monthly_to_yearly_sum(df1_m, "rg1")
    df2_y = monthly_to_yearly_sum(df2_m, "rg2")
    
    df = pd.merge(df1_y, df2_y, on=["id", "year"], how="inner")
    df["gwn"] = df["rg1"] + df["rg2"]
    return df[["id", "year", "gwn"]]


@st.cache_data
def compute_parameter_yearly(base_dir: Path, parameter: str) -> pd.DataFrame:
    """Berechnet jährliche Summen für beliebigen Parameter"""
    csv_path = find_parameter_csv(base_dir, parameter)
    if csv_path is None:
        raise FileNotFoundError(f"{parameter} CSV nicht gefunden in {base_dir}")
    
    df_m = load_monthly_csv(csv_path)
    return monthly_to_yearly_sum(df_m, "value")

@st.cache_data
def load_gwk_geometries(shapefile_path: str) -> gpd.GeoDataFrame:
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
        vals = g[value_col].dropna().to_numpy()
        if vals.size == 0:
            continue
        rows.append({
            "GWK_ID": gwk,
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "std": float(np.std(vals, ddof=1)) if vals.size > 1 else np.nan,
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "n_years": int(vals.size),
        })
    return pd.DataFrame(rows)


def compute_trend_stats(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Berechnet Trendstatistiken für jedes GWK"""
    rows = []
    for gwk, g in df.groupby("GWK_ID"):
        g = g.sort_values("year")
        vals = g[value_col].to_numpy()
        yrs = g["year"].to_numpy()
        
        if len(vals) < 2:
            continue
        
        # Lineare Regression
        lr = linregress(yrs, vals)
        
        # Kendall Tau
        tau, p_tau = kendalltau(yrs, vals)
        
        row = {
            "GWK_ID": gwk,
            "n_years": int(len(vals)),
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "std": float(np.std(vals, ddof=1)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "lr_slope": float(lr.slope),
            "lr_intercept": float(lr.intercept),
            "lr_rvalue": float(lr.rvalue),
            "lr_pvalue": float(lr.pvalue),
            "lr_stderr": float(lr.stderr),
            "kendall_tau": float(tau),
            "kendall_p": float(p_tau),
        }
        rows.append(row)
    
    return pd.DataFrame(rows)




# ============================================================================
# DATEN LADEN (Hauptfunktion)
# ============================================================================

@st.cache_data
def load_all_data(data_base_dir: str, mapping_csv: str, target_gwk: List[str]) -> Dict:
    """Lädt und verarbeitet alle Daten"""
    
    data_base_path = Path(data_base_dir)
    obs_dir = data_base_path
    
    # Mapping laden
    mapping = load_gwk_mapping(mapping_csv)
    
    # GWN berechnen
    df_gwn_id = compute_gwn_yearly(obs_dir)
    df_gwn = attach_gwk_id(df_gwn_id, mapping)
    df_gwn = aggregate_to_gwk(df_gwn, "gwn")
    df_gwn = filter_target_gwk(df_gwn, target_gwk)
    df_gwn = df_gwn.rename(columns={"gwn": "gwn_mm_a"})
    
    # Niederschlag
    df_precip_id = compute_parameter_yearly(obs_dir, "P")
    df_precip = attach_gwk_id(df_precip_id, mapping)
    df_precip = aggregate_to_gwk(df_precip, "value")
    df_precip = filter_target_gwk(df_precip, target_gwk)
    
    # ETp
    df_etp_id = compute_parameter_yearly(obs_dir, "ETp")
    df_etp = attach_gwk_id(df_etp_id, mapping)
    df_etp = aggregate_to_gwk(df_etp, "value")
    df_etp = filter_target_gwk(df_etp, target_gwk)
    
    # Periodenvergleich GWN
    ref_stats = period_stats(df_gwn, "gwn_mm_a", 1961, 1990).rename(columns={
        "mean": "mean_ref",
        "median": "median_ref",
        "std": "std_ref",
        "min": "min_ref",
        "max": "max_ref",
        "n_years": "n_years_ref",
    })
    
    hist_stats = period_stats(df_gwn, "gwn_mm_a", 1991, 2020).rename(columns={
        "mean": "mean_hist",
        "median": "median_hist",
        "std": "std_hist",
        "min": "min_hist",
        "max": "max_hist",
        "n_years": "n_years_hist",
    })
    
    comparison = ref_stats.merge(hist_stats, on="GWK_ID", how="inner")
    comparison["delta_abs"] = comparison["mean_hist"] - comparison["mean_ref"]
    comparison["delta_rel_pct"] = np.where(
        comparison["mean_ref"].abs() > 1e-12,
        comparison["delta_abs"] / comparison["mean_ref"] * 100.0,
        np.nan,
    )
    
    # Trendanalyse
    trend_stats = compute_trend_stats(df_gwn, "gwn_mm_a")
    
    return {
        "gwn": df_gwn,
        "precip": df_precip,
        "etp": df_etp,
        "comparison": comparison,
        "trend": trend_stats,
    }


# ============================================================================
# PLOT-FUNKTIONEN
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
    
    precip_ref = precip_data[(precip_data['year'] >= ref_start) & (precip_data['year'] <= ref_end)]['value'].mean()
    precip_hist = precip_data[(precip_data['year'] >= hist_start) & (precip_data['year'] <= hist_end)]['value'].mean()
    
    # Subplots erstellen
    specs = [[{"secondary_y": True}]]
    fig = make_subplots(specs=specs)
    
    # GWN (primäre y-Achse)
    fig.add_trace(
        go.Scatter(
            x=gwn_data['year'],
            y=gwn_data['gwn_mm_a'],
            name='GWN',
            line=dict(color='steelblue', width=3),
            mode='lines+markers',
            marker=dict(size=6),
            hovertemplate='<b>Jahr:</b> %{x}<br><b>GWN:</b> %{y:.1f} mm/a<extra></extra>'
        ),
        secondary_y=False
    )
    
    # GWN Mittelwerte
    fig.add_trace(
        go.Scatter(
            x=[ref_start, ref_end],
            y=[gwn_ref, gwn_ref],
            name=f'GWN Ø 1961-1990 ({gwn_ref:.1f} mm/a)',
            line=dict(color='darkgreen', width=2, dash='dash'),
            mode='lines',
            hoverinfo='skip'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=[hist_start, hist_end],
            y=[gwn_hist, gwn_hist],
            name=f'GWN Ø 1991-2020 ({gwn_hist:.1f} mm/a)',
            line=dict(color='darkorange', width=2, dash='dash'),
            mode='lines',
            hoverinfo='skip'
        ),
        secondary_y=False
    )
    
    # Niederschlag (sekundäre y-Achse)
    if show_precip and not precip_data.empty:
        fig.add_trace(
            go.Scatter(
                x=precip_data['year'],
                y=precip_data['value'],
                name='Niederschlag',
                line=dict(color='darkblue', width=2, dash='dot'),
                mode='lines+markers',
                marker=dict(size=4, symbol='square'),
                opacity=0.7,
                hovertemplate='<b>Jahr:</b> %{x}<br><b>P:</b> %{y:.1f} mm/a<extra></extra>'
            ),
            secondary_y=True
        )
        
        fig.add_trace(
            go.Scatter(
                x=[ref_start, ref_end],
                y=[precip_ref, precip_ref],
                name=f'P Ø 1961-1990 ({precip_ref:.1f} mm/a)',
                line=dict(color='navy', width=1.5, dash='dot'),
                mode='lines',
                opacity=0.5,
                hoverinfo='skip'
            ),
            secondary_y=True
        )
    
    # ETp (sekundäre y-Achse)
    if show_etp and not etp_data.empty:
        etp_ref = etp_data[(etp_data['year'] >= ref_start) & (etp_data['year'] <= ref_end)]['value'].mean()
        etp_hist = etp_data[(etp_data['year'] >= hist_start) & (etp_data['year'] <= hist_end)]['value'].mean()
        
        fig.add_trace(
            go.Scatter(
                x=etp_data['year'],
                y=etp_data['value'],
                name='ETp',
                line=dict(color='orangered', width=2, dash='dot'),
                mode='lines+markers',
                marker=dict(size=4, symbol='diamond'),
                opacity=0.6,
                hovertemplate='<b>Jahr:</b> %{x}<br><b>ETp:</b> %{y:.1f} mm/a<extra></extra>'
            ),
            secondary_y=True
        )
    
    # Perioden-Hintergrund
    fig.add_vrect(
        x0=ref_start, x1=ref_end,
        fillcolor="green", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="1961-1990", annotation_position="top left"
    )
    
    fig.add_vrect(
        x0=hist_start, x1=hist_end,
        fillcolor="orange", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="1991-2020", annotation_position="top left"
    )
    
    # Layout
    fig.update_xaxes(title_text="Jahr", gridcolor='lightgray')
    fig.update_yaxes(title_text="<b>GWN</b> [mm/a]", secondary_y=False, gridcolor='lightgray')
    
    if show_precip or show_etp:
        y_label = []
        if show_precip:
            y_label.append("Niederschlag")
        if show_etp:
            y_label.append("ETp")
        fig.update_yaxes(title_text=f"<b>{' / '.join(y_label)}</b> [mm/a]", secondary_y=True)
    
    fig.update_layout(
        title=f"<b>Grundwasserneubildung – {gwk}</b>",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=600,
        template='plotly_white'
    )
    
    return fig


def create_correlation_plot(df_gwn, df_precip, gwk):
    """Erstellt interaktiven Korrelationsplot"""
    
    gwn_data = df_gwn[df_gwn['GWK_ID'] == gwk][['year', 'gwn_mm_a']]
    precip_data = df_precip[df_precip['GWK_ID'] == gwk][['year', 'value']]
    
    merged = gwn_data.merge(precip_data, on='year', suffixes=('_gwn', '_precip'))
    
    if merged.empty:
        return None
    
    # Perioden zuordnen
    ref_start, ref_end = 1961, 1990
    hist_start, hist_end = 1991, 2020
    
    merged['period'] = 'Andere'
    merged.loc[(merged['year'] >= ref_start) & (merged['year'] <= ref_end), 'period'] = '1961-1990'
    merged.loc[(merged['year'] >= hist_start) & (merged['year'] <= hist_end), 'period'] = '1991-2020'
    
    # Plot erstellen
    fig = go.Figure()
    
    colors = {'1961-1990': 'green', '1991-2020': 'orange', 'Andere': 'gray'}
    
    for period, color in colors.items():
        subset = merged[merged['period'] == period]
        if not subset.empty:
            fig.add_trace(go.Scatter(
                x=subset['value'],
                y=subset['gwn_mm_a'],
                mode='markers',
                name=period,
                marker=dict(size=10, color=color, opacity=0.7, line=dict(width=1, color='black')),
                text=subset['year'],
                hovertemplate='<b>Jahr:</b> %{text}<br><b>P:</b> %{x:.1f} mm/a<br><b>GWN:</b> %{y:.1f} mm/a<extra></extra>'
            ))
    
    # Regression
    slope, intercept, r_value, p_value, _ = linregress(merged['value'], merged['gwn_mm_a'])
    
    x_fit = np.linspace(merged['value'].min(), merged['value'].max(), 100)
    y_fit = slope * x_fit + intercept
    
    fig.add_trace(go.Scatter(
        x=x_fit,
        y=y_fit,
        mode='lines',
        name=f'Regression (R²={r_value**2:.3f}, p={p_value:.4f})',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title=f"<b>Korrelation: GWN vs. Niederschlag – {gwk}</b>",
        xaxis_title="Niederschlag [mm/a]",
        yaxis_title="GWN [mm/a]",
        height=500,
        template='plotly_white',
        hovermode='closest'
    )
    
    return fig


def create_comparison_barplot(comparison_df):
    """Erstellt interaktiven Vergleichsplot"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=comparison_df['GWK_ID'],
        y=comparison_df['mean_ref'],
        name='1961-1990',
        marker_color='green',
        opacity=0.7,
        hovertemplate='<b>%{x}</b><br>1961-1990: %{y:.1f} mm/a<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=comparison_df['GWK_ID'],
        y=comparison_df['mean_hist'],
        name='1991-2020',
        marker_color='orange',
        opacity=0.7,
        hovertemplate='<b>%{x}</b><br>1991-2020: %{y:.1f} mm/a<extra></extra>'
    ))
    
    fig.update_layout(
        title="<b>Vergleich GWN: 1961-1990 vs. 1991-2020</b>",
        xaxis_title="GWK",
        yaxis_title="GWN [mm/a]",
        barmode='group',
        height=400,
        template='plotly_white'
    )
    
    return fig

def create_gwk_map(gdf, comparison_df, selected_gwk=None):
    """Erstellt interaktive Karte mit GWK und Änderungen"""
    
    if gdf is None or gdf.empty:
        return None
    
    # Merge mit Vergleichsdaten
    gdf_merged = gdf.merge(comparison_df, on='GWK_ID', how='left')
    
    # Zentrum der Karte berechnen
    centroid = gdf_merged.geometry.unary_union.centroid
    
    # Farbe basierend auf Änderung
    fig = px.choropleth_mapbox(
        gdf_merged,
        geojson=gdf_merged.geometry.__geo_interface__,
        locations=gdf_merged.index,
        color='delta_abs',
        hover_name='GWK_ID',
        hover_data={
            'mean_ref': ':.1f',
            'mean_hist': ':.1f',
            'delta_abs': ':+.1f',
            'delta_rel_pct': ':+.1f'
        },
        color_continuous_scale='RdYlGn',
        range_color=[-50, 50],
        mapbox_style='open-street-map',
        zoom=7,
        center={'lat': centroid.y, 'lon': centroid.x},
        opacity=0.7,
        labels={
            'delta_abs': 'Änderung [mm/a]',
            'mean_ref': 'GWN 1961-1990 [mm/a]',
            'mean_hist': 'GWN 1991-2020 [mm/a]',
            'delta_rel_pct': 'Änderung [%]'
        }
    )
    
    # Ausgewähltes GWK hervorheben
    if selected_gwk:
        selected_geom = gdf_merged[gdf_merged['GWK_ID'] == selected_gwk]
        if not selected_geom.empty:
            fig.add_trace(
                px.choropleth_mapbox(
                    selected_geom,
                    geojson=selected_geom.geometry.__geo_interface__,
                    locations=selected_geom.index,
                    color_discrete_sequence=['yellow'],
                    mapbox_style='open-street-map',
                    opacity=0
                ).data[0]
            )
    
    fig.update_layout(
        title='<b>GWK-Karte: Änderung der Grundwasserneubildung</b>',
        height=600,
        margin={"r":0,"t":40,"l":0,"b":0}
    )
    
    return fig


def create_simple_gwk_map(gdf, comparison_df, selected_gwk=None):
    """Erstellt einfachere Karte mit Plotly (funktioniert besser bei vielen GWK)"""
    
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
    
    import json
    geojson = json.loads(gdf_merged.to_json())
    
    # Zentrum berechnen
    center_lat = gdf_merged['lat'].mean()
    center_lon = gdf_merged['lon'].mean()
    
    # Farbskala
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Für jedes GWK eine Trace
    for idx, row in gdf_merged.iterrows():
        # Farbe basierend auf Änderung
        if pd.notna(row['delta_abs']):
            if row['delta_abs'] < -20:
                color = 'darkred'
            elif row['delta_abs'] < -10:
                color = 'red'
            elif row['delta_abs'] < 0:
                color = 'orange'
            elif row['delta_abs'] < 10:
                color = 'lightgreen'
            elif row['delta_abs'] < 20:
                color = 'green'
            else:
                color = 'darkgreen'
        else:
            color = 'gray'
        
        # Highlight für ausgewähltes GWK
        if row['GWK_ID'] == selected_gwk:
            line_width = 3
            line_color = 'yellow'
        else:
            line_width = 1
            line_color = 'white'
        
        # GeoJSON Feature für dieses GWK
        coords = []
        if row.geometry.geom_type == 'Polygon':
            coords = [list(row.geometry.exterior.coords)]
        elif row.geometry.geom_type == 'MultiPolygon':
            coords = [list(poly.exterior.coords) for poly in row.geometry.geoms]
        
        for coord_list in coords:
            lons = [c[0] for c in coord_list]
            lats = [c[1] for c in coord_list]
            
            hover_text = f"<b>{row['GWK_ID']}</b><br>"
            if pd.notna(row['delta_abs']):
                hover_text += f"Änderung: {row['delta_abs']:+.1f} mm/a<br>"
                hover_text += f"1961-1990: {row['mean_ref']:.1f} mm/a<br>"
                hover_text += f"1991-2020: {row['mean_hist']:.1f} mm/a"
            
            fig.add_trace(go.Scattermapbox(
                lon=lons,
                lat=lats,
                mode='lines',
                fill='toself',
                fillcolor=color,
                line=dict(width=line_width, color=line_color),
                opacity=0.6,
                name=row['GWK_ID'],
                showlegend=False,
                hovertext=hover_text,
                hoverinfo='text'
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
# MESSSTELLEN-FUNKTIONEN (von Kollege integriert)
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
        mess_gwk = pd.read_csv(mkz_gwk_path, sep=';', quotechar='"', dtype={'MKZ': str})
        mess_gwk = mess_gwk.fillna("na")
        # Sicherstellen, dass MKZ-Spalte in beiden DataFrames als String vorliegt
        messstellen['MKZ'] = messstellen['MKZ'].astype(str)
        mess_gwk['MKZ'] = mess_gwk['MKZ'].astype(str)
        messstellen = messstellen.merge(mess_gwk, on="MKZ", how="outer")
    else:
        st.warning(f"⚠️ MKZ_GWK.csv nicht gefunden unter {mkz_gwk_path}")
        messstellen['GWK'] = "unbekannt"
        messstellen['GWK25'] = "unbekannt"
    
    # Datums-Spalten konvertieren (falls vorhanden)
    if 'Erstes_Messdatum' in messstellen.columns:
        messstellen['Erstes_Messdatum'] = pd.to_datetime(messstellen['Erstes_Messdatum'], format='%Y-%m-%d', errors='coerce')
    if 'Letztes_Messdatum' in messstellen.columns:
        messstellen['Letztes_Messdatum'] = pd.to_datetime(messstellen['Letztes_Messdatum'], format='%Y-%m-%d', errors='coerce')
    if 'GRIMM-STRELE' in messstellen.columns:
        messstellen['GRIMM-STRELE'] = pd.to_numeric(messstellen['GRIMM-STRELE'], errors='coerce')
    
    # Koordinatentransformation ETRS89 → WGS84 (falls Koordinaten vorhanden)
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
# HAUPTAPP
# ============================================================================

def main():
    
    # Header
    st.title("💧 Grundwasserneubildung – Interaktive Analyse")
    st.markdown("---")
    
    # Sidebar Konfiguration
    st.sidebar.header("⚙️ Konfiguration")
    
    # Pfade eingeben
    with st.sidebar.expander("📁 Datenpfade", expanded=False):
        BASE_PATH = Path(__file__).parent / "data" / "kalib_beo_ERA5"
        data_base_dir = st.text_input(
            "Basis-Datenordner:",
            value=str(BASE_PATH),
            help="Wird automatisch erkannt"
        )
        
        default_mapping = str(Path(data_base_dir) / "GWK_2025" / "GWK_2025.csv")
        mapping_csv = st.text_input(
            "GWK Mapping CSV:",
            value=default_mapping
        )
    
    # Zuerst Mapping laden, um verfügbare GWK zu sehen
    try:
        with st.spinner("🔄 Lade GWK-Mapping..."):
            mapping = load_gwk_mapping(mapping_csv)
            all_available_gwk = sorted(mapping['GWK_ID'].dropna().unique().tolist())
        
        st.sidebar.success(f"✅ {len(all_available_gwk)} GWK gefunden")
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden des GWK-Mappings:\n\n{str(e)}")
        st.stop()
    
    # Shapefile laden
    default_shapefile = str(Path(data_base_dir) / "GWK_2025" / "GWK_2025.shp")

    shapefile_path = st.sidebar.text_input(
        "Shapefile Pfad:",
        value=default_shapefile
    )
    
    try:
        with st.spinner("🗺️ Lade Geometrien..."):
            gdf = load_gwk_geometries(shapefile_path)
        if gdf is not None:
            st.sidebar.success(f"✅ {len(gdf)} Geometrien geladen")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Shapefile konnte nicht geladen werden: {e}")
        gdf = None

    # GWK Auswahl
    st.sidebar.subheader("🎯 GWK Auswahl")
    
    # Auswahlmodus
    selection_mode = st.sidebar.radio(
        "Auswahlmodus:",
        ["Eigene Auswahl", "Alle GWK"]
    )
    
    # if selection_mode == "Vordefinierte Auswahl":
    #     # Standard 4 GWK
    #     default_gwk = [
    #         "DESN_EL-2-1",
    #         "DESN_NE-3",
    #         "DESN_SAL-GW-060",
    #         "DESN_SE-1-1-1",
    #     ]
        
    #     # Nur die, die auch existieren
    #     target_gwk = [gwk for gwk in default_gwk if gwk in all_available_gwk]
        
    #     st.sidebar.info(f"📋 Verwende {len(target_gwk)} Standard-GWK")
    #     st.sidebar.write(target_gwk)
        
    if selection_mode == "Eigene Auswahl":
        # Multiselect für individuelle Auswahl
        
        # Standard-GWK auswählen, falls vorhanden
        default_selection = [gwk for gwk in ["DESN_EL-2-1"] if gwk in all_available_gwk]
        
        # Falls keine Standard-GWK vorhanden, nimm erste 2
        if not default_selection:
            default_selection = all_available_gwk[:min(2, len(all_available_gwk))]
        
        target_gwk = st.sidebar.multiselect(
            "Wähle GWK aus:",
            options=all_available_gwk,
            default=default_selection,
            help="Mehrfachauswahl möglich (Strg/Cmd + Klick)"
        )
        
        if not target_gwk:
            st.sidebar.warning("⚠️ Bitte mindestens ein GWK auswählen!")
            st.stop()
            
    else:  # "Alle GWK"
        target_gwk = all_available_gwk
        st.sidebar.info(f"📋 Verwende alle {len(target_gwk)} verfügbaren GWK")
        
        # Option: Anzahl begrenzen für Performance
        if len(target_gwk) > 20:
            st.sidebar.warning(f"⚠️ {len(target_gwk)} GWK können die Verarbeitung verlangsamen")
            
            limit = st.sidebar.checkbox("Auf erste 20 GWK begrenzen", value=False)
            if limit:
                target_gwk = target_gwk[:20]
                st.sidebar.info(f"✂️ Begrenzt auf {len(target_gwk)} GWK")
    
    # Zeige ausgewählte GWK
    with st.sidebar.expander(f"📋 Ausgewählte GWK ({len(target_gwk)})", expanded=False):
        st.write(target_gwk)
    
    # Daten laden
    try:
        with st.spinner(f"🔄 Lade und verarbeite Daten für {len(target_gwk)} GWK..."):
            data = load_all_data(data_base_dir, mapping_csv, target_gwk)
        st.sidebar.success(f"✅ Daten geladen für {len(target_gwk)} GWK")
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Daten:\n\n{str(e)}")
        st.info("💡 Tipp: Prüfe die Pfade und stelle sicher, dass die Datenordner existieren.")
        with st.expander("🐛 Detaillierte Fehlermeldung"):
            st.code(str(e))
        st.stop()
    
    # GWK Auswahl für Detailansicht
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Visualisierung")
    
    available_gwk = sorted(data['gwn']['GWK_ID'].unique())
    
    # Suchfeld für GWK
    search_term = st.sidebar.text_input(
        "🔍 GWK suchen:",
        placeholder="z.B. DESN_EL",
        help="Filtert die Dropdown-Liste"
    )
    
    if search_term:
        filtered_gwk = [gwk for gwk in available_gwk if search_term.upper() in gwk.upper()]
        if not filtered_gwk:
            st.sidebar.warning(f"❌ Keine GWK gefunden mit '{search_term}'")
            filtered_gwk = available_gwk
    else:
        filtered_gwk = available_gwk
    
    selected_gwk = st.sidebar.selectbox(
        "GWK für Detailansicht:",
        filtered_gwk,
        index=0
    )
        
    # ========================================================================
    # ÜBERSICHT ÜBER ALLE GWK
    # ========================================================================
    
    st.subheader(f"📊 Übersicht: {len(target_gwk)} ausgewählte GWK")
    
    # Zusammenfassende Statistik
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_gwn_ref = data['comparison']['mean_ref'].mean()
        st.metric("⌀ GWN 1961-1990", f"{avg_gwn_ref:.1f} mm/a")
    
    with col2:
        avg_gwn_hist = data['comparison']['mean_hist'].mean()
        st.metric("⌀ GWN 1991-2020", f"{avg_gwn_hist:.1f} mm/a")
    
    with col3:
        avg_change = data['comparison']['delta_abs'].mean()
        st.metric("⌀ Änderung", f"{avg_change:+.1f} mm/a")
    
    with col4:
        n_decreasing = (data['comparison']['delta_abs'] < 0).sum()
        st.metric("GWK mit Rückgang", f"{n_decreasing} / {len(target_gwk)}")
    
    st.markdown("---")
    
    # ========================================================================
    # TAB-NAVIGATION
    # ========================================================================
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Zeitreihen", 
        "🔄 Korrelation", 
        "📊 Vergleich", 
        "📋 Statistiken",
        "🗺️ Übersichtskarte"
    ])
    
    # ====== TAB 1: ZEITREIHEN ======
    with tab1:
        st.header(f"Zeitreihenanalyse: {selected_gwk}")
        
        # Metriken anzeigen
        gwk_comparison = data['comparison'][data['comparison']['GWK_ID'] == selected_gwk]
        
        if not gwk_comparison.empty:
            gwk_comparison = gwk_comparison.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "GWN 1961-1990",
                    f"{gwk_comparison['mean_ref']:.1f} mm/a"
                )
            
            with col2:
                st.metric(
                    "GWN 1991-2020",
                    f"{gwk_comparison['mean_hist']:.1f} mm/a",
                    delta=f"{gwk_comparison['delta_abs']:.1f} mm/a"
                )
            
            with col3:
                st.metric(
                    "Änderung",
                    f"{gwk_comparison['delta_rel_pct']:.1f} %"
                )
            
            with col4:
                gwk_trend = data['trend'][data['trend']['GWK_ID'] == selected_gwk]
                if not gwk_trend.empty:
                    gwk_trend = gwk_trend.iloc[0]
                    trend_sig = "✅" if gwk_trend['lr_pvalue'] < 0.05 else "❌"
                    st.metric(
                        "Trend signifikant",
                        trend_sig,
                        delta=f"p={gwk_trend['lr_pvalue']:.3f}"
                    )
        
        st.markdown("---")
        
        # ========================================================================
        # GWN PLOT MIT OPTIONEN
        # ========================================================================
        
        st.subheader("📈 Grundwasserneubildung (Flächenmittel)")
        
        # Optionen direkt beim Plot
        col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 3])
        
        with col_opt1:
            show_precip_gwn = st.checkbox("Niederschlag", value=True, key="gwn_precip")
        
        with col_opt2:
            show_etp_gwn = st.checkbox("ETp", value=False, key="gwn_etp")
        
        fig_gwn = create_interactive_timeseries(
            data['gwn'], 
            data['precip'], 
            data['etp'], 
            selected_gwk,
            show_precip=show_precip_gwn,
            show_etp=show_etp_gwn
        )
        st.plotly_chart(fig_gwn, use_container_width=True)
        
        # ========================================================================
        # MESSSTELLEN-GANGLINIEN
        # ========================================================================
        
        st.markdown("---")
        st.subheader("💧 Grundwasser-Messstellen im GWK")
        
        try:
            # Messstellen für ausgewähltes GWK laden
            messstellen = load_messstellen_data()
            messstellen_gwk = messstellen[messstellen['GWK25'] == selected_gwk]
            
            if len(messstellen_gwk) == 0:
                st.info(f"ℹ️ Keine Messstellen für {selected_gwk} verfügbar.")
            else:
                st.success(f"✅ {len(messstellen_gwk)} Messstellen gefunden")
                
                # Konfiguration
                col_config1, col_config2 = st.columns([2, 1])
                
                with col_config1:
                    # MKZ Auswahl
                    available_mkz = sorted(messstellen_gwk['MKZ'].tolist())
                    
                    if len(available_mkz) > 10:
                        st.warning(f"⚠️ {len(available_mkz)} Messstellen verfügbar - empfohlen: max. 10 für gute Lesbarkeit")
                    
                    selected_mkz = st.multiselect(
                        "Wähle Messstellen aus:",
                        options=available_mkz,
                        default=available_mkz[:min(5, len(available_mkz))],
                        help="Mehrfachauswahl möglich"
                    )
                
                with col_config2:
                    # Darstellungsoptionen
                    plot_type = st.radio(
                        "Darstellung:",
                        ["WERT_UNTER_GELAENDE", "WERT_IM_HOEHENSYSTEM"],
                        help="Unter Gelände: je tiefer, desto niedriger der Wasserstand"
                    )
                    
                    show_trend_lines = st.checkbox("Trendlinien", value=False, key="mkz_trend")
                
                if selected_mkz:
                    
                    with st.spinner(f"Lade Ganglinien für {len(selected_mkz)} Messstellen..."):
                        
                        alle_daten = []
                        trend_daten = []
                        
                        for mkz in selected_mkz:
                            try:
                                # Zeitreihe laden
                                df_ts = load_mkz_timeseries(mkz)
                                
                                if df_ts.empty:
                                    continue
                                
                                # Messwerte hinzufügen
                                for _, row in df_ts.iterrows():
                                    alle_daten.append({
                                        'MKZ': mkz,
                                        'MESSZEITPUNKT': row['MESSZEITPUNKT'],
                                        'Wert': row[plot_type] if plot_type in df_ts.columns else row['WERT_UNTER_GELAENDE'],
                                        'Typ': 'Messung'
                                    })
                                
                                # Trend berechnen falls gewünscht
                                if show_trend_lines:
                                    df_monthly = df_ts.set_index('MESSZEITPUNKT')[plot_type if plot_type in df_ts.columns else 'WERT_UNTER_GELAENDE']
                                    df_monthly = df_monthly.resample('MS').mean().dropna()
                                    
                                    if len(df_monthly) > 1:
                                        x = (df_monthly.index - df_monthly.index[0]).days.values.reshape(-1, 1) / 365.0
                                        y = df_monthly.values
                                        
                                        model = linear_model.LinearRegression().fit(x, y)
                                        
                                        y_start = model.predict([[0]])[0]
                                        y_end = model.predict([[x.max()]])[0]
                                        
                                        trend_daten.append({
                                            'MKZ': mkz,
                                            'MESSZEITPUNKT': df_monthly.index[0],
                                            'Wert': y_start,
                                            'Typ': 'Trend'
                                        })
                                        
                                        trend_daten.append({
                                            'MKZ': mkz,
                                            'MESSZEITPUNKT': df_monthly.index[-1],
                                            'Wert': y_end,
                                            'Typ': 'Trend'
                                        })
                            
                            except Exception as e:
                                st.warning(f"⚠️ Fehler bei {mkz}: {e}")
                        
                        if alle_daten:
                            # DataFrame erstellen
                            df_plot = pd.DataFrame(alle_daten + trend_daten)
                            
                            # Ganglinien-Plot (OHNE P/ETp)
                            fig_mkz = px.line(
                                df_plot,
                                x='MESSZEITPUNKT',
                                y='Wert',
                                color='MKZ',
                                line_dash='Typ',
                                title=f"<b>Grundwasserganglinien - {selected_gwk}</b>",
                                labels={
                                    'MESSZEITPUNKT': 'Datum',
                                    'Wert': f'{plot_type.replace("_", " ")} [cm]',
                                    'MKZ': 'Messstelle'
                                },
                                height=500
                            )
                            
                            # Y-Achse umkehren bei "unter Gelände"
                            if plot_type == "WERT_UNTER_GELAENDE":
                                fig_mkz.update_yaxes(autorange="reversed")
                            
                            fig_mkz.update_layout(
                                template='plotly_white',
                                hovermode='x unified',
                                legend=dict(
                                    orientation="v",
                                    yanchor="top",
                                    y=1,
                                    xanchor="left",
                                    x=1.02
                                )
                            )
                            
                            st.plotly_chart(fig_mkz, use_container_width=True)
                            
                            # ========================================================================
                            # OPTIONEN FÜR KLIMADATEN (UNTERHALB DES PLOTS)
                            # ========================================================================
                            
                            st.markdown("**Klimadaten hinzufügen:**")
                            col_klima1, col_klima2, col_klima3 = st.columns([1, 1, 4])
                            
                            with col_klima1:
                                show_precip_mkz = st.checkbox("Niederschlag", value=False, key="mkz_precip")
                            
                            with col_klima2:
                                show_etp_mkz = st.checkbox("ETp", value=False, key="mkz_etp")
                            
                            # ========================================================================
                            # SEPARATES BALKENDIAGRAMM FÜR P/ETp
                            # ========================================================================
                            
                            if show_precip_mkz or show_etp_mkz:
                                
                                # Daten vorbereiten
                                precip_data = data['precip'][data['precip']['GWK_ID'] == selected_gwk].sort_values('year').copy()
                                etp_data = data['etp'][data['etp']['GWK_ID'] == selected_gwk].sort_values('year').copy()
                                
                                # Plot erstellen
                                fig_klima = go.Figure()
                                
                                if show_precip_mkz and not precip_data.empty:
                                    fig_klima.add_trace(go.Bar(
                                        x=precip_data['year'],
                                        y=precip_data['value'],
                                        name='Niederschlag',
                                        marker_color='darkblue',
                                        opacity=0.7,
                                        hovertemplate='<b>Niederschlag</b><br>Jahr: %{x}<br>P: %{y:.1f} mm/a<extra></extra>'
                                    ))
                                
                                if show_etp_mkz and not etp_data.empty:
                                    fig_klima.add_trace(go.Bar(
                                        x=etp_data['year'],
                                        y=etp_data['value'],
                                        name='ETp',
                                        marker_color='orangered',
                                        opacity=0.7,
                                        hovertemplate='<b>ETp</b><br>Jahr: %{x}<br>ETp: %{y:.1f} mm/a<extra></extra>'
                                    ))
                                
                                fig_klima.update_layout(
                                    title=f"<b>Klimadaten - {selected_gwk}</b>",
                                    xaxis_title="Jahr",
                                    yaxis_title="[mm/a]",
                                    barmode='group',
                                    height=400,
                                    template='plotly_white',
                                    hovermode='x unified',
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=1.02,
                                        xanchor="right",
                                        x=1
                                    )
                                )
                                
                                st.plotly_chart(fig_klima, use_container_width=True)
                            
                            # Statistik-Tabelle
                            with st.expander("📊 Messstellen-Statistik", expanded=False):
                                
                                stats_rows = []
                                
                                for mkz in selected_mkz:
                                    mkz_data = messstellen_gwk[messstellen_gwk['MKZ'] == mkz]
                                    
                                    if not mkz_data.empty:
                                        mkz_data = mkz_data.iloc[0]
                                        stats_rows.append({
                                            'MKZ': mkz,
                                            'Erstes Datum': mkz_data['Erstes_Messdatum'].strftime('%Y-%m-%d') if pd.notna(mkz_data['Erstes_Messdatum']) else 'N/A',
                                            'Letztes Datum': mkz_data['Letztes_Messdatum'].strftime('%Y-%m-%d') if pd.notna(mkz_data['Letztes_Messdatum']) else 'N/A',
                                            'Grimm-Strele [%/a]': f"{mkz_data['GRIMM-STRELE']:.2f}" if pd.notna(mkz_data['GRIMM-STRELE']) else 'N/A',
                                            'Trend': 'Fallend' if pd.notna(mkz_data['GRIMM-STRELE']) and mkz_data['GRIMM-STRELE'] <= -1 else (
                                                'Steigend' if pd.notna(mkz_data['GRIMM-STRELE']) and mkz_data['GRIMM-STRELE'] > 1 else 'Stabil'
                                            )
                                        })
                                
                                if stats_rows:
                                    df_stats = pd.DataFrame(stats_rows)
                                    st.dataframe(df_stats, use_container_width=True)
                        
                        else:
                            st.warning("⚠️ Keine Daten für ausgewählte Messstellen verfügbar")
                
                else:
                    st.info("👆 Bitte Messstellen auswählen")
        
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Messstellen: {e}")
            st.info("💡 Messstellen-Feature benötigt MKZ_GWK.csv und Zugriff auf NIWIS")
        
        # ========================================================================
        # DETAILSTATISTIKEN (wie bisher)
        # ========================================================================
        
        st.markdown("---")
        
        with st.expander("📋 Detaillierte GWN-Statistiken"):
            st.subheader("Trendanalyse GWN")
            trend_data = data['trend'][data['trend']['GWK_ID'] == selected_gwk]
            if not trend_data.empty:
                trend_cols = ['GWK_ID', 'mean', 'std', 'lr_slope', 'lr_rvalue', 
                             'lr_pvalue', 'kendall_tau', 'kendall_p']
                st.dataframe(
                    trend_data[trend_cols],
                    use_container_width=True
                )
    
    # ====== TAB 2: KORRELATION ======
    with tab2:
        st.header(f"Korrelationsanalyse: {selected_gwk}")
        
        fig = create_correlation_plot(data['gwn'], data['precip'], selected_gwk)
        
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            
            # Erklärung
            st.info("""
            **Interpretation:**
            - Jeder Punkt repräsentiert ein Jahr
            - Grün = 1961-1990, Orange = 1991-2020
            - Je steiler die Regressionsgerade, desto stärker der Zusammenhang
            - R² nahe 1 = starker linearer Zusammenhang
            """)
        else:
            st.warning("⚠️ Keine Daten für Korrelationsanalyse verfügbar.")
    
    # ====== TAB 3: VERGLEICH ======
    with tab3:
        st.header("Vergleich aller ausgewählten GWK")
        
        # Barplot
        fig = create_comparison_barplot(data['comparison'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Sortieroptionen
        st.subheader("📋 Detaillierte Vergleichstabelle")
        
        sort_by = st.selectbox(
            "Sortieren nach:",
            ["GWK_ID", "delta_abs", "delta_rel_pct", "mean_ref", "mean_hist"],
            index=0
        )
        
        ascending = st.checkbox("Aufsteigend sortieren", value=True)
        
        display_cols = ['GWK_ID', 'mean_ref', 'mean_hist', 'delta_abs', 'delta_rel_pct', 
                       'std_ref', 'std_hist']
        
        sorted_comparison = data['comparison'].sort_values(by=sort_by, ascending=ascending)
        
        styled_df = sorted_comparison[display_cols].style.format({
            'mean_ref': '{:.1f}',
            'mean_hist': '{:.1f}',
            'delta_abs': '{:+.1f}',
            'delta_rel_pct': '{:+.1f}%',
            'std_ref': '{:.1f}',
            'std_hist': '{:.1f}'
        }).background_gradient(subset=['delta_rel_pct'], cmap='RdYlGn_r')
        
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    # ====== TAB 4: STATISTIKEN ======
    with tab4:
        st.header("Vollständige Statistiken")
        
        # Filter-Option
        show_significant_only = st.checkbox(
            "Nur signifikante Trends anzeigen (p < 0.05)", 
            value=False
        )
        
        st.subheader("📊 Trendanalyse (1961-2020)")
        
        trend_display = data['trend'].copy()
        if show_significant_only:
            trend_display = trend_display[trend_display['lr_pvalue'] < 0.05]
            st.info(f"Zeige {len(trend_display)} von {len(data['trend'])} GWK mit signifikantem Trend")
        
        st.dataframe(trend_display, use_container_width=True, height=400)
        
        st.markdown("---")
        
        st.subheader("📊 Periodenvergleich")
        st.dataframe(data['comparison'], use_container_width=True, height=400)
    
        # ====== TAB 5: ÜBERSICHTSKARTE ======
    with tab5:
        st.header("🗺️ Räumliche Übersicht")
        
        if gdf is not None and not gdf.empty:
            
            # Kartenoptionen
            col1, col2 = st.columns([3, 1])
            
            with col2:
                st.subheader("Karteneinstellungen")
                
                map_type = st.radio(
                    "Kartentyp:",
                    ["Choropleth (Farbe nach Änderung)", "Einfache Polygone"],
                    help="Choropleth kann bei vielen GWK langsam sein"
                )
                
                show_labels = st.checkbox("GWK-Namen anzeigen", value=False)
                
                st.markdown("---")
                
                # NEUE MESSSTELLEN-FUNKTIONALITÄT
                st.subheader("💧 Messstellen")
                show_messstellen = st.checkbox("Messstellen anzeigen", value=False)
                
                if show_messstellen:
                    # Messstellen laden
                    try:
                        with st.spinner("Lade Messstellen..."):
                            messstellen = load_messstellen_data()
                        
                        st.success(f"✅ {len(messstellen)} Messstellen")
                        
                        # Filter nach GWK
                        filter_by_gwk = st.checkbox(
                            "Nur Messstellen in ausgewählten GWK",
                            value=True,
                            help="Filtert auf GWK aus der aktuellen Auswahl"
                        )
                        
                        if filter_by_gwk:
                            messstellen_filtered = messstellen[messstellen['GWK25'].isin(target_gwk)]
                            st.info(f"📊 {len(messstellen_filtered)} Messstellen in ausgewählten GWK")
                        else:
                            messstellen_filtered = messstellen
                        
                        # Filter nach Trend
                        trend_filter = st.radio(
                            "Trend-Filter:",
                            ["Alle", "Nur fallende (Grimm-Strele < -1)", "Nur stabile/steigende"],
                            index=0
                        )
                        
                        if trend_filter == "Nur fallende (Grimm-Strele < -1)":
                            messstellen_filtered = messstellen_filtered[messstellen_filtered['GRIMM-STRELE'] <= -1]
                        elif trend_filter == "Nur stabile/steigende":
                            messstellen_filtered = messstellen_filtered[messstellen_filtered['GRIMM-STRELE'] > -1]
                        
                        st.caption(f"🔍 {len(messstellen_filtered)} nach Filterung")
                        
                    except Exception as e:
                        st.error(f"❌ Fehler beim Laden: {e}")
                        show_messstellen = False
                        messstellen_filtered = None
                else:
                    messstellen_filtered = None
            
            with col1:
                # Karte erstellen
                if map_type == "Choropleth (Farbe nach Änderung)":
                    fig_map = create_gwk_map(gdf, data['comparison'], selected_gwk)
                else:
                    fig_map = create_simple_gwk_map(gdf, data['comparison'], selected_gwk)
                
                if fig_map is not None:
                    
                    # MESSSTELLEN ALS LAYER HINZUFÜGEN
                    if show_messstellen and messstellen_filtered is not None and len(messstellen_filtered) > 0:
                        
                        # Farbe nach Trend
                        messstellen_filtered['color'] = messstellen_filtered['GRIMM-STRELE'].apply(
                            lambda x: 'red' if pd.notna(x) and x <= -1 else (
                                'green' if pd.notna(x) and x > 1 else 'orange'
                            )
                        )
                        
                        messstellen_filtered['size'] = 8
                        
                        # Hover-Text
                        messstellen_filtered['hover_text'] = messstellen_filtered.apply(
                            lambda row: f"<b>{row['MKZ']}</b><br>"
                                       f"GWK: {row['GWK']}<br>"
                                       f"Grimm-Strele: {row['GRIMM-STRELE']:.2f} %/a"
                                       if pd.notna(row['GRIMM-STRELE']) else
                                       f"<b>{row['MKZ']}</b><br>GWK: {row['GWK']}<br>Kein Trend",
                            axis=1
                        )
                        
                        # Messstellen-Trace hinzufügen
                        fig_map.add_trace(
                            go.Scattermapbox(
                                lon=messstellen_filtered['lon'],
                                lat=messstellen_filtered['lat'],
                                mode='markers',
                                marker=dict(
                                    size=messstellen_filtered['size'],
                                    color=messstellen_filtered['color'],
                                    opacity=0.8,
                                    symbol='circle'
                                ),
                                text=messstellen_filtered['hover_text'],
                                hoverinfo='text',
                                name='Messstellen',
                                showlegend=True
                            )
                        )
                        
                        st.caption(f"🔴 Fallend ({len(messstellen_filtered[messstellen_filtered['color']=='red'])}) | "
                                  f"🟠 Stabil ({len(messstellen_filtered[messstellen_filtered['color']=='orange'])}) | "
                                  f"🟢 Steigend ({len(messstellen_filtered[messstellen_filtered['color']=='green'])})")
                    
                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.error("Karte konnte nicht erstellt werden")
            
            # Legende
            st.markdown("---")
            st.subheader("📊 Farbskala GWK")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown("🟥 **< -20 mm/a**")
                st.caption("Starker Rückgang")
            
            with col2:
                st.markdown("🟧 **-20 bis -10**")
                st.caption("Rückgang")
            
            with col3:
                st.markdown("🟨 **-10 bis 0**")
                st.caption("Leichter Rückgang")
            
            with col4:
                st.markdown("🟩 **0 bis +10**")
                st.caption("Leichte Zunahme")
            
            with col5:
                st.markdown("🟢 **> +10 mm/a**")
                st.caption("Starke Zunahme")
            
            if show_messstellen:
                st.markdown("---")
                st.subheader("💧 Messstellen-Legende")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("🔴 **Fallend**")
                    st.caption("Grimm-Strele ≤ -1 %/a")
                
                with col2:
                    st.markdown("🟠 **Stabil**")
                    st.caption("-1 < Grimm-Strele ≤ 1 %/a")
                
                with col3:
                    st.markdown("🟢 **Steigend**")
                    st.caption("Grimm-Strele > 1 %/a")
            
        else:
            st.warning("⚠️ Keine Geometrien verfügbar. Shapefile konnte nicht geladen werden.")
            st.info(f"💡 Prüfe den Pfad: {shapefile_path}")
        
        st.markdown("---")
        
        # Histogramm der Änderungen (bleibt wie gehabt)
        st.subheader("Verteilung der Änderungen")
        
        fig_hist = px.histogram(
            data['comparison'],
            x='delta_abs',
            nbins=20,
            title="Verteilung der GWN-Änderungen (mm/a)",
            labels={'delta_abs': 'Änderung GWN [mm/a]', 'count': 'Anzahl GWK'},
            color_discrete_sequence=['steelblue']
        )
        
        fig_hist.add_vline(x=0, line_dash="dash", line_color="red", 
                          annotation_text="Keine Änderung")
        
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Box Plot (bleibt wie gehabt)
        st.subheader("Box Plot: Verteilung nach Perioden")
        
        box_data = []
        for _, row in data['comparison'].iterrows():
            box_data.append({'GWK_ID': row['GWK_ID'], 'Periode': '1961-1990', 'GWN': row['mean_ref']})
            box_data.append({'GWK_ID': row['GWK_ID'], 'Periode': '1991-2020', 'GWN': row['mean_hist']})
        
        box_df = pd.DataFrame(box_data)
        
        fig_box = px.box(
            box_df,
            x='Periode',
            y='GWN',
            color='Periode',
            title="Verteilung der GWN nach Perioden",
            labels={'GWN': 'GWN [mm/a]'},
            color_discrete_map={'1961-1990': 'green', '1991-2020': 'orange'}
        )
        
        st.plotly_chart(fig_box, use_container_width=True)
    
    # ========================================================================
    # SIDEBAR: EXPORT
    # ========================================================================
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Daten-Export")
    
    # CSV Download Comparison
    csv_comparison = data['comparison'].to_csv(index=False, sep=';', decimal=',')
    st.sidebar.download_button(
        label="📄 Vergleichstabelle (CSV)",
        data=csv_comparison,
        file_name=f"gwn_vergleich_{len(target_gwk)}_gwk.csv",
        mime="text/csv"
    )
    
    # CSV Download Trend
    csv_trend = data['trend'].to_csv(index=False, sep=';', decimal=',')
    st.sidebar.download_button(
        label="📄 Trendanalyse (CSV)",
        data=csv_trend,
        file_name=f"gwn_trend_{len(target_gwk)}_gwk.csv",
        mime="text/csv"
    )
    
    # CSV Download Zeitreihen
    csv_timeseries = data['gwn'].to_csv(index=False, sep=';', decimal=',')
    st.sidebar.download_button(
        label="📄 GWN Zeitreihen (CSV)",
        data=csv_timeseries,
        file_name=f"gwn_zeitreihen_{len(target_gwk)}_gwk.csv",
        mime="text/csv"
    )
    
    # Excel Export (alle Daten zusammen)
    if st.sidebar.button("📊 Excel-Export (alle Tabellen)"):
        from io import BytesIO
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            data['comparison'].to_excel(writer, sheet_name='Vergleich', index=False)
            data['trend'].to_excel(writer, sheet_name='Trend', index=False)
            data['gwn'].to_excel(writer, sheet_name='GWN_Zeitreihen', index=False)
            data['precip'].to_excel(writer, sheet_name='Niederschlag', index=False)
            data['etp'].to_excel(writer, sheet_name='ETp', index=False)
        
        excel_data = output.getvalue()
        
        st.sidebar.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"gwn_komplett_{len(target_gwk)}_gwk.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"""
    **💡 Hinweise:**
    - Aktuell: {len(target_gwk)} GWK ausgewählt
    - Alle Daten werden live berechnet
    - Plots sind interaktiv (Zoom, Pan, Hover)
    - Download: Kamera-Icon im Plot
    - Caching beschleunigt wiederholte Aufrufe
    """)


if __name__ == "__main__":
    main()