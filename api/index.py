from flask import Flask, request, jsonify, session
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key')

def db():
    c = sqlite3.connect('/tmp/app.db')
    c.row_factory = sqlite3.Row
    return c

def init():
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,password TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY,name TEXT,provider TEXT,desc TEXT,url TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,user_id INTEGER,course_id INTEGER,rating INTEGER,text TEXT)')
        
        if not c.execute('SELECT 1 FROM courses LIMIT 1').fetchone():
            c.executemany('INSERT INTO courses VALUES(?,?,?,?,?)', [
                (1,'Python Programming','Coursera','Complete Python course','https://coursera.org/python'),
                (2,'React Development','Udemy','Build modern web apps','https://udemy.com/react'),
                (3,'Machine Learning','Stanford','ML course with projects','https://coursera.org/ml'),
                (4,'Digital Marketing','Google','Complete digital marketing','https://skillshop.withgoogle.com'),
                (5,'UI/UX Design','Adobe','Design principles','https://adobe.com/education')
            ])

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>CourseHub</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font:16px Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;color:#333}
.nav{background:rgba(44,62,80,0.95);padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:1000}
.nav h1{color:white;font-size:1.8rem}
.nav div{display:flex;gap:1rem;align-items:center}
.nav a,.btn{color:white;text-decoration:none;padding:0.5rem 1rem;border-radius:25px;background:rgba(255,255,255,0.1);transition:all 0.3s;border:none;cursor:pointer;font-size:14px}
.nav a:hover,.btn:hover{background:rgba(255,255,255,0.2);transform:translateY(-2px)}
.btn-primary{background:linear-gradient(45deg,#667eea,#764ba2)}
.btn-success{background:linear-gradient(45deg,#28a745,#20c997)}
.btn-danger{background:linear-gradient(45deg,#dc3545,#e74c3c)}
.container{max-width:1200px;margin:0 auto;padding:2rem}
.hero{text-align:center;color:white;margin:3rem 0}
.hero h2{font-size:3rem;margin-bottom:1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:2rem;margin:2rem 0}
.card{background:rgba(255,255,255,0.95);padding:2rem;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.1);transition:transform 0.3s}
.card:hover{transform:translateY(-5px)}
.card h3{color:#333;margin-bottom:1rem}
.card h3 a{color:inherit;text-decoration:none;cursor:pointer}
.provider{color:#667eea;font-weight:bold;margin-bottom:1rem}
.desc{color:#666;line-height:1.6;margin-bottom:1rem}
.rating{color:#f39c12}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;justify-content:center;align-items:center;z-index:1000}
.modal-content{background:white;padding:3rem;border-radius:15px;width:90%;max-width:800px;max-height:80vh;overflow-y:auto;position:relative}
.close{position:absolute;top:1rem;right:1rem;background:none;border:none;font-size:1.5rem;cursor:pointer}
.form input,textarea{width:100%;padding:1rem;margin:0.5rem 0;border:2px solid #eee;border-radius:8px;font-size:1rem}
.form button{width:100%;padding:1rem;background:#667eea;color:white;border:none;border-radius:8px;font-size:1.1rem;cursor:pointer;margin-top:1rem}
.stars{display:flex;gap:0.25rem;margin:1rem 0;justify-content:center}
.stars input{display:none}
.stars label{font-size:2rem;color:#ddd;cursor:pointer}
.stars input:checked~label,.stars label:hover,.stars label:hover~label{color:#f39c12}
.review{border:1px solid #eee;padding:1.5rem;margin:1rem 0;border-radius:8px;background:#f9f9f9}
.review-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}
.hide{display:none}
@media (max-width:768px){.grid{grid-template-columns:1fr}.nav{flex-direction:column;gap:1rem}.modal-content{width:95%;padding:1.5rem}}
</style>
</head>
<body>
<nav class="nav">
<h1>🎓 CourseHub</h1>
<div id="nav"></div>
</nav>
<div class="container">
<div class="hero">
<h2>Course Reviews</h2>
<p>Discover and review courses</p>
</div>
<div class="grid" id="courses"></div>
</div>
<div id="loginModal" class="modal hide">
<div class="modal-content">
<button class="close" onclick="closeModal()">&times;</button>
<h2>Login</h2>
<div class="form">
<input id="loginEmail" type="email" placeholder="Email">
<input id="loginPassword" type="password" placeholder="Password">
<button onclick="login()">Login</button>
<p><a href="#" onclick="switchModal('register')">Register</a></p>
</div>
</div>
</div>
<div id="registerModal" class="modal hide">
<div class="modal-content">
<button class="close" onclick="closeModal()">&times;</button>
<h2>Register</h2>
<div class="form">
<input id="registerEmail" type="email" placeholder="Email">
<input id="registerPassword" type="password" placeholder="Password">
<button onclick="register()">Register</button>
<p><a href="#" onclick="switchModal('login')">Login</a></p>
</div>
</div>
</div>
<div id="courseModal" class="modal hide">
<div class="modal-content">
<button class="close" onclick="closeModal()">&times;</button>
<div id="courseDetail"></div>
</div>
</div>
<script>
let user=null;
function msg(t){const d=document.createElement('div');d.style.cssText='position:fixed;top:20px;right:20px;background:#28a745;color:white;padding:1rem;border-radius:8px;z-index:2000';d.textContent=t;document.body.appendChild(d);setTimeout(()=>d.remove(),3000)}
function updateNav(){document.getElementById('nav').innerHTML=user?`<span style="margin-right:1rem">👋 ${user.email}</span><button class="btn btn-danger" onclick="logout()">Logout</button>`:'<button class="btn btn-primary" onclick="showModal(\'login\')" style="margin-right:0.5rem">Login</button><button class="btn btn-success" onclick="showModal(\'register\')" >Register</button>'}
function showModal(t){document.getElementById(t+'Modal').classList.remove('hide')}
function closeModal(){document.querySelectorAll('.modal').forEach(m=>m.classList.add('hide'))}
function switchModal(t){closeModal();showModal(t)}
async function api(u,d,m='POST'){const r=await fetch('/api'+u,{method:d?m:'GET',headers:{'Content-Type':'application/json'},body:d?JSON.stringify(d):null});return await r.json()}
async function login(){const r=await api('/auth',{email:document.getElementById('loginEmail').value,password:document.getElementById('loginPassword').value});if(r.ok){user=r.user;updateNav();closeModal();msg('Login successful!')}else{msg(r.msg||'Login failed')}}
async function register(){const r=await api('/auth',{email:document.getElementById('registerEmail').value,password:document.getElementById('registerPassword').value,register:true});if(r.ok){msg('Registration successful!');switchModal('login')}else{msg(r.msg||'Registration failed')}}
async function logout(){user=null;updateNav();msg('Logged out')}
function stars(r,c=0){if(!r)return '<span style="color:#999">No reviews</span>';return `<span style="color:#f39c12">${'⭐'.repeat(Math.round(r))}</span> ${r.toFixed(1)} (${c})`}
async function loadCourses(){const c=await api('/courses');document.getElementById('courses').innerHTML=c.map(c=>`<div class="card"><h3><a href="#" onclick="showCourse(${c.id})">${c.name}</a></h3><div class="provider">${c.provider}</div><div class="desc">${c.desc}</div><div class="rating">${stars(c.avg,c.cnt)}</div></div>`).join('')}
async function showCourse(id){const d=await api('/courses/'+id);const c=d.course;const r=d.reviews;document.getElementById('courseDetail').innerHTML=`<h2>${c.name}</h2><div class="provider">${c.provider}</div><p>${c.desc}</p><div class="rating">${stars(d.avg,r.length)}</div><a href="${c.url}" target="_blank" style="display:inline-block;background:#667eea;color:white;padding:1rem 2rem;text-decoration:none;border-radius:8px;margin:1rem 0">Visit Course</a>${user?`<div style="background:#f9f9f9;padding:2rem;border-radius:8px;margin:2rem 0"><h3>Write Review</h3><div class="stars"><input type="radio" name="rating" value="5" id="s5"><label for="s5">⭐</label><input type="radio" name="rating" value="4" id="s4"><label for="s4">⭐</label><input type="radio" name="rating" value="3" id="s3"><label for="s3">⭐</label><input type="radio" name="rating" value="2" id="s2"><label for="s2">⭐</label><input type="radio" name="rating" value="1" id="s1"><label for="s1">⭐</label></div><textarea id="reviewText" placeholder="Write review..." rows="4"></textarea><button onclick="submitReview(${id})">Submit</button></div>`:'<div style="text-align:center;padding:2rem;background:#f9f9f9;border-radius:8px;margin:2rem 0"><p>Login to review</p><button onclick="showModal(\'login\')">Login</button></div>'}<h3>Reviews</h3>${r.length?r.map(r=>`<div class="review"><div class="review-header"><strong>${r.email}</strong><span style="color:#f39c12">${'⭐'.repeat(r.rating)}</span></div><p>${r.text}</p></div>`).join(''):'<p>No reviews yet</p>'}`;showModal('course')}
async function submitReview(id){const r=document.querySelector('input[name="rating"]:checked')?.value;const t=document.getElementById('reviewText').value;if(!r){msg('Select rating');return}const res=await api('/reviews',{course_id:id,rating:parseInt(r),text:t});if(res.ok){msg('Review submitted!');showCourse(id)}else{msg('Failed')}}
async function init(){const r=await api('/user');if(r.user)user=r.user;updateNav();loadCourses()}
init();
</script>
</body>
</html>'''

@app.route('/api/courses')
def courses():
    with db() as c:
        courses = c.execute('SELECT c.*, AVG(r.rating) avg, COUNT(r.id) cnt FROM courses c LEFT JOIN reviews r ON c.id=r.course_id GROUP BY c.id').fetchall()
        return jsonify([dict(c) for c in courses])

@app.route('/api/courses/<int:id>')
def course(id):
    with db() as c:
        course = c.execute('SELECT * FROM courses WHERE id=?', (id,)).fetchone()
        reviews = c.execute('SELECT r.*, u.email FROM reviews r JOIN users u ON r.user_id=u.id WHERE r.course_id=?', (id,)).fetchall()
        avg = c.execute('SELECT AVG(rating) FROM reviews WHERE course_id=?', (id,)).fetchone()[0]
        return jsonify({'course': dict(course), 'reviews': [dict(r) for r in reviews], 'avg': avg})

@app.route('/api/auth', methods=['POST'])
def auth():
    d = request.json
    email, pwd = d['email'], hashlib.sha256(d['password'].encode()).hexdigest()
    with db() as c:
        if d.get('register'):
            try:
                c.execute('INSERT INTO users(email,password)VALUES(?,?)', (email, pwd))
                return jsonify({'ok': 1})
            except:
                return jsonify({'ok': 0, 'msg': 'Email exists'}), 400
        else:
            u = c.execute('SELECT id,email FROM users WHERE email=? AND password=?', (email, pwd)).fetchone()
            if u:
                session.update({'uid': u[0], 'email': u[1]})
                return jsonify({'ok': 1, 'user': dict(u)})
            return jsonify({'ok': 0, 'msg': 'Invalid'}), 401

@app.route('/api/reviews', methods=['POST'])
def review():
    if 'uid' not in session:
        return jsonify({'error': 'Login required'}), 401
    d = request.json
    with db() as c:
        c.execute('INSERT INTO reviews(user_id,course_id,rating,text)VALUES(?,?,?,?)', (session['uid'], d['course_id'], d['rating'], d['text']))
        return jsonify({'ok': 1})

@app.route('/api/user')
def user():
    return jsonify({'user': {'id': session.get('uid'), 'email': session.get('email')} if 'uid' in session else None})

init()

# Vercel serverless function handler
from werkzeug.wrappers import Request, Response

def handler(environ, start_response):
    return app(environ, start_response)

# For Vercel
app = app