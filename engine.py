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
    "urban": 0.9,
    "suburban": 1.00,
    "rural": 1.25,
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
    (34, 0.8),
    (36, 0.5),
    (1000, 0.25),
]

WIND_MULT = [
    (10, 1.00),
    (15, 1.05),
    (20, 1.15),
    (25, 1.30),
    (30, 1.50),
    (1000, 1.80),
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

    # Normalize by climatology (reduced suppression for high-snow regions)
    base = total_eq / (avg_annual_snow + 1) ** 0.4
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
    snowscore -= prev_snow_days * 1.5

    return round(snowscore, 1)


# =========================================================
# DECISION LOGIC (FIXED, EXHAUSTIVE)
# =========================================================
def determine_decision(snowscore, peak_windows):
    # 0–25
    if snowscore <= 25:
        return "School ON"

    # 26–34
    if snowscore <= 34:
        if "6AM-9AM" in peak_windows and "9AM-12PM" not in peak_windows:
            return "Late Start"
        return "School ON"

    # 35–43
    if snowscore <= 43:
        if any(w in peak_windows for w in ["3AM-6AM", "6AM-9AM"]):
            return "Late Start"
        if any(w in peak_windows for w in ["12PM-3PM", "3PM-6PM"]):
            return "Early Dismissal"
        return "School ON"

    # 44–50
    if snowscore <= 50:
        if any(w in peak_windows for w in ["3AM-6AM", "6AM-9AM", "9AM-12PM", "12AM-3AM"]):
            return "Cancel"
        if any(w in peak_windows for w in ["6PM-9PM", "9PM-12AM"]):
            return "Late Start"
        if any(w in peak_windows for w in ["12PM-3PM", "3PM-6PM"]):
            return "Early Dismissal"
        return "Cancel"

    # 50+
    return "Cancel"


# =========================================================
# RECOVERY SCORE FUNCTIONS (ALL OPTIONAL)
# =========================================================
def snowscore_recovery_contribution(snowscore: float | None) -> float:
    """Contribution from current storm SnowScore. Optional."""
    if snowscore is None or snowscore < 20:
        return 0.0
    return ((int(snowscore) // 10) - 1) * 0.75


def time_gap_contribution(hours_until_next_storm: float | None) -> int:
    if hours_until_next_storm is None:
        return 0
    if hours_until_next_storm > 72:
        return 0
    elif hours_until_next_storm > 48:
        return 1
    elif hours_until_next_storm > 24:
        return 2
    else:
        return 3


def next_storm_contribution(next_snowscore: float | None) -> int:
    if next_snowscore is None:
        return 0
    if next_snowscore < 15: 
        return 0
    elif next_snowscore < 25:
        return 1
    elif next_snowscore < 35:
        return 2
    elif next_snowscore < 45:
        return 3
    elif next_snowscore < 55:
        return 4
    else:
        return 5


def future_temp_contribution(high_temp_f: float | None) -> int:
    if high_temp_f is None:
        return 0
    if high_temp_f >= 38:
        return 0
    elif high_temp_f >= 34:
        return 1
    elif high_temp_f >= 30:
        return 2
    elif high_temp_f >= 25:
        return 3
    else:
        return 4


def calculate_recovery_score(
    current_storm_snowscore: float | None = None,
    hours_until_next_storm: float | None = None,
    next_snowscore: float | None = None,
    future_high_temp_f: float | None = None,
) -> float:
    """Calculate total recovery score from optional inputs."""
    score = 0.0
    score += snowscore_recovery_contribution(current_storm_snowscore)
    score += time_gap_contribution(hours_until_next_storm)
    score += next_storm_contribution(next_snowscore)
    score += future_temp_contribution(future_high_temp_f)
    return round(score, 2)


def interpret_recovery_score(score: float) -> str:
    if score <= 0:
        return "No inputs provided"
    if score <= 3:
        return "Normal recovery expected"
    elif score <= 6:
        return "Slight risk of future cancellations"
    elif score <= 9:
        return "Elevated risk of additional snow day"
    else:
        return "High likelihood of extended closures"

