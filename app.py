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

            <label>Peak Intensity Windows (check all that apply):</label><br>
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



