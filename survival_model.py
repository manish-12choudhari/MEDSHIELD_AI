from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.linear_model import LogisticRegression


Severity = Literal["Critical", "Moderate", "Low"]


def severity_to_numeric(severity: Severity) -> int:
    # Higher number => higher severity
    return {"Low": 0, "Moderate": 1, "Critical": 2}[severity]


@dataclass(frozen=True)
class SurvivalPrediction:
    survival_probability: float


class SurvivalModel:
    """
    Tiny logistic regression model.

    Trained on synthetic data so the project runs out-of-the-box.
    """

    def __init__(self) -> None:
        self.model = LogisticRegression(max_iter=1000)
        self._fit_synthetic()

    def _fit_synthetic(self) -> None:
        rng = np.random.default_rng(42)

        n = 4000
        severity = rng.integers(0, 3, size=n)  # 0..2
        delay_min = rng.uniform(0, 180, size=n)  # 0..180 minutes

        # Generate a plausible survival signal:
        # - Critical reduces survival heavily
        # - More delay reduces survival
        logits = 2.2 - 1.7 * severity - 0.018 * delay_min
        p = 1.0 / (1.0 + np.exp(-logits))
        y = rng.binomial(1, p, size=n)

        X = np.column_stack([severity, delay_min])
        self.model.fit(X, y)

    def predict(self, severity: Severity, delay_minutes: float) -> SurvivalPrediction:
        delay = float(max(0.0, delay_minutes))
        sev = float(severity_to_numeric(severity))
        X = np.array([[sev, delay]], dtype=float)
        prob = float(self.model.predict_proba(X)[0, 1])
        return SurvivalPrediction(survival_probability=round(prob, 4))

