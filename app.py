from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from engine import (
    calculate_snowscore,
    determine_decision,
    calculate_recovery_score,
    interpret_recovery_score
)

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Snow Day Calculator</title>
        <style>
            .optional-section {
                background: #e0f7ff;
                padding: 15px;
                border: 1px solid #66c2ff;
                margin-top: 20px;
                width: fit-content;
            }
        </style>
    </head>
    <body>
        <h1>Snow Day Calculator</h1>

        <form action="/calculate" method="post">
            <!-- Existing SnowScore Inputs -->
            <label>Snow Expected (inches):</label><br>
            <input type="number" step="0.1" name="snow" required><br><br>

            <label>Freezing Rain Expected (inches):</label><br>
            <input type="number" step="0.01" name="freezing_rain" value="0"><br><br>

            <label>Sleet Expected (inches):</label><br>
            <input type="number" step="0.01" name="sleet" value="0"><br><br>

            <label>Average Annual Snow (inches):</label><br>
            <input type="number" name="avg_annual_snow" required><br><br>

            <label>Average Temperature During Storm (°F):</label><br>
            <input type="number" name="temp_f" required><br><br>

            <label>Maximum Sustained Winds (mph):</label><br>
            <input type="number" name="wind_mph" required><br><br>

            <label>Minimum Wind Chill (°F):</label><br>
            <input type="number" name="wind_chill" step="1"><br><br>

            <label>Previous Snow Days:</label><br>
            <input type="number" name="prev_snow_days" value="0"><br><br>

            <label>Region:</label><br>
            <select name="region">
                <option value="urban">Urban</option>
                <option value="suburban" selected>Suburban</option>
                <option value="rural">Rural</option>
            </select><br><br>

            <label>School Type:</label><br>
            <select name="school_type">
                <option value="public" selected>Public</option>
                <option value="charter">Charter</option>
                <option value="private">Private</option>
            </select><br><br>

            <label>Peak Intensity Windows:</label><br>
            <input type="checkbox" name="peak_windows" value="12AM-3AM">12AM–3AM<br>
            <input type="checkbox" name="peak_windows" value="3AM-6AM">3AM–6AM<br>
            <input type="checkbox" name="peak_windows" value="6AM-9AM">6AM–9AM<br>
            <input type="checkbox" name="peak_windows" value="9AM-12PM">9AM–12PM<br>
            <input type="checkbox" name="peak_windows" value="12PM-3PM">12PM–3PM<br>
            <input type="checkbox" name="peak_windows" value="3PM-6PM">3PM–6PM<br>
            <input type="checkbox" name="peak_windows" value="6PM-9PM">6PM–9PM<br>
            <input type="checkbox" name="peak_windows" value="9PM-12AM">9PM–12AM<br><br>

            <!-- Recovery Score Optional Inputs -->
            <div class="optional-section">
                <h3>Recovery Score Inputs (Optional)</h3>
                <label>Current Storm SnowScore:</label><br>
                <input type="number" step="0.1" name="current_storm_snowscore"><br><br>

                <label>Hours Until Next Storm (only if there is a next storm):</label><br>
                <input type="number" step="0.1" name="hours_until_next_storm"><br><br>

                <label>Next Storm SnowScore (only if there is a next storm):</label><br>
                <input type="number" step="0.1" name="next_snowscore"><br><br>

                <label>High Temperature on Day of First Closure °F:</label><br>
                <input type="number" step="0.1" name="future_high_temp_f"><br><br>
            </div>

            <button type="submit">Calculate</button>
        </form>
    </body>
    </html>
    """


@app.post("/calculate", response_class=HTMLResponse)
def calculate(
    # SnowScore fields
    snow: float = Form(...),
    freezing_rain: float = Form(0),
    sleet: float = Form(0),
    avg_annual_snow: float = Form(...),
    region: str = Form(...),
    school_type: str = Form(...),
    temp_f: float = Form(...),
    wind_mph: float = Form(...),
    wind_chill: str = Form(""),  # <- keep as string for safe conversion
    prev_snow_days: int = Form(0),
    peak_windows: list[str] = Form([]),
    # Recovery Score optional fields
    current_storm_snowscore: float | None = Form(None),
    hours_until_next_storm: float | None = Form(None),
    next_snowscore: float | None = Form(None),
    future_high_temp_f: float | None = Form(None)
):
    # Safe conversion of wind_chill to float; blank defaults to 0
    try:
        wind_chill_f = float(wind_chill)
    except (ValueError, TypeError):
        wind_chill_f = 0.0

    # --- Calculate SnowScore ---
    snowscore = calculate_snowscore(
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
        wind_chill_f=wind_chill_f
    )

    decision = determine_decision(snowscore, peak_windows)

    # --- Recovery Score ---
    recovery_score = calculate_recovery_score(
        current_storm_snowscore,
        hours_until_next_storm,
        next_snowscore,
        future_high_temp_f
    )
    recovery_interpretation = interpret_recovery_score(recovery_score)

    # --- Explanation ---
    if snowscore <= 25:
        explanation = "Conditions are adequate to keep school open."
    elif snowscore <= 34:
        if "6AM-9AM" in peak_windows and "9AM-12PM" not in peak_windows:
            explanation = "While disruptions are relatively insignificant, peak intensity during the morning commute necessitates a late start."
        else:
            explanation = "While roads may be adversely affected, conditions remain manageable overall allowing school to stay open."
    elif snowscore <= 43:
        if ("3AM-6AM" in peak_windows or "6AM-9AM" in peak_windows) and "9AM-12PM" not in peak_windows:
            explanation = "Due to hazardous conditions during or directly before the morning commute, a late start is the best course of action."
        elif ("12PM-3PM" in peak_windows or "3PM-6PM" in peak_windows) and "9AM-12PM" not in peak_windows:
            explanation = "With subpar conditions later in the school day, an early dismissal makes the most sense."
        else:
            explanation = "While disruptions will be moderately impactful, timing dampens the danger enough for school to remain open."
    elif snowscore <= 50:
        if "6PM-9PM" in peak_windows or "9PM-12AM" in peak_windows:
            explanation = "While a considerably impactful event, fortunate timing only necessitates a late start."
        elif any(w in peak_windows for w in ["12AM-3AM","3AM-6AM","6AM-9AM","9AM-12PM"]):
            explanation = "Dangerous conditions overnight or during morning hours support cancellation."
        elif any(w in peak_windows for w in ["12PM-3PM","3PM-6PM"]):
            explanation = "Peak winter precipitation later in the school day supports early dismissal."
        else:
            explanation = "Overall conditions are too disruptive for safe operations."
    else:
        explanation = "Extreme winter conditions make school operations unsafe."

    return f"""
