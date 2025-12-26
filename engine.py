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
    peak_window must be one of:
    '12AM-3AM', '3AM-6AM', '6AM-9AM',
    '9AM-12PM', '12PM-3PM', '3PM-6PM',
    '6PM-9PM', '9PM-12AM'
    """

    # 0–25
    if score <= 25:
        return (
            "School ON",
            "SnowScore is low, indicating minimal winter weather impact. "
            "Road conditions and school operations are expected to remain manageable."
        )

    # -----------------------
    # 26–34
    # -----------------------
    if 26 <= score <= 34:
        if peak_window == "6AM-9AM":
            return (
                "Late Start",
                "SnowScore is in the lower-moderate range, with peak intensity occurring "
                "during the morning commute (6–9 AM). A late start reduces travel risk "
                "during the most hazardous period."
            )
        else:
            return (
                "School ON",
                "SnowScore is in the lower-moderate range, but peak intensity does not "
                "occur during critical travel hours. Normal operations are reasonable."
            )

    # -----------------------
    # 35–44
    # -----------------------
    if 35 <= score <= 44:
        if peak_window in ["3AM-6AM", "6AM-9AM"]:
            return (
                "Late Start",
                "SnowScore indicates moderate winter impacts with peak intensity "
                "occurring overnight or during the morning commute. A late start allows "
                "additional time for road treatment and safer travel."
            )
        elif peak_window in ["12PM-3PM", "3PM-6PM"]:
            return (
                "Early Dismissal",
                "SnowScore indicates moderate impacts with peak intensity expected "
                "during the afternoon. Early dismissal reduces exposure during worsening "
                "conditions later in the day."
            )
        else:
            return (
                "School ON",
                "SnowScore is moderate, but peak intensity falls outside critical "
                "travel windows. Normal operations are acceptable."
            )

    # -----------------------
    # 45–50
    # -----------------------
    if 45 <= score <= 50:
        if peak_window in ["6PM-9PM", "9PM-12AM", "12AM-3AM"]:
            return (
                "Late Start",
                "SnowScore is high-moderate with peak intensity occurring overnight. "
                "A late start allows crews additional time to improve road conditions "
                "before the morning commute."
            )
        elif peak_window in ["3AM-6AM", "6AM-9AM"]:
            return (
                "Cancel School",
                "SnowScore is high-moderate with peak intensity during the morning "
                "commute. Travel conditions are likely unsafe, making cancellation "
                "the safest option."
            )
        elif peak_window in ["12PM-3PM", "3PM-6PM"]:
            return (
                "Early Dismissal",
                "SnowScore is high-moderate with peak intensity expected in the afternoon. "
                "Early dismissal reduces travel risk as conditions deteriorate."
            )

    # -----------------------
    # 51+
    # -----------------------
    return (
        "Cancel School",
        "SnowScore is very high, indicating significant winter weather impacts. "
        "Road conditions and travel safety are likely compromised throughout the day."
    )



