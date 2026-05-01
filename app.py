"""
app.py — Magnetic Conjugate Point Explorer

Run with:
    streamlit run app.py
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from streamlit_plotly_events import plotly_events

from get_conjugate_apex import get_conjugate_point
from field_line import trace_field_line, geo_to_cartesian

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Magnetic Conjugate Point Explorer",
    page_icon="🌐",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "lat" not in st.session_state:
    st.session_state.lat = -30.3
if "lon" not in st.session_state:
    st.session_state.lon = -70.7
if "alt" not in st.session_state:
    st.session_state.alt = 0.0
if "result" not in st.session_state:
    st.session_state.result = None
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None

# ---------------------------------------------------------------------------
# Sidebar — inputs and results
# ---------------------------------------------------------------------------
st.sidebar.title("🌐 Conjugate Explorer")
st.sidebar.markdown("Enter a location or click the map below.")

lat = st.sidebar.number_input(
    "Latitude (°)", min_value=-90.0, max_value=90.0,
    value=float(st.session_state.lat), step=0.1, format="%.4f", key="lat_input",
)
lon = st.sidebar.number_input(
    "Longitude (°)", min_value=-180.0, max_value=180.0,
    value=float(st.session_state.lon), step=0.1, format="%.4f", key="lon_input",
)
alt = st.sidebar.number_input(
    "Altitude (km)", min_value=0.0, max_value=50000.0,
    value=float(st.session_state.alt), step=10.0, format="%.1f", key="alt_input",
)

# Sync sidebar values back to session state
st.session_state.lat = lat
st.session_state.lon = lon
st.session_state.alt = alt

compute = st.sidebar.button("⚡ Compute Conjugate", use_container_width=True)

# --- Results panel ---
st.sidebar.divider()
if st.session_state.result:
    r = st.session_state.result
    st.sidebar.markdown("### Conjugate Point")
    st.sidebar.markdown(f"**Lat:** `{r['c_lat']:.4f}°`")
    st.sidebar.markdown(f"**Lon:** `{r['c_lon']:.4f}°`")
    st.sidebar.markdown(f"**Alt:** `{alt:.1f} km`")
    st.sidebar.markdown(f"**Error est:** `{r['error']:.2e}°`")
elif st.session_state.error_msg:
    st.sidebar.error(st.session_state.error_msg)
else:
    st.sidebar.caption("Results appear here after computing.")

# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------
if compute:
    st.session_state.error_msg = None
    st.session_state.result = None
    try:
        c_lat, c_lon, error = get_conjugate_point(lat, lon, alt)
        field_line = trace_field_line(lat, lon, alt)
        ix, iy, iz = geo_to_cartesian(lat, lon, alt)
        cx, cy, cz = geo_to_cartesian(c_lat, c_lon, alt)
        st.session_state.result = {
            "c_lat": c_lat,
            "c_lon": c_lon,
            "error": error,
            "field_line": field_line,
            "input_xyz": (ix, iy, iz),
            "conj_xyz": (cx, cy, cz),
        }
    except ValueError as e:
        st.session_state.error_msg = str(e)
    except Exception as e:
        st.session_state.error_msg = f"Calculation error: {e}"

# ---------------------------------------------------------------------------
# 3D Globe
# ---------------------------------------------------------------------------
def make_globe_fig(lat, lon, alt, result):
    # Sphere surface
    phi   = np.linspace(0, 2 * np.pi, 120)
    theta = np.linspace(0, np.pi, 60)
    phi, theta = np.meshgrid(phi, theta)
    sx = np.sin(theta) * np.cos(phi)
    sy = np.sin(theta) * np.sin(phi)
    sz = np.cos(theta)

    colorscale = [
        [0.0, "#0a2a4a"],
        [0.4, "#1a5276"],
        [0.7, "#2e7d32"],
        [1.0, "#a5d6a7"],
    ]

    traces = [
        go.Surface(
            x=sx, y=sy, z=sz,
            colorscale=colorscale,
            showscale=False,
            opacity=0.95,
            hoverinfo="skip",
            lightposition=dict(x=1, y=1, z=1),
        )
    ]

    r = result
    if r:
        fl = r["field_line"]

        # Field line arc — colour gradient blue→purple→green
        n = len(fl["x"])
        colours = [
            f"hsl({int(240 - 120 * i / max(n - 1, 1))}, 90%, 65%)"
            for i in range(n)
        ]
        traces.append(
            go.Scatter3d(
                x=fl["x"], y=fl["y"], z=fl["z"],
                mode="lines",
                line=dict(color=colours, width=5),
                name="Field line",
                hoverinfo="skip",
            )
        )

        # Input point (blue)
        ix, iy, iz = r["input_xyz"]
        traces.append(
            go.Scatter3d(
                x=[ix], y=[iy], z=[iz],
                mode="markers",
                marker=dict(size=8, color="#89b4fa", symbol="circle",
                            line=dict(color="white", width=1)),
                name=f"Input ({lat:.2f}°, {lon:.2f}°)",
            )
        )

        # Conjugate point (green)
        cx, cy, cz = r["conj_xyz"]
        traces.append(
            go.Scatter3d(
                x=[cx], y=[cy], z=[cz],
                mode="markers",
                marker=dict(size=8, color="#a6e3a1", symbol="circle",
                            line=dict(color="white", width=1)),
                name=f"Conjugate ({r['c_lat']:.2f}°, {r['c_lon']:.2f}°)",
            )
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0e1117",
        scene=dict(
            bgcolor="#0e1117",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="cube",
            camera=dict(eye=dict(x=1.4, y=1.0, z=0.7)),
        ),
        legend=dict(
            font=dict(color="white", size=11),
            bgcolor="rgba(0,0,0,0.4)",
            x=0.01, y=0.99,
        ),
        height=500,
    )
    return fig


# ---------------------------------------------------------------------------
# 2D Clickable Map
# ---------------------------------------------------------------------------
def make_map_fig(lat, lon, result):
    # Coastlines as explicit first trace
    coast_trace = go.Scattergeo(
        lat=[None], lon=[None],
        mode="lines",
        line=dict(color="#4a7a9b", width=1),
        showlegend=False,
        hoverinfo="skip",
    )

    # Invisible click-target grid (lon as x, lat as y for streamlit-plotly-events)
    lats = np.linspace(-90, 90, 37)
    lons = np.linspace(-180, 180, 73)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    click_trace = go.Scattergeo(
        lat=lat_grid.flatten(),
        lon=lon_grid.flatten(),
        mode="markers",
        marker=dict(size=12, color="rgba(0,0,0,0)", opacity=0),
        hoverinfo="skip",
        showlegend=False,
    )

    # Current input point marker on map
    input_marker = go.Scattergeo(
        lat=[lat], lon=[lon],
        mode="markers",
        marker=dict(size=10, color="#89b4fa", symbol="circle",
                    line=dict(color="white", width=1.5)),
        name="Input",
        hovertemplate=f"Input: {lat:.2f}°, {lon:.2f}°<extra></extra>",
    )

    traces = [coast_trace, click_trace, input_marker]

    r = result
    if r:
        traces.append(go.Scattergeo(
            lat=[r["c_lat"]], lon=[r["c_lon"]],
            mode="markers",
            marker=dict(size=10, color="#a6e3a1", symbol="circle",
                        line=dict(color="white", width=1.5)),
            name="Conjugate",
            hovertemplate=f"Conjugate: {r['c_lat']:.2f}°, {r['c_lon']:.2f}°<extra></extra>",
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        geo=dict(
            showland=True, landcolor="#1a3a1a",
            showocean=True, oceancolor="#0a2a4a",
            showcoastlines=True, coastlinecolor="#4a7a9b",
            showframe=False,
            bgcolor="#0e1117",
            projection_type="natural earth",
        ),
        paper_bgcolor="#0e1117",
        margin=dict(l=0, r=0, t=0, b=0),
        height=260,
        legend=dict(font=dict(color="white", size=10), bgcolor="rgba(0,0,0,0.4)"),
    )
    return fig


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
st.markdown("### 🌍 3D Globe")
st.plotly_chart(make_globe_fig(lat, lon, alt, st.session_state.result), key="globe")

st.markdown("### 🗺️ Click map to set input point")
clicked = plotly_events(make_map_fig(lat, lon, st.session_state.result), click_event=True, key="map",
                        override_height=260)
if clicked:
    # streamlit-plotly-events returns 'x' = lon, 'y' = lat for Scattergeo traces
    try:
        st.session_state.lon = float(clicked[0]["x"])
        st.session_state.lat = float(clicked[0]["y"])
        st.rerun()
    except (KeyError, TypeError, ValueError):
        pass  # Malformed click payload — ignore silently
