from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.route import compute_route


Severity = Literal["Critical", "Moderate", "Low"]


@dataclass(frozen=True)
class Hospital:
    id: str
    name: str
    city: str
    lat: float
    lon: float
    icu_beds_available: int
    oxygen_available: bool
    doctors_available: int
    trauma_center: bool


@dataclass(frozen=True)
class RankedHospital:
    hospital: Hospital
    score: float
    distance_km: float
    eta_minutes: int
    why_selected: list[str]


def load_hospitals(data_path: str | Path) -> list[Hospital]:
    p = Path(data_path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    hospitals: list[Hospital] = []
    for r in raw:
        hospitals.append(
            Hospital(
                id=r["id"],
                name=r["name"],
                city=r.get("city", ""),
                lat=float(r["location"]["lat"]),
                lon=float(r["location"]["lon"]),
                icu_beds_available=int(r["icu_beds_available"]),
                oxygen_available=bool(r["oxygen_available"]),
                doctors_available=int(r["doctors_available"]),
                trauma_center=bool(r.get("trauma_center", False)),
            )
        )
    return hospitals


def _requirements_for_severity(severity: Severity) -> dict[str, object]:
    if severity == "Critical":
        return {"needs_icu": True, "needs_oxygen": True, "min_doctors": 6}
    if severity == "Moderate":
        return {"needs_icu": False, "needs_oxygen": True, "min_doctors": 3}
    return {"needs_icu": False, "needs_oxygen": False, "min_doctors": 1}


def _eligible(h: Hospital, severity: Severity) -> tuple[bool, list[str]]:
    req = _requirements_for_severity(severity)
    why: list[str] = []

    if bool(req["needs_icu"]):
        if h.icu_beds_available <= 0:
            return False, ["No ICU beds available"]
        why.append(f"ICU beds available: {h.icu_beds_available}")

    if bool(req["needs_oxygen"]):
        if not h.oxygen_available:
            return False, ["Oxygen not available"]
        why.append("Oxygen available")

    min_docs = int(req["min_doctors"])
    if h.doctors_available < min_docs:
        return False, [f"Not enough doctors (need ≥{min_docs})"]
    why.append(f"Doctors available: {h.doctors_available}")

    if severity == "Critical" and h.trauma_center:
        why.append("Trauma center support")

    return True, why


def score_hospital(
    h: Hospital, severity: Severity, patient_lat: float, patient_lon: float
) -> RankedHospital | None:
    ok, reasons = _eligible(h, severity)
    if not ok:
        return None

    route = compute_route(patient_lat, patient_lon, h.lat, h.lon, avg_speed_kmph=40.0)

    # Scoring: higher is better.
    # - penalize ETA strongly for Critical
    # - reward ICU beds and doctors, and trauma center for Critical
    eta_penalty = route.eta_minutes * (2.5 if severity == "Critical" else 1.3)
    distance_penalty = route.distance_km * 0.8
    icu_reward = h.icu_beds_available * (12.0 if severity == "Critical" else 5.0)
    doctor_reward = h.doctors_available * (2.4 if severity == "Critical" else 1.6)
    trauma_reward = 18.0 if (severity == "Critical" and h.trauma_center) else 0.0

    score = (icu_reward + doctor_reward + trauma_reward) - (eta_penalty + distance_penalty)

    why_selected = [
        *reasons,
        f"Estimated ETA: {route.eta_minutes} min",
        f"Distance: {route.distance_km} km",
    ]

    return RankedHospital(
        hospital=h,
        score=round(float(score), 3),
        distance_km=route.distance_km,
        eta_minutes=route.eta_minutes,
        why_selected=why_selected,
    )


def rank_hospitals(
    hospitals: list[Hospital], severity: Severity, patient_lat: float, patient_lon: float
) -> list[RankedHospital]:
    ranked: list[RankedHospital] = []
    for h in hospitals:
        rh = score_hospital(h, severity, patient_lat, patient_lon)
        if rh is not None:
            ranked.append(rh)

    ranked.sort(key=lambda r: (r.score,), reverse=True)
    return ranked

