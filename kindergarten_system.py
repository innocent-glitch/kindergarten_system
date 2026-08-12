from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
import os, re

app = Flask(__name__)
app.secret_key = 'key'

def vn(n): return bool(re.match(r'^[A-Za-z\s\'\-]+$', n.strip()))
def vp(p): return bool(re.match(r'^[\d\s\-+()]+$', p))
def att(s):
    if not s.get('attendance'): return 0
    p = sum(1 for a in s['attendance'] if a['status'] == "Present")
    return (p/len(s['attendance']))*100 if s['attendance'] else 0
app.jinja_env.globals.update(att=att)

students, teachers, classrooms = [], [], []
sc = tc = 1

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
        'base.html':'<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Kindergarten</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css"><style>:root{--p:#FF69B4;--s:#87CEEB;--g:linear-gradient(135deg,#FF69B4,#87CEEB)}body{background:#f8f9fa}.navbar{background:var(--g)!important}.navbar-brand{font-weight:bold;color:white!important}.card{border-radius:15px;border:none;box-shadow:0 2px 10px rgba(0,0,0,0.1)}.card-header{background:var(--g);color:white}.btn-primary{background:var(--g);border:none}.stat-number{font-size:2.5rem;font-weight:bold;color:#FF69B4}footer{background:var(--g);color:white;padding:20px 0;margin-top:40px}</style></head><body><nav class="navbar navbar-expand-lg"><div class="container"><a class="navbar-brand" href="/"><i class="bi bi-heart-fill"></i> Abel\'s</a><button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button><div class="collapse navbar-collapse" id="navbarNav"><ul class="navbar-nav ms-auto"><li class="nav-item"><a class="nav-link" href="/">Home</a></li><li class="nav-item"><a class="nav-link" href="/students">Students</a></li><li class="nav-item"><a class="nav-link" href="/teachers">Teachers</a></li><li class="nav-item"><a class="nav-link" href="/classrooms">Rooms</a></li></ul></div></div></nav><div class="container">{% with m=get_flashed_messages(with_categories=true) %}{% if m %}{% for c,msg in m %}<div class="alert alert-{{"success" if c=="success" else"danger"}}">{{msg}}</div>{% endfor %}{% endif %}{% endwith %}{% block content %}{% endblock %}</div><footer class="text-center"><p><i class="bi bi-heart-fill text-warning"></i> Abel\'s Learners</p></footer></body></html>',
        'index.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-12 text-center"><h1 style="background:var(--g);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Welcome to Abel\'s</h1><p>Where learning begins with love.</p></div></div><div class="row mt-4">{% for l,c,u in [("Students",students|length,"/students"),("Teachers",teachers|length,"/teachers"),("Rooms",classrooms|length,"/classrooms")] %}<div class="col-md-4"><div class="card text-center"><div class="card-body"><h3 class="stat-number">{{c}}</h3><h5>{{l}}</h5><a href="{{u}}" class="btn btn-primary btn-sm">View</a></div></div></div>{% endfor %}</div><div class="row mt-4"><div class="col-md-6"><div class="card"><div class="card-header">Actions</div><div class="card-body"><div class="d-grid gap-2">{% for n,u in [("Add Student","/students/add"),("Add Teacher","/teachers/add"),("Add Room","/classrooms/add"),("Assign Student","/assign/student"),("Assign Teacher","/assign/teacher")] %}<a href="{{u}}" class="btn btn-outline-primary">{{n}}</a>{% endfor %}</div></div></div></div><div class="col-md-6"><div class="card"><div class="card-header">Stats</div><div class="card-body"><ul class="list-group">{% for l,c in [("Students",students|length),("Teachers",teachers|length),("Rooms",classrooms|length)] %}<li class="list-group-item">{{l}}: {{c}}</li>{% endfor %}</ul></div></div></div></div>{% endblock %}',
        'students.html':'{% extends "base.html" %}{% block content %}<div class="d-flex justify-content-between"><h2>Students</h2><a href="/students/add" class="btn btn-primary">+</a></div><div class="card mt-3"><div class="card-body"><table class="table"><thead><tr><th>ID</th><th>Name</th><th>Age</th><th>Parent</th><th>Room</th><th>%</th><th>Action</th></tr></thead><tbody>{% for s in students %}<tr><td>{{s.id}}</td><td>{{s.name}}</td><td>{{s.age}}</td><td>{{s.parent}}</td><td>{{s.classroom or "-"}}</td><td><span class="badge bg-{% set a=att(s) %}{{"success" if a>=80 else"warning" if a>=50 else"danger"}}">{{"%.0f"|format(a)}}%</span></td><td><button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#m{{s.id}}">Mark</button><a href="/students/{{s.id}}" class="btn btn-sm btn-info">View</a></td></tr><div class="modal fade" id="m{{s.id}}"><div class="modal-dialog"><div class="modal-content"><form method="POST" action="/mark"><div class="modal-header"><h5>{{s.name}}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><input type="hidden" name="name" value="{{s.name}}"><select name="status" class="form-select"><option value="Present">Present</option><option value="Absent">Absent</option></select></div><div class="modal-footer"><button type="submit" class="btn btn-primary">Save</button></div></form></div></div></div>{% endfor %}</tbody></table></div></div>{% endblock %}',
        'add_student.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-md-6 mx-auto"><div class="card"><div class="card-header">Add Student</div><div class="card-body"><form method="POST"><input class="form-control mb-2" name="name" placeholder="Name" pattern="[A-Za-z\\s\\\'\\-]+" required><input class="form-control mb-2" name="age" type="number" placeholder="Age" min="2" max="6" required><input class="form-control mb-2" name="contact" placeholder="Phone" pattern="[0-9\\-+() ]+" required><input class="form-control mb-2" name="parent" placeholder="Parent" pattern="[A-Za-z\\s\\\'\\-]+" required><button class="btn btn-primary">Add</button><a href="/students" class="btn btn-secondary">Cancel</a></form></div></div></div></div>{% endblock %}',
        'teachers.html':'{% extends "base.html" %}{% block content %}<div class="d-flex justify-content-between"><h2>Teachers</h2><a href="/teachers/add" class="btn btn-primary">+</a></div><div class="card mt-3"><div class="card-body"><table class="table"><thead><tr><th>ID</th><th>Name</th><th>Subject</th><th>Room</th><th>Contact</th></tr></thead><tbody>{% for t in teachers %}<tr><td>{{t.id}}</td><td>{{t.name}}</td><td>{{t.subject}}</td><td>{{t.classroom or "-"}}</td><td>{{t.contact}}</td></tr>{% endfor %}</tbody></table></div></div>{% endblock %}',
        'add_teacher.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-md-6 mx-auto"><div class="card"><div class="card-header">Add Teacher</div><div class="card-body"><form method="POST"><input class="form-control mb-2" name="name" placeholder="Name" pattern="[A-Za-z\\s\\\'\\-]+" required><input class="form-control mb-2" name="age" type="number" placeholder="Age" required><input class="form-control mb-2" name="contact" placeholder="Phone" pattern="[0-9\\-+() ]+" required><input class="form-control mb-2" name="subject" placeholder="Subject" required><button class="btn btn-primary">Add</button><a href="/teachers" class="btn btn-secondary">Cancel</a></form></div></div></div></div>{% endblock %}',
        'classrooms.html':'{% extends "base.html" %}{% block content %}<div class="d-flex justify-content-between"><h2>Rooms</h2><a href="/classrooms/add" class="btn btn-primary">+</a></div><div class="row mt-3">{% for c in classrooms %}<div class="col-md-4 mb-3"><div class="card"><div class="card-header">{{c.name}}</div><div class="card-body"><p>Capacity: {{c.students|length}}/{{c.capacity}}</p><p>Teacher: {{c.teacher or"-"}}</p><a href="/classrooms/{{c.name}}" class="btn btn-primary btn-sm">View</a></div></div></div>{% endfor %}</div>{% endblock %}',
        'add_classroom.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-md-6 mx-auto"><div class="card"><div class="card-header">Add Room</div><div class="card-body"><form method="POST"><input class="form-control mb-2" name="name" placeholder="Room Name" pattern="[A-Za-z\\s\\\'\\-]+" required><input class="form-control mb-2" name="capacity" type="number" placeholder="Capacity" min="5" max="30" required><button class="btn btn-primary">Create</button><a href="/classrooms" class="btn btn-secondary">Cancel</a></form></div></div></div></div>{% endblock %}',
        'assign_student.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-md-6 mx-auto"><div class="card"><div class="card-header">Assign Student</div><div class="card-body">{% if students and classrooms %}<form method="POST"><select class="form-select mb-2" name="student_name">{% for s in students %}<option value="{{s.name}}">{{s.name}}</option>{% endfor %}</select><select class="form-select mb-2" name="class_name">{% for c in classrooms %}<option value="{{c.name}}">{{c.name}}</option>{% endfor %}</select><button class="btn btn-primary">Assign</button></form>{% else %}<p>No students/rooms available.</p>{% endif %}</div></div></div></div>{% endblock %}',
        'assign_teacher.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-md-6 mx-auto"><div class="card"><div class="card-header">Assign Teacher</div><div class="card-body">{% if teachers and classrooms %}<form method="POST"><select class="form-select mb-2" name="teacher_name">{% for t in teachers %}<option value="{{t.name}}">{{t.name}}</option>{% endfor %}</select><select class="form-select mb-2" name="class_name">{% for c in classrooms %}<option value="{{c.name}}">{{c.name}}</option>{% endfor %}</select><button class="btn btn-primary">Assign</button></form>{% else %}<p>No teachers/rooms available.</p>{% endif %}</div></div></div></div>{% endblock %}',
        'student_detail.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header">{{student.name}}</div><div class="card-body"><p><b>ID:</b> {{student.id}}</p><p><b>Age:</b> {{student.age}}</p><p><b>Parent:</b> {{student.parent}}</p><p><b>Phone:</b> {{student.contact}}</p><p><b>Room:</b> {{student.classroom or"None"}}</p><p><b>Attendance:</b> {{"%.0f"|format(att(student))}}%</p><hr><h5>Records</h5>{% if student.attendance %}{% for a in student.attendance %}<p>{{a.date}}: {{a.status}}</p>{% endfor %}{% else %}<p>No records.</p>{% endif %}<a href="/students" class="btn btn-secondary">Back</a></div></div></div></div>{% endblock %}',
        'classroom_detail.html':'{% extends "base.html" %}{% block content %}<div class="row mt-4"><div class="col-md-8 mx-auto"><div class="card"><div class="card-header">{{classroom.name}}</div><div class="card-body"><p><b>Capacity:</b> {{classroom.students|length}}/{{classroom.capacity}}</p><p><b>Teacher:</b> {{classroom.teacher or"None"}}</p><hr><h5>Students</h5>{% if classroom.students %}{% for s in classroom.students %}<p>{{s}}</p>{% endfor %}{% else %}<p>No students.</p>{% endif %}<a href="/classrooms" class="btn btn-secondary">Back</a></div></div></div></div>{% endblock %}'
    }
    for name, content in t.items():
        with open(os.path.join('templates', name), 'w') as f: f.write(content)

