import http.server
import socketserver
import json
import sqlite3
import hashlib
import urllib.parse

PORT = 5555
sessions = {}

def init_db():
    conn = sqlite3.connect('fixed.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        provider TEXT NOT NULL,
        description TEXT NOT NULL,
        url TEXT NOT NULL,
        category TEXT DEFAULT 'Technology'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        review_text TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (course_id) REFERENCES courses (id)
    )''')
    
    if not c.execute('SELECT 1 FROM courses LIMIT 1').fetchone():
        courses = [
            ('Python for Everybody', 'University of Michigan', 'Master Python programming from basics to advanced concepts', 'https://coursera.org/python', 'Programming'),
            ('Machine Learning', 'Stanford University', 'Andrew Ng comprehensive ML course with practical applications', 'https://coursera.org/ml', 'AI/ML'),
            ('React Development', 'Meta', 'Build interactive UIs with React hooks and modern patterns', 'https://react.dev', 'Frontend'),
            ('Digital Marketing', 'Google', 'Complete digital marketing strategy and analytics course', 'https://skillshop.withgoogle.com', 'Marketing'),
            ('UI/UX Design', 'Adobe', 'Design thinking, prototyping, and user experience principles', 'https://adobe.com/education', 'Design'),
            ('AWS Cloud', 'Amazon', 'Learn cloud computing fundamentals and AWS services', 'https://aws.amazon.com/training', 'Cloud'),
            ('Data Science', 'IBM', 'Complete data science workflow with Python and machine learning', 'https://ibm.com/training', 'Data Science'),
            ('JavaScript Advanced', 'Mozilla', 'Advanced JavaScript concepts and modern ES6+ features', 'https://developer.mozilla.org', 'Programming'),
            ('Cybersecurity', 'Cisco', 'Network security, ethical hacking, and risk management', 'https://cisco.com/training', 'Security'),
            ('Mobile Development', 'Apple', 'iOS app development with Swift and modern frameworks', 'https://developer.apple.com', 'Mobile')
        ]
        
        c.executemany('INSERT INTO courses (name, provider, description, url, category) VALUES (?, ?, ?, ?, ?)', courses)
    
    conn.commit()
    conn.close()

HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>CourseHub - Working Search</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
.header { text-align: center; color: white; margin-bottom: 3rem; }
.header h1 { font-size: 3rem; margin-bottom: 1rem; }
.search-box { background: white; padding: 1rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
.search-input { width: 100%; padding: 1rem; border: 2px solid #eee; border-radius: 10px; font-size: 1.1rem; }
.search-btn { width: 100%; padding: 1rem; background: #667eea; color: white; border: none; border-radius: 10px; font-size: 1.1rem; margin-top: 1rem; cursor: pointer; }
.results { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 2rem; }
.course { background: white; padding: 1.5rem; margin: 1rem 0; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
.course h3 { color: #333; margin-bottom: 0.5rem; font-size: 1.3rem; }
.provider { color: #667eea; font-weight: bold; margin-bottom: 1rem; }
.description { color: #666; line-height: 1.6; }
.category { background: #f0f2f5; padding: 0.5rem 1rem; border-radius: 20px; display: inline-block; font-size: 0.9rem; color: #666; margin-top: 1rem; }
.no-results { text-align: center; color: #666; padding: 3rem; font-style: italic; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🎓 CourseHub</h1>
<p>Search and discover amazing online courses</p>
</div>

<div class="search-box">
<input type="text" class="search-input" id="searchInput" placeholder="Search for Python, React, Marketing, Design, AI, Security...">
<button class="search-btn" onclick="search()">🔍 Search Courses</button>
</div>

<div class="results" id="results">
<div id="courseList"></div>
</div>
</div>

<script>
let allCourses = [];

async function loadCourses() {
    try {
        const response = await fetch('/api/courses');
        const courses = await response.json();
        allCourses = courses;
        displayCourses(courses, 'All Courses');
    } catch (error) {
        console.error('Error loading courses:', error);
        document.getElementById('courseList').innerHTML = '<div class="no-results">Error loading courses. Please refresh the page.</div>';
    }
}

function displayCourses(courses, title) {
    const courseList = document.getElementById('courseList');
    
    if (courses.length === 0) {
        courseList.innerHTML = '<div class="no-results">No courses found. Try different search terms.</div>';
        return;
    }
    
    courseList.innerHTML = `
        <h2 style="color: #333; margin-bottom: 1.5rem;">${title} (${courses.length} found)</h2>
        ${courses.map(course => `
            <div class="course">
                <h3>${course.name}</h3>
                <div class="provider">${course.provider}</div>
                <div class="description">${course.description}</div>
                <div class="category">${course.category || 'General'}</div>
            </div>
        `).join('')}
    `;
}

function search() {
    const query = document.getElementById('searchInput').value.trim().toLowerCase();
    
    if (!query) {
        displayCourses(allCourses, 'All Courses');
        return;
    }
    
    const filtered = allCourses.filter(course => 
        course.name.toLowerCase().includes(query) ||
        course.provider.toLowerCase().includes(query) ||
        course.description.toLowerCase().includes(query) ||
        (course.category && course.category.toLowerCase().includes(query))
    );
    
    displayCourses(filtered, `Search Results for "${query}"`);
}

document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        search();
    }
});

document.getElementById('searchInput').addEventListener('input', function() {
    const query = this.value.trim();
    if (query.length > 2) {
        search();
    } else if (query.length === 0) {
        displayCourses(allCourses, 'All Courses');
    }
});

// Load courses when page loads
loadCourses();
</script>
</body>
</html>'''

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/api/'):
            self.handle_api()
        else:
            self.send_error(404)
    
    def handle_api(self):
        path = self.path[4:]  # Remove /api
        
        try:
            conn = sqlite3.connect('fixed.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            if path == '/courses':
                # Parse search parameter
                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                search = query_params.get('search', [''])[0]
                
                if search:
                    search_term = f'%{search}%'
                    courses = c.execute('''
                        SELECT * FROM courses 
                        WHERE LOWER(name) LIKE LOWER(?) 
                           OR LOWER(provider) LIKE LOWER(?) 
                           OR LOWER(description) LIKE LOWER(?) 
                           OR LOWER(category) LIKE LOWER(?)
                        ORDER BY name
                    ''', (search_term, search_term, search_term, search_term)).fetchall()
                else:
                    courses = c.execute('SELECT * FROM courses ORDER BY name').fetchall()
                
                self.json_response([dict(course) for course in courses])
            else:
                self.json_response({'error': 'Endpoint not found'}, 404)
            
            conn.close()
            
        except Exception as e:
            print(f"API Error: {e}")
            self.json_response({'error': 'Internal server error'}, 500)
    
    def json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == '__main__':
    init_db()
    print(f"Fixed CourseHub running at http://localhost:{PORT}")
    print("Search functionality:")
    print("- Type in the search box")
    print("- Press Enter or it searches as you type")
    print("- Try: Python, React, Marketing, Design, Security")
    print("Press Ctrl+C to stop")
    
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        httpd.serve_forever()