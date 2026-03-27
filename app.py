from __future__ import annotations

import os
from typing import Any, Literal

import httpx
import streamlit as st


Severity = Literal["Critical", "Moderate", "Low"]


def backend_base_url() -> str:
    # Allow overriding when deploying
    return os.getenv("MEDSHIELD_BACKEND_URL", "http://localhost:8000").rstrip("/")


def post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{backend_base_url()}{path}"
    with httpx.Client(timeout=20.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json()


def get_json(path: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{backend_base_url()}{path}"
    with httpx.Client(timeout=20.0) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def severity_color(sev: Severity) -> str:
    return {"Critical": "#d64545", "Moderate": "#f39c12", "Low": "#2ecc71"}[sev]


def main() -> None:
    st.set_page_config(page_title="MedShield AI", page_icon="🛡️", layout="wide")

    st.title("MedShield AI – Emergency Triage & Hospital Allocation")
    st.caption("FastAPI + Groq LLM triage + hospital ranking + route + survival prediction.")

    with st.sidebar:
        st.subheader("Patient location")
        st.caption("Defaults point to Hyderabad. Update for your scenario.")
        patient_lat = st.number_input("Latitude", value=17.3850, format="%.6f")
        patient_lon = st.number_input("Longitude", value=78.4867, format="%.6f")

        st.divider()
        st.subheader("LLM settings")
        model = st.selectbox(
            "Groq model",
            options=["llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            index=0,
        )
        st.caption(
            "Set `GROQ_API_KEY` for LLM triage. Without it, the backend uses a safe rules fallback."
        )

    st.subheader("Emergency description")
    text = st.text_area(
        "Describe the emergency (symptoms, condition, duration, etc.)",
        height=140,
        placeholder="Example: Unconscious after road accident, heavy bleeding from head, breathing irregular...",
    )

    col_a, col_b = st.columns([1, 3])
    with col_a:
        analyze = st.button("Analyze", type="primary", use_container_width=True)
    with col_b:
        st.caption("Tip: Start the backend first: `uvicorn backend.main:app --reload --port 8000`")

    if not analyze:
        return

    if not text.strip():
        st.warning("Please enter an emergency description.")
        return

    try:
        triage = post_json(
            "/triage",
            {"text": text, "voice_placeholder": None, "model": model},
        )
        severity: Severity = triage["severity"]
        confidence = float(triage["confidence"])
        reason = str(triage["reason"])
        used_llm = bool(triage.get("used_llm", False))

        allocation = post_json(
            "/allocate-hospital",
            {
                "severity": severity,
                "patient_lat": patient_lat,
                "patient_lon": patient_lon,
                "top_k": 5,
            },
        )
        selected = allocation["selected"]
        hosp = selected["hospital"]

        route = get_json(
            "/route",
            {
                "origin_lat": patient_lat,
                "origin_lon": patient_lon,
                "dest_lat": hosp["lat"],
                "dest_lon": hosp["lon"],
                "avg_speed_kmph": 40.0,
            },
        )

        delay_minutes = float(route["eta_minutes"])
        survival = get_json(
            "/predict-survival",
            {"severity": severity, "delay_minutes": delay_minutes},
        )
        survival_prob = float(survival["survival_probability"])

    except httpx.HTTPError as e:
        st.error(
            "Backend request failed. Make sure FastAPI is running at "
            f"`{backend_base_url()}`.\n\n"
            f"Details: {e}"
        )
        return
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return

    # --- UI output
    sev_bg = severity_color(severity)

    st.divider()
    st.subheader("Triage result")
    st.markdown(
        f"""
<div style="padding: 14px; border-radius: 10px; background: {sev_bg}20; border: 1px solid {sev_bg}55;">
  <div style="font-size: 20px; font-weight: 700; color: {sev_bg};">Severity: {severity}</div>
  <div style="margin-top: 6px;"><b>Confidence</b>: {confidence:.2f} &nbsp; | &nbsp; <b>LLM used</b>: {used_llm}</div>
  <div style="margin-top: 6px;"><b>Reason</b>: {reason}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.subheader("Recommended hospital")
    st.write(
        {
            "Name": hosp["name"],
            "City": hosp["city"],
            "ICU beds available": hosp["icu_beds_available"],
            "Oxygen": hosp["oxygen_available"],
            "Doctors available": hosp["doctors_available"],
            "Trauma center": hosp["trauma_center"],
            "Score": selected["score"],
        }
    )

    with st.expander("Why this hospital was selected", expanded=True):
        for r in selected["why_selected"]:
            st.write(f"- {r}")
        st.caption(allocation.get("note", ""))

    st.subheader("Route (simulated)")
    st.write(
        {
            "Distance (km)": route["distance_km"],
            "Estimated travel time (min)": route["eta_minutes"],
        }
    )

    st.subheader("Survival prediction (demo model)")
    st.markdown(
        f"**Estimated survival probability:** `{survival_prob:.2%}` (given severity `{severity}` and ETA `{delay_minutes:.0f}` min)"
    )

    st.subheader("Top ranked hospitals")
    ranked = allocation["ranked"]
    st.dataframe(
        [
            {
                "Rank": i + 1,
                "Hospital": r["hospital"]["name"],
                "City": r["hospital"]["city"],
                "ETA (min)": r["eta_minutes"],
                "Distance (km)": r["distance_km"],
                "ICU": r["hospital"]["icu_beds_available"],
                "Doctors": r["hospital"]["doctors_available"],
                "Oxygen": r["hospital"]["oxygen_available"],
                "Trauma": r["hospital"]["trauma_center"],
                "Score": r["score"],
            }
            for i, r in enumerate(ranked)
        ],
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()

