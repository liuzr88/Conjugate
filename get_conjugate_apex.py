import apexpy
import datetime

# Lazy initialization: the IGRF model is loaded on first use rather than at
# import time, so importing this module does not trigger expensive I/O and
# does not fail in restricted environments.
_apex = None


def _get_apex():
    global _apex
    if _apex is None:
        _apex = apexpy.Apex(date=datetime.datetime.now(datetime.timezone.utc))
    return _apex


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

    c_lat, c_lon, error = _get_apex().map_to_height(lat, lon, height, height, conjugate=True)
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
