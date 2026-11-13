"""Deterministic, land-safe coordinate obfuscation for public map data.

Private exact coordinates never leave the server. Whenever a profile or help
request is only allowed to publish an *approximate* position, the exact point is
passed through :func:`approximate_point`, which walks a deterministic sequence of
bearings and distances inside the requested kilometre band and returns the first
candidate that the offline `global-land-mask` dataset reports as land.

Determinism matters: the same record always resolves to the same public point, so
a pin never jitters between page loads, while the offset is large enough that the
real address cannot be inferred. When no land candidate exists inside the band
(mid-ocean, tiny island) the function returns ``None`` and the caller MUST omit
the coordinate rather than fall back to the exact point.

Exact coordinates are never written to logs.
"""

import reflex as rx

import functools
import hashlib
import importlib.metadata
import logging
import math
import threading
import zipfile
from typing import Protocol

EARTH_RADIUS_KM = 6371.0088

# Public offset bands, in kilometres.
PROFILE_BAND: tuple[float, float] = (0.5, 1.0)
POST_MEMBER_BAND: tuple[float, float] = (0.5, 1.0)
POST_GUEST_BAND: tuple[float, float] = (0.5, 1.0)

# 24 evenly spaced bearings x 4 distances = up to 96 land probes per record.
_BEARING_STEPS: tuple[int, ...] = tuple(range(0, 360, 15))
_DISTANCE_OFFSETS: tuple[float, ...] = (0.0, 0.37, 0.71, 0.5)


class _LandMask(Protocol):
    def is_land(self, lat: float, lon: float) -> bool: ...


