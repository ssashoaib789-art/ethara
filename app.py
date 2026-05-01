from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
import os

app = Flask(__name__)
CORS(app)

# =========================
# DATABASE CONFIG (Railway)
# =========================
database_url = os.environ.get("DATABASE_URL")

if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# MODEL
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))

# create tables
with app.app_context():
    db.create_all()

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return "Backend is running 🚀"


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        if not name or not email or not password:
            return jsonify({"message": "Missing fields"}), 400

        # check existing user
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "User already exists"}), 400

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user = User(
            username=name,
            email=email,
            password=hashed_pw.decode("utf-8"),
            role=role
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"message": "Server error"}), 500


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            return jsonify({
                "message": "Login successful",
                "user": {
                    "name": user.username,
                    "email": user.email,
                    "role": user.role
                }
            })

        return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"message": "Server error"}), 500


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run()