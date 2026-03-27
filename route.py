from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True)
class RouteInfo:
    distance_km: float
    eta_minutes: int


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two coordinates.

    Returns kilometers.
    """
    r = 6371.0  # Earth radius (km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    lat1r = radians(lat1)
    lat2r = radians(lat2)

    a = sin(dlat / 2) ** 2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return r * c


def estimate_eta_minutes(distance_km: float, avg_speed_kmph: float = 40.0) -> int:
    """
    Simple travel-time simulation (no external map API).
    """
    if avg_speed_kmph <= 0:
        avg_speed_kmph = 40.0
    hours = distance_km / avg_speed_kmph
    return max(1, int(round(hours * 60)))


def compute_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    avg_speed_kmph: float = 40.0,
) -> RouteInfo:
    distance = haversine_km(origin_lat, origin_lon, dest_lat, dest_lon)
    eta = estimate_eta_minutes(distance, avg_speed_kmph=avg_speed_kmph)
    return RouteInfo(distance_km=round(distance, 2), eta_minutes=eta)