class _PackedLandMask:
    """The original water mask, stored losslessly at one bit per grid cell."""

    def __init__(self) -> None:
        import numpy as np
        from numpy.lib import format as npy

        distribution = importlib.metadata.distribution("global-land-mask")
        archives = [
            distribution.locate_file(path)
            for path in distribution.files or ()
            if path.name == "globe_combined_mask_compressed.npz"
        ]
        if len(archives) != 1:
            raise ValueError("Offline land dataset is missing or ambiguous")
        with zipfile.ZipFile(archives[0]) as archive:
            with archive.open("lat.npy") as source:
                self._lat = npy.read_array(source, allow_pickle=False)
            with archive.open("lon.npy") as source:
                self._lon = npy.read_array(source, allow_pickle=False)
            with archive.open("mask.npy") as source:
                version = npy.read_magic(source)
                if version == (1, 0):
                    shape, fortran, dtype = npy.read_array_header_1_0(source)
                elif version == (2, 0):
                    shape, fortran, dtype = npy.read_array_header_2_0(source)
                else:
                    raise ValueError("Unsupported offline land dataset format")
                if (
                    dtype != np.dtype(bool)
                    or fortran
                    or shape != (len(self._lat), len(self._lon))
                    or len(self._lat) < 2
                    or len(self._lon) < 2
                ):
                    raise ValueError("Invalid offline land dataset grid")
                self._columns = shape[1]
                cells = math.prod(shape)
                self._bits = bytearray((cells + 7) // 8)
                # Never materialize the ~933 MB decompressed NumPy grid.
                chunk_cells = 1024 * 1024
                for offset in range(0, cells, chunk_cells):
                    count = min(chunk_cells, cells - offset)
                    raw = source.read(count)
                    if len(raw) != count:
                        raise ValueError("Truncated offline land dataset")
                    packed = np.packbits(np.frombuffer(raw, dtype=bool))
                    start = offset // 8
                    self._bits[start : start + len(packed)] = packed.tobytes()

    def is_land(self, lat: float, lon: float) -> bool:
        latitude = min(max(lat, float(self._lat.min())), float(self._lat.max()))
        longitude = min(
            max(lon, float(self._lon.min())), float(self._lon.max())
        )
        row = int((latitude - self._lat[0]) / (self._lat[1] - self._lat[0]))
        column = int((longitude - self._lon[0]) / (self._lon[1] - self._lon[0]))
        row = min(max(row, 0), len(self._lat) - 1)
        column = min(max(column, 0), len(self._lon) - 1)
        index = row * self._columns + column
        return not bool(self._bits[index // 8] & (1 << (7 - index % 8)))


_MASK_LOAD_LOCK = threading.Lock()


@functools.lru_cache(maxsize=1)
def _packed_globe() -> _LandMask:
    return _PackedLandMask()


def _globe() -> _LandMask:
    """Load once even when guest and member background workers race.

    Importing the package's globe module expands its compressed water mask to
    nearly a gigabyte. Deferring that import only moves the OOM from compilation
    to the first map request. Stream and pack the same cells instead, retaining
    about 117 MB with bounded decompression workspace and unchanged resolution.
    """
    with _MASK_LOAD_LOCK:
        return _packed_globe()


def clamp_latitude(latitude: float) -> float:
    """Keep a latitude inside the dataset's valid range."""
    return max(-89.9, min(89.9, float(latitude)))


def wrap_longitude(longitude: float) -> float:
    """Wrap a longitude into [-180, 180] instead of raising at the date line."""
    wrapped = (float(longitude) + 180.0) % 360.0 - 180.0
    return max(-180.0, min(180.0, wrapped))


def _destination(
    latitude: float, longitude: float, bearing_deg: float, distance_km: float
) -> tuple[float, float]:
    """Great-circle destination point from a start point, bearing and distance."""
    angular = max(distance_km, 0.0) / EARTH_RADIUS_KM
    lat1 = math.radians(clamp_latitude(latitude))
    lon1 = math.radians(wrap_longitude(longitude))
    bearing = math.radians(bearing_deg % 360.0)
    sin_lat2 = math.sin(lat1) * math.cos(angular) + math.cos(lat1) * math.sin(
        angular
    ) * math.cos(bearing)
    sin_lat2 = max(-1.0, min(1.0, sin_lat2))
    lat2 = math.asin(sin_lat2)
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angular) * math.cos(lat1),
        math.cos(angular) - math.sin(lat1) * sin_lat2,
    )
    return clamp_latitude(math.degrees(lat2)), wrap_longitude(
        math.degrees(lon2)
    )


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Measure the actual published point, including coordinate rounding."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    hav = (
        math.sin((phi2 - phi1) / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(max(0.0, min(1.0, hav))))


def is_land(latitude: float, longitude: float) -> bool:
    """Offline land check. Any dataset problem is treated as 'not land'."""
    try:
        return bool(
            _globe().is_land(
                clamp_latitude(latitude), wrap_longitude(longitude)
            )
        )
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Land mask lookup failed: {e}")
        return False


def approximate_point(
    record_id: int,
    salt: str,
    latitude: float | None,
    longitude: float | None,
    band: tuple[float, float],
) -> tuple[float, float] | None:
    """Return a deterministic land point ``band`` km away, or ``None``.

    Args:
        record_id: Stable identifier (profile id, help post id) so the offset is
            reproducible for that record.
        salt: Namespace so the same record yields different public points for
            different audiences (members vs. guests).
        latitude / longitude: The PRIVATE exact source coordinates.
        band: Inclusive (minimum, maximum) offset distance in kilometres.
    """
    if latitude is None or longitude is None:
        return None
    try:
        source_lat = float(latitude)
        source_lon = float(longitude)
        if not (math.isfinite(source_lat) and math.isfinite(source_lon)):
            return None
        if not (-90 <= source_lat <= 90 and -180 <= source_lon <= 180):
            return None
    except (TypeError, ValueError):
        return None

    low, high = float(band[0]), float(band[1])
    if high < low:
        low, high = high, low
    spread = max(high - low, 0.0)

    digest = hashlib.sha256(
        f"goandhelp-approx::{salt}::{int(record_id)}".encode()
    ).hexdigest()
    base_bearing = (int(digest[0:8], 16) % 3600) / 10.0
    base_fraction = (int(digest[8:16], 16) % 1000) / 1000.0

    for offset in _DISTANCE_OFFSETS:
        fraction = (base_fraction + offset) % 1.0
        distance = low + spread * fraction
        for step in _BEARING_STEPS:
            bearing = (base_bearing + step) % 360.0
            candidate_lat, candidate_lon = _destination(
                source_lat, source_lon, bearing, distance
            )
            public_lat, public_lon = (
                round(candidate_lat, 4),
                round(candidate_lon, 4),
            )
            if low <= _distance_km(
                source_lat, source_lon, public_lat, public_lon
            ) <= high and is_land(public_lat, public_lon):
                return public_lat, public_lon

    # No safe land point inside the band: withhold the coordinate entirely
    # rather than publish a sea pin or risk revealing the exact place. The
    # exact coordinates are deliberately not logged.
    logging.info(
        "No land-safe approximate point within %.1f-%.1f km for %s record %s; "
        "withholding the public coordinate.",
        low,
        high,
        salt,
        int(record_id),
    )
    return None


def profile_approximate(
    profile_subscriber_id: int,
    latitude: float | None,
    longitude: float | None,
) -> tuple[float, float] | None:
    """Public point for a member sharing an approximate profile location."""
    return approximate_point(
        profile_subscriber_id, "profile", latitude, longitude, PROFILE_BAND
    )


def post_member_approximate(
    post_id: int, latitude: float | None, longitude: float | None
) -> tuple[float, float] | None:
    """Public point shown to signed-in members for an approximate request."""
    return approximate_point(
        post_id, "post-member", latitude, longitude, POST_MEMBER_BAND
    )


def post_guest_approximate(
    post_id: int, latitude: float | None, longitude: float | None
) -> tuple[float, float] | None:
    """Separately salted, land-safe 0.5–1 km public point for guests."""
    return approximate_point(
        post_id, "post-guest", latitude, longitude, POST_GUEST_BAND
    )
