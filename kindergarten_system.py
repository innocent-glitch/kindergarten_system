from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
import os
import sys

app = Flask(__name__)
app.secret_key = 'abel_kindergarten_secret'

def get_attendance_percentage(student):
    if not student.get('attendance'):
        return 0
    present = sum(1 for a in student['attendance'] if a['status'] == "Present")
    if len(student['attendance']) == 0:
        return 0
    return (present / len(student['attendance'])) * 100

app.jinja_env.globals.update(get_attendance_percentage=get_attendance_percentage)

students = []
teachers = []
classrooms = []
student_counter = 1
teacher_counter = 1

def find_student(name):
    for s in students:
        if s['name'].lower() == name.lower():
            return s
    return None

def find_teacher(name):
    for t in teachers:
        if t['name'].lower() == name.lower():
            return t
    return None

def find_classroom(name):
    for c in classrooms:
        if c['name'].lower() == name.lower():
            return c
    return None

def assign_student(student_name, class_name):
    student = find_student(student_name)
    classroom = find_classroom(class_name)
    if student and classroom:
        if len(classroom['students']) < classroom['capacity']:
            student['classroom'] = class_name
            classroom['students'].append(student_name)
            return True
    return False

def assign_teacher(teacher_name, class_name):
    teacher = find_teacher(teacher_name)
    classroom = find_classroom(class_name)
    if teacher and classroom:
        teacher['classroom'] = class_name
        classroom['teacher'] = teacher_name
        return True
    return False

def mark_attendance(student_name, status="Present"):
    student = find_student(student_name)
    if student:
        today = date.today().strftime("%Y-%m-%d")
        student['attendance'].append({"date": today, "status": status})
        return True
    return False

@app.route('/')
def index():
    return render_template('index.html',
                           students=students,
                           teachers=teachers,
                           classrooms=classrooms,
                           system_name="Abel's Little Learners",
                           get_attendance_percentage=get_attendance_percentage)

@app.route('/students')
def view_students():
    return render_template('students.html',
                           students=students,
                           get_attendance_percentage=get_attendance_percentage)

@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    global student_counter
    if request.method == 'POST':
        name = request.form.get('name')
        age = int(request.form.get('age'))
        contact = request.form.get('contact')
        parent = request.form.get('parent')

        if name and age and contact and parent:
            students.append({
                "id": f"S{student_counter:04d}",
                "name": name,
                "age": age,
                "contact": contact,
                "parent": parent,
                "classroom": "",
                "attendance": []
            })
            student_counter += 1
            flash(f'Student {name} added successfully!', 'success')
            return redirect(url_for('view_students'))
        flash('All fields are required!', 'danger')
    return render_template('add_student.html')

@app.route('/students/attendance', methods=['POST'])
def attendance():
    name = request.form.get('student_name')
    status = request.form.get('status')
    if mark_attendance(name, status):
        flash(f'Attendance marked for {name}: {status}', 'success')
    else:
        flash('Student not found!', 'danger')
    return redirect(url_for('view_students'))

@app.route('/students/<student_id>')
def student_detail(student_id):
    student = next((s for s in students if s['id'] == student_id), None)
    if student:
        return render_template('student_detail.html',
                               student=student,
                               get_attendance_percentage=get_attendance_percentage)
    flash('Student not found!', 'danger')
    return redirect(url_for('view_students'))

@app.route('/teachers')
def view_teachers():
    return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/add', methods=['GET', 'POST'])
def add_teacher():
    global teacher_counter
    if request.method == 'POST':
        name = request.form.get('name')
        age = int(request.form.get('age'))
        contact = request.form.get('contact')
        subject = request.form.get('subject')

        if name and age and contact and subject:
            teachers.append({
                "id": f"T{teacher_counter:04d}",
                "name": name,
                "age": age,
                "contact": contact,
                "subject": subject,
                "classroom": ""
            })
            teacher_counter += 1
            flash(f'Teacher {name} added successfully!', 'success')
            return redirect(url_for('view_teachers'))
        flash('All fields are required!', 'danger')
    return render_template('add_teacher.html')

@app.route('/classrooms')
def view_classrooms():
    return render_template('classrooms.html', classrooms=classrooms)

