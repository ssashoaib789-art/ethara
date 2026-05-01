TASKFLOW – TEAM TASK MANAGER
============================

A full-stack web application for team project and task management with role-based access control.

LIVE URL
--------
https://your-app.railway.app  (replace after deployment)

TECH STACK
----------
- Backend  : Python Flask
- Database : SQLite (via Flask-SQLAlchemy)
- Auth     : JWT (PyJWT) + bcrypt password hashing
- Frontend : Vanilla HTML/CSS/JavaScript (single-page app)
- Deploy   : Railway (Gunicorn WSGI)

FEATURES
--------
1. Authentication
   - User signup and login with JWT tokens
   - Passwords hashed with bcrypt
   - Token expires after 7 days

2. Role-Based Access Control
   - Admin: Create/delete projects, manage tasks, add/remove members, view all team
   - Member: View assigned projects, update status of their own tasks only

3. Project Management
   - Create and delete projects (admin only)
   - View progress bar per project
   - Add/remove team members per project

4. Task Management
   - Create tasks with title, description, priority (low/medium/high), due date, assignee
   - Kanban-style board: To Do | In Progress | Done
   - Members can update status of their own tasks
   - Admins can update all fields and delete tasks

5. Dashboard
   - Stats: total tasks, completed, in progress, overdue
   - My pending tasks and overdue tasks at a glance

6. Team View (Admin only)
   - View all registered users with their roles

API ENDPOINTS
-------------
POST   /api/signup                       Register a new user
POST   /api/login                        Login and get JWT token
GET    /api/me                           Get current user info
GET    /api/projects                     List accessible projects
POST   /api/projects                     Create project (admin)
GET    /api/projects/:id                 Get project with tasks and members
DELETE /api/projects/:id                 Delete project (admin)
POST   /api/projects/:id/members        Add member to project (admin)
DELETE /api/projects/:id/members/:uid   Remove member (admin)
POST   /api/projects/:id/tasks          Create task (admin)
PUT    /api/tasks/:id                    Update task
DELETE /api/tasks/:id                    Delete task (admin)
GET    /api/dashboard                    Dashboard stats
GET    /api/users                        All users (admin)

DATABASE SCHEMA
---------------
users          (id, name, email, password, role, created_at)
projects       (id, name, description, owner_id, created_at)
tasks          (id, title, description, status, priority, project_id, assignee_id, due_date, created_at)
project_members(id, project_id, user_id, role)

HOW TO RUN LOCALLY
-------------------
1. Clone the repo
   git clone https://github.com/YOUR_USERNAME/team-task-manager.git
   cd team-task-manager

2. Create a virtual environment
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate

3. Install dependencies
   pip install -r requirements.txt

4. Run the app
   python app.py

5. Open browser at http://localhost:5000

HOW TO DEPLOY ON RAILWAY
------------------------
1. Push code to GitHub

2. Go to https://railway.app and sign in

3. Click "New Project" → "Deploy from GitHub Repo"

4. Select your repository

5. Railway auto-detects Procfile and runs:
   gunicorn app:app --bind 0.0.0.0:$PORT

6. Add environment variable:
   SECRET_KEY = any_random_long_string

7. Click "Deploy" — your app will be live in ~2 minutes

8. Copy the live URL from the Railway dashboard

FILE STRUCTURE
--------------
team-task-manager/
├── app.py            # Flask routes and app factory
├── database.py       # SQLAlchemy models
├── auth.py           # JWT + bcrypt helpers
├── requirements.txt  # Python dependencies
├── Procfile          # Railway/Gunicorn startup command
├── README.txt        # This file
└── frontend/
    └── index.html    # Complete single-page frontend

DEMO CREDENTIALS (for testing)
-------------------------------
Create an Admin account from the signup page (select "Admin" role).
Then create Member accounts to test role-based access.

AUTHOR
------
Built for technical assessment submission.
