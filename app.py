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

    <div style="border:2px solid black; padding:10px; margin-bottom:20px;">
        <strong>SNOWSCORE RUBRIC</strong><br>
        0–25: School ON<br>
        26–50: Late Start / Early Dismissal / Cancellation Possible<br>
        51+: Cancel School
    </div>

    <form action="/calculate" method="post">
        Snow (inches):<br>
        <input type="number" step="0.1" name="snow" required><br><br>

        Freezing Rain (inches):<br>
        <input type="number" step="0.01" name="freezing_rain" value="0"><br><br>

        Sleet (inches):<br>
        <input type="number" step="0.01" name="sleet" value="0"><br><br>

        Avg Annual Snow (inches):<br>
        <input type="number" name="avg_annual_snow" required><br><br>

        Temperature (°F):<br>
        <input type="number" name="temp_f" required><br><br>

        Peak Window (e.g. 3AM–9AM):<br>
        <input type="text" name="peak_window" required><br><br>

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
    temp_f: float = Form(...),
    peak_window: str = Form(...)
):
    score = calculate_snowscore(
        snow,
        freezing_rain,
        sleet,
        avg_annual_snow,
        temp_f
    )

    decision, explanation = determine_decision(score, peak_window)

    return f"""
    <html>
    <head>
        <title>Result</title>
    </head>
    <body>
        <h2>SnowScore: {score}</h2>
        <h2>Decision: {decision}</h2>
        <p>{explanation}</p>
        <br>
        <a href="/">← Back</a>
    </body>
    </html>
    """


