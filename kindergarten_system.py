from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import date
import os, re
from functools import wraps

app = Flask(__name__)
app.secret_key = 'key'

USERS = {'admin': 'admin123', 'teacher': 'teacher123', 'director': 'director123'}


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


def vn(n): return bool(re.match(r'^[A-Za-z\s\'\-]+$', n.strip()))


def vp(p):
    digits = re.sub(r'\D', '', p)
    return bool(re.match(r'^[\d\s\-+()]+$', p)) and len(digits) == 10


def att(s):
    if not s.get('attendance'): return 0
    p = sum(1 for a in s['attendance'] if a['status'] == "Present")
    return (p / len(s['attendance'])) * 100 if s['attendance'] else 0


app.jinja_env.globals.update(att=att)

students, teachers, classrooms = [], [], []
sc = tc = 1

# Pre-create default classrooms
default_classrooms = ["Sunshine Stars", "Rainbow Garden", "Little Angels", "Happy Hearts", "Bright Minds"]
for name in default_classrooms:
    classrooms.append({"name": name, "capacity": 15, "teacher": "", "students": []})


def find(k, n):
    for i in globals()[k]:
        if i['name'].lower() == n.lower(): return i
    return None


def create_templates():
    if not os.path.exists('templates'): os.makedirs('templates')

    with open('templates/base.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Innocent Abel's Kindergarten</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
<style>
:root{--p:#FF69B4;--s:#87CEEB;--g:linear-gradient(135deg,#FF69B4,#87CEEB)}
body{background:#f8f9fa}
.navbar{background:var(--g)!important}
.navbar-brand{font-weight:bold;color:white!important}
.navbar-brand i{color:#FFD700}
.nav-link{color:white!important}
.card{border-radius:15px;border:none;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.card-header{background:var(--g);color:white;border-radius:15px 15px 0 0!important}
.btn-primary{background:var(--g);border:none}
.stat-number{font-size:2.5rem;font-weight:bold;color:#FF69B4}
footer{background:var(--g);color:white;padding:20px 0;margin-top:40px}
.alert{border-radius:10px}
</style>
</head>
<body>
<nav class="navbar navbar-expand-lg"><div class="container">
<a class="navbar-brand" href="/"><i class="bi bi-heart-fill"></i> Innocent Abel's</a>
<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
<span class="navbar-toggler-icon"></span></button>
<div class="collapse navbar-collapse" id="navbarNav">
<ul class="navbar-nav ms-auto">
<li class="nav-item"><a class="nav-link" href="/">Home</a></li>
{% if session.user %}
<li class="nav-item"><a class="nav-link" href="/students">Students</a></li>
<li class="nav-item"><a class="nav-link" href="/teachers">Teachers</a></li>
<li class="nav-item"><a class="nav-link" href="/classrooms">Classrooms</a></li>
<li class="nav-item"><a class="nav-link" href="/assign/student">Assign Student</a></li>
<li class="nav-item"><a class="nav-link" href="/assign/teacher">Assign Teacher</a></li>
<li class="nav-item"><a class="nav-link" href="/logout">Logout ({{session.user}})</a></li>
{% else %}
<li class="nav-item"><a class="nav-link" href="/login">Login</a></li>
{% endif %}
</ul></div></div></nav>
<div class="container mt-3">
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category, message in messages %}
<div class="alert alert-{{'success' if category=='success' else 'danger'}}">{{message}}</div>
{% endfor %}{% endif %}
{% endwith %}
{% block content %}{% endblock %}
</div>
<footer class="text-center"><p><i class="bi bi-heart-fill text-warning"></i> Innocent Abel's Learners - Where Every Child Matters</p></footer>
</body>
</html>''')

    with open('templates/login.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-5"><div class="col-md-4 mx-auto">
<div class="card"><div class="card-header text-center"><h4><i class="bi bi-box-arrow-in-right"></i> Login</h4></div>
<div class="card-body">
<form method="POST">
<div class="mb-3"><label>Username</label><input type="text" class="form-control" name="username" required></div>
<div class="mb-3"><label>Password</label><input type="password" class="form-control" name="password" required></div>
<button type="submit" class="btn btn-primary w-100">Login</button>
</form>
<hr><p class="text-center text-muted small">Demo: admin/admin123</p>
</div></div></div></div>
{% endblock %}''')

    with open('templates/index.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4"><div class="col-12 text-center">
<h1 style="background:var(--g);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Welcome to Innocent Abel's</h1>
<p>Where every child's journey begins with love and care.</p>
<p class="text-muted"><i class="bi bi-quote"></i> "Every child is a different kind of flower, and together they make this world a beautiful garden."</p>
</div></div>
{% if session.user %}
<div class="row mt-4">
<div class="col-md-4"><div class="card text-center"><div class="card-body">
<h3 class="stat-number">{{students|length}}</h3><h5>Students</h5>
<a href="/students" class="btn btn-primary btn-sm">View</a>
</div></div></div>
<div class="col-md-4"><div class="card text-center"><div class="card-body">
<h3 class="stat-number">{{teachers|length}}</h3><h5>Teachers</h5>
<a href="/teachers" class="btn btn-primary btn-sm">View</a>
</div></div></div>
<div class="col-md-4"><div class="card text-center"><div class="card-body">
<h3 class="stat-number">{{classrooms|length}}</h3><h5>Classrooms</h5>
<a href="/classrooms" class="btn btn-primary btn-sm">View</a>
</div></div></div>
</div>
<div class="row mt-4">
<div class="col-md-6"><div class="card"><div class="card-header">Quick Actions</div>
<div class="card-body"><div class="d-grid gap-2">
<a href="/students/add" class="btn btn-outline-primary">Add Student</a>
<a href="/teachers/add" class="btn btn-outline-primary">Add Teacher</a>
<a href="/assign/student" class="btn btn-outline-primary">Assign Student</a>
<a href="/assign/teacher" class="btn btn-outline-primary">Assign Teacher</a>
</div></div></div></div>
<div class="col-md-6"><div class="card"><div class="card-header">Statistics</div>
<div class="card-body"><ul class="list-group">
<li class="list-group-item">Total Students: {{students|length}}</li>
<li class="list-group-item">Total Teachers: {{teachers|length}}</li>
<li class="list-group-item">Total Classrooms: {{classrooms|length}}</li>
<li class="list-group-item">Assigned Students: {{students|selectattr("classroom","ne","")|list|length}}</li>
<li class="list-group-item">Assigned Teachers: {{teachers|selectattr("classroom","ne","")|list|length}}</li>
</ul></div></div></div></div>
{% else %}
<div class="row mt-4"><div class="col-md-6 mx-auto text-center">
<div class="card"><div class="card-body">
<h4><i class="bi bi-lock"></i> Please Login</h4>
<a href="/login" class="btn btn-primary">Login</a>
</div></div></div></div>
{% endif %}
{% endblock %}''')

    with open('templates/students.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="d-flex justify-content-between"><h2><i class="bi bi-people"></i> Our Students</h2><a href="/students/add" class="btn btn-primary">+ Add Student</a></div>
<div class="card mt-3"><div class="card-body">
<table class="table table-hover">
<thead><tr><th>ID</th><th>Name</th><th>Age</th><th>Parent</th><th>Classroom</th><th>Attendance</th><th>Actions</th></tr></thead>
<tbody>{% for s in students %}
<tr><td>{{s.id}}</td><td>{{s.name}}</td><td>{{s.age}}</td><td>{{s.parent}}</td>
<td>{{s.classroom or "Not assigned"}}</td>
<td>{% set a=att(s) %}<span class="badge bg-{{'success' if a>=80 else'warning' if a>=50 else'danger'}}">{{"%.0f"|format(a)}}%</span></td>
<td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#m{{s.id}}">Mark</button>
<a href="/students/{{s.id}}" class="btn btn-sm btn-info">View</a></td></tr>
<div class="modal fade" id="m{{s.id}}"><div class="modal-dialog"><div class="modal-content">
<form method="POST" action="/mark">
<div class="modal-header"><h5>Mark Attendance - {{s.name}}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
<div class="modal-body"><input type="hidden" name="name" value="{{s.name}}">
<select name="status" class="form-select"><option value="Present">Present</option><option value="Absent">Absent</option></select></div>
<div class="modal-footer"><button type="submit" class="btn btn-primary">Save</button></div>
</form></div></div></div>
{% endfor %}</tbody></table></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/add_student.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="row mt-4"><div class="col-md-6 mx-auto">
<div class="card"><div class="card-header"><i class="bi bi-person-plus"></i> Register New Student</div><div class="card-body">
<form method="POST">
<div class="mb-3"><label>Full Name</label>
<input type="text" class="form-control" name="name" placeholder="Enter student's full name" pattern="[A-Za-z\\s\\'\\-]+" required>
<small class="text-muted">Only letters, spaces, hyphens, apostrophes</small></div>
<div class="mb-3"><label>Age</label>
<input type="number" class="form-control" name="age" min="2" max="6" required></div>
<div class="mb-3"><label>Phone Number</label>
<input type="text" class="form-control" name="contact" placeholder="0712345678" pattern="[0-9]{10}" maxlength="10" required>
<small class="text-muted">Enter exactly 10 digits (e.g., 0712345678)</small></div>
<div class="mb-3"><label>Parent/Guardian Name</label>
<input type="text" class="form-control" name="parent" placeholder="Enter parent/guardian name" pattern="[A-Za-z\\s\\'\\-]+" required>
<small class="text-muted">Only letters, spaces, hyphens, apostrophes</small></div>
<button type="submit" class="btn btn-primary">Register Student</button>
<a href="/students" class="btn btn-secondary">Cancel</a>
</form></div></div></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/teachers.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="d-flex justify-content-between"><h2><i class="bi bi-person-badge"></i> Our Teachers</h2><a href="/teachers/add" class="btn btn-primary">+ Add Teacher</a></div>
<div class="card mt-3"><div class="card-body">
<table class="table table-hover">
<thead><tr><th>ID</th><th>Name</th><th>Subject</th><th>Classroom</th><th>Contact</th></tr></thead>
<tbody>{% for t in teachers %}
<tr><td>{{t.id}}</td><td>{{t.name}}</td><td>{{t.subject}}</td><td>{{t.classroom or "Not assigned"}}</td><td>{{t.contact}}</td></tr>
{% endfor %}</tbody></table></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/add_teacher.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="row mt-4"><div class="col-md-6 mx-auto">
<div class="card"><div class="card-header"><i class="bi bi-person-plus"></i> Add New Teacher</div><div class="card-body">
<form method="POST">
<div class="mb-3"><label>Full Name</label>
<input type="text" class="form-control" name="name" placeholder="Enter teacher's full name" pattern="[A-Za-z\\s\\'\\-]+" required>
<small class="text-muted">Only letters, spaces, hyphens, apostrophes</small></div>
<div class="mb-3"><label>Age</label><input type="number" class="form-control" name="age" required></div>
<div class="mb-3"><label>Phone Number</label>
<input type="text" class="form-control" name="contact" placeholder="0712345678" pattern="[0-9]{10}" maxlength="10" required>
<small class="text-muted">Enter exactly 10 digits (e.g., 0712345678)</small></div>
<div class="mb-3"><label>Subject/Specialty</label>
<input type="text" class="form-control" name="subject" placeholder="e.g., Art, Math, Reading" required></div>
<button type="submit" class="btn btn-primary">Add Teacher</button>
<a href="/teachers" class="btn btn-secondary">Cancel</a>
</form></div></div></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/classrooms.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="d-flex justify-content-between"><h2><i class="bi bi-building"></i> Our Classrooms</h2></div>
<div class="row mt-3">{% for c in classrooms %}
<div class="col-md-4 mb-3"><div class="card"><div class="card-header"><i class="bi bi-house-heart"></i> {{c.name}}</div>
<div class="card-body"><p><strong>Capacity:</strong> {{c.students|length}}/{{c.capacity}}</p>
<p><strong>Teacher:</strong> {{c.teacher or "Not assigned"}}</p>
<p><strong>Students:</strong> {{c.students|length}}</p>
<a href="/classrooms/{{c.name}}" class="btn btn-primary btn-sm">View Details</a>
</div></div></div>{% endfor %}</div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/assign_student.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="row mt-4"><div class="col-md-6 mx-auto">
<div class="card"><div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assign Student to Classroom</div><div class="card-body">
{% if students and classrooms %}
<form method="POST">
<div class="mb-3"><label>Select Student</label>
<select class="form-select" name="student_name" required>
<option value="">Choose a student...</option>{% for s in students %}<option value="{{s.name}}">{{s.name}} ({{s.id}})</option>{% endfor %}</select></div>
<div class="mb-3"><label>Select Classroom</label>
<select class="form-select" name="class_name" required>
<option value="">Choose a classroom...</option>{% for c in classrooms %}<option value="{{c.name}}">{{c.name}} ({{c.students|length}}/{{c.capacity}})</option>{% endfor %}</select></div>
<button type="submit" class="btn btn-primary">Assign Student</button>
<a href="/" class="btn btn-secondary">Cancel</a>
</form>
{% else %}<p>No students or classrooms available.</p>{% endif %}
</div></div></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/assign_teacher.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="row mt-4"><div class="col-md-6 mx-auto">
<div class="card"><div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assign Teacher to Classroom</div><div class="card-body">
{% if teachers and classrooms %}
<form method="POST">
<div class="mb-3"><label>Select Teacher</label>
<select class="form-select" name="teacher_name" required>
<option value="">Choose a teacher...</option>{% for t in teachers %}<option value="{{t.name}}">{{t.name}} ({{t.subject}})</option>{% endfor %}</select></div>
<div class="mb-3"><label>Select Classroom</label>
<select class="form-select" name="class_name" required>
<option value="">Choose a classroom...</option>{% for c in classrooms %}<option value="{{c.name}}">{{c.name}}</option>{% endfor %}</select></div>
<button type="submit" class="btn btn-primary">Assign Teacher</button>
<a href="/" class="btn btn-secondary">Cancel</a>
</form>
{% else %}<p>No teachers or classrooms available.</p>{% endif %}
</div></div></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/student_detail.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="row mt-4"><div class="col-md-8 mx-auto">
<div class="card"><div class="card-header"><i class="bi bi-person"></i> Student Details - {{student.name}}</div><div class="card-body">
<div class="row"><div class="col-md-6">
<p><strong>Student ID:</strong> {{student.id}}</p>
<p><strong>Full Name:</strong> {{student.name}}</p>
<p><strong>Age:</strong> {{student.age}}</p>
<p><strong>Parent/Guardian:</strong> {{student.parent}}</p></div>
<div class="col-md-6">
<p><strong>Phone:</strong> {{student.contact}}</p>
<p><strong>Classroom:</strong> {{student.classroom or "Not assigned"}}</p>
<p><strong>Attendance Rate:</strong> {{"%.0f"|format(att(student))}}%</p>
<p><strong>Total Days:</strong> {{student.attendance|length}}</p></div></div>
<hr><h5><i class="bi bi-calendar-check"></i> Attendance Records</h5>
{% if student.attendance %}
<table class="table table-sm"><thead><tr><th>Date</th><th>Status</th></tr></thead>
<tbody>{% for a in student.attendance %}
<tr><td>{{a.date}}</td><td><span class="badge bg-{{'success' if a.status=='Present' else 'danger'}}">{{a.status}}</span></td></tr>
{% endfor %}</tbody></table>
{% else %}<p class="text-muted">No attendance records yet.</p>{% endif %}
<a href="/students" class="btn btn-secondary">Back to Students</a>
</div></div></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')

    with open('templates/classroom_detail.html', 'w') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
{% if session.user %}
<div class="row mt-4"><div class="col-md-8 mx-auto">
<div class="card"><div class="card-header"><i class="bi bi-building"></i> Classroom Details - {{classroom.name}}</div><div class="card-body">
<p><strong>Classroom Name:</strong> {{classroom.name}}</p>
<p><strong>Capacity:</strong> {{classroom.students|length}}/{{classroom.capacity}}</p>
<p><strong>Teacher:</strong> {{classroom.teacher or "Not assigned"}}</p>
<hr><h5><i class="bi bi-people"></i> Students in this Classroom</h5>
{% if classroom.students %}
<ul class="list-group">{% for s in classroom.students %}
<li class="list-group-item"><i class="bi bi-person"></i> {{s}}</li>
{% endfor %}</ul>
{% else %}<p class="text-muted">No students assigned to this classroom.</p>{% endif %}
<a href="/classrooms" class="btn btn-secondary">Back to Classrooms</a>
</div></div></div></div>
{% else %}<div class="alert alert-danger">Please login first</div>{% endif %}
{% endblock %}''')


create_templates()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if u in USERS and USERS[u] == p:
            session['user'] = u
            flash(f'Welcome {u}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('index.html', students=students, teachers=teachers, classrooms=classrooms)


@app.route('/students')
@login_required
def students_page():
    return render_template('students.html', students=students)


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    global sc
    if request.method == 'POST':
        n, a, c, p = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get(
            'parent')
        if not all([n, a, c, p]):
            flash('All fields are required!', 'danger')
        elif not vn(n) or not vn(p):
            flash('Name must contain only letters, spaces, hyphens, and apostrophes!', 'danger')
        elif not vp(c):
            flash('Phone number must be exactly 10 digits! (e.g., 0712345678)', 'danger')
        else:
            students.append({"id": f"S{sc:04d}", "name": n.strip(), "age": int(a), "contact": c, "parent": p.strip(),
                             "classroom": "", "attendance": []})
            sc += 1
            flash(f'{n} has been registered successfully!', 'success')
            return redirect(url_for('students_page'))
    return render_template('add_student.html')


@app.route('/mark', methods=['POST'])
@login_required
def mark():
    s = find('students', request.form.get('name'))
    if s:
        s['attendance'].append({"date": date.today().strftime("%Y-%m-%d"), "status": request.form.get('status')})
        flash('Attendance marked successfully!', 'success')
    else:
        flash('Student not found!', 'danger')
    return redirect(url_for('students_page'))


@app.route('/students/<id>')
@login_required
def student_detail(id):
    s = next((s for s in students if s['id'] == id), None)
    return render_template('student_detail.html', student=s) if s else (
                flash('Student not found!', 'danger') or redirect(url_for('students_page')))


@app.route('/teachers')
@login_required
def teachers_page():
    return render_template('teachers.html', teachers=teachers)


@app.route('/teachers/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    global tc
    if request.method == 'POST':
        n, a, c, s = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get(
            'subject')
        if not all([n, a, c, s]):
            flash('All fields are required!', 'danger')
        elif not vn(n):
            flash('Name must contain only letters, spaces, hyphens, and apostrophes!', 'danger')
        elif not vp(c):
            flash('Phone number must be exactly 10 digits! (e.g., 0712345678)', 'danger')
        else:
            teachers.append({"id": f"T{tc:04d}", "name": n.strip(), "age": int(a), "contact": c, "subject": s.strip(),
                             "classroom": ""})
            tc += 1
            flash(f'{n} has been added successfully!', 'success')
            return redirect(url_for('teachers_page'))
    return render_template('add_teacher.html')


@app.route('/classrooms')
@login_required
def classrooms_page():
    return render_template('classrooms.html', classrooms=classrooms)


@app.route('/assign/student', methods=['GET', 'POST'])
@login_required
def assign_student():
    if request.method == 'POST':
        sn, cn = request.form.get('student_name'), request.form.get('class_name')
        s, c = find('students', sn), find('classrooms', cn)
        if s and c and len(c['students']) < c['capacity']:
            s['classroom'] = c['name']
            c['students'].append(s['name'])
            flash(f'{sn} assigned to {cn} successfully!', 'success')
        else:
            flash('Assignment failed! Classroom might be full or student already assigned.', 'danger')
        return redirect(url_for('index'))
    return render_template('assign_student.html', students=[s for s in students if not s['classroom']],
                           classrooms=classrooms)


@app.route('/assign/teacher', methods=['GET', 'POST'])
@login_required
def assign_teacher():
    if request.method == 'POST':
        tn, cn = request.form.get('teacher_name'), request.form.get('class_name')
        t, c = find('teachers', tn), find('classrooms', cn)
        if t and c:
            t['classroom'] = c['name']
            c['teacher'] = t['name']
            flash(f'{tn} assigned to {cn} successfully!', 'success')
        else:
            flash('Assignment failed! Teacher might already be assigned.', 'danger')
        return redirect(url_for('index'))
    return render_template('assign_teacher.html', teachers=[t for t in teachers if not t['classroom']],
                           classrooms=classrooms)


@app.route('/classrooms/<name>')
@login_required
def classroom_detail(name):
    c = find('classrooms', name)
    return render_template('classroom_detail.html', classroom=c) if c else (
                flash('Classroom not found!', 'danger') or redirect(url_for('classrooms_page')))


@app.route('/api/data')
@login_required
def api_data():
    return jsonify({"students": students, "teachers": teachers, "classrooms": classrooms})


@app.route('/api/students')
@login_required
def api_students():
    return jsonify(students)


@app.route('/api/teachers')
@login_required
def api_teachers():
    return jsonify(teachers)


@app.route('/api/classrooms')
@login_required
def api_classrooms():
    return jsonify(classrooms)


@app.route('/api/students/add', methods=['POST'])
@login_required
def api_add_student():
    global sc
    data = request.json
    n, a, c, p = data.get('name'), data.get('age'), data.get('contact'), data.get('parent')
    if not all([n, a, c, p]):
        return jsonify({"error": "All fields required"}), 400
    if not vn(n) or not vn(p):
        return jsonify({"error": "Invalid name"}), 400
    if not vp(c):
        return jsonify({"error": "Phone must be exactly 10 digits"}), 400
    students.append(
        {"id": f"S{sc:04d}", "name": n.strip(), "age": int(a), "contact": c, "parent": p.strip(), "classroom": "",
         "attendance": []})
    sc += 1
    return jsonify({"success": f"{n} added", "student": students[-1]}), 201


@app.route('/api/teachers/add', methods=['POST'])
@login_required
def api_add_teacher():
    global tc
    data = request.json
    n, a, c, s = data.get('name'), data.get('age'), data.get('contact'), data.get('subject')
    if not all([n, a, c, s]):
        return jsonify({"error": "All fields required"}), 400
    if not vn(n):
        return jsonify({"error": "Invalid name"}), 400
    if not vp(c):
        return jsonify({"error": "Phone must be exactly 10 digits"}), 400
    teachers.append(
        {"id": f"T{tc:04d}", "name": n.strip(), "age": int(a), "contact": c, "subject": s.strip(), "classroom": ""})
    tc += 1
    return jsonify({"success": f"{n} added", "teacher": teachers[-1]}), 201


@app.route('/api/assign/student', methods=['POST'])
@login_required
def api_assign_student():
    data = request.json
    sn, cn = data.get('student_name'), data.get('class_name')
    s, c = find('students', sn), find('classrooms', cn)
    if not s or not c:
        return jsonify({"error": "Student or classroom not found"}), 404
    if len(c['students']) >= c['capacity']:
        return jsonify({"error": "Classroom is full"}), 400
    s['classroom'] = c['name']
    c['students'].append(s['name'])
    return jsonify({"success": f"{sn} assigned to {cn}"}), 200


@app.route('/api/assign/teacher', methods=['POST'])
@login_required
def api_assign_teacher():
    data = request.json
    tn, cn = data.get('teacher_name'), data.get('class_name')
    t, c = find('teachers', tn), find('classrooms', cn)
    if not t or not c:
        return jsonify({"error": "Teacher or classroom not found"}), 404
    t['classroom'] = c['name']
    c['teacher'] = t['name']
    return jsonify({"success": f"{tn} assigned to {cn}"}), 200


@app.route('/api/attendance', methods=['POST'])
@login_required
def api_mark_attendance():
    data = request.json
    name, status = data.get('name'), data.get('status', 'Present')
    s = find('students', name)
    if not s:
        return jsonify({"error": "Student not found"}), 404
    s['attendance'].append({"date": date.today().strftime("%Y-%m-%d"), "status": status})
    return jsonify({"success": f"Attendance marked for {name}"}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
