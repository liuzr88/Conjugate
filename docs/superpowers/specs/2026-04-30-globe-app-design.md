# Design Spec: Magnetic Conjugate Point Globe App

**Date:** 2026-04-30
**New files:**
- `app.py` — Streamlit application (UI, globe, 2D map, state management)
- `field_line.py` — field line tracing (pure function, returns 3D Cartesian points)

**Existing files — NOT modified:**
- `get_conjugate.py` — aacgmv2 implementation, untouched
- `get_conjugate_apex.py` — apexpy implementation, imported by app but not changed
- `tests/test_get_conjugate_apex.py` — unchanged
- `pytest.ini` — unchanged

---

## Purpose

A local web application that lets the user input a geographic location (by typing lat/lon or clicking a 2D map), computes its magnetic conjugate point using apexpy IGRF field-line tracing, and renders both points and the connecting field line arc on an interactive 3D globe.

---

## Architecture

```
app.py
  ├── imports get_conjugate_point()  from get_conjugate_apex.py
  ├── imports trace_field_line()     from field_line.py
  └── renders via streamlit + plotly

field_line.py
  └── imports _get_apex()            from get_conjugate_apex.py
      (reuses the same lazy-initialised apexpy.Apex singleton)
```

No API layer. Everything runs in a single Python process. Run with:

```bash
streamlit run app.py
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.33 | UI framework and local server |
| `plotly` | ≥ 5.0 | 3D globe (`go.Surface`, `go.Scatter3d`) and 2D map (`go.Scattergeo`) |
| `streamlit-plotly-events` | ≥ 0.0.6 | Captures Plotly click events inside Streamlit (map click → lat/lon) |
| `apexpy` | 2.1.0 | Field-line tracing (via existing `get_conjugate_apex.py`) |
| `numpy` | any | Coordinate math in `field_line.py` |

Install command: `pip install streamlit plotly streamlit-plotly-events`
(`apexpy` and `numpy` already installed.)

---

## `field_line.py`

Single public function:

```python
def trace_field_line(lat, lon, height, n_steps=50):
    """
    Trace the IGRF magnetic field line through space.

    Returns a dict with keys 'x', 'y', 'z' (lists of floats) representing
    3D Cartesian coordinates on/above a unit sphere scaled by Earth's radius.
    Points run from the input point, up through the apex, down to the conjugate.

    Parameters
    ----------
    lat, lon : float   Geographic coordinates of the input point (degrees).
    height   : float   Altitude in km (>= 0). Passed to apexpy.
    n_steps  : int     Number of altitude samples per leg (default 50).

    Returns
    -------
    dict with keys 'x', 'y', 'z' — each a list of floats (length 2*n_steps+1).

    Raises
    ------
    ValueError  if height < 0.
    Exception   propagated from apexpy for undefined field-line regions.
    """
```

**Algorithm:**
1. Find the apex altitude:
   - Convert input to Modified Apex coordinates: `alat, alon = _get_apex().geo2apex(lat, lon, height)` — this returns the apex latitude (degrees).
   - Estimate apex height from the dipole formula: `apex_alt = 6371.0 * (1.0 / cos(radians(alat))**2 - 1.0)` (km above Earth's surface). This is a reliable approximation that avoids needing `get_apex()`.
2. Sample `n_steps` altitudes linearly from `height` → `apex_alt` (upward leg, input hemisphere).
3. Sample `n_steps` altitudes linearly from `apex_alt` → `height` (downward leg, conjugate hemisphere).
4. For each altitude sample:
   - **Upward leg:** `_get_apex().map_to_height(lat, lon, height, sample_alt)` — maps the input point along the same field line to the new altitude in the same hemisphere. As `sample_alt` increases toward `apex_alt`, the returned geographic coordinates trace the arc upward.
   - **Downward leg:** `_get_apex().map_to_height(lat, lon, height, sample_alt, conjugate=True)` — maps to the conjugate hemisphere at `sample_alt`. As `sample_alt` decreases from `apex_alt` to `height`, the returned coordinates trace the arc down to the conjugate point.
5. Convert each (lat, lon, alt) sample to 3D Cartesian:
   ```python
   R = 1.0 + alt_km / 6371.0   # normalised radius
   x = R * cos(lat_rad) * cos(lon_rad)
   y = R * cos(lat_rad) * sin(lon_rad)
   z = R * sin(lat_rad)
   ```
6. Return concatenated x, y, z arrays (upward leg + downward leg).

---

## `app.py`

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Sidebar          │ Main area                         │
│                  │                                   │
│ [Lat input]      │  ┌─────────────────────────────┐ │
│ [Lon input]      │  │   3D Globe (Plotly)         │ │
│ [Alt input]      │  │   drag to rotate            │ │
│ [COMPUTE button] │  │                             │ │
│                  │  └─────────────────────────────┘ │
│ ── Results ──    │  ┌─────────────────────────────┐ │
│ Conj lat         │  │   2D Clickable Map (Plotly) │ │
│ Conj lon         │  │   click to set input point  │ │
│ Error est        │  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### State management

Streamlit session state keys:
- `lat`, `lon`, `alt` — current input values (float)
- `result` — dict with `c_lat`, `c_lon`, `error`, `field_line` (or `None`)
- `error_msg` — string error message to display (or `None`)

### Interaction flow

1. **On load:** Globe renders empty (just the sphere, no markers or field line).
2. **Click on 2D map:** `plotly_click` event updates `st.session_state.lat` and `st.session_state.lon`; sidebar inputs reflect new values; computation does NOT auto-run (user presses Compute).
3. **Press Compute:** Validates inputs → calls `get_conjugate_point()` → calls `trace_field_line()` → stores result in session state → re-renders globe with markers and field line.
4. **Type in sidebar inputs:** Updates session state values directly.

### 3D Globe figure (`go.Figure`)

Traces (in render order):
1. `go.Surface` — unit sphere with blue/ocean colorscale, `showscale=False`
2. `go.Scatter3d` — field line arc, mode=`lines`, gradient colour (blue → purple → green)
3. `go.Scatter3d` — input point marker, blue, size 8
4. `go.Scatter3d` — conjugate point marker, green, size 8

Globe settings: `scene_bgcolor='#0e1117'`, axis labels off, aspect ratio equal, camera set to slightly elevated view.

### 2D Map figure (`go.Figure`)

Single `go.Scattergeo` trace of world coastlines (`scope='world'`), dark theme. A second invisible `go.Scattergeo` trace covers the full globe as a dense grid of transparent points, with geographic longitude as `x` and latitude as `y`, making every location clickable.

Click events are captured using `streamlit_plotly_events` from the `streamlit-plotly-events` package. The return dict contains `x` (longitude) and `y` (latitude) directly — `customdata` is not forwarded by this component:
```python
from streamlit_plotly_events import plotly_events
clicked = plotly_events(map_fig, click_event=True, key="map")
if clicked:
    st.session_state.lon = clicked[0]["x"]   # Scattergeo x = longitude
    st.session_state.lat = clicked[0]["y"]   # Scattergeo y = latitude
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Latitude outside [-90, 90] | Red warning in sidebar, no computation |
| Altitude < 0 | Red warning in sidebar, no computation |
| apexpy raises (undefined field line) | Error message shown below map, globe cleared to empty state |
| `streamlit` not installed | Clear install instructions printed on import error |

---

## Out of Scope

- Saving or exporting results
- Comparing aacgmv2 vs apexpy results in the UI
- Batch input (multiple points at once)
- Deployment (this is local only)
- Animation or time-varying field
