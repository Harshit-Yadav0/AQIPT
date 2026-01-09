from flask import Flask, request, render_template_string
import requests
import re
import os
from datetime import datetime

app = Flask(__name__)

# AQI API Key from Render environment variable
AQI_API_KEY = os.getenv("AQI_API_KEY")

# Temporary memory for emails
used_emails = set()

# HTML Template (modern frontend, inline)
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🌍 AQI Checker</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body { font-family: 'Roboto', sans-serif; background: linear-gradient(135deg, #0f172a, #020617); color: #fff;
           display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .container { background: #1e293b; padding: 30px; border-radius: 15px; box-shadow: 0 0 20px rgba(0,0,0,0.5);
                 width: 400px; text-align: center; }
    h1 { margin-bottom: 20px; color: #22c55e; }
    input { width: 90%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; }
    button { width: 95%; padding: 12px; border: none; border-radius: 8px; background: #22c55e;
             color: #fff; font-weight: bold; cursor: pointer; transition: 0.3s; }
    button:hover { background: #16a34a; }
    .result { margin-top: 20px; padding: 15px; border-radius: 10px; background: #334155; }
    .error { color: #f87171; font-weight: bold; }
    .aqi-good { color: #22c55e; font-weight: bold; }
    .aqi-moderate { color: #eab308; font-weight: bold; }
    .aqi-poor { color: #f97316; font-weight: bold; }
    .aqi-verypoor { color: #f43f5e; font-weight: bold; }
    .aqi-severe { color: #8b5cf6; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
    <h1>🌍 AQI Checker</h1>
    <form method="post">
        <input type="text" name="city" placeholder="Enter city" required>
        <input type="email" name="email" placeholder="Enter email" required>
        <!-- Honeypot -->
        <input name="website" style="display:none">
        <button type="submit">Check AQI</button>
    </form>

    {% if aqi %}
    <div class="result">
        <p><b>City:</b> {{ city }}</p>
        <p><b>AQI:</b> {{ aqi }}</p>
        <p><b>Status:</b> <span class="{{ status_class }}">{{ status }}</span></p>
    </div>
    {% elif error %}
    <div class="result error">{{ error }}</div>
    {% endif %}
</div>
</body>
</html>
"""

# Email validation
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

# AQI status helper
def aqi_status(aqi):
    try: aqi = int(aqi)
    except: return "Unknown", ""
    if aqi <= 50: return "Good 😊", "aqi-good"
    elif aqi <= 100: return "Moderate 🙂", "aqi-moderate"
    elif aqi <= 200: return "Poor 😷", "aqi-poor"
    elif aqi <= 300: return "Very Poor 🤢", "aqi-verypoor"
    else: return "Severe ☠️", "aqi-severe"

# Helper to get real IP
def get_client_ip():
    ip = request.headers.get("X-Forwarded-For")
    if ip:
        # Sometimes multiple IPs: "client, proxy1, proxy2"
        ip = ip.split(",")[0].strip()
    else:
        ip = request.remote_addr
    return ip

@app.route("/", methods=["GET","POST"])
def home():
    aqi = None
    city = None
    status = None
    status_class = ""
    error = None

    if request.method == "POST":
        city = request.form.get("city")
        email = request.form.get("email")
        honeypot = request.form.get("website")

        # Bot check
        if honeypot:
            error = "Bot detected"
            return render_template_string(HTML, error=error)

        # Required fields
        if not city or not email:
            error = "City and email required"
            return render_template_string(HTML, error=error)

        # Email validation
        if not is_valid_email(email):
            error = "Invalid email format"
            return render_template_string(HTML, error=error)

        # Duplicate email
        if email in used_emails:
            error = "Too many requests from this email"
            return render_template_string(HTML, error=error)

        used_emails.add(email)

        # Get real client IP
        ip = get_client_ip()
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log IP + Email + City + Timestamp
        print(f"[{time_now}] IP: {ip} | Email: {email} | City: {city}")

        # AQI API call
        if not AQI_API_KEY:
            error = "AQI API key not set"
            return render_template_string(HTML, error=error)

        try:
            url = f"https://api.waqi.info/feed/{city}/?token={AQI_API_KEY}"
            data = requests.get(url, timeout=10).json()
            if data.get("status") != "ok":
                error = "City not found or API error"
                return render_template_string(HTML, error=error)
            aqi = data["data"]["aqi"]
            status, status_class = aqi_status(aqi)
        except Exception as e:
            error = f"API request failed: {e}"

    return render_template_string(HTML, city=city, aqi=aqi, status=status, status_class=status_class, error=error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
