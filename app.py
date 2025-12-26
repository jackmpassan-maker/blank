from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from engine import calculate_snowscore, determine_decision

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Snow Day Calculator</title>
    </head>
    <body>
        <h1>Snow Day Calculator</h1>

        <div style="margin-bottom:20px; font-size:16px;">
    <strong>Decision Guide:</strong><br>
    0–25: School is ON<br>
    26–50: Consider Late Start / Early Dismissal / Cancellation<br>
    51+: Cancel School
</div>

        <form action="/calculate" method="post">
            <label>Snow (inches):</label><br>
            <input type="number" step="0.1" name="snow" required><br><br>

            <label>Freezing Rain (inches):</label><br>
            <input type="number" step="0.01" name="freezing_rain" value="0"><br><br>

            <label>Sleet (inches):</label><br>
            <input type="number" step="0.01" name="sleet" value="0"><br><br>

            <label>Average Annual Snow (inches):</label><br>
            <input type="number" name="avg_annual_snow" required><br><br>

            <label>Temperature (°F):</label><br>
            <input type="number" name="temp_f" required><br><br>

            <label>Wind Speed (mph):</label><br>
            <input type="number" name="wind_mph" required><br><br>

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

            <button type="submit">Calculate</button>
        </form>
    </body>
    </html>
    """


@app.post("/calculate", response_class=HTMLResponse)
def calculate(
    snow: float = Form(...),
    freezing_rain: float = Form(0),
    sleet: float = Form(0),
    avg_annual_snow: float = Form(...),
    region: str = Form(...),
    school_type: str = Form(...),
    temp_f: float = Form(...),
    wind_mph: float = Form(...),
    prev_snow_days: int = Form(0),
    peak_windows: list[str] = Form([])
):
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
        peak_windows
    )

    decision = determine_decision(snowscore, peak_windows)

    # Explanation logic (mirrors decision rubric)
if snowscore <= 25:
    explanation = "Overall conditions are minor, so school can operate as normal."

elif snowscore <= 34:
    if "6AM-9AM" in peak_windows:
        explanation = "Peak intensity during the morning commute increases travel risk, supporting a late start."
    else:
        explanation = "Conditions are manageable overall, so school can remain open."

elif snowscore <= 44:
    if any(w in peak_windows for w in ["3AM-6AM", "6AM-9AM"]):
        explanation = "Snow is heaviest during the morning commute, increasing the need for a late start."
    elif any(w in peak_windows for w in ["12PM-3PM", "3PM-6PM"]):
        explanation = "Peak conditions occur during school hours, which may justify an early dismissal."
    else:
        explanation = "Despite moderate snowfall, timing reduces disruption, allowing school to remain open."

elif snowscore <= 50:
    if any(w in peak_windows for w in ["6PM-9PM", "9PM-12AM", "12AM-3AM"]):
        explanation = "Overnight or evening peak intensity suggests delayed morning conditions, favoring a late start."
    elif any(w in peak_windows for w in ["3AM-6AM", "6AM-9AM"]):
        explanation = "Dangerous conditions during the morning commute increase the likelihood of cancellation."
    elif any(w in peak_windows for w in ["12PM-3PM", "3PM-6PM"]):
        explanation = "Peak snowfall during the school day increases the need for an early dismissal."
    else:
        explanation = "High overall impact suggests school operations would be unsafe."

else:
    explanation = "Extreme winter conditions make normal school operations unsafe."

    return f"""
    <html>
    <head>
        <title>Result</title>
    </head>
    <body>
        <h2>SnowScore: {snowscore}</h2>
        <h2>Decision: {decision}</h2>
        <br>
        <a href="/">← Back</a>
    </body>
    </html>
    """