create_templates()

@app.route('/')
def index(): return render_template('index.html', students=students, teachers=teachers, classrooms=classrooms)

@app.route('/students')
def students_page(): return render_template('students.html', students=students)

@app.route('/students/add', methods=['GET','POST'])
def add_student():
    if request.method == 'POST':
        n,a,c,p = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get('parent')
        if not all([n,a,c,p]): flash('All fields required!','danger')
        elif not vn(n) or not vn(p): flash('Invalid name!','danger')
        elif not vp(c): flash('Invalid phone!','danger')
        else: add_student_data(n,a,c,p); flash(f'{n} added!','success'); return redirect(url_for('students_page'))
    return render_template('add_student.html')

@app.route('/mark', methods=['POST'])
def mark():
    s = find('students', request.form.get('name'))
    if s:
        s['attendance'].append({"date": date.today().strftime("%Y-%m-%d"), "status": request.form.get('status')})
        flash('Marked!','success')
    else: flash('Not found!','danger')
    return redirect(url_for('students_page'))

@app.route('/students/<id>')
def student_detail(id):
    s = next((s for s in students if s['id'] == id), None)
    return render_template('student_detail.html', student=s) if s else (flash('Not found!','danger') or redirect(url_for('students_page')))

@app.route('/teachers')
def teachers_page(): return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/add', methods=['GET','POST'])
def add_teacher():
    if request.method == 'POST':
        n,a,c,s = request.form.get('name'), request.form.get('age'), request.form.get('contact'), request.form.get('subject')
        if not all([n,a,c,s]): flash('All fields required!','danger')
        elif not vn(n): flash('Invalid name!','danger')
        elif not vp(c): flash('Invalid phone!','danger')
        else: add_teacher_data(n,a,c,s); flash(f'{n} added!','success'); return redirect(url_for('teachers_page'))
    return render_template('add_teacher.html')

