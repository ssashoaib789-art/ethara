from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import jwt
import datetime
import bcrypt

app = Flask(__name__)
CORS(app)

# 🔐 Secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret123')

# 🗄️ Database config (PostgreSQL for Railway)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///taskmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(50))
    project_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)

# ================= ROUTES =================

# ✅ Serve frontend
@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')


# 🔐 Register
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_pw
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered"})


# 🔑 Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({"token": token})

    return jsonify({"message": "Invalid credentials"}), 401


# 📁 Create Project
@app.route('/projects', methods=['POST'])
def create_project():
    data = request.json
    project = Project(name=data['name'], owner_id=data['owner_id'])

    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


# 📋 Add Task
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    task = Task(
        title=data['title'],
        status="pending",
        project_id=data['project_id'],
        assigned_to=data['assigned_to']
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task created"})


# 📊 Get Tasks
@app.route('/tasks/<int:user_id>', methods=['GET'])
def get_tasks(user_id):
    tasks = Task.query.filter_by(assigned_to=user_id).all()

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "status": t.status
        } for t in tasks
    ])


# ================= INIT =================

with app.app_context():
    db.create_all()

# ================= RUN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)