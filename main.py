from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.hospital import load_hospitals, rank_hospitals
from backend.route import compute_route
from backend.survival_model import SurvivalModel
from backend.triage import triage_with_groq


Severity = Literal["Critical", "Moderate", "Low"]


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "hospitals.json"

app = FastAPI(
    title="MedShield AI",
    version="1.0.0",
    description="Real-time emergency triage & hospital allocation demo (Groq + FastAPI).",
)

hospitals = load_hospitals(DATA_PATH)
survival_model = SurvivalModel()


class TriageRequest(BaseModel):
    text: str = Field(..., description="Emergency description from patient/bystander")
    voice_placeholder: str | None = Field(
        default=None,
        description="Optional placeholder (e.g., voice transcript id). Not used in this demo.",
    )
    model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model name (e.g., llama-3.1-8b-instant, mixtral-8x7b-32768)",
    )


class TriageResponse(BaseModel):
    severity: Severity
    confidence: float
    reason: str
    used_llm: bool


class AllocateRequest(BaseModel):
    severity: Severity
    patient_lat: float = Field(..., ge=-90, le=90)
    patient_lon: float = Field(..., ge=-180, le=180)
    top_k: int = Field(default=5, ge=1, le=20)


class HospitalOut(BaseModel):
    id: str
    name: str
    city: str
    lat: float
    lon: float
    icu_beds_available: int
    oxygen_available: bool
    doctors_available: int
    trauma_center: bool


class RankedHospitalOut(BaseModel):
    hospital: HospitalOut
    score: float
    distance_km: float
    eta_minutes: int
    why_selected: list[str]


class AllocateResponse(BaseModel):
    selected: RankedHospitalOut
    ranked: list[RankedHospitalOut]
    note: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest) -> TriageResponse:
    res = triage_with_groq(text=req.text, model=req.model)
    return TriageResponse(
        severity=res.severity,
        confidence=res.confidence,
        reason=res.reason,
        used_llm=res.used_llm,
    )


@app.post("/allocate-hospital", response_model=AllocateResponse)
def allocate_hospital(req: AllocateRequest) -> AllocateResponse:
    ranked = rank_hospitals(
        hospitals=hospitals,
        severity=req.severity,
        patient_lat=req.patient_lat,
        patient_lon=req.patient_lon,
    )
    if not ranked:
        raise HTTPException(
            status_code=404,
            detail="No hospitals meet the minimum requirements for this severity.",
        )

    top = ranked[: req.top_k]
    selected = top[0]

    def to_out(rh) -> RankedHospitalOut:
        h = rh.hospital
        return RankedHospitalOut(
            hospital=HospitalOut(
                id=h.id,
                name=h.name,
                city=h.city,
                lat=h.lat,
                lon=h.lon,
                icu_beds_available=h.icu_beds_available,
                oxygen_available=h.oxygen_available,
                doctors_available=h.doctors_available,
                trauma_center=h.trauma_center,
            ),
            score=rh.score,
            distance_km=rh.distance_km,
            eta_minutes=rh.eta_minutes,
            why_selected=rh.why_selected,
        )

    return AllocateResponse(
        selected=to_out(selected),
        ranked=[to_out(r) for r in top],
        note="Ranking considers capability + capacity + ETA (not only nearest).",
    )


@app.get("/route")
def route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    avg_speed_kmph: float = 40.0,
) -> dict[str, float | int]:
    info = compute_route(origin_lat, origin_lon, dest_lat, dest_lon, avg_speed_kmph)
    return {"distance_km": info.distance_km, "eta_minutes": info.eta_minutes}


@app.get("/predict-survival")
def predict_survival(severity: Severity, delay_minutes: float) -> dict[str, float | str]:
    pred = survival_model.predict(severity=severity, delay_minutes=delay_minutes)
    return {"severity": severity, "delay_minutes": float(delay_minutes), "survival_probability": pred.survival_probability}

