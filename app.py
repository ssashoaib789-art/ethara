from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
import os

app = Flask(__name__)
CORS(app)

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


class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)


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


# REGISTER
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User already exists"}), 400

    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

    user = User(
        username=data["name"],
        email=data["email"],
        password=hashed,
        role=data.get("role", "Member")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if bcrypt.checkpw(data["password"].encode(), user.password.encode()):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.username,
                "role": user.role
            }
        })

    return jsonify({"message": "Invalid credentials"}), 401


# USERS
@app.route("/users")
def users():
    users = User.query.all()
    return jsonify([{"id": u.id, "name": u.username} for u in users])


# CREATE PROJECT (ADMIN ONLY)
@app.route("/projects", methods=["POST"])
def create_project():
    data = request.json

    user = User.query.get(data["owner_id"])

    if user.role != "Admin":
        return jsonify({"message": "Only Admin allowed"}), 403

    project = Project(name=data["name"], owner_id=data["owner_id"])

    db.session.add(project)
    db.session.commit()

    return jsonify({"message": "Project created"})


# GET PROJECTS
@app.route("/projects/<int:user_id>")
def get_projects(user_id):
    user = User.query.get(user_id)

    if user.role == "Admin":
        projects = Project.query.filter_by(owner_id=user_id).all()
    else:
        memberships = ProjectMember.query.filter_by(user_id=user_id).all()
        ids = [m.project_id for m in memberships]
        projects = Project.query.filter(Project.id.in_(ids)).all()

    return jsonify([{"id": p.id, "name": p.name} for p in projects])


# ADD MEMBER (ADMIN)
@app.route("/projects/<int:pid>/members", methods=["POST"])
def add_member(pid):
    data = request.json

    admin = User.query.get(data["admin_id"])

    if admin.role != "Admin":
        return jsonify({"message": "Only Admin"}), 403

    existing = ProjectMember.query.filter_by(project_id=pid, user_id=data["user_id"]).first()

    if existing:
        return jsonify({"message": "Already added"}), 400

    db.session.add(ProjectMember(project_id=pid, user_id=data["user_id"]))
    db.session.commit()

    return jsonify({"message": "Member added"})


# GET MEMBERS
@app.route("/projects/<int:pid>/members")
def get_members(pid):
    members = ProjectMember.query.filter_by(project_id=pid).all()

    result = []
    for m in members:
        u = User.query.get(m.user_id)
        result.append({"id": u.id, "name": u.username})

    return jsonify(result)


# CREATE TASK
@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.json

    member = ProjectMember.query.filter_by(
        project_id=data["project_id"],
        user_id=data["assigned_to"]
    ).first()

    if not member:
        return jsonify({"message": "User not in project"}), 400

    task = Task(
        title=data["title"],
        project_id=data["project_id"],
        assigned_to=data["assigned_to"]
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({"message": "Task created"})


# GET TASKS
@app.route("/tasks/<int:user_id>")
def get_tasks(user_id):
    tasks = Task.query.filter_by(assigned_to=user_id).all()

    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "project_id": t.project_id,
            "status": t.status
        } for t in tasks
    ])


# TOGGLE STATUS
@app.route("/tasks/<int:id>/status", methods=["PUT"])
def status(id):
    t = Task.query.get(id)

    t.status = "completed" if t.status == "pending" else "pending"
    db.session.commit()

    return jsonify({"message": "Updated"})


if __name__ == "__main__":
    app.run(debug=True)