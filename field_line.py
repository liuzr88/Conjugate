"""
field_line.py — IGRF magnetic field line tracing for 3D visualisation.

Public API:
    trace_field_line(lat, lon, height, n_steps=50) -> dict[str, list[float]]
"""

from math import radians, cos, sin, sqrt
import numpy as np
from get_conjugate_apex import _get_apex


def _geo_to_cartesian(lat_deg: float, lon_deg: float, alt_km: float):
    """
    Convert geographic (lat, lon, alt) to normalised 3D Cartesian coordinates.

    The unit sphere (R=1) represents Earth's surface. Points above the surface
    have R = 1 + alt_km / 6371.0.

    Returns (x, y, z) as floats.
    """
    R = 1.0 + alt_km / 6371.0
    lat_r = radians(lat_deg)
    lon_r = radians(lon_deg)
    x = R * cos(lat_r) * cos(lon_r)
    y = R * cos(lat_r) * sin(lon_r)
    z = R * sin(lat_r)
    return x, y, z


def trace_field_line(lat: float, lon: float, height: float, n_steps: int = 50) -> dict:
    """
    Trace the IGRF magnetic field line through space from (lat, lon, height)
    up to the magnetic apex and back down to the conjugate hemisphere.

    Parameters
    ----------
    lat     : Geographic latitude of the input point (degrees, [-90, 90]).
    lon     : Geographic longitude of the input point (degrees).
    height  : Altitude of the input point in km. Must be >= 0.
    n_steps : Number of altitude samples per leg (upward + downward). Default 50.

    Returns
    -------
    dict with keys 'x', 'y', 'z' — each a list of floats of length 2 * n_steps.
    Coordinates are normalised 3D Cartesian (Earth radius = 1.0).
    The sequence runs: input point → apex → conjugate point.
    Note: the apex point appears at position n_steps-1 and n_steps (duplicated),
    which is visually harmless and keeps the two legs symmetric.

    Raises
    ------
    ValueError  if height < 0.
    Exception   propagated from apexpy for undefined field-line regions.
    """
    if height < 0:
        raise ValueError("Altitude must be >= 0 km")

    apex = _get_apex()

    # --- Find apex altitude via Modified Apex latitude ---
    # geo2apex returns the Modified Apex latitude (alat) for this field line.
    # The dipole formula gives the apex height from alat.
    alat, _ = apex.geo2apex(lat, lon, height)
    alat_rad = radians(abs(alat))          # use abs: formula is symmetric
    cos_alat = cos(alat_rad)
    if cos_alat < 1e-6:
        # Near magnetic equator — apex is essentially at infinity; cap at 50 000 km
        apex_alt = 50_000.0
    else:
        apex_alt = 6371.0 * (1.0 / cos_alat**2 - 1.0)

    # --- Sample altitudes for each leg ---
    upward_alts   = np.linspace(height, apex_alt, n_steps)   # input → apex
    downward_alts = np.linspace(apex_alt, height, n_steps)   # apex → conjugate

    xs, ys, zs = [], [], []

    # Upward leg: same hemisphere, increasing altitude
    for alt in upward_alts:
        g_lat, g_lon, _ = apex.map_to_height(lat, lon, height, float(alt))
        x, y, z = _geo_to_cartesian(float(g_lat), float(g_lon), float(alt))
        xs.append(x); ys.append(y); zs.append(z)

    # Downward leg: conjugate hemisphere, decreasing altitude
    for alt in downward_alts:
        g_lat, g_lon, _ = apex.map_to_height(lat, lon, height, float(alt), conjugate=True)
        x, y, z = _geo_to_cartesian(float(g_lat), float(g_lon), float(alt))
        xs.append(x); ys.append(y); zs.append(z)

    return {"x": xs, "y": ys, "z": zs}
