from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import date
import os, re

app = Flask(__name__)
app.secret_key = 'key'

def validate_name(n):
    if not n: return False
    return bool(re.match(r'^[A-Za-z\s\'\-]+$', n.strip()))

def validate_phone(p):
    if not p: return False
    return bool(re.match(r'^[0-9]{10}$', p.strip()))

def att(s):
    if not s.get('attendance'): return 0
    p = sum(1 for a in s['attendance'] if a['status'] == "Present")
    return (p/len(s['attendance']))*100 if s['attendance'] else 0

app.jinja_env.globals.update(att=att)

students, teachers, classrooms = [], [], []
sc = tc = 1
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def find(k, n):
    for i in globals()[k]:
        if i['name'].lower() == n.lower(): return i
    return None

def add_student_data(n, a, c, p):
    global sc
    students.append({"id": f"S{sc:04d}", "name": n.strip(), "age": int(a), "contact": c, "parent": p.strip(), "classroom": "", "attendance": []})
    sc += 1

def add_teacher_data(n, a, c, s):
    global tc
    teachers.append({"id": f"T{tc:04d}", "name": n.strip(), "age": int(a), "contact": c, "subject": s.strip(), "classroom": ""})
    tc += 1

def create_templates():
    if not os.path.exists('templates'): os.makedirs('templates')
    t = {
        'login.html':'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
<style>
body{background:linear-gradient(135deg,#FF69B4,#87CEEB);min-height:100vh;display:flex;align-items:center;margin:0}
.login-card{max-width:400px;margin:auto;padding:40px;border-radius:20px;box-shadow:0 10px 40px rgba(0,0,0,0.2);background:white;width:100%}
.login-card .logo{text-align:center;margin-bottom:30px}
.login-card .logo i{font-size:3rem;color:#FF69B4;background:linear-gradient(135deg,#FF69B4,#87CEEB);-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:block}
.login-card .logo h2{margin-top:10px;color:#333;font-weight:bold}
.login-card .logo p{color:#888;font-size:0.9rem}
.login-card .form-label{font-weight:600;color:#333}
.login-card .form-control{border-radius:10px;padding:12px 15px;border:2px solid #e0e0e0}
.login-card .form-control:focus{border-color:#FF69B4;box-shadow:0 0 0 0.2rem rgba(255,105,180,0.25)}
.login-card .btn-primary{background:linear-gradient(135deg,#FF69B4,#87CEEB);border:none;width:100%;padding:12px;font-weight:bold;border-radius:10px}
.login-card .btn-primary:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(255,105,180,0.4)}
.login-card .alert{border-radius:10px}
.login-card .role-selector{display:flex;gap:10px;margin-bottom:25px}
.login-card .role-selector .btn-role{flex:1;padding:10px;border-radius:10px;border:2px solid #e0e0e0;background:white;color:#888;font-weight:600;transition:all 0.3s;cursor:pointer}
.login-card .role-selector .btn-role:hover{border-color:#FF69B4;color:#FF69B4}
.login-card .role-selector .btn-role.active{border-color:#FF69B4;background:linear-gradient(135deg,#FF69B4,#87CEEB);color:white}
.login-card .role-selector .btn-role i{display:block;font-size:1.5rem;margin-bottom:5px}
</style>
</head>
<body>
<div class="login-card">
<div class="logo"><i class="bi bi-heart-fill"></i><h2>Abel's Learners</h2><p>Choose your role to login</p></div>
{% with m=get_flashed_messages(with_categories=true) %}{% if m %}{% for c,msg in m %}<div class="alert alert-{{'danger' if c=='danger' else 'success'}}">{{msg}}</div>{% endfor %}{% endif %}{% endwith %}
<div class="role-selector">
<button class="btn-role active" data-role="admin" onclick="selectRole('admin')"><i class="bi bi-shield-lock"></i>Admin</button>
<button class="btn-role" data-role="student" onclick="selectRole('student')"><i class="bi bi-person"></i>Student</button>
<button class="btn-role" data-role="teacher" onclick="selectRole('teacher')"><i class="bi bi-person-badge"></i>Teacher</button>
</div>
<form method="POST" id="loginForm">
<div id="adminFields"><div class="mb-3"><label class="form-label">Username</label><input type="text" class="form-control" name="username" placeholder="Enter username"></div><div class="mb-3"><label class="form-label">Password</label><input type="password" class="form-control" name="password" placeholder="Enter password"></div></div>
<div id="studentFields" style="display:none;"><div class="mb-3"><label class="form-label">Student ID</label><input type="text" class="form-control" name="student_id" placeholder="e.g., S0001"></div><div class="mb-3"><label class="form-label">Password</label><input type="password" class="form-control" name="student_password" placeholder="Enter password"></div></div>
<div id="teacherFields" style="display:none;"><div class="mb-3"><label class="form-label">Teacher ID</label><input type="text" class="form-control" name="teacher_id" placeholder="e.g., T0001"></div><div class="mb-3"><label class="form-label">Password</label><input type="password" class="form-control" name="teacher_password" placeholder="Enter password"></div></div>
<button type="submit" class="btn btn-primary" id="loginBtn">Login as Admin</button>
</form>
</div>
<script>
function selectRole(role){document.querySelectorAll('.btn-role').forEach(b=>b.classList.remove('active'));document.querySelector(`.btn-role[data-role="${role}"]`).classList.add('active');document.getElementById('adminFields').style.display=role==='admin'?'block':'none';document.getElementById('studentFields').style.display=role==='student'?'block':'none';document.getElementById('teacherFields').style.display=role==='teacher'?'block':'none';document.getElementById('loginBtn').textContent='Login as '+role.charAt(0).toUpperCase()+role.slice(1);}
document.getElementById('loginForm').addEventListener('submit',function(e){const r=document.querySelector('.btn-role.active').dataset.role;this.action=r==='admin'?'/login':r==='student'?'/student/login':'/teacher/login';});
</script>
</body>
</html>''',
        'base.html':'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Kindergarten</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
<style>:root{--p:#FF69B4;--s:#87CEEB;--g:linear-gradient(135deg,#FF69B4,#87CEEB)}body{background:#f8f9fa}.navbar{background:var(--g)!important;box-shadow:0 2px 10px rgba(0,0,0,0.1)}.navbar-brand{font-weight:bold;color:white!important;font-size:1.5rem}.navbar-brand i{color:#FFD700}.nav-link{color:white!important;font-weight:500}.nav-link:hover{background:rgba(255,255,255,0.2);border-radius:5px}.card{border-radius:15px;border:none;box-shadow:0 2px 10px rgba(0,0,0,0.1)}.card-header{background:var(--g);color:white;border-radius:15px 15px 0 0!important;font-weight:bold}.btn-primary{background:var(--g);border:none;padding:10px 30px;font-weight:bold}.btn-primary:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(255,105,180,0.4)}.stat-number{font-size:2.5rem;font-weight:bold;color:#FF69B4}footer{background:var(--g);color:white;padding:20px 0;margin-top:40px}.form-control:focus{border-color:#FF69B4;box-shadow:0 0 0 0.2rem rgba(255,105,180,0.25)}.form-label{font-weight:600;color:#333}.text-muted{font-size:12px}.btn-outline-primary{border-color:#FF69B4;color:#FF69B4}.btn-outline-primary:hover{background:var(--g);color:white;border-color:transparent}.btn-secondary:hover{background:#6c757d;color:white}.bg-pink{background:#FF69B4;color:white}</style>
</head>
<body>
<nav class="navbar navbar-expand-lg"><div class="container"><a class="navbar-brand" href="/"><i class="bi bi-heart-fill"></i> Abel's</a><button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button><div class="collapse navbar-collapse" id="navbarNav"><ul class="navbar-nav ms-auto"><li class="nav-item"><a class="nav-link" href="/"><i class="bi bi-house"></i> Home</a></li><li class="nav-item"><a class="nav-link" href="/students"><i class="bi bi-people"></i> Students</a></li><li class="nav-item"><a class="nav-link" href="/teachers"><i class="bi bi-person-badge"></i> Teachers</a></li><li class="nav-item"><a class="nav-link" href="/classrooms"><i class="bi bi-building"></i> Rooms</a></li><li class="nav-item"><a class="nav-link" href="/manage"><i class="bi bi-gear"></i> Manage</a></li><li class="nav-item"><a class="nav-link" href="/logout"><i class="bi bi-box-arrow-right"></i> Logout</a></li></ul></div></div></nav>
<div class="container">{% with m=get_flashed_messages(with_categories=true) %}{% if m %}{% for c,msg in m %}<div class="alert alert-{{'success' if c=='success' else 'danger'}} alert-dismissible fade show mt-3">{{msg}}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>{% endfor %}{% endif %}{% endwith %}{% block content %}{% endblock %}</div>
<footer class="text-center"><div class="container"><p><i class="bi bi-heart-fill text-warning"></i> Abel's Little Learners - Nurturing Young Minds <i class="bi bi-heart-fill text-warning"></i></p></div></footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>''',
        'index.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-12 text-center"><h1 style="background:var(--g);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:bold;">Welcome to Abel's Little Learners</h1><p class="lead">Where every child's journey begins with love and care.</p></div></div>
<div class="row mt-4">{% for l,c,u in [("Students",students|length,"/students"),("Teachers",teachers|length,"/teachers"),("Rooms",classrooms|length,"/classrooms")] %}<div class="col-md-4"><div class="card text-center"><div class="card-body"><i class="bi bi-{{'people' if l=='Students' else 'person-badge' if l=='Teachers' else 'building'}}" style="font-size:3rem;color:#FF69B4;"></i><h3 class="stat-number">{{c}}</h3><h5>{{l}}</h5><a href="{{u}}" class="btn btn-primary btn-sm">View All</a></div></div></div>{% endfor %}</div>
<div class="row mt-4"><div class="col-md-6"><div class="card"><div class="card-header"><i class="bi bi-clock-history"></i> Quick Actions</div><div class="card-body"><div class="d-grid gap-2">{% for n,u in [("Add Student","/students/add"),("Add Teacher","/teachers/add"),("Add Room","/classrooms/add"),("Assign Student","/assign/student"),("Assign Teacher","/assign/teacher")] %}<a href="{{u}}" class="btn btn-outline-primary">{{n}}</a>{% endfor %}</div></div></div></div><div class="col-md-6"><div class="card"><div class="card-header"><i class="bi bi-info-circle"></i> Quick Stats</div><div class="card-body"><ul class="list-group"><li class="list-group-item"><i class="bi bi-check-circle text-success"></i> System running</li><li class="list-group-item"><i class="bi bi-people text-primary"></i> {{ students|length }} students</li><li class="list-group-item"><i class="bi bi-person-badge text-info"></i> {{ teachers|length }} teachers</li><li class="list-group-item"><i class="bi bi-building text-danger"></i> {{ classrooms|length }} classrooms</li></ul></div></div></div></div>
{% endblock %}''',
        'manage.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-12"><h2><i class="bi bi-gear"></i> System Management</h2><hr></div></div>
<div class="row mt-3">
<div class="col-md-4"><div class="card"><div class="card-header"><i class="bi bi-people"></i> Students</div><div class="card-body"><p><strong>Total:</strong> {{ students|length }}</p><a href="/students" class="btn btn-primary btn-sm">Manage</a></div></div></div>
<div class="col-md-4"><div class="card"><div class="card-header"><i class="bi bi-person-badge"></i> Teachers</div><div class="card-body"><p><strong>Total:</strong> {{ teachers|length }}</p><a href="/teachers" class="btn btn-primary btn-sm">Manage</a></div></div></div>
<div class="col-md-4"><div class="card"><div class="card-header"><i class="bi bi-building"></i> Classrooms</div><div class="card-body"><p><strong>Total:</strong> {{ classrooms|length }}</p><a href="/classrooms" class="btn btn-primary btn-sm">Manage</a></div></div></div>
</div>
<div class="row mt-3">
<div class="col-md-6"><div class="card"><div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assignments</div><div class="card-body"><a href="/assign/student" class="btn btn-outline-primary">Assign Student</a><a href="/assign/teacher" class="btn btn-outline-primary">Assign Teacher</a></div></div></div>
<div class="col-md-6"><div class="card"><div class="card-header"><i class="bi bi-database"></i> System Info</div><div class="card-body"><p><strong>Total Records:</strong> {{ students|length + teachers|length + classrooms|length }}</p></div></div></div></div>
{% endblock %}''',
        'student_dashboard.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-12"><div class="card"><div class="card-header"><i class="bi bi-person"></i> Welcome, {{student.name}}!</div><div class="card-body"><div class="row"><div class="col-md-6"><p><strong>ID:</strong> {{student.id}}</p><p><strong>Name:</strong> {{student.name}}</p><p><strong>Age:</strong> {{student.age}}</p><p><strong>Parent:</strong> {{student.parent}}</p></div><div class="col-md-6"><p><strong>Classroom:</strong> {{student.classroom or "Not assigned"}}</p><p><strong>Attendance:</strong> {% set a=att(student) %}{{"%.0f"|format(a)}}%</p><p><strong>Total Days:</strong> {{student.attendance|length}}</p></div></div></div></div></div></div>
<div class="row mt-4"><div class="col-12"><div class="card"><div class="card-header"><i class="bi bi-calendar-check"></i> My Attendance</div><div class="card-body">{% if student.attendance %}<table class="table"><thead><tr><th>Date</th><th>Status</th></tr></thead><tbody>{% for a in student.attendance %}<tr><td>{{a.date}}</td><td><span class="badge bg-{{'success' if a.status=='Present' else 'danger'}}">{{a.status}}</span></td></tr>{% endfor %}</tbody></table>{% else %}<p>No records yet.</p>{% endif %}</div></div></div></div>
{% endblock %}''',
        'teacher_dashboard.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-12"><div class="card"><div class="card-header"><i class="bi bi-person-badge"></i> Welcome, {{teacher.name}}!</div><div class="card-body"><div class="row"><div class="col-md-6"><p><strong>ID:</strong> {{teacher.id}}</p><p><strong>Name:</strong> {{teacher.name}}</p><p><strong>Age:</strong> {{teacher.age}}</p><p><strong>Subject:</strong> {{teacher.subject}}</p></div><div class="col-md-6"><p><strong>Classroom:</strong> {{teacher.classroom or "Not assigned"}}</p><p><strong>Contact:</strong> {{teacher.contact}}</p></div></div></div></div></div></div>
<div class="row mt-4"><div class="col-12"><div class="card"><div class="card-header"><i class="bi bi-people"></i> My Students</div><div class="card-body">{% if teacher.classroom %}{% set class_students=[] %}{% for s in students %}{% if s.classroom==teacher.classroom %}{% set _=class_students.append(s) %}{% endif %}{% endfor %}{% if class_students %}<table class="table"><thead><tr><th>ID</th><th>Name</th><th>Age</th><th>Parent</th><th>Attendance</th></tr></thead><tbody>{% for s in class_students %}<tr><td>{{s.id}}</td><td>{{s.name}}</td><td>{{s.age}}</td><td>{{s.parent}}</td><td><span class="badge bg-{% set a=att(s) %}{{'success' if a>=80 else 'warning' if a>=50 else 'danger'}}">{{"%.0f"|format(a)}}%</span></td></tr>{% endfor %}</tbody></table>{% else %}<p>No students assigned.</p>{% endif %}{% else %}<p>Not assigned to any classroom.</p>{% endif %}</div></div></div></div>
{% endblock %}''',
        'students.html':'''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mt-4"><h2><i class="bi bi-people" style="color:#FF69B4;"></i> Students</h2><a href="/students/add" class="btn btn-primary"><i class="bi bi-person-plus"></i> Add</a></div>
<div class="card mt-3"><div class="card-body"><div class="table-responsive"><table class="table table-hover"><thead><tr><th>ID</th><th>Name</th><th>Age</th><th>Parent</th><th>Room</th><th>%</th><th>Actions</th></tr></thead><tbody>{% for s in students %}<tr><td><strong>{{s.id}}</strong></td><td>{{s.name}}</td><td>{{s.age}}</td><td>{{s.parent}}</td><td>{% if s.classroom %}<span class="badge bg-info">{{s.classroom}}</span>{% else %}<span class="badge bg-secondary">-</span>{% endif %}</td><td>{% set a=att(s) %}<span class="badge bg-{{'success' if a>=80 else 'warning' if a>=50 else 'danger'}}">{{"%.0f"|format(a)}}%</span></td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#m{{s.id}}"><i class="bi bi-check-circle"></i></button><a href="/students/{{s.id}}" class="btn btn-sm btn-info"><i class="bi bi-eye"></i></a><a href="/students/edit/{{s.id}}" class="btn btn-sm btn-warning"><i class="bi bi-pencil"></i></a><button class="btn btn-sm btn-danger" onclick="if(confirm('Delete?'))location.href='/students/delete/{{s.id}}'"><i class="bi bi-trash"></i></button></td></tr>
<div class="modal fade" id="m{{s.id}}"><div class="modal-dialog"><div class="modal-content"><form method="POST" action="/mark"><div class="modal-header"><h5>Mark - {{s.name}}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><input type="hidden" name="name" value="{{s.name}}"><select name="status" class="form-select"><option value="Present">Present</option><option value="Absent">Absent</option></select></div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><button type="submit" class="btn btn-primary">Save</button></div></form></div></div></div>{% endfor %}</tbody></table></div></div></div>
{% endblock %}''',
        'add_student.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-person-plus"></i> Register Student</div><div class="card-body"><form method="POST"><div class="mb-3"><label class="form-label">Full Name <span class="text-danger">*</span></label><input type="text" class="form-control" name="name" placeholder="Enter full name" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"><small class="text-muted">Letters only</small></div><div class="mb-3"><label class="form-label">Age <span class="text-danger">*</span></label><input type="number" class="form-control" name="age" min="2" max="6" required></div><div class="mb-3"><label class="form-label">Phone <span class="text-danger">*</span></label><input type="text" class="form-control" name="contact" placeholder="0712345678" pattern="[0-9]{10}" maxlength="10" required oninput="this.value=this.value.replace(/[^0-9]/g,'')"><small class="text-muted">10 digits only</small></div><div class="mb-3"><label class="form-label">Parent <span class="text-danger">*</span></label><input type="text" class="form-control" name="parent" placeholder="Enter parent name" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"><small class="text-muted">Letters only</small></div><div class="d-flex gap-2"><button type="submit" class="btn btn-primary"><i class="bi bi-check-circle"></i> Register</button><a href="/students" class="btn btn-secondary">Cancel</a></div></form></div></div></div></div>
{% endblock %}''',
        'edit_student.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-pencil"></i> Edit Student</div><div class="card-body"><form method="POST"><div class="mb-3"><label class="form-label">Full Name</label><input type="text" class="form-control" name="name" value="{{student.name}}" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"></div><div class="mb-3"><label class="form-label">Age</label><input type="number" class="form-control" name="age" value="{{student.age}}" min="2" max="6" required></div><div class="mb-3"><label class="form-label">Phone</label><input type="text" class="form-control" name="contact" value="{{student.contact}}" pattern="[0-9]{10}" maxlength="10" required oninput="this.value=this.value.replace(/[^0-9]/g,'')"></div><div class="mb-3"><label class="form-label">Parent</label><input type="text" class="form-control" name="parent" value="{{student.parent}}" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"></div><div class="d-flex gap-2"><button type="submit" class="btn btn-primary"><i class="bi bi-check-circle"></i> Update</button><a href="/students" class="btn btn-secondary">Cancel</a></div></form></div></div></div></div>
{% endblock %}''',
        'teachers.html':'''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mt-4"><h2><i class="bi bi-person-badge" style="color:#87CEEB;"></i> Teachers</h2><a href="/teachers/add" class="btn btn-primary"><i class="bi bi-person-plus"></i> Add</a></div>
<div class="card mt-3"><div class="card-body"><div class="table-responsive"><table class="table table-hover"><thead><tr><th>ID</th><th>Name</th><th>Subject</th><th>Room</th><th>Contact</th><th>Actions</th></tr></thead><tbody>{% for t in teachers %}<tr><td><strong>{{t.id}}</strong></td><td>{{t.name}}</td><td><span class="badge bg-pink">{{t.subject}}</span></td><td>{% if t.classroom %}<span class="badge bg-info">{{t.classroom}}</span>{% else %}<span class="badge bg-secondary">-</span>{% endif %}</td><td>{{t.contact}}</td><td><a href="/teachers/edit/{{t.id}}" class="btn btn-sm btn-warning"><i class="bi bi-pencil"></i></a><button class="btn btn-sm btn-danger" onclick="if(confirm('Delete?'))location.href='/teachers/delete/{{t.id}}'"><i class="bi bi-trash"></i></button></td></tr>{% endfor %}</tbody></table></div></div></div>
{% endblock %}''',
        'add_teacher.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-person-plus"></i> Add Teacher</div><div class="card-body"><form method="POST"><div class="mb-3"><label class="form-label">Full Name</label><input type="text" class="form-control" name="name" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"></div><div class="mb-3"><label class="form-label">Age</label><input type="number" class="form-control" name="age" required></div><div class="mb-3"><label class="form-label">Phone</label><input type="text" class="form-control" name="contact" placeholder="0712345678" pattern="[0-9]{10}" maxlength="10" required oninput="this.value=this.value.replace(/[^0-9]/g,'')"></div><div class="mb-3"><label class="form-label">Subject</label><input type="text" class="form-control" name="subject" pattern="[A-Za-z\\s\\&\\,]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\&\\,]/g,'')"></div><div class="d-flex gap-2"><button type="submit" class="btn btn-primary">Add</button><a href="/teachers" class="btn btn-secondary">Cancel</a></div></form></div></div></div></div>
{% endblock %}''',
        'edit_teacher.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-pencil"></i> Edit Teacher</div><div class="card-body"><form method="POST"><div class="mb-3"><label class="form-label">Full Name</label><input type="text" class="form-control" name="name" value="{{teacher.name}}" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"></div><div class="mb-3"><label class="form-label">Age</label><input type="number" class="form-control" name="age" value="{{teacher.age}}" required></div><div class="mb-3"><label class="form-label">Phone</label><input type="text" class="form-control" name="contact" value="{{teacher.contact}}" pattern="[0-9]{10}" maxlength="10" required oninput="this.value=this.value.replace(/[^0-9]/g,'')"></div><div class="mb-3"><label class="form-label">Subject</label><input type="text" class="form-control" name="subject" value="{{teacher.subject}}" pattern="[A-Za-z\\s\\&\\,]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\&\\,]/g,'')"></div><div class="d-flex gap-2"><button type="submit" class="btn btn-primary">Update</button><a href="/teachers" class="btn btn-secondary">Cancel</a></div></form></div></div></div></div>
{% endblock %}''',
        'classrooms.html':'''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mt-4"><h2><i class="bi bi-building" style="color:#FF1493;"></i> Classrooms</h2><a href="/classrooms/add" class="btn btn-primary"><i class="bi bi-building-add"></i> Create</a></div>
<div class="row mt-3">{% for c in classrooms %}<div class="col-md-4 mb-3"><div class="card h-100"><div class="card-header">{{c.name}}</div><div class="card-body"><p><strong>Capacity:</strong> <span class="badge bg-pink">{{c.students|length}}/{{c.capacity}}</span></p><p><strong>Teacher:</strong> {{c.teacher or "-"}}</p><p><strong>Students:</strong> {{c.students|length}}</p><a href="/classrooms/{{c.name}}" class="btn btn-primary btn-sm"><i class="bi bi-eye"></i></a><a href="/classrooms/edit/{{c.name}}" class="btn btn-warning btn-sm"><i class="bi bi-pencil"></i></a><button class="btn btn-danger btn-sm" onclick="if(confirm('Delete?'))location.href='/classrooms/delete/{{c.name}}'"><i class="bi bi-trash"></i></button></div></div></div>{% endfor %}</div>
{% endblock %}''',
        'add_classroom.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-building-add"></i> Create Classroom</div><div class="card-body"><form method="POST"><div class="mb-3"><label class="form-label">Room Name</label><input type="text" class="form-control" name="name" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"></div><div class="mb-3"><label class="form-label">Capacity</label><input type="number" class="form-control" name="capacity" min="5" max="30" required><small class="text-muted">Min 5, Max 30</small></div><div class="d-flex gap-2"><button type="submit" class="btn btn-primary">Create</button><a href="/classrooms" class="btn btn-secondary">Cancel</a></div></form></div></div></div></div>
{% endblock %}''',
        'edit_classroom.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-pencil"></i> Edit Classroom</div><div class="card-body"><form method="POST"><div class="mb-3"><label class="form-label">Room Name</label><input type="text" class="form-control" name="name" value="{{classroom.name}}" pattern="[A-Za-z\\s\\\'\\-]+" required oninput="this.value=this.value.replace(/[^A-Za-z\\s\\\'\\-]/g,'')"></div><div class="mb-3"><label class="form-label">Capacity</label><input type="number" class="form-control" name="capacity" value="{{classroom.capacity}}" min="5" max="30" required></div><div class="d-flex gap-2"><button type="submit" class="btn btn-primary">Update</button><a href="/classrooms" class="btn btn-secondary">Cancel</a></div></form></div></div></div></div>
{% endblock %}''',
        'assign_student.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assign Student</div><div class="card-body">{% if students and classrooms %}<form method="POST"><div class="mb-3"><label class="form-label">Student</label><select class="form-select" name="student_name">{% for s in students %}<option value="{{s.name}}">{{s.name}} ({{s.id}})</option>{% endfor %}</select></div><div class="mb-3"><label class="form-label">Classroom</label><select class="form-select" name="class_name">{% for c in classrooms %}<option value="{{c.name}}">{{c.name}} ({{c.students|length}}/{{c.capacity}})</option>{% endfor %}</select></div><button type="submit" class="btn btn-primary">Assign</button><a href="/classrooms" class="btn btn-secondary">Cancel</a></form>{% else %}<p>No students or classrooms available.</p>{% endif %}</div></div></div></div>
{% endblock %}''',
        'assign_teacher.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assign Teacher</div><div class="card-body">{% if teachers and classrooms %}<form method="POST"><div class="mb-3"><label class="form-label">Teacher</label><select class="form-select" name="teacher_name">{% for t in teachers %}<option value="{{t.name}}">{{t.name}} ({{t.subject}})</option>{% endfor %}</select></div><div class="mb-3"><label class="form-label">Classroom</label><select class="form-select" name="class_name">{% for c in classrooms %}<option value="{{c.name}}">{{c.name}}</option>{% endfor %}</select></div><button type="submit" class="btn btn-primary">Assign</button><a href="/classrooms" class="btn btn-secondary">Cancel</a></form>{% else %}<p>No teachers or classrooms available.</p>{% endif %}</div></div></div></div>
{% endblock %}''',
        'student_detail.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-person"></i> Student Details</div><div class="card-body"><div class="row"><div class="col-md-6"><p><strong>ID:</strong> {{student.id}}</p><p><strong>Name:</strong> {{student.name}}</p><p><strong>Age:</strong> {{student.age}}</p><p><strong>Parent:</strong> {{student.parent}}</p></div><div class="col-md-6"><p><strong>Contact:</strong> {{student.contact}}</p><p><strong>Classroom:</strong> {{student.classroom or "Not assigned"}}</p><p><strong>Attendance:</strong> {% set a=att(student) %}{{"%.0f"|format(a)}}%</p><p><strong>Total Days:</strong> {{student.attendance|length}}</p></div></div><hr><h5>Attendance Records</h5>{% if student.attendance %}<table class="table"><thead><tr><th>Date</th><th>Status</th></tr></thead><tbody>{% for a in student.attendance %}<tr><td>{{a.date}}</td><td><span class="badge bg-{{'success' if a.status=='Present' else 'danger'}}">{{a.status}}</span></td></tr>{% endfor %}</tbody></table>{% else %}<p>No records.</p>{% endif %}<a href="/students" class="btn btn-secondary">Back</a></div></div></div></div>
{% endblock %}''',
        'classroom_detail.html':'''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header"><i class="bi bi-building"></i> Classroom Details</div><div class="card-body"><p><strong>Name:</strong> {{classroom.name}}</p><p><strong>Capacity:</strong> <span class="badge bg-pink">{{classroom.students|length}}/{{classroom.capacity}}</span></p><p><strong>Teacher:</strong> {{classroom.teacher or "Not assigned"}}</p><hr><h5>Students</h5>{% if classroom.students %}<ul class="list-group">{% for s in classroom.students %}<li class="list-group-item"><i class="bi bi-person"></i> {{s}}</li>{% endfor %}</ul>{% else %}<p>No students.</p>{% endif %}<a href="/classrooms" class="btn btn-secondary">Back</a></div></div></div></div>
{% endblock %}'''
    }
    for name, content in t.items():
        with open(os.path.join('templates', name), 'w') as f: f.write(content)

create_templates()

def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please login first!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            session['role'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('student_password')
        student = next((s for s in students if s['id'] == student_id), None)
        if student and password == "student123":
            session['student_logged_in'] = True
            session['student_id'] = student_id
            session['role'] = 'student'
            flash(f'Welcome {student["name"]}!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid student ID or password!', 'danger')
    return render_template('login.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        password = request.form.get('teacher_password')
        teacher = next((t for t in teachers if t['id'] == teacher_id), None)
        if teacher and password == "teacher123":
            session['teacher_logged_in'] = True
            session['teacher_id'] = teacher_id
            session['role'] = 'teacher'
            flash(f'Welcome {teacher["name"]}!', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid teacher ID or password!', 'danger')
    return render_template('login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('student_logged_in'):
        flash('Please login first!', 'danger')
        return redirect(url_for('login'))
    student = next((s for s in students if s['id'] == session.get('student_id')), None)
    if not student:
        flash('Student not found!', 'danger')
        return redirect(url_for('login'))
    return render_template('student_dashboard.html', student=student)

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if not session.get('teacher_logged_in'):
        flash('Please login first!', 'danger')
        return redirect(url_for('login'))
    teacher = next((t for t in teachers if t['id'] == session.get('teacher_id')), None)
    if not teacher:
        flash('Teacher not found!', 'danger')
        return redirect(url_for('login'))
    return render_template('teacher_dashboard.html', teacher=teacher, students=students)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', students=students, teachers=teachers, classrooms=classrooms)

@app.route('/manage')
@login_required
def manage():
    return render_template('manage.html', students=students, teachers=teachers, classrooms=classrooms)

@app.route('/students')
@login_required
def students_page():
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['GET','POST'])
@login_required
def add_student():
    if request.method == 'POST':
        n,a,c,p = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get('parent')
        if not all([n,a,c,p]): flash('All fields required!','danger')
        elif not validate_name(n): flash('Name cannot contain numbers!','danger')
        elif not validate_name(p): flash('Parent name cannot contain numbers!','danger')
        elif not validate_phone(c): flash('Phone must be 10 digits!','danger')
        else: add_student_data(n,a,c,p); flash(f'{n} added!','success'); return redirect(url_for('students_page'))
    return render_template('add_student.html')

@app.route('/students/edit/<id>', methods=['GET','POST'])
@login_required
def edit_student(id):
    s = next((s for s in students if s['id'] == id), None)
    if not s: flash('Not found!','danger'); return redirect(url_for('students_page'))
    if request.method == 'POST':
        n,a,c,p = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get('parent')
        if not all([n,a,c,p]): flash('All fields required!','danger')
        elif not validate_name(n): flash('Name cannot contain numbers!','danger')
        elif not validate_name(p): flash('Parent name cannot contain numbers!','danger')
        elif not validate_phone(c): flash('Phone must be 10 digits!','danger')
        else: s.update({'name':n.strip(),'age':int(a),'contact':c,'parent':p.strip()}); flash('Updated!','success'); return redirect(url_for('students_page'))
    return render_template('edit_student.html', student=s)

@app.route('/students/delete/<id>')
@login_required
def delete_student(id):
    global students
    s = next((s for s in students if s['id'] == id), None)
    if s: students = [x for x in students if x['id'] != id]; flash(f'{s["name"]} deleted!','success')
    else: flash('Not found!','danger')
    return redirect(url_for('students_page'))

@app.route('/mark', methods=['POST'])
@login_required
def mark():
    s = find('students', request.form.get('name'))
    if s:
        s['attendance'].append({"date": date.today().strftime("%Y-%m-%d"), "status": request.form.get('status')})
        flash('Marked!','success')
    else: flash('Not found!','danger')
    return redirect(url_for('students_page'))

@app.route('/students/<id>')
@login_required
def student_detail(id):
    s = next((s for s in students if s['id'] == id), None)
    return render_template('student_detail.html', student=s) if s else (flash('Not found!','danger') or redirect(url_for('students_page')))

@app.route('/teachers')
@login_required
def teachers_page():
    return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/add', methods=['GET','POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        n,a,c,s = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get('subject')
        if not all([n,a,c,s]): flash('All fields required!','danger')
        elif not validate_name(n): flash('Name cannot contain numbers!','danger')
        elif not validate_phone(c): flash('Phone must be 10 digits!','danger')
        elif not validate_name(s.replace('&','').replace(',','')): flash('Subject cannot contain numbers!','danger')
        else: add_teacher_data(n,a,c,s); flash(f'{n} added!','success'); return redirect(url_for('teachers_page'))
    return render_template('add_teacher.html')

@app.route('/teachers/edit/<id>', methods=['GET','POST'])
@login_required
def edit_teacher(id):
    t = next((t for t in teachers if t['id'] == id), None)
    if not t: flash('Not found!','danger'); return redirect(url_for('teachers_page'))
    if request.method == 'POST':
        n,a,c,s = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get('subject')
        if not all([n,a,c,s]): flash('All fields required!','danger')
        elif not validate_name(n): flash('Name cannot contain numbers!','danger')
        elif not validate_phone(c): flash('Phone must be 10 digits!','danger')
        elif not validate_name(s.replace('&','').replace(',','')): flash('Subject cannot contain numbers!','danger')
        else: t.update({'name':n.strip(),'age':int(a),'contact':c,'subject':s.strip()}); flash('Updated!','success'); return redirect(url_for('teachers_page'))
    return render_template('edit_teacher.html', teacher=t)

@app.route('/teachers/delete/<id>')
@login_required
def delete_teacher(id):
    global teachers
    t = next((t for t in teachers if t['id'] == id), None)
    if t: teachers = [x for x in teachers if x['id'] != id]; flash(f'{t["name"]} deleted!','success')
    else: flash('Not found!','danger')
    return redirect(url_for('teachers_page'))

@app.route('/classrooms')
@login_required
def classrooms_page():
    return render_template('classrooms.html', classrooms=classrooms)

@app.route('/classrooms/add', methods=['GET','POST'])
@login_required
def add_classroom():
    if request.method == 'POST':
        n,c = request.form.get('name'), request.form.get('capacity')
        if not n or not c: flash('All fields required!','danger')
        elif not validate_name(n): flash('Name cannot contain numbers!','danger')
        else: classrooms.append({"name": n.strip(), "capacity": int(c), "teacher": "", "students": [], "schedule": {}}); flash(f'{n} created!','success'); return redirect(url_for('classrooms_page'))
    return render_template('add_classroom.html')

@app.route('/classrooms/edit/<name>', methods=['GET','POST'])
@login_required
def edit_classroom(name):
    c = find('classrooms', name)
    if not c: flash('Not found!','danger'); return redirect(url_for('classrooms_page'))
    if request.method == 'POST':
        n,cap = request.form.get('name'), request.form.get('capacity')
        if not n or not cap: flash('All fields required!','danger')
        elif not validate_name(n): flash('Name cannot contain numbers!','danger')
        else:
            old = c['name']; c.update({'name':n.strip(),'capacity':int(cap)})
            for s in students:
                if s['classroom'] == old: s['classroom'] = n.strip()
            flash('Updated!','success'); return redirect(url_for('classrooms_page'))
    return render_template('edit_classroom.html', classroom=c)

@app.route('/classrooms/delete/<name>')
@login_required
def delete_classroom(name):
    global classrooms
    c = find('classrooms', name)
    if c:
        classrooms = [x for x in classrooms if x['name'] != name]
        for s in students:
            if s['classroom'] == name: s['classroom'] = ''
        flash(f'{name} deleted!','success')
    else: flash('Not found!','danger')
    return redirect(url_for('classrooms_page'))

@app.route('/assign/student', methods=['GET','POST'])
@login_required
def assign_student():
    if request.method == 'POST':
        s,c = find('students', request.form.get('student_name')), find('classrooms', request.form.get('class_name'))
        if s and c and len(c['students']) < c['capacity']:
            s['classroom'] = c['name']; c['students'].append(s['name']); flash('Assigned!','success')
        else: flash('Failed!','danger')
        return redirect(url_for('classrooms_page'))
    return render_template('assign_student.html', students=[s for s in students if not s['classroom']], classrooms=classrooms)

@app.route('/assign/teacher', methods=['GET','POST'])
@login_required
def assign_teacher():
    if request.method == 'POST':
        t,c = find('teachers', request.form.get('teacher_name')), find('classrooms', request.form.get('class_name'))
        if t and c: t['classroom'] = c['name']; c['teacher'] = t['name']; flash('Assigned!','success')
        else: flash('Failed!','danger')
        return redirect(url_for('classrooms_page'))
    return render_template('assign_teacher.html', teachers=[t for t in teachers if not t['classroom']], classrooms=classrooms)

@app.route('/classrooms/<name>')
@login_required
def classroom_detail(name):
    c = find('classrooms', name)
    return render_template('classroom_detail.html', classroom=c) if c else (flash('Not found!','danger') or redirect(url_for('classrooms_page')))

@app.route('/api/data')
@login_required
def api():
    return jsonify({"students": students, "teachers": teachers, "classrooms": classrooms})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
