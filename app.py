from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import db, User, Project, Task, ProjectMember
from auth import generate_token, verify_token, hash_password, check_password
import os
from datetime import datetime, date

app = Flask(__name__, static_folder='frontend', static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///taskmanager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# ─── Auth Middleware ─────────────────────────────────────────────────────────

def require_auth():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None, jsonify({'error': 'No token provided'}), 401
    payload = verify_token(token, app.config['SECRET_KEY'])
    if not payload:
        return None, jsonify({'error': 'Invalid or expired token'}), 401
    user = User.query.get(payload['user_id'])
    if not user:
        return None, jsonify({'error': 'User not found'}), 401
    return user, None, None

# ─── Serve Frontend ──────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)

# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'member')

    if not name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if role not in ['admin', 'member']:
        return jsonify({'error': 'Role must be admin or member'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(name=name, email=email, password=hash_password(password), role=role)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id, app.config['SECRET_KEY'])
    return jsonify({'token': token, 'user': user.to_dict()}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not check_password(password, user.password):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = generate_token(user.id, app.config['SECRET_KEY'])
    return jsonify({'token': token, 'user': user.to_dict()})

@app.route('/api/me', methods=['GET'])
def me():
    user, err, code = require_auth()
    if err:
        return err, code
    return jsonify(user.to_dict())

# ─── Project Routes ───────────────────────────────────────────────────────────

@app.route('/api/projects', methods=['GET'])
def get_projects():
    user, err, code = require_auth()
    if err:
        return err, code

    if user.role == 'admin':
        projects = Project.query.all()
    else:
        member_projects = ProjectMember.query.filter_by(user_id=user.id).all()
        project_ids = [pm.project_id for pm in member_projects]
        projects = Project.query.filter(Project.id.in_(project_ids)).all()

    return jsonify([p.to_dict() for p in projects])

@app.route('/api/projects', methods=['POST'])
def create_project():
    user, err, code = require_auth()
    if err:
        return err, code
    if user.role != 'admin':
        return jsonify({'error': 'Only admins can create projects'}), 403

    data = request.json
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'error': 'Project name is required'}), 400

    project = Project(name=name, description=description, owner_id=user.id)
    db.session.add(project)
    db.session.flush()

    member = ProjectMember(project_id=project.id, user_id=user.id, role='admin')
    db.session.add(member)
    db.session.commit()

    return jsonify(project.to_dict()), 201

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    user, err, code = require_auth()
    if err:
        return err, code

    project = Project.query.get_or_404(project_id)
    if user.role != 'admin':
        if not ProjectMember.query.filter_by(project_id=project_id, user_id=user.id).first():
            return jsonify({'error': 'Access denied'}), 403

    tasks = Task.query.filter_by(project_id=project_id).all()
    members = ProjectMember.query.filter_by(project_id=project_id).all()
    member_data = []
    for m in members:
        u = User.query.get(m.user_id)
        if u:
            member_data.append({'id': u.id, 'name': u.name, 'email': u.email, 'role': m.role})

    result = project.to_dict()
    result['tasks'] = [t.to_dict() for t in tasks]
    result['members'] = member_data
    return jsonify(result)

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    user, err, code = require_auth()
    if err:
        return err, code
    if user.role != 'admin':
        return jsonify({'error': 'Only admins can delete projects'}), 403

    project = Project.query.get_or_404(project_id)
    Task.query.filter_by(project_id=project_id).delete()
    ProjectMember.query.filter_by(project_id=project_id).delete()
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted'})

@app.route('/api/projects/<int:project_id>/members', methods=['POST'])
def add_member(project_id):
    user, err, code = require_auth()
    if err:
        return err, code
    if user.role != 'admin':
        return jsonify({'error': 'Only admins can add members'}), 403

    data = request.json
    email = data.get('email', '').strip().lower()
    member_user = User.query.filter_by(email=email).first()
    if not member_user:
        return jsonify({'error': 'User not found'}), 404

    existing = ProjectMember.query.filter_by(project_id=project_id, user_id=member_user.id).first()
    if existing:
        return jsonify({'error': 'User already a member'}), 409

    pm = ProjectMember(project_id=project_id, user_id=member_user.id, role='member')
    db.session.add(pm)
    db.session.commit()
    return jsonify({'message': 'Member added', 'user': member_user.to_dict()}), 201

@app.route('/api/projects/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
def remove_member(project_id, user_id):
    user, err, code = require_auth()
    if err:
        return err, code
    if user.role != 'admin':
        return jsonify({'error': 'Only admins can remove members'}), 403

    pm = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not pm:
        return jsonify({'error': 'Member not found'}), 404
    db.session.delete(pm)
    db.session.commit()
    return jsonify({'message': 'Member removed'})

# ─── Task Routes ──────────────────────────────────────────────────────────────

@app.route('/api/projects/<int:project_id>/tasks', methods=['POST'])
def create_task(project_id):
    user, err, code = require_auth()
    if err:
        return err, code
    if user.role != 'admin':
        return jsonify({'error': 'Only admins can create tasks'}), 403

    data = request.json
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Task title is required'}), 400

    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid due date format'}), 400

    assignee_id = data.get('assignee_id')
    if assignee_id:
        if not ProjectMember.query.filter_by(project_id=project_id, user_id=assignee_id).first():
            return jsonify({'error': 'Assignee is not a project member'}), 400

    task = Task(
        title=title,
        description=data.get('description', ''),
        project_id=project_id,
        assignee_id=assignee_id,
        due_date=due_date,
        priority=data.get('priority', 'medium'),
        status='todo'
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    user, err, code = require_auth()
    if err:
        return err, code

    task = Task.query.get_or_404(task_id)
    data = request.json

    # Members can only update status of their assigned tasks
    if user.role == 'member':
        if task.assignee_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        if 'status' in data:
            task.status = data['status']
    else:
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']
        if 'assignee_id' in data:
            task.assignee_id = data['assignee_id']
        if 'due_date' in data:
            if data['due_date']:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            else:
                task.due_date = None

    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    user, err, code = require_auth()
    if err:
        return err, code
    if user.role != 'admin':
        return jsonify({'error': 'Only admins can delete tasks'}), 403

    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'})

# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    user, err, code = require_auth()
    if err:
        return err, code

    today = date.today()

    if user.role == 'admin':
        all_tasks = Task.query.all()
        total_projects = Project.query.count()
        total_users = User.query.count()
    else:
        member_projects = ProjectMember.query.filter_by(user_id=user.id).all()
        project_ids = [pm.project_id for pm in member_projects]
        all_tasks = Task.query.filter(Task.project_id.in_(project_ids)).all()
        total_projects = len(project_ids)
        total_users = None

    total_tasks = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.status == 'done')
    in_progress = sum(1 for t in all_tasks if t.status == 'in_progress')
    todo = sum(1 for t in all_tasks if t.status == 'todo')
    overdue = sum(1 for t in all_tasks if t.due_date and t.due_date < today and t.status != 'done')

    my_tasks = Task.query.filter_by(assignee_id=user.id).all()
    my_overdue = [t.to_dict() for t in my_tasks if t.due_date and t.due_date < today and t.status != 'done']
    my_pending = [t.to_dict() for t in my_tasks if t.status != 'done']

    result = {
        'total_tasks': total_tasks,
        'completed': completed,
        'in_progress': in_progress,
        'todo': todo,
        'overdue': overdue,
        'total_projects': total_projects,
        'my_tasks': my_pending[:5],
        'my_overdue': my_overdue
    }
    if total_users is not None:
        result['total_users'] = total_users

    return jsonify(result)

@app.route('/api/users', methods=['GET'])
def get_users():
    user, err, code = require_auth()
    if err:
        return err, code
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
