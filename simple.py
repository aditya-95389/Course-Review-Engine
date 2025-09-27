import http.server
import socketserver

PORT = 3000

HTML = '''<!DOCTYPE html>
<html>
<head>
<title>Course Reviews</title>
<style>
body{font-family:Arial;margin:0;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;min-height:100vh}
.container{max-width:1200px;margin:0 auto;padding:2rem}
.hero{text-align:center;margin:3rem 0}
.hero h1{font-size:3rem;margin-bottom:1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:2rem;margin:2rem 0}
.card{background:rgba(255,255,255,0.9);color:#333;padding:2rem;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.2)}
.card h3{color:#007bff;margin-bottom:1rem}
.provider{color:#666;font-weight:bold;margin:0.5rem 0}
</style>
</head>
<body>
<div class="container">
<div class="hero">
<h1>🎓 CourseHub</h1>
<p>Discover Amazing Online Courses</p>
</div>
<div class="grid">
<div class="card">
<h3>Python for Everybody</h3>
<div class="provider">Coursera</div>
<p>Complete Python programming course from basics to advanced</p>
</div>
<div class="card">
<h3>Machine Learning</h3>
<div class="provider">Stanford</div>
<p>Andrew Ng's famous ML course with practical applications</p>
</div>
<div class="card">
<h3>Full Stack Web Development</h3>
<div class="provider">Udemy</div>
<p>Build modern web applications with React, Node.js, and MongoDB</p>
</div>
<div class="card">
<h3>React Development</h3>
<div class="provider">Meta</div>
<p>Build interactive UIs with React hooks, context, and routing</p>
</div>
<div class="card">
<h3>AWS Cloud Practitioner</h3>
<div class="provider">Amazon</div>
<p>Learn cloud computing fundamentals and AWS services</p>
</div>
<div class="card">
<h3>Digital Marketing</h3>
<div class="provider">Google</div>
<p>Complete digital marketing strategy and analytics course</p>
</div>
</div>
</div>
</body>
</html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML.encode())

print(f"✅ Course Review Engine running at http://localhost:{PORT}")
print("🌐 Open your browser and go to the URL above")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()