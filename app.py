from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
import os

app = Flask(__name__)
CORS(app)

# DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    project_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)
    status = db.Column(db.String(20), default="pending")

# ================= ROUTES =================

@app.route("/")
def home():
    return "Backend is running 🚀"

# -------- REGISTER --------
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    if not data.get("email") or not data.get("password"):
        return jsonify({"message": "Missing fields"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User already exists"}), 400

    hashed_pw = bcrypt.hashpw(
        data["password"].encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user = User(
        username=data.get("name"),
        email=data.get("email"),
        password=hashed_pw,
        role=data.get("role", "Member")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


# -------- LOGIN --------
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(email=data.get("email")).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if bcrypt.checkpw(
        data.get("password").encode("utf-8"),
        user.password.encode("utf-8")
    ):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.username,
                "role": user.role
            }
        })

    return jsonify({"message": "Invalid credentials"}), 401


# -------- GET USERS (TEAM) --------
@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([
        {"id": u.id, "name": u.username, "role": u.role}
        for u in users
    ])


# -------- CREATE PROJECT (ADMIN ONLY) --------
@app.route("/projects", methods=["POST"])
def create_project():
    data = request.json

    user = User.query.get(data["owner_id"])

    if user.role != "Admin":
        return jsonify({"message": "Only Admin can create project"}), 403

    if not data.get("name"):
        return jsonify({"message": "Project name required"}), 400

    project = Project(
        name=data["name"],
        owner_id=data["owner_id"]
    )

    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


# -------- GET PROJECTS --------
@app.route("/projects/<int:user_id>")
def get_projects(user_id):
    projects = Project.query.filter_by(owner_id=user_id).all()

    return jsonify([
        {"id": p.id, "name": p.name}
        for p in projects
    ])


# -------- DELETE PROJECT (ADMIN ONLY) --------
@app.route("/projects/<int:id>", methods=["DELETE"])
def delete_project(id):
    project = Project.query.get(id)

    if not project:
        return jsonify({"message": "Project not found"}), 404

    user_id = request.args.get("user_id")
    user = User.query.get(user_id)

    if user.role != "Admin":
        return jsonify({"message": "Only Admin can delete project"}), 403

    Task.query.filter_by(project_id=id).delete()

    db.session.delete(project)
    db.session.commit()

    return jsonify({"message": "Project deleted"})


# -------- CREATE TASK --------
@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.json

    if not data.get("title"):
        return jsonify({"message": "Task title required"}), 400

    task = Task(
        title=data["title"],
        project_id=data["project_id"],
        assigned_to=data["assigned_to"]
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task created"})


# -------- GET TASKS --------
@app.route("/tasks/<int:user_id>")
def get_tasks(user_id):
    tasks = Task.query.filter_by(assigned_to=user_id).all()

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "project_id": t.project_id,
            "status": t.status
        }
        for t in tasks
    ])


# -------- DELETE TASK --------
@app.route("/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    task = Task.query.get(id)

    if not task:
        return jsonify({"message": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"})


# -------- TOGGLE STATUS --------
@app.route("/tasks/<int:id>/status", methods=["PUT"])
def update_status(id):
    task = Task.query.get(id)

    if not task:
        return jsonify({"message": "Task not found"}), 404

    task.status = "completed" if task.status == "pending" else "pending"

    db.session.commit()

    return jsonify({"message": "Status updated"})


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)