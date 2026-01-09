from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

# ✅ API KEY environment variable se aayegi
AQI_API_KEY = os.getenv("AQI_API_KEY")

def aqi_status(aqi):
    if aqi <= 50:
        return "Good 😊"
    elif aqi <= 100:
        return "Moderate 🙂"
    elif aqi <= 200:
        return "Poor 😷"
    elif aqi <= 300:
        return "Very Poor 🤢"
    else:
        return "Severe ☠️"

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AQI Checker</title>
<style>
body{background:#020617;color:white;font-family:Arial;}
.box{background:#0f172a;padding:20px;width:360px;border-radius:12px;}
input,button{width:100%;padding:10px;margin:6px 0;}
button{background:#22c55e;border:none;font-weight:bold;}
</style>
</head>
<body>

<div class="box">
<h2>🌍 AQI Checker</h2>

<form method="post">
    <input name="city" placeholder="Enter city name" required>
    <button type="submit">Check AQI</button>
</form>

{% if aqi %}
<hr>
<p><b>City:</b> {{city}}</p>
<p><b>AQI:</b> {{aqi}}</p>
<p><b>Status:</b> {{status}}</p>
<p><b>Your IP:</b> {{ip}}</p>
{% endif %}
</div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form["city"]

        if not AQI_API_KEY:
            return "<h3>API key not set</h3>"

        url = f"https://api.waqi.info/feed/{city}/?token={AQI_API_KEY}"
        data = requests.get(url).json()

        if data["status"] != "ok":
            return "<h3>City not found or API error</h3>"

        aqi = data["data"]["aqi"]
        status = aqi_status(aqi)

        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        return render_template_string(
            HTML,
            city=city,
            aqi=aqi,
            status=status,
            ip=ip
        )

    return render_template_string(HTML)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
