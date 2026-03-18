# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Cardiac risk calculation and assessment tools.

Implements simplified ASCVD 10-year risk estimation and risk factor assessment
for early identification of cardiac risk. Not a substitute for clinical decision-making.
"""

import math
from typing import Literal


def calculate_ascvd_risk(
    age_years: int,
    sex: Literal["male", "female", "other"],
    total_cholesterol_mg_dl: float,
    hdl_cholesterol_mg_dl: float,
    systolic_bp_mmhg: float,
    on_bp_medication: bool,
    current_smoker: bool,
    has_diabetes: bool,
) -> dict:
    """
    Estimate 10-year risk of atherosclerotic cardiovascular disease (ASCVD) using
    a simplified Pooled Cohort Equations-style model for early risk stratification.

    Use this when the user provides demographics and key risk factors (age, sex,lipids, blood pressure, smoking, diabetes) to get a numeric risk estimate
    and risk category.

    Args:
        age_years: Age in years (typically 40-79 for standard calculators).
        sex: Biological sex for risk equations.
        total_cholesterol_mg_dl: Total cholesterol in mg/dL.
        hdl_cholesterol_mg_dl: HDL cholesterol in mg/dL.
        systolic_bp_mmhg: Systolic blood pressure in mmHg.
        on_bp_medication: True if on antihypertensive medication.
        current_smoker: True if current cigarette smoker.
        has_diabetes: True if diabetes (type 1 or 2).

    Returns:
        Dict with risk_percent_10y, risk_category, and brief interpretation.
    """
    # Simplified linear predictor (demonstration; real equations use full Pooled Cohort coefficients)
    ln_age = math.log(age_years)
    ln_tc = math.log(total_cholesterol_mg_dl)
    ln_hdl = math.log(hdl_cholesterol_mg_dl)
    ln_sbp = math.log(systolic_bp_mmhg) if systolic_bp_mmhg > 0 else 0

    # Approximate contribution of risk factors (simplified for demo)
    score = 0
    score += ln_age * 3.0
    score -= ln_hdl * 0.9
    score += ln_tc * 0.5
    score += ln_sbp * 0.4
    if sex == "male":
        score += 0.5
    if current_smoker:
        score += 0.7
    if has_diabetes:
        score += 0.6
    if on_bp_medication:
        score += 0.2

    # Map to approximate 10-year risk percentage (bounded 1-30% for demo)
    risk_pct = min(30.0, max(1.0, (1.0 / (1.0 + math.exp(-(score - 5.0))) * 35.0)))

    if risk_pct < 5.0:
        category = "low"
        interpretation = "10-year ASCVD risk is in the low range. Focus on preventive lifestyle and periodic reassessment."
    elif risk_pct < 7.5:
        category = "borderline"
        interpretation = "Borderline 10-year risk. Consider risk-enhancing factors and shared decision-making for statin."
    elif risk_pct < 20.0:
        category = "intermediate"
        interpretation = "Intermediate risk. Discuss risk enhancers, calcium scoring, and statin therapy per guidelines."
    else:
        category = "high"
        interpretation = "High 10-year ASCVD risk. Strong recommendation for lifestyle and statin therapy; consider cardiology referral."

    return {
        "risk_percent_10y": round(risk_pct, 1),
        "risk_category": category,
        "interpretation": interpretation,
        "disclaimer": "Estimate for stratification only; not a substitute for clinical judgment or full ASCVD calculator.",
    }


def assess_risk_factors(
    age: int,
    bmi: float | None,
    systolic_bp: float | None,
    diastolic_bp: float | None,
    total_cholesterol: float | None,
    hdl_cholesterol: float | None,
    ldl_cholesterol: float | None,
    fasting_glucose: float | None,
    hba1c_percent: float | None,
    current_smoker: bool = False,
    family_history_chd: bool = False,
    sedentary: bool = False,
) -> dict:
    """
    Assess cardiovascular risk factors from available data and flag modifiable vs
    non-modifiable factors for early intervention.

    Call this when the user provides vitals, labs, or lifestyle information to
    get a structured list of risk factors and actionable recommendations.

    Args:
        age: Age in years.
        bmi: Body mass index (kg/m^2) if known.
        systolic_bp: Systolic BP mmHg if known.
        diastolic_bp: Diastolic BP mmHg if known.
        total_cholesterol: Total cholesterol mg/dL if known.
        hdl_cholesterol: HDL cholesterol mg/dL if known.
        ldl_cholesterol: LDL cholesterol mg/dL if known.
        fasting_glucose: Fasting glucose mg/dL if known.
        hba1c_percent: HbA1c % if known.
        current_smoker: Whether the patient currently smokes.
        family_history_chd: Family history of premature CHD.
        sedentary: Sedentary lifestyle (little/no regular exercise).

    Returns:
        Dict with risk_factors, modifiable_factors, non_modifiable_factors, and recommendations.
    """
    risk_factors = []
    modifiable = []
    non_modifiable = []

    if age >= 55:
        risk_factors.append("Age ≥55 (cardiovascular risk increases with age)")
        non_modifiable.append("Age")
    elif age >= 45:
        risk_factors.append("Age 45–54 (cardiovascular risk increases with age)")
        non_modifiable.append("Age")

    if bmi is not None:
        if bmi >= 30:
            risk_factors.append(f"BMI {bmi:.1f} (obesity)")
            modifiable.append("Obesity / weight")
        elif bmi >= 25:
            risk_factors.append(f"BMI {bmi:.1f} (overweight)")
            modifiable.append("Overweight")

    if systolic_bp is not None:
        if systolic_bp >= 140:
            risk_factors.append(f"Elevated systolic BP ({systolic_bp:.0f} mmHg)")
            modifiable.append("Blood pressure")
        elif systolic_bp >= 130:
            risk_factors.append(f"Borderline elevated systolic BP ({systolic_bp:.0f} mmHg)")
            modifiable.append("Blood pressure")

    if diastolic_bp is not None and diastolic_bp >= 90:
        risk_factors.append(f"Elevated diastolic BP ({diastolic_bp:.0f} mmHg)")
        if "Blood pressure" not in modifiable:
            modifiable.append("Blood pressure")

    if ldl_cholesterol is not None:
        if ldl_cholesterol >= 190:
            risk_factors.append(f"Very high LDL ({ldl_cholesterol:.0f} mg/dL)")
            modifiable.append("LDL cholesterol")
        elif ldl_cholesterol >= 160:
            risk_factors.append(f"High LDL ({ldl_cholesterol:.0f} mg/dL)")
            modifiable.append("LDL cholesterol")
        elif ldl_cholesterol >= 100:
            risk_factors.append(f"Borderline-high LDL ({ldl_cholesterol:.0f} mg/dL)")
            modifiable.append("LDL cholesterol")

    if hdl_cholesterol is not None and hdl_cholesterol < 40:
        risk_factors.append(f"Low HDL ({hdl_cholesterol:.0f} mg/dL)")
        modifiable.append("HDL (exercise, weight, diet)")

    if fasting_glucose is not None and fasting_glucose >= 126:
        risk_factors.append(f"Elevated fasting glucose ({fasting_glucose:.0f} mg/dL) — possible diabetes")
        modifiable.append("Glycemic control")
    elif hba1c_percent is not None and hba1c_percent >= 6.5:
        risk_factors.append(f"HbA1c in diabetic range ({hba1c_percent:.1f}%)")
        modifiable.append("Glycemic control")

    if current_smoker:
        risk_factors.append("Current smoking")
        modifiable.append("Smoking cessation")

    if family_history_chd:
        risk_factors.append("Family history of premature CHD")
        non_modifiable.append("Family history")

    if sedentary:
        risk_factors.append("Sedentary lifestyle")
        modifiable.append("Physical activity")

    recommendations = []
    if modifiable:
        recommendations.append("Prioritize modifiable factors: " + ", ".join(modifiable))
    if "Blood pressure" in modifiable:
        recommendations.append("Lifestyle (DASH diet, sodium, exercise) and consider BP recheck; treat per guidelines if persistently elevated.")
    if "LDL cholesterol" in modifiable or "HDL" in modifiable:
        recommendations.append("Cardiovascular diet, exercise, and consider lipid panel follow-up; statin per ASCVD risk.")
    if "Smoking cessation" in modifiable:
        recommendations.append("Strong recommendation for smoking cessation; offer counseling and pharmacotherapy.")
    if not risk_factors:
        recommendations.append("Limited data provided; encourage routine screening (BP, lipids, glucose) per guidelines for early detection.")

    return {
        "risk_factors": risk_factors,
        "modifiable_factors": list(dict.fromkeys(modifiable)),
        "non_modifiable_factors": list(dict.fromkeys(non_modifiable)),
        "recommendations": recommendations,
    }


def interpret_lab_trends(
    metric_name: str,
    current_value: float,
    prior_value: float,
    unit: str,
    lower_is_better: bool,
) -> dict:
    """
    Compare current vs prior lab value to flag worsening or improving trends for
    early detection of cardiac risk progression.

    Use when the user provides serial lab results (e.g., LDL, HbA1c, BP) to
    identify trend direction and suggest follow-up.

    Args:
        metric_name: Name of the lab or vital (e.g., LDL cholesterol, HbA1c, systolic BP).
        current_value: Most recent value.
        prior_value: Previous value for comparison.
        unit: Unit of measure (e.g., mg/dL, %, mmHg).
        lower_is_better: True if lower values are better (e.g., LDL, BP); False for HDL.

    Returns:
        Dict with trend direction, percent change, and brief clinical note.
    """
    if prior_value == 0:
        return {
            "trend": "unknown",
            "percent_change": None,
            "clinical_note": "Prior value is zero; cannot compute trend.",
        }

    pct_change = ((current_value - prior_value) / prior_value) * 100.0

    if lower_is_better:
        if current_value < prior_value:
            trend = "improving"
            note = f"{metric_name} improved; reinforce current management."
        elif current_value > prior_value:
            trend = "worsening"
            note = f"{metric_name} increased; consider intensifying therapy or reassessing adherence."
        else:
            trend = "stable"
            note = f"{metric_name} unchanged."
    else:
        if current_value > prior_value:
            trend = "improving"
            note = f"{metric_name} increased (desired); encourage continuation."
        elif current_value < prior_value:
            trend = "worsening"
            note = f"{metric_name} decreased; review causes if unintended."
        else:
            trend = "stable"
            note = f"{metric_name} unchanged."

    return {
        "metric": metric_name,
        "current_value": current_value,
        "prior_value": prior_value,
        "unit": unit,
        "trend": trend,
        "percent_change": round(pct_change, 1),
        "clinical_note": note,
    }
