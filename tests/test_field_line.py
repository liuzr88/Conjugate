import pytest
import math
from field_line import trace_field_line


def test_returns_xyz_dict():
    """trace_field_line returns a dict with x, y, z keys."""
    result = trace_field_line(-30.3, -70.7, 0)
    assert isinstance(result, dict)
    assert set(result.keys()) == {"x", "y", "z"}


def test_xyz_same_length():
    """x, y, z arrays are all the same length."""
    result = trace_field_line(-30.3, -70.7, 0)
    assert len(result["x"]) == len(result["y"]) == len(result["z"])


def test_length_is_two_n_steps():
    """Total points = 2 * n_steps (upward n_steps + downward n_steps).
    The apex appears at both the end of the upward leg and the start of
    the downward leg — a harmless duplicate that is invisible in the render."""
    n = 20
    result = trace_field_line(-30.3, -70.7, 0, n_steps=n)
    assert len(result["x"]) == 2 * n


def test_endpoints_on_earth_surface():
    """First and last points should be at Earth's surface (R ≈ 1.0 in normalised coords)."""
    result = trace_field_line(-30.3, -70.7, 0)
    x, y, z = result["x"], result["y"], result["z"]
    r_start = math.sqrt(x[0]**2 + y[0]**2 + z[0]**2)
    r_end   = math.sqrt(x[-1]**2 + y[-1]**2 + z[-1]**2)
    assert abs(r_start - 1.0) < 0.01, f"Start radius {r_start:.4f} not near 1.0"
    assert abs(r_end - 1.0) < 0.01,   f"End radius {r_end:.4f} not near 1.0"


def test_arc_rises_above_surface():
    """The field line arc must rise above the Earth's surface (max R > 1.0)."""
    result = trace_field_line(-30.3, -70.7, 0)
    x, y, z = result["x"], result["y"], result["z"]
    radii = [math.sqrt(xi**2 + yi**2 + zi**2) for xi, yi, zi in zip(x, y, z)]
    assert max(radii) > 1.05, f"Arc never rises above surface, max R={max(radii):.4f}"


def test_negative_altitude_raises():
    """Negative altitude must raise ValueError."""
    with pytest.raises(ValueError, match="Altitude must be >= 0"):
        trace_field_line(-30.3, -70.7, -1)


def test_altitude_above_zero_shifts_endpoints():
    """Points at higher altitude start/end further from Earth's centre."""
    result0   = trace_field_line(-30.3, -70.7, 0)
    result300 = trace_field_line(-30.3, -70.7, 300)
    r0_start   = math.sqrt(result0["x"][0]**2   + result0["y"][0]**2   + result0["z"][0]**2)
    r300_start = math.sqrt(result300["x"][0]**2 + result300["y"][0]**2 + result300["z"][0]**2)
    assert r300_start > r0_start, "300 km start should be further from centre than 0 km start"
