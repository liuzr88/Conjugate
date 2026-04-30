# apexpy Conjugate Point Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `get_conjugate_apex.py`, a standalone interactive script that uses `apexpy` field-line tracing to compute magnetic conjugate points, alongside the existing `get_conjugate.py`.

**Architecture:** Single script file mirroring `get_conjugate.py`'s structure. `apexpy.Apex` is initialised once at module level. A `get_conjugate_point(lat, lon, height)` function wraps `apex.map_to_height(..., conjugate=True)` and returns `(c_lat, c_lon, error_deg)`. An interactive `while` loop reads `lat lon alt_km` from stdin.

**Tech Stack:** Python 3.11, `apexpy` 2.1.0, `datetime` (stdlib), `pytest` for tests.

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `get_conjugate_apex.py` | Create | Main script: Apex init, core function, interactive loop |
| `tests/test_get_conjugate_apex.py` | Create | Unit tests for core function |

---

### Task 1: Create the test file with a failing test for the core function

**Files:**
- Create: `tests/test_get_conjugate_apex.py`

- [ ] **Step 1: Create the tests directory**

```bash
mkdir -p /Users/alanliu/Git/Conjugate/tests
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_get_conjugate_apex.py`:

```python
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
```

- [ ] **Step 3: Run tests to confirm they all fail (ImportError expected)**

```bash
cd /Users/alanliu/Git/Conjugate && python -m pytest tests/test_get_conjugate_apex.py -v
```

Expected: All 6 tests fail with `ModuleNotFoundError: No module named 'get_conjugate_apex'`

---

### Task 2: Implement `get_conjugate_apex.py`

**Files:**
- Create: `get_conjugate_apex.py`

- [ ] **Step 1: Write the implementation**

Create `/Users/alanliu/Git/Conjugate/get_conjugate_apex.py`:

```python
import apexpy
import datetime

# Initialise the IGRF model once using today's date.
# apexpy.Apex accepts a datetime object and derives the decimal year internally.
apex = apexpy.Apex(date=datetime.datetime.now())


def get_conjugate_point(lat, lon, height):
    """
    Compute the magnetic conjugate point using apexpy field-line tracing.

    Uses Modified Apex coordinates (IGRF model) to trace the magnetic field
    line from (lat, lon, height) to its apex, then back down to the same
    altitude in the conjugate hemisphere.

    Parameters
    ----------
    lat : float
        Geographic latitude in degrees [-90, 90].
    lon : float
        Geographic longitude in degrees. apexpy accepts [-180, 360] and
        wraps silently outside that range.
    height : float
        Altitude in km. Must be >= 0.

    Returns
    -------
    c_lat : float
        Geographic latitude of the conjugate point (degrees).
    c_lon : float
        Geographic longitude of the conjugate point (degrees).
    error : float
        Angular precision of the result in degrees (from apexpy's internal
        iterative solver). Typically < 1e-5 for well-defined field lines.

    Raises
    ------
    ValueError
        If height < 0.
    Exception
        Propagates apexpy errors for undefined field-line regions (e.g. near
        the magnetic equator at very low altitudes).
    """
    if height < 0:
        raise ValueError("Altitude must be >= 0 km")

    c_lat, c_lon, error = apex.map_to_height(lat, lon, height, height, conjugate=True)
    return float(c_lat), float(c_lon), float(error)


if __name__ == "__main__":
    print("Magnetic Conjugate Point Calculator (apexpy / IGRF field-line tracing)")
    print("Enter coordinates as 'lat lon alt_km' (e.g. -30.3 -70.7 0). Type 'quit' to exit.\n")

    while True:
        raw = input("Enter lat lon alt_km: ").strip()
        if raw.lower() in ("quit", "exit", "q"):
            break
        try:
            parts = raw.split()
            if len(parts) != 3:
                raise ValueError("Expected exactly 3 values.")
            lat, lon, height = map(float, parts)
        except ValueError as e:
            print(f"  Invalid input: {e} Please enter three numbers: lat lon alt_km.\n")
            continue

        try:
            c_lat, c_lon, error = get_conjugate_point(lat, lon, height)
        except ValueError as e:
            print(f"  {e}\n")
            continue
        except Exception as e:
            print(f"  Calculation error: {e}\n")
            continue

        print(f"  Input:     ({lat:.4f}, {lon:.4f}) at {height:.1f} km")
        print(f"  Conjugate: ({c_lat:.4f}, {c_lon:.4f}) at {height:.1f} km")
        print(f"  Error est: {error:.2e}°\n")
```

- [ ] **Step 2: Run the tests and confirm they all pass**

```bash
cd /Users/alanliu/Git/Conjugate && python -m pytest tests/test_get_conjugate_apex.py -v
```

Expected output:
```
PASSED tests/test_get_conjugate_apex.py::test_conjugate_returns_three_values
PASSED tests/test_get_conjugate_apex.py::test_conjugate_opposite_hemisphere
PASSED tests/test_get_conjugate_apex.py::test_conjugate_of_northern_is_southern
PASSED tests/test_get_conjugate_apex.py::test_error_estimate_is_small
PASSED tests/test_get_conjugate_apex.py::test_negative_altitude_raises
PASSED tests/test_get_conjugate_apex.py::test_altitude_affects_result
6 passed
```

- [ ] **Step 3: Smoke-test the interactive loop**

```bash
echo "-30.3 -70.7 0
51.5 -0.1 300
bad input
-30.3 -70.7 -5
quit" | python get_conjugate_apex.py
```

Expected: Valid coordinates print conjugate + error estimate, `bad input` prints a hint, negative altitude prints a ValueError message, `quit` exits cleanly.

- [ ] **Step 4: Commit**

```bash
cd /Users/alanliu/Git/Conjugate && git add get_conjugate_apex.py tests/test_get_conjugate_apex.py && git commit -m "feat: add apexpy conjugate point calculator with tests"
```

---

## Done

The feature is complete when:
- All 6 tests pass
- The smoke test behaves as described
- `get_conjugate_apex.py` exists alongside `get_conjugate.py` with no changes to the latter
