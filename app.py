"""
app.py — Magnetic Conjugate Point Explorer

A small 2D web app that computes the magnetic conjugate point for a
geographic location using apexpy IGRF tracing.

Run with:
    streamlit run app.py
"""

import plotly.graph_objects as go
import streamlit as st

from get_conjugate_apex import get_conjugate_point

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Magnetic Conjugate Point Explorer",
    page_icon="🌐",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Session state initialisation — widget keys are the only state.
# ---------------------------------------------------------------------------
if "lat_input" not in st.session_state:
    st.session_state["lat_input"] = -30.3
if "lon_input" not in st.session_state:
    st.session_state["lon_input"] = -70.7
if "alt_input" not in st.session_state:
    st.session_state["alt_input"] = 0.0
if "result" not in st.session_state:
    st.session_state["result"] = None
if "error_msg" not in st.session_state:
    st.session_state["error_msg"] = None

# ---------------------------------------------------------------------------
# Sidebar — inputs
# ---------------------------------------------------------------------------
st.sidebar.title("🌐 Conjugate Explorer")
st.sidebar.markdown("Enter a location and press **Compute**.")

lat = st.sidebar.number_input(
    "Latitude (°)", min_value=-90.0, max_value=90.0,
    step=0.1, format="%.4f", key="lat_input",
)
lon = st.sidebar.number_input(
    "Longitude (°)", min_value=-180.0, max_value=180.0,
    step=0.1, format="%.4f", key="lon_input",
)
alt = st.sidebar.number_input(
    "Altitude (km)", min_value=0.0, max_value=50000.0,
    step=10.0, format="%.1f", key="alt_input",
)

compute = st.sidebar.button("⚡ Compute Conjugate", use_container_width=True)

# ---------------------------------------------------------------------------
# Compute (BEFORE the results panel renders so the new result shows in the
# same rerun the user clicked the button)
# ---------------------------------------------------------------------------
if compute:
    st.session_state["error_msg"] = None
    st.session_state["result"] = None
    try:
        c_lat, c_lon, error = get_conjugate_point(lat, lon, alt)
        st.session_state["result"] = {
            "c_lat": c_lat,
            "c_lon": c_lon,
            "error": error,
        }
    except ValueError as e:
        st.session_state["error_msg"] = str(e)
    except Exception as e:
        st.session_state["error_msg"] = f"Calculation error: {e}"

# --- Sidebar results panel ---
st.sidebar.divider()
if st.session_state["result"]:
    r = st.session_state["result"]
    st.sidebar.markdown("### Conjugate Point")
    st.sidebar.markdown(f"**Lat:** `{r['c_lat']:.4f}°`")
    st.sidebar.markdown(f"**Lon:** `{r['c_lon']:.4f}°`")
    st.sidebar.markdown(f"**Alt:** `{alt:.1f} km`")
    st.sidebar.markdown(f"**Error est:** `{r['error']:.2e}°`")
elif st.session_state["error_msg"]:
    st.sidebar.error(st.session_state["error_msg"])
else:
    st.sidebar.caption("Results appear here after computing.")

# ---------------------------------------------------------------------------
# 2D Map (display only)
# ---------------------------------------------------------------------------
def make_map_fig(lat, lon, result):
    input_marker = go.Scattergeo(
        lat=[lat], lon=[lon],
        mode="markers",
        marker=dict(size=12, color="#89b4fa", symbol="circle",
                    line=dict(color="white", width=1.5)),
        name="Input",
        hovertemplate=f"Input: {lat:.2f}°, {lon:.2f}°<extra></extra>",
    )
    traces = [input_marker]

    if result:
        traces.append(go.Scattergeo(
            lat=[result["c_lat"]], lon=[result["c_lon"]],
            mode="markers",
            marker=dict(size=12, color="#a6e3a1", symbol="circle",
                        line=dict(color="white", width=1.5)),
            name="Conjugate",
            hovertemplate=(
                f"Conjugate: {result['c_lat']:.2f}°, "
                f"{result['c_lon']:.2f}°<extra></extra>"
            ),
        ))
        traces.append(go.Scattergeo(
            lat=[lat, result["c_lat"]],
            lon=[lon, result["c_lon"]],
            mode="lines",
            line=dict(color="#cba6f7", width=2, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
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
        height=520,
        legend=dict(
            font=dict(color="white", size=11),
            bgcolor="rgba(0,0,0,0.4)",
            x=0.01, y=0.99,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
st.plotly_chart(
    make_map_fig(lat, lon, st.session_state["result"]),
    use_container_width=True,
    key="map",
)