<html>
<head>
    <title>Result</title>
</head>
<body>

    <!-- SnowScore Rubric -->
    <h2>SnowScore Rubric:</h2>
    <div style="background:#f0f0f0; padding:10px; border:1px solid #ccc; margin-bottom:20px;">
        <div style="font-size:16px; margin-bottom:10px;">
            0–25: School ON<br>
            25–50: Consider Late Start / Early Dismissal / Cancellation<br>
            50+: Cancel School
        </div>
        <h3>SnowScore: {snowscore}</h3>
        <p><strong>Decision:</strong> {decision}</p>
        <p><strong>Explanation:</strong><br>{explanation}</p>
    </div>

    <!-- Recovery Score Rubric -->
    <h2>Recovery Score Rubric (Optional Inputs Only):</h2>
    <div style="background:#e0f7ff; padding:10px; border:1px solid #66c2ff; margin-bottom:20px;">
        <div style="font-size:16px; margin-bottom:10px;">
            0–3: Normal recovery expected<br>
            3–6: Slight risk of future cancellations<br>
            6–9: Elevated risk of additional snow day<br>
            9+: High likelihood of extended closures
        </div>
        <h3>Recovery Score: {recovery_score}</h3>
        <p><strong>Interpretation:</strong> {recovery_interpretation}</p>
    </div>

    <br>
    <a href="/">← Back</a>
</body>
</html>
"""

