import pytest
from get_conjugate_apex import get_conjugate_point


def test_conjugate_returns_three_values():
    """Core function returns (c_lat, c_lon, error)."""
    result = get_conjugate_point(-30.3, -70.7, 0)
    assert len(result) == 3
    assert all(isinstance(v, float) for v in result)


def test_conjugate_opposite_hemisphere():
    """Conjugate of a southern-hemisphere point is in the northern hemisphere."""
    c_lat, c_lon, error = get_conjugate_point(-30.3, -70.7, 0)
    assert c_lat > 0, f"Expected northern hemisphere conjugate, got lat={c_lat}"


def test_conjugate_of_northern_is_southern():
    """Conjugate of a northern-hemisphere point is in the southern hemisphere."""
    c_lat, c_lon, error = get_conjugate_point(51.5, -0.1, 0)
    assert c_lat < 0, f"Expected southern hemisphere conjugate, got lat={c_lat}"


def test_error_estimate_is_small():
    """Error estimate from apexpy should be very small.

    Threshold is 1e-3 degrees — 100× the documented typical value of 1e-5,
    providing a generous safety margin while still catching runaway errors.
    """
    c_lat, c_lon, error = get_conjugate_point(-30.3, -70.7, 0)
    assert error < 1e-3, f"Error estimate too large: {error}"


def test_negative_altitude_raises():
    """Negative altitude should raise a ValueError before calling apexpy."""
    with pytest.raises(ValueError, match="Altitude must be >= 0"):
        get_conjugate_point(-30.3, -70.7, -10)


def test_altitude_affects_result():
    """Results at different altitudes should differ."""
    lat0, lon0, _ = get_conjugate_point(-30.3, -70.7, 0)
    lat300, lon300, _ = get_conjugate_point(-30.3, -70.7, 300)
    assert lat0 != lat300 or lon0 != lon300


def test_equatorial_point_behavior():
    """Points at the magnetic equator return a result rather than raising.

    apexpy maps lat=0, lon=0, height=0 to a conjugate point without error.
    This test documents the actual behavior: a valid 3-tuple is returned.
    If apexpy's behavior changes in a future version this test will catch it.
    """
    result = get_conjugate_point(0.0, 0.0, 0)
    assert len(result) == 3
    assert all(isinstance(v, float) for v in result)
