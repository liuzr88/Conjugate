# Design Spec: apexpy-based Magnetic Conjugate Point Calculator

**Date:** 2026-04-30
**File to create:** `get_conjugate_apex.py`
**Sits alongside:** `get_conjugate.py` (existing AACGM-v2 implementation)

---

## Purpose

Replace the AACGM-v2 coordinate-flip approximation with a proper field-line tracing
approach using `apexpy`. The Modified Apex coordinate system traces the actual IGRF
magnetic field line from the input point to its apex and back down to the conjugate
hemisphere, producing a more accurate result along with a built-in error estimate.

---

## Architecture

Single standalone script. No classes, no external modules beyond `apexpy` and `datetime`.
Mirrors the structure of `get_conjugate.py` for consistency.

### Initialization

```python
import apexpy
import datetime

apex = apexpy.Apex(date=datetime.datetime.now())
```

`apexpy.Apex` accepts a `datetime` object and converts it to the decimal year internally.
It loads the IGRF model coefficients once at startup and reuses them for all queries.

### Core Function

```python
def get_conjugate_point(lat, lon, height):
    ...
    c_lat, c_lon, error = apex.map_to_height(lat, lon, height, height, conjugate=True)
    return c_lat, c_lon, error
```

- `height` is used as both source and destination altitude (km), so the conjugate point
  is mapped to the same altitude as the input. Must be >= 0.
- `conjugate=True` internally negates the Modified Apex latitude before converting back
  to geographic, tracing the field line to the opposite hemisphere.
- `error` is the angular difference (degrees) between the input quasi-dipole coordinates
  and those produced by back-converting the output — a built-in precision indicator.
- Wrapped in try/except to handle edge cases (e.g. points near the magnetic equator or
  above ±90° apex latitude where mapping is undefined).

### Interactive Loop

Prompt: `Enter lat lon alt_km:`

- Parses 3 whitespace-separated floats.
- On `ValueError` (wrong number of tokens or non-numeric): prints a usage hint and re-prompts.
- On `quit` / `exit` / `q`: exits cleanly.
- On successful calculation: prints input coordinates, conjugate coordinates, and error estimate.

### Output Format

```
  Input:     (-30.3000, -70.7000) at 0.0 km
  Conjugate: (9.3821, -75.0912) at 0.0 km
  Error est: 0.000001°
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Non-numeric or wrong token count | Print hint, re-prompt |
| apexpy raises exception (undefined region) | Print error message, re-prompt |
| Latitude out of [-90, 90] | apexpy raises; caught and reported |
| Altitude < 0 | Validated before calling apexpy; print error and re-prompt |
| Longitude out of [-180, 360] | apexpy wraps silently; no validation needed |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `apexpy` | 2.1.0 | Modified Apex field-line tracing |
| `datetime` | stdlib | Epoch for IGRF model |

`apexpy` must be installed: `pip install apexpy`

---

## Why apexpy over aacgmv2

| | aacgmv2 (`get_conjugate.py`) | apexpy (`get_conjugate_apex.py`) |
|---|---|---|
| Method | Negate AACGM magnetic latitude | Trace field line via Modified Apex coords |
| Accuracy | Approximation; ~0.06° round-trip error | Iterative; returns explicit error estimate |
| Altitude handling | Fixed 0 km | Configurable source & destination altitude |
| Edge cases | Silent errors near SAA | Raises exceptions with clear messages |
| Error estimate | None | Yes (`error` return value, in degrees) |

---

## Out of Scope

- Batch file input/output
- Graphical output or mapping
- Changing the epoch mid-session
- Comparison output between aacgmv2 and apexpy results
