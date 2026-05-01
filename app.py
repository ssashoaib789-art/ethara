from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
import os

app = Flask(__name__)
CORS(app)

# DATABASE CONFIG
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(50), default="pending")
    project_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)


with app.app_context():
    db.create_all()

# ================= ROUTES =================

@app.route("/")
def home():
    return "Backend running 🚀"

# -------- AUTH --------

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User already exists"}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    user = User(
        username=name,
        email=email,
        password=hashed.decode(),
        role=role
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()

    if user and bcrypt.checkpw(data.get("password").encode(), user.password.encode()):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.username,
                "role": user.role
            }
        })

    return jsonify({"message": "Invalid credentials"}), 401

# -------- PROJECTS --------

@app.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()

    project = Project(
        name=data.get("name"),
        owner_id=data.get("owner_id")
    )

    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


@app.route("/projects/<int:user_id>", methods=["GET"])
def get_projects(user_id):
    projects = Project.query.filter_by(owner_id=user_id).all()

    return jsonify([
        {"id": p.id, "name": p.name}
        for p in projects
    ])

# -------- TASKS --------

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    task = Task(
        title=data.get("title"),
        project_id=data.get("project_id"),
        assigned_to=data.get("assigned_to")
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task created"})


@app.route("/tasks/<int:user_id>", methods=["GET"])
def get_tasks(user_id):
    tasks = Task.query.filter_by(assigned_to=user_id).all()

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "status": t.status
        } for t in tasks
    ])


@app.route("/tasks/update/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = Task.query.get(task_id)

    task.status = "completed"
    db.session.commit()

    return jsonify({"message": "Task updated"})


# ================= RUN =================

if __name__ == "__main__":
    app.run()
# DELETE TASK
@app.route("/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"})

# DELETE PROJECT
# DELETE PROJECT
@app.route("/projects/<int:id>", methods=["DELETE"])
def delete_project(id):
    project = Project.query.get(id)

    if not project:
        return jsonify({"message": "Project not found"}), 404

    # delete related tasks first
    Task.query.filter_by(project_id=id).delete()

    db.session.delete(project)
    db.session.commit()

    return jsonify({"message": "Project deleted"})


# DELETE TASK
@app.route("/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    task = Task.query.get(id)

    if not task:
        return jsonify({"message": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"})