@app.route('/classrooms/add', methods=['GET', 'POST'])
def add_classroom():
    if request.method == 'POST':
        name = request.form.get('name')
        capacity = int(request.form.get('capacity'))

        if name and capacity:
            classrooms.append({
                "name": name,
                "capacity": capacity,
                "teacher": "",
                "students": [],
                "schedule": {}
            })
            flash(f'Classroom {name} created!', 'success')
            return redirect(url_for('view_classrooms'))
        flash('All fields are required!', 'danger')
    return render_template('add_classroom.html')

@app.route('/assign/student', methods=['GET', 'POST'])
def assign_student_view():
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        class_name = request.form.get('class_name')
        if assign_student(student_name, class_name):
            flash(f'{student_name} assigned to {class_name}!', 'success')
        else:
            flash('Assignment failed! Classroom might be full.', 'danger')
        return redirect(url_for('view_classrooms'))

    unassigned = [s for s in students if not s['classroom']]
    return render_template('assign_student.html',
                           students=unassigned,
                           classrooms=classrooms)

@app.route('/assign/teacher', methods=['GET', 'POST'])
def assign_teacher_view():
    if request.method == 'POST':
        teacher_name = request.form.get('teacher_name')
        class_name = request.form.get('class_name')
        if assign_teacher(teacher_name, class_name):
            flash(f'{teacher_name} assigned to {class_name}!', 'success')
        else:
            flash('Assignment failed!', 'danger')
        return redirect(url_for('view_classrooms'))

    unassigned = [t for t in teachers if not t['classroom']]
    return render_template('assign_teacher.html',
                           teachers=unassigned,
                           classrooms=classrooms)

@app.route('/classrooms/<classroom_name>')
def classroom_detail(classroom_name):
    classroom = find_classroom(classroom_name)
    if classroom:
        class_students = [s for s in students if s['classroom'] == classroom_name]
        return render_template('classroom_detail.html',
                               classroom=classroom,
                               students=class_students)
    flash('Classroom not found!', 'danger')
    return redirect(url_for('view_classrooms'))

@app.route('/api/data')
def api_data():
    return jsonify({
        "students": students,
        "teachers": teachers,
        "classrooms": classrooms
    })

@app.route('/api/students')
def api_students():
    return jsonify(students)

@app.route('/api/teachers')
def api_teachers():
    return jsonify(teachers)

@app.route('/api/classrooms')
def api_classrooms():
    return jsonify(classrooms)

