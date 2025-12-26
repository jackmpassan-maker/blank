import math

# --------------------
# Timing multipliers
# --------------------
TIMING_MULTIPLIERS = {
    "12AM-3AM": 1.05,
    "3AM-6AM": 1.20,
    "6AM-9AM": 1.40,
    "9AM-12PM": 0.90,
    "12PM-3PM": 1.00,
    "3PM-6PM": 1.30,
    "6PM-9PM": 0.75,
    "9PM-12AM": 0.85,
}

# --------------------
# Regional multipliers
# --------------------
REGION_MULT = {
    "urban": 0.8,
    "suburban": 1.00,
    "rural": 1.3,
}

# --------------------
# School type multipliers
# --------------------
SCHOOL_MULT = {
    "public": 1.10,
    "charter": 1.05,
    "private": 0.90,
}

# --------------------
# Temperature & wind tables
# --------------------
TEMP_MULT = [
    (15, 1.10),
    (25, 1.20),
    (30, 1.15),
    (32, 1.00),
    (34, 0.75),
    (36, 0.40),
    (100, 0.20),
]

WIND_MULT = [
    (10, 1.00),
    (15, 1.05),
    (20, 1.15),
    (25, 1.30),
    (30, 1.50),
    (100, 1.80),
]


def get_multiplier(value, table):
    for limit, mult in table:
        if value <= limit:
            return mult
    return 1.0


# =========================================================
# MAIN SNOWSCORE FUNCTION (YOUR REAL FORMULA)
# =========================================================
def calculate_snowscore(
    snow,
    freezing_rain,
    sleet,
    avg_annual_snow,
    region,
    school_type,
    temp_f,
    wind_mph,
    prev_snow_days,
    peak_windows,
):
    # Base equivalents
    snow_eq = snow
    ice_eq = 4.0 * (freezing_rain / 0.10) ** 0.7 if freezing_rain > 0 else 0
    sleet_eq = 1.4 * (sleet / 0.10) ** 0.7 if sleet > 0 else 0

    total_eq = snow_eq + ice_eq + sleet_eq

    if total_eq <= 0:
        return 0.0

    # Normalize by climatology
    base = total_eq / math.sqrt(avg_annual_snow + 1)
    snowscore = base * 30

    # Apply multipliers
    snowscore *= REGION_MULT.get(region.lower(), 1.0)
    snowscore *= SCHOOL_MULT.get(school_type.lower(), 1.0)
    snowscore *= get_multiplier(temp_f, TEMP_MULT)
    snowscore *= get_multiplier(wind_mph, WIND_MULT)

    # Timing windows (stackable)
    for w in peak_windows:
        snowscore *= TIMING_MULTIPLIERS.get(w, 1.0)

    # Previous snow days penalty
    snowscore -= prev_snow_days

    return round(snowscore, 1)


# =========================================================
# DECISION LOGIC (FIXED, EXHAUSTIVE)
# =========================================================
def determine_decision(score, peak_window):
    """
    Returns (decision, explanation)
    """

    # 0–25
    if score <= 25:
        return (
            "School ON",
            "SnowScore is low (0–25). Conditions are manageable for normal operations."
        )

    # 26–34
    if 26 <= score <= 34:
        if peak_window == "6AM–9AM":
            return (
                "Late Start",
                "Moderate impacts during the morning commute window (6–9 AM)."
            )
        else:
            return (
                "School ON",
                "Moderate impacts occur outside critical school hours."
            )

    # 35–44
    if 35 <= score <= 44:
        if peak_window == "3AM–9AM":
            return (
                "Late Start",
                "Significant overnight to morning impacts affecting buses and roads."
            )
        elif peak_window == "12PM–6PM":
            return (
                "Early Dismissal",
                "Impacts peak during the afternoon dismissal window."
            )
        else:
            return (
                "School ON",
                "Impacts occur outside major school operation windows."
            )

    # 45–50
    if 45 <= score <= 50:
        if peak_window == "6PM–3AM":
            return (
                "Late Start",
                "Severe overnight impacts may allow cleanup before morning."
            )
        elif peak_window == "3AM–9AM":
            return (
                "Cancel School",
                "Severe impacts coincide with morning commute hours."
            )
        elif peak_window == "12PM–6PM":
            return (
                "Early Dismissal",
                "Severe impacts peak during afternoon dismissal."
            )

    # 51+
    return (
        "Cancel School",
        "Extreme SnowScore (51+) indicates unsafe conditions throughout the day."
    )


