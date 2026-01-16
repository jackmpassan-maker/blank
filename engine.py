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


# --------------------
# WIND CHILL POINTS (REGION-SCALED)
# --------------------
def wind_chill_points(wind_chill_f: float, avg_annual_snow: float) -> float:
    """
    Convert a minimum wind chill into snow day points, scaled by region/climatology.
    """

    # Clamp average annual snow for scaling (0–100 in)
    avg_snow_clamped = max(0, min(avg_annual_snow, 100))
    region_factor = 1.2 - (avg_snow_clamped / 100) * 0.4  # 1.2 -> 0.8

    # Determine bucket
    if wind_chill_f > 0:
        base_points = 0
    elif -10 <= wind_chill_f <= 0:
        base_points = 6
    elif -20 <= wind_chill_f < -10:
        base_points = 15
    elif -30 <= wind_chill_f < -20:
        base_points = 25
    else:  # < -30
        base_points = 40

    # Apply region factor
    points = base_points * region_factor

    return points


# =========================================================
# MAIN SNOWSCORE FUNCTION
# =========================================================
def calculate_snowscore(
    snow: float,
    freezing_rain: float,
    sleet: float,
    avg_annual_snow: float,
    region: str,
    school_type: str,
    temp_f: float,
    wind_mph: float,
    prev_snow_days: int,
    peak_windows: list[str],
    wind_chill_f: float = 0.0
) -> float:

    # --- Step 1: Base snow/ice/sleet equivalents ---
    snow_eq = snow
    ice_eq = 4.0 * (freezing_rain / 0.10) ** 0.7 if freezing_rain > 0 else 0
    sleet_eq = 1.4 * (sleet / 0.10) ** 0.7 if sleet > 0 else 0
    total_eq = snow_eq + ice_eq + sleet_eq

    if total_eq <= 0:
        return 0.0

    # --- Step 2: Normalize by climatology ---
    base = total_eq / (avg_annual_snow + 1) ** 0.4
    snowscore = base * 30

    # --- Step 3: Apply multipliers ---
    snowscore *= REGION_MULT.get(region.lower(), 1.0)
    snowscore *= SCHOOL_MULT.get(school_type.lower(), 1.0)
    snowscore *= get_multiplier(temp_f, TEMP_MULT)
    snowscore *= get_multiplier(wind_mph, WIND_MULT)

    # --- Step 4: Apply peak intensity timing multipliers ---
    for w in peak_windows:
        snowscore *= TIMING_MULTIPLIERS.get(w, 1.0)

    # --- Step 5: Previous snow days penalty ---
    snowscore -= prev_snow_days * 1.5

    # --- Step 6: Add wind chill points AFTER all multipliers ---
    snowscore += wind_chill_points(wind_chill_f, avg_annual_snow)

    # --- Step 7: Round for presentation ---
    return round(snowscore, 1)


# =========================================================
# DECISION LOGIC
# =========================================================
def determine_decision(snowscore, peak_windows):
    if snowscore <= 25:
        return "School ON"
    if snowscore <= 34:
        if "6AM-9AM" in peak_windows and "9AM-12PM" not in peak_windows:
            return "Late Start"
        return "School ON"
    if snowscore <= 43:
        if any(w in peak_windows for w in ["3AM-6AM", "6AM-9AM"]):
            return "Late Start"
        if any(w in peak_windows for w in ["12PM-3PM", "3PM-6PM"]):
            return "Early Dismissal"
        return "School ON"
    if snowscore <= 50:
        if any(w in peak_windows for w in ["3AM-6AM", "6AM-9AM", "9AM-12PM", "12AM-3AM"]):
            return "Cancel"
        if any(w in peak_windows for w in ["6PM-9PM", "9PM-12AM"]):
            return "Late Start"
        if any(w in peak_windows for w in ["12PM-3PM", "3PM-6PM"]):
            return "Early Dismissal"
        return "Cancel"
    return "Cancel"


# =========================================================
# RECOVERY SCORE FUNCTIONS (OPTIONAL)
# =========================================================
def snowscore_recovery_contribution(snowscore: float | None) -> float:
    if snowscore is None or snowscore < 10:
        return 0.0
    return (int(snowscore) // 10) * 0.75

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