@app.route('/classrooms')
def classrooms_page(): return render_template('classrooms.html', classrooms=classrooms)

@app.route('/classrooms/add', methods=['GET','POST'])
def add_classroom():
    if request.method == 'POST':
        n,c = request.form.get('name'), request.form.get('capacity')
        if not n or not c: flash('All fields required!','danger')
        elif not vn(n): flash('Invalid name!','danger')
        else:
            classrooms.append({"name": n.strip(), "capacity": int(c), "teacher": "", "students": [], "schedule": {}})
            flash(f'{n} created!','success'); return redirect(url_for('classrooms_page'))
    return render_template('add_classroom.html')

@app.route('/assign/student', methods=['GET','POST'])
def assign_student():
    if request.method == 'POST':
        s,c = find('students', request.form.get('student_name')), find('classrooms', request.form.get('class_name'))
        if s and c and len(c['students']) < c['capacity']:
            s['classroom'] = c['name']; c['students'].append(s['name']); flash('Assigned!','success')
        else: flash('Failed!','danger')
        return redirect(url_for('classrooms_page'))
    return render_template('assign_student.html', students=[s for s in students if not s['classroom']], classrooms=classrooms)

@app.route('/assign/teacher', methods=['GET','POST'])
def assign_teacher():
    if request.method == 'POST':
        t,c = find('teachers', request.form.get('teacher_name')), find('classrooms', request.form.get('class_name'))
        if t and c: t['classroom'] = c['name']; c['teacher'] = t['name']; flash('Assigned!','success')
        else: flash('Failed!','danger')
        return redirect(url_for('classrooms_page'))
    return render_template('assign_teacher.html', teachers=[t for t in teachers if not t['classroom']], classrooms=classrooms)

@app.route('/classrooms/<name>')
def classroom_detail(name):
    c = find('classrooms', name)
    return render_template('classroom_detail.html', classroom=c) if c else (flash('Not found!','danger') or redirect(url_for('classrooms_page')))

@app.route('/api/data')
def api(): return jsonify({"students": students, "teachers": teachers, "classrooms": classrooms})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
