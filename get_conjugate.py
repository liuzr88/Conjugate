import aacgmv2
import datetime

# Using today's date for the magnetic model
dtime = datetime.datetime.now()

def get_conjugate_point(lat, lon, height=0):
    """
    Given a geographic (lat, lon) in degrees and an altitude in km,
    return the geographic (lat, lon) of the magnetic conjugate point.

    Uses AACGM-v2 coordinates:
      'G2A' converts Geographic -> AACGM magnetic
      'A2G' converts AACGM magnetic -> Geographic
    The conjugate point is found by negating the magnetic latitude
    (same field line, opposite hemisphere).
    """
    try:
        # 1. Convert Geographic -> AACGM Magnetic
        mag_result = aacgmv2.convert_latlon(lat, lon, height, dtime, 'G2A')
        mlat, mlon = mag_result[0], mag_result[1]

        # 2. Conjugate flip: negate magnetic latitude, keep magnetic longitude
        conj_mlat = -mlat
        conj_mlon = mlon

        # 3. Convert AACGM Magnetic -> Geographic
        geo_result = aacgmv2.convert_latlon(conj_mlat, conj_mlon, height, dtime, 'A2G')

        return geo_result[0], geo_result[1]
    except Exception as e:
        return f"Error: {e}", None

print("Magnetic Conjugate Point Calculator")
print("Enter coordinates as 'lat lon' (e.g. -30.3 -70.7). Type 'quit' to exit.\n")

while True:
    raw = input("Enter lat lon: ").strip()
    if raw.lower() in ("quit", "exit", "q"):
        break
    try:
        lat, lon = map(float, raw.split())
    except ValueError:
        print("  Invalid input. Please enter two numbers separated by a space.\n")
        continue

    c_lat, c_lon = get_conjugate_point(lat, lon)

    if c_lon is not None:
        print(f"  Input:     ({lat:.4f}, {lon:.4f})")
        print(f"  Conjugate: ({c_lat:.4f}, {c_lon:.4f})\n")
    else:
        print(f"  {c_lat}\n")