def create_templates():
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)

    with open(os.path.join(template_dir, 'base.html'), 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ system_name or "Kindergarten" }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        :root {
            --pink: #FF69B4;
            --sky: #87CEEB;
            --gradient: linear-gradient(135deg, #FF69B4, #87CEEB);
        }
        body { background: #f8f9fa; }
        .navbar { background: var(--gradient) !important; }
        .navbar-brand { font-weight: bold; color: white !important; }
        .navbar-brand i { color: #FFD700; }
        .nav-link { color: white !important; }
        .nav-link:hover { background: rgba(255,255,255,0.2); border-radius: 5px; }
        .card { border-radius: 15px; border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card-header { background: var(--gradient); color: white; border-radius: 15px 15px 0 0 !important; }
        .btn-primary { background: var(--gradient); border: none; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(255,105,180,0.3); }
        .stat-number { font-size: 2.5rem; font-weight: bold; color: #FF69B4; }
        footer { background: var(--gradient); color: white; padding: 20px 0; margin-top: 40px; }
        .badge-pink { background: #FF69B4; color: white; }
        .badge-sky { background: #87CEEB; color: white; }
        .flash-messages { margin-top: 20px; }
        .main-content { min-height: 70vh; }
        .btn-outline-primary {
            border-color: #FF69B4;
            color: #FF69B4;
        }
        .btn-outline-primary:hover {
            background: var(--gradient);
            color: white;
            border-color: transparent;
        }
        .btn-outline-success {
            border-color: #87CEEB;
            color: #87CEEB;
        }
        .btn-outline-success:hover {
            background: var(--gradient);
            color: white;
            border-color: transparent;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="bi bi-heart-fill"></i> {{ system_name or "Kindergarten" }}</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="/"><i class="bi bi-house"></i> Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link" href="/students"><i class="bi bi-people"></i> Students</a></li>
                    <li class="nav-item"><a class="nav-link" href="/teachers"><i class="bi bi-person-badge"></i> Teachers</a></li>
                    <li class="nav-item"><a class="nav-link" href="/classrooms"><i class="bi bi-building"></i> Classrooms</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container main-content">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                            <i class="bi bi-{{ 'check-circle' if category == 'success' else 'exclamation-circle' }}"></i>
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>

    <footer>
        <div class="container text-center">
            <p><i class="bi bi-heart-fill text-warning"></i> Abel's Little Learners - Nurturing Young Minds <i class="bi bi-heart-fill text-warning"></i></p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''')

    with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-12 text-center">
        <h1 class="display-4" style="background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            <i class="bi bi-heart-fill" style="color: #FF69B4;"></i> Welcome to Abel's Little Learners
        </h1>
        <p class="lead">Where every child's journey begins with love and care.</p>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <i class="bi bi-people" style="font-size: 3rem; color: #FF69B4;"></i>
                <h3 class="stat-number">{{ students|length }}</h3>
                <h5>Students</h5>
                <a href="/students" class="btn btn-primary btn-sm">View All</a>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <i class="bi bi-person-badge" style="font-size: 3rem; color: #87CEEB;"></i>
                <h3 class="stat-number">{{ teachers|length }}</h3>
                <h5>Teachers</h5>
                <a href="/teachers" class="btn btn-primary btn-sm">View All</a>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <i class="bi bi-building" style="font-size: 3rem; color: #FF1493;"></i>
                <h3 class="stat-number">{{ classrooms|length }}</h3>
                <h5>Classrooms</h5>
                <a href="/classrooms" class="btn btn-primary btn-sm">View All</a>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header"><i class="bi bi-clock-history"></i> Quick Actions</div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="/students/add" class="btn btn-outline-primary"><i class="bi bi-person-plus"></i> Add Student</a>
                    <a href="/teachers/add" class="btn btn-outline-success"><i class="bi bi-person-plus"></i> Add Teacher</a>
                    <a href="/classrooms/add" class="btn btn-outline-primary"><i class="bi bi-building-add"></i> Create Classroom</a>
                    <a href="/assign/student" class="btn btn-outline-primary"><i class="bi bi-arrow-right-circle"></i> Assign Student</a>
                    <a href="/assign/teacher" class="btn btn-outline-success"><i class="bi bi-arrow-right-circle"></i> Assign Teacher</a>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header"><i class="bi bi-info-circle"></i> Quick Stats</div>
            <div class="card-body">
                <ul class="list-group">
                    <li class="list-group-item"><i class="bi bi-check-circle text-success"></i> System running</li>
                    <li class="list-group-item"><i class="bi bi-people text-primary"></i> {{ students|length }} students enrolled</li>
                    <li class="list-group-item"><i class="bi bi-person-badge text-info"></i> {{ teachers|length }} teachers</li>
                    <li class="list-group-item"><i class="bi bi-building text-danger"></i> {{ classrooms|length }} classrooms</li>
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'students.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mt-4">
    <h2><i class="bi bi-people" style="color: #FF69B4;"></i> Students</h2>
    <a href="/students/add" class="btn btn-primary"><i class="bi bi-person-plus"></i> Add Student</a>
</div>
<div class="card mt-3">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Parent</th>
                        <th>Classroom</th>
                        <th>Attendance</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for s in students %}
                    <tr>
                        <td><strong>{{ s.id }}</strong></td>
                        <td>{{ s.name }}</td>
                        <td>{{ s.age }}</td>
                        <td>{{ s.parent }}</td>
                        <td>
                            {% if s.classroom %}
                                <span class="badge badge-sky">{{ s.classroom }}</span>
                            {% else %}
                                <span class="badge bg-secondary">Not assigned</span>
                            {% endif %}
                        </td>
                        <td>
                            {% set att = get_attendance_percentage(s) %}
                            <span class="badge bg-{% if att >= 80 %}success{% elif att >= 50 %}warning{% else %}danger{% endif %}">
                                {{ "%.1f"|format(att) }}%
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#attendanceModal{{ s.id }}">
                                <i class="bi bi-check-circle"></i>
                            </button>
                            <a href="/students/{{ s.id }}" class="btn btn-sm btn-outline-info">
                                <i class="bi bi-eye"></i>
                            </a>
                        </td>
                    </tr>
                    <div class="modal fade" id="attendanceModal{{ s.id }}" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <form method="POST" action="/students/attendance">
                                    <div class="modal-header">
                                        <h5>Mark Attendance - {{ s.name }}</h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body">
                                        <input type="hidden" name="student_name" value="{{ s.name }}">
                                        <div class="mb-3">
                                            <label class="form-label">Status</label>
                                            <select name="status" class="form-select">
                                                <option value="Present">Present</option>
                                                <option value="Absent">Absent</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                        <button type="submit" class="btn btn-primary">Save</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'add_student.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-md-6 mx-auto">
        <div class="card">
            <div class="card-header"><i class="bi bi-person-plus"></i> Register New Student</div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Full Name <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Age <span class="text-danger">*</span></label>
                        <input type="number" class="form-control" name="age" min="2" max="6" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Contact Number <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="contact" placeholder="e.g., 555-1234" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Parent/Guardian <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="parent" required>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary"><i class="bi bi-check-circle"></i> Register</button>
                        <a href="/students" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'teachers.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mt-4">
    <h2><i class="bi bi-person-badge" style="color: #87CEEB;"></i> Teachers</h2>
    <a href="/teachers/add" class="btn btn-primary"><i class="bi bi-person-plus"></i> Add Teacher</a>
</div>
<div class="card mt-3">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>Subject</th>
                        <th>Classroom</th>
                        <th>Contact</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in teachers %}
                    <tr>
                        <td><strong>{{ t.id }}</strong></td>
                        <td>{{ t.name }}</td>
                        <td>{{ t.age }}</td>
                        <td><span class="badge badge-pink">{{ t.subject }}</span></td>
                        <td>
                            {% if t.classroom %}
                                <span class="badge badge-sky">{{ t.classroom }}</span>
                            {% else %}
                                <span class="badge bg-secondary">Not assigned</span>
                            {% endif %}
                        </td>
                        <td>{{ t.contact }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'add_teacher.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-md-6 mx-auto">
        <div class="card">
            <div class="card-header"><i class="bi bi-person-plus"></i> Add New Teacher</div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Full Name <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Age <span class="text-danger">*</span></label>
                        <input type="number" class="form-control" name="age" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Contact <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="contact" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Subject/Specialty <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="subject" placeholder="e.g., Art, Math, Reading" required>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary"><i class="bi bi-check-circle"></i> Add Teacher</button>
                        <a href="/teachers" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'classrooms.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mt-4">
    <h2><i class="bi bi-building" style="color: #FF1493;"></i> Classrooms</h2>
    <a href="/classrooms/add" class="btn btn-primary"><i class="bi bi-building-add"></i> Create Classroom</a>
</div>
<div class="row mt-3">
    {% for c in classrooms %}
    <div class="col-md-4 mb-3">
        <div class="card h-100">
            <div class="card-header">{{ c.name }}</div>
            <div class="card-body">
                <p><strong>Capacity:</strong> <span class="badge badge-pink">{{ c.students|length }}/{{ c.capacity }}</span></p>
                <p><strong>Teacher:</strong> {{ c.teacher or "Not assigned" }}</p>
                <p><strong>Students:</strong> {{ c.students|length }}</p>
                <a href="/classrooms/{{ c.name }}" class="btn btn-primary btn-sm"><i class="bi bi-eye"></i> View Details</a>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
<div class="row mt-3">
    <div class="col-12">
        <div class="card">
            <div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assignments</div>
            <div class="card-body">
                <a href="/assign/student" class="btn btn-outline-primary"><i class="bi bi-person-plus"></i> Assign Student</a>
                <a href="/assign/teacher" class="btn btn-outline-success"><i class="bi bi-person-plus"></i> Assign Teacher</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'add_classroom.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-md-6 mx-auto">
        <div class="card">
            <div class="card-header"><i class="bi bi-building-add"></i> Create Classroom</div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Classroom Name <span class="text-danger">*</span></label>
                        <input type="text" class="form-control" name="name" placeholder="e.g., Sunshine Stars" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Capacity <span class="text-danger">*</span></label>
                        <input type="number" class="form-control" name="capacity" min="5" max="30" required>
                        <small class="text-muted">Minimum 5, Maximum 30 students</small>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary"><i class="bi bi-check-circle"></i> Create</button>
                        <a href="/classrooms" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'assign_student.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-md-6 mx-auto">
        <div class="card">
            <div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assign Student to Classroom</div>
            <div class="card-body">
                {% if students and classrooms %}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Student <span class="text-danger">*</span></label>
                        <select class="form-select" name="student_name" required>
                            <option value="">Select Student</option>
                            {% for s in students %}
                                <option value="{{ s.name }}">{{ s.name }} ({{ s.id }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Classroom <span class="text-danger">*</span></label>
                        <select class="form-select" name="class_name" required>
                            <option value="">Select Classroom</option>
                            {% for c in classrooms %}
                                <option value="{{ c.name }}">{{ c.name }} ({{ c.students|length }}/{{ c.capacity }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary"><i class="bi bi-check-circle"></i> Assign</button>
                        <a href="/classrooms" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
                {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-info-circle" style="font-size: 3rem; color: #FFD700;"></i>
                    <p>No students or classrooms available to assign.</p>
                    <a href="/students/add" class="btn btn-primary btn-sm">Add Student</a>
                    <a href="/classrooms/add" class="btn btn-outline-primary btn-sm">Create Classroom</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'assign_teacher.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-md-6 mx-auto">
        <div class="card">
            <div class="card-header"><i class="bi bi-arrow-right-circle"></i> Assign Teacher to Classroom</div>
            <div class="card-body">
                {% if teachers and classrooms %}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Teacher <span class="text-danger">*</span></label>
                        <select class="form-select" name="teacher_name" required>
                            <option value="">Select Teacher</option>
                            {% for t in teachers %}
                                <option value="{{ t.name }}">{{ t.name }} ({{ t.subject }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Classroom <span class="text-danger">*</span></label>
                        <select class="form-select" name="class_name" required>
                            <option value="">Select Classroom</option>
                            {% for c in classrooms %}
                                <option value="{{ c.name }}">{{ c.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary"><i class="bi bi-check-circle"></i> Assign</button>
                        <a href="/classrooms" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
                {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-info-circle" style="font-size: 3rem; color: #9370DB;"></i>
                    <p>No teachers or classrooms available to assign.</p>
                    <a href="/teachers/add" class="btn btn-primary btn-sm">Add Teacher</a>
                    <a href="/classrooms/add" class="btn btn-outline-primary btn-sm">Create Classroom</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'student_detail.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-md-8 mx-auto">
        <div class="card">
            <div class="card-header"><i class="bi bi-person"></i> Student Details</div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>ID:</strong> {{ student.id }}</p>
                        <p><strong>Name:</strong> {{ student.name }}</p>
                        <p><strong>Age:</strong> {{ student.age }}</p>
                        <p><strong>Parent:</strong> {{ student.parent }}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Contact:</strong> {{ student.contact }}</p>
                        <p><strong>Classroom:</strong> {{ student.classroom or "Not assigned" }}</p>
                        <p><strong>Attendance:</strong> 
                            {% set att = get_attendance_percentage(student) %}
                            <span class="badge bg-{% if att >= 80 %}success{% elif att >= 50 %}warning{% else %}danger{% endif %}">
                                {{ "%.1f"|format(att) }}%
                            </span>
                        </p>
                        <p><strong>Total Days:</strong> {{ student.attendance|length }}</p>
                    </div>
                </div>
                <hr>
                <h5>Attendance Records</h5>
                {% if student.attendance %}
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for a in student.attendance %}
                            <tr>
                                <td>{{ a.date }}</td>
                                <td>
                                    <span class="badge bg-{{ 'success' if a.status == 'Present' else 'danger' }}">
                                        {{ a.status }}
                                    </span>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p class="text-muted">No attendance records yet.</p>
                {% endif %}
                <div class="d-grid gap-2 mt-3">
                    <a href="/students" class="btn btn-secondary"><i class="bi bi-arrow-left"></i> Back to Students</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

    with open(os.path.join(template_dir, 'classroom_detail.html'), 'w', encoding='utf-8') as f:
        f.write('''{% extends "base.html" %}
{% block content %}
<div class="row mt-4">
    <div class="col-md-8 mx-auto">
        <div class="card">
            <div class="card-header"><i class="bi bi-building"></i> Classroom Details</div>
            <div class="card-body">
                <p><strong>Name:</strong> {{ classroom.name }}</p>
                <p><strong>Capacity:</strong> <span class="badge badge-pink">{{ classroom.students|length }}/{{ classroom.capacity }}</span></p>
                <p><strong>Teacher:</strong> {{ classroom.teacher or "Not assigned" }}</p>
                <hr>
                <h5>Students in this Classroom</h5>
                {% if classroom.students %}
                <ul class="list-group">
                    {% for s in classroom.students %}
                    <li class="list-group-item">
                        <i class="bi bi-person"></i> {{ s }}
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p class="text-muted">No students assigned to this classroom.</p>
                {% endif %}
                <div class="d-grid gap-2 mt-3">
                    <a href="/classrooms" class="btn btn-secondary"><i class="bi bi-arrow-left"></i> Back to Classrooms</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

if __name__ == '__main__':
    create_templates()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
