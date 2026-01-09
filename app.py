from flask import Flask, request, jsonify
import requests
import re
import os

app = Flask(__name__)

# 🔐 API key (Render → Environment Variables)
AQI_API_KEY = os.getenv("AQI_API_KEY")

# 🧠 Temporary memory (restart pe clear)
used_emails = set()

# ✅ Email validation
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "running",
        "usage": "POST /check_aqi with JSON { city, email, website:'' }"
    })

@app.route("/check_aqi", methods=["POST"])
def check_aqi():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    city = data.get("city")
    email = data.get("email")
    honeypot = data.get("website")  # 🕵️ bot trap

    # 🛑 Bot detected
    if honeypot:
        return jsonify({"error": "Bot detected"}), 403

    if not city or not email:
        return jsonify({"error": "City and email required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email"}), 400

    if email in used_emails:
        return jsonify({"error": "Too many requests from this email"}), 429

    used_emails.add(email)

    # 👀 EMAIL ONLY IN RENDER LOGS (ADMIN ONLY)
    print(f"[EMAIL LOG] {email}")

    # 🌍 AQI API call
    url = f"https://api.waqi.info/feed/{city}/?token={AQI_API_KEY}"
    response = requests.get(url).json()

    if response.get("status") != "ok":
        return jsonify({"error": "City not found"}), 404

    return jsonify({
        "status": "success",
        "city": city,
        "aqi": response["data"]["aqi"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
