import http.server
import socketserver
import json
import sqlite3
import hashlib
import urllib.parse
from urllib.parse import urlparse, parse_qs
import os

PORT = 5000
sessions = {}

def db():
    c = sqlite3.connect('db.db')
    c.row_factory = sqlite3.Row
    return c

def init():
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,password TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY,name TEXT,provider TEXT,desc TEXT,url TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,user_id INTEGER,course_id INTEGER,rating INTEGER,text TEXT)')
        
        if not c.execute('SELECT 1 FROM courses LIMIT 1').fetchone():
            c.executemany('INSERT INTO courses VALUES(?,?,?,?,?)', [
                (1,'Python','Coursera','Learn Python','https://coursera.org/python'),
                (2,'ML','Coursera','Machine Learning','https://coursera.org/ml'),
                (3,'Web Dev','Udemy','Web Development','https://udemy.com/web'),
                (4,'Data Science','edX','Data Science','https://edx.org/data'),
                (5,'JavaScript','Codecademy','JavaScript','https://codecademy.com/js')
            ])

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('templates/app.html', 'r') as f:
                self.wfile.write(f.read().encode())
        elif self.path.startswith('/api/'):
            self.handle_api()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api()
        else:
            super().do_POST()
    
    def handle_api(self):
        path = self.path[4:]  # Remove /api
        
        if self.command == 'POST':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
        
        try:
            if path == '/auth' and self.command == 'POST':
                email, pwd = data['email'], hashlib.sha256(data['password'].encode()).hexdigest()
                with db() as c:
                    if data.get('register'):
                        try:
                            c.execute('INSERT INTO users(email,password)VALUES(?,?)', (email, pwd))
                            self.json_response({'ok': 1})
                        except:
                            self.json_response({'ok': 0, 'msg': 'Email exists'}, 400)
                    else:
                        u = c.execute('SELECT id,email FROM users WHERE email=? AND password=?', (email, pwd)).fetchone()
                        if u:
                            sessions[self.client_address[0]] = {'uid': u[0], 'email': u[1]}
                            self.json_response({'ok': 1, 'user': dict(u)})
                        else:
                            self.json_response({'ok': 0, 'msg': 'Invalid'}, 401)
            
            elif path == '/logout' and self.command == 'POST':
                sessions.pop(self.client_address[0], None)
                self.json_response({'ok': 1})
            
            elif path == '/user':
                session = sessions.get(self.client_address[0])
                self.json_response({'user': session if session else None})
            
            elif path == '/courses':
                parsed = urlparse(self.path)
                s = parse_qs(parsed.query).get('s', [''])[0]
                with db() as c:
                    q = '''SELECT c.id,c.name,c.provider,c.desc,c.url,AVG(r.rating)avg,COUNT(r.id)cnt 
                           FROM courses c LEFT JOIN reviews r ON c.id=r.course_id'''
                    if s:
                        q += ' WHERE c.name LIKE ? OR c.provider LIKE ? GROUP BY c.id'
                        rows = c.execute(q, (f'%{s}%', f'%{s}%')).fetchall()
                    else:
                        rows = c.execute(q + ' GROUP BY c.id').fetchall()
                    self.json_response([dict(r) for r in rows])
            
            elif path.startswith('/courses/'):
                course_id = int(path.split('/')[-1])
                with db() as c:
                    course = c.execute('SELECT * FROM courses WHERE id=?', (course_id,)).fetchone()
                    if not course:
                        self.json_response({'error': 'Not found'}, 404)
                        return
                    avg, cnt = c.execute('SELECT AVG(rating),COUNT(*) FROM reviews WHERE course_id=?', (course_id,)).fetchone()
                    reviews = c.execute('SELECT r.rating,r.text,u.email FROM reviews r JOIN users u ON r.user_id=u.id WHERE r.course_id=?', (course_id,)).fetchall()
                    self.json_response({'course': dict(course), 'avg': avg, 'cnt': cnt, 'reviews': [dict(r) for r in reviews]})
            
            elif path == '/recs':
                with db() as c:
                    top = c.execute('SELECT c.id,c.name,c.provider,AVG(r.rating)avg,COUNT(r.id)cnt FROM courses c LEFT JOIN reviews r ON c.id=r.course_id GROUP BY c.id ORDER BY avg DESC LIMIT 3').fetchall()
                    most = c.execute('SELECT c.id,c.name,c.provider,AVG(r.rating)avg,COUNT(r.id)cnt FROM courses c LEFT JOIN reviews r ON c.id=r.course_id GROUP BY c.id ORDER BY cnt DESC LIMIT 3').fetchall()
                    self.json_response({'top': [dict(r) for r in top], 'most': [dict(r) for r in most]})
            
            elif path == '/reviews' and self.command == 'POST':
                session = sessions.get(self.client_address[0])
                if not session:
                    self.json_response({'error': 'Auth required'}, 401)
                    return
                with db() as c:
                    c.execute('INSERT INTO reviews(user_id,course_id,rating,text)VALUES(?,?,?,?)', 
                             (session['uid'], data['cid'], data['rating'], data['text']))
                    self.json_response({'ok': 1})
            
            elif path == '/user/reviews':
                session = sessions.get(self.client_address[0])
                if not session:
                    self.json_response({'error': 'Auth required'}, 401)
                    return
                with db() as c:
                    reviews = c.execute('SELECT c.name,r.rating,r.text FROM reviews r JOIN courses c ON r.course_id=c.id WHERE r.user_id=?', (session['uid'],)).fetchall()
                    self.json_response([dict(r) for r in reviews])
            
            else:
                self.json_response({'error': 'Not found'}, 404)
        
        except Exception as e:
            self.json_response({'error': str(e)}, 500)
    
    def json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == '__main__':
    init()
    print(f"Server running at http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()