from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal

from groq import Groq


Severity = Literal["Critical", "Moderate", "Low"]


@dataclass(frozen=True)
class TriageResult:
    severity: Severity
    confidence: float
    reason: str
    used_llm: bool


SYSTEM_PROMPT = """You are MedShield AI, an emergency triage classifier.
Classify the user's description into exactly one severity label:
- Critical: life-threatening, airway/breathing/circulation compromised, severe trauma, unconsciousness, stroke/heart attack signs, severe bleeding, seizures, etc.
- Moderate: needs urgent care but not immediately life-threatening (fever with dehydration, moderate bleeding controlled, fracture pain stable, asthma mild/moderate, etc.)
- Low: minor issues (mild pain, small cuts, mild cold symptoms, etc.)

Return ONLY valid JSON with this exact schema:
{
  "severity": "Critical|Moderate|Low",
  "confidence": 0.0-1.0,
  "reason": "short reason"
}

No extra keys. No markdown. No commentary.
"""


def _rule_based_triage(text: str) -> TriageResult:
    t = (text or "").lower()

    critical_terms = [
        "unconscious",
        "not breathing",
        "no pulse",
        "heavy bleeding",
        "severe bleeding",
        "chest pain",
        "stroke",
        "seizure",
        "fits",
        "gunshot",
        "stab",
        "road accident",
        "crash",
        "burns",
        "heart attack",
        "blue lips",
    ]
    moderate_terms = [
        "fracture",
        "broken",
        "moderate bleeding",
        "high fever",
        "vomiting",
        "dehydration",
        "asthma",
        "wheezing",
        "severe pain",
        "difficulty breathing",
    ]

    if any(k in t for k in critical_terms):
        return TriageResult(
            severity="Critical",
            confidence=0.78,
            reason="High-risk symptoms detected from description",
            used_llm=False,
        )
    if any(k in t for k in moderate_terms):
        return TriageResult(
            severity="Moderate",
            confidence=0.7,
            reason="Urgent symptoms detected from description",
            used_llm=False,
        )
    return TriageResult(
        severity="Low",
        confidence=0.62,
        reason="No life-threatening indicators detected",
        used_llm=False,
    )


def triage_with_groq(
    text: str,
    model: str = "llama-3.1-8b-instant",
    timeout_s: float = 12.0,
) -> TriageResult:
    """
    Uses Groq LLM when GROQ_API_KEY is set; otherwise falls back to rules.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _rule_based_triage(text)

    client = Groq(api_key=api_key)
    user_prompt = f"User emergency description:\n{text}\n"

    try:
        chat = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=200,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            # groq python client supports request timeout via underlying httpx
            timeout=timeout_s,
        )
        content = (chat.choices[0].message.content or "").strip()
        data = json.loads(content)

        severity = data.get("severity")
        confidence = float(data.get("confidence"))
        reason = str(data.get("reason"))

        if severity not in ("Critical", "Moderate", "Low"):
            raise ValueError("Invalid severity from model")

        confidence = max(0.0, min(1.0, confidence))
        if not reason:
            reason = "Model classified the case based on provided symptoms"

        return TriageResult(
            severity=severity, confidence=round(confidence, 4), reason=reason, used_llm=True
        )
    except Exception:
        # If anything goes wrong (bad JSON / timeout / API error), still return a usable result.
        return _rule_based_triage(text)

