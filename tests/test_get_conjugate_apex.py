import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_conjugate_returns_three_values():
    """Core function returns (c_lat, c_lon, error)."""
    from get_conjugate_apex import get_conjugate_point
    result = get_conjugate_point(-30.3, -70.7, 0)
    assert len(result) == 3


def test_conjugate_opposite_hemisphere():
    """Conjugate of a southern-hemisphere point is in the northern hemisphere."""
    from get_conjugate_apex import get_conjugate_point
    c_lat, c_lon, error = get_conjugate_point(-30.3, -70.7, 0)
    assert c_lat > 0, f"Expected northern hemisphere conjugate, got lat={c_lat}"


def test_conjugate_of_northern_is_southern():
    """Conjugate of a northern-hemisphere point is in the southern hemisphere."""
    from get_conjugate_apex import get_conjugate_point
    c_lat, c_lon, error = get_conjugate_point(51.5, -0.1, 0)
    assert c_lat < 0, f"Expected southern hemisphere conjugate, got lat={c_lat}"


def test_error_estimate_is_small():
    """Error estimate from apexpy should be very small (< 0.01 degrees)."""
    from get_conjugate_apex import get_conjugate_point
    c_lat, c_lon, error = get_conjugate_point(-30.3, -70.7, 0)
    assert error < 0.01, f"Error estimate too large: {error}"


def test_negative_altitude_raises():
    """Negative altitude should raise a ValueError before calling apexpy."""
    from get_conjugate_apex import get_conjugate_point
    with pytest.raises(ValueError, match="Altitude must be >= 0"):
        get_conjugate_point(-30.3, -70.7, -10)


def test_altitude_affects_result():
    """Results at different altitudes should differ."""
    from get_conjugate_apex import get_conjugate_point
    lat0, lon0, _ = get_conjugate_point(-30.3, -70.7, 0)
    lat300, lon300, _ = get_conjugate_point(-30.3, -70.7, 300)
    assert lat0 != lat300 or lon0 != lon300
