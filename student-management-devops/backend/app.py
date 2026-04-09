from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import time

app = Flask(__name__)
CORS(app)

# Retry logic
while True:
    try:
        db = mysql.connector.connect(
            host="db",
            user="root",
            password="root",
            database="students"
        )
        print("✅ Connected to MySQL")
        break
    except:
        print("⏳ Waiting for MySQL...")
        time.sleep(5)

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/add_student", methods=["POST"])
def add_student():
    data = request.json

    cursor = db.cursor()
    query = "INSERT INTO student (name, email, tech, location) VALUES (%s, %s, %s, %s)"
    values = (data['name'], data['email'], data['tech'], data['location'])

    cursor.execute(query, values)
    db.commit()

    return jsonify({"message": "Student added successfully"})

# 🔥 THIS IS REQUIRED
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)