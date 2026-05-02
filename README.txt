TaskFlow - Team Task Manager

Description:
TaskFlow is a full-stack web application that allows users to manage projects, assign tasks, and track progress with role-based access control.

Features:
- User Authentication (Signup & Login)
- Role-based access (Admin / Member)
- Admin can create projects
- Admin can add members to projects
- Admin can assign tasks to project members
- Members can view assigned projects and tasks
- Task status tracking (Pending / Completed)
- Dashboard with total, completed, and pending tasks

Tech Stack:
Frontend: HTML, CSS, JavaScript
Backend: Flask (Python)
Database: PostgreSQL
Deployment: Railway

System Design:
- One Admin manages projects
- Projects contain multiple members
- Tasks are assigned only to project members
- Backend validates task assignment strictly

API Endpoints:
POST   /register          → Register user
POST   /login             → Login user
GET    /users             → Get all users
POST   /projects          → Create project (Admin only)
GET    /projects/<id>     → Get projects
POST   /projects/<id>/members → Add member
GET    /projects/<id>/members → Get members
POST   /tasks             → Create task
GET    /tasks/<id>        → Get tasks
PUT    /tasks/<id>/status → Update status

How to Use:
1. Register as Admin
2. Login as Admin
3. Create a project
4. Add members to the project
5. Assign tasks to members
6. Login as Member
7. View assigned tasks and projects

Live URL:
<PASTE YOUR RAILWAY LINK>

GitHub Repository:
<PASTE YOUR GITHUB LINK>

Author:
Shaik Shoaib Ahmed
Final Year Project Submission