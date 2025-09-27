from flask import Flask, request, jsonify, session
import sqlite3
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def get_db():
    conn = sqlite3.connect('courses.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('courses.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS courses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  course_name TEXT NOT NULL,
                  provider TEXT NOT NULL,
                  description TEXT NOT NULL,
                  course_url TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  course_id INTEGER,
                  rating INTEGER NOT NULL,
                  review_text TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (course_id) REFERENCES courses (id))''')
    
    conn.commit()
    conn.close()

def seed_courses():
    conn = sqlite3.connect('courses.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM courses')
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    courses = [
        ("Python for Everybody", "Coursera", "Learn Python programming from scratch", "https://coursera.org/python"),
        ("Machine Learning", "Coursera", "Introduction to machine learning algorithms", "https://coursera.org/ml"),
        ("Web Development Bootcamp", "Udemy", "Complete web development course", "https://udemy.com/web-dev"),
        ("Data Science Fundamentals", "edX", "Learn data science basics", "https://edx.org/data-science"),
        ("JavaScript Essentials", "Codecademy", "Master JavaScript programming", "https://codecademy.com/js"),
        ("React Development", "Udemy", "Build modern web apps with React", "https://udemy.com/react"),
        ("SQL Database Design", "Coursera", "Learn database design and SQL", "https://coursera.org/sql"),
        ("Digital Marketing", "edX", "Complete digital marketing course", "https://edx.org/marketing"),
        ("UI/UX Design", "Coursera", "User interface and experience design", "https://coursera.org/ux"),
        ("Cloud Computing AWS", "Udemy", "Amazon Web Services fundamentals", "https://udemy.com/aws")
    ]
    
    c.executemany('INSERT INTO courses (course_name, provider, description, course_url) VALUES (?, ?, ?, ?)', courses)
    conn.commit()
    conn.close()

# Auth APIs
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    email = data.get('email')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()
    
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
        conn.commit()
        return jsonify({'success': True, 'message': 'Registration successful'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()
    
    conn = get_db()
    user = conn.execute('SELECT id, email FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['email'] = user['email']
        return jsonify({'success': True, 'user': {'id': user['id'], 'email': user['email']}})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/user', methods=['GET'])
def api_get_user():
    if 'user_id' in session:
        return jsonify({'user': {'id': session['user_id'], 'email': session['email']}})
    return jsonify({'user': None})

# Course APIs
@app.route('/api/courses', methods=['GET'])
def api_get_courses():
    search = request.args.get('search', '')
    conn = get_db()
    
    if search:
        courses = conn.execute('''SELECT c.id, c.course_name, c.provider, c.description, c.course_url,
                                 AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
                                 FROM courses c LEFT JOIN reviews r ON c.id = r.course_id
                                 WHERE c.course_name LIKE ? OR c.provider LIKE ?
                                 GROUP BY c.id''', (f'%{search}%', f'%{search}%')).fetchall()
    else:
        courses = conn.execute('''SELECT c.id, c.course_name, c.provider, c.description, c.course_url,
                                 AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
                                 FROM courses c LEFT JOIN reviews r ON c.id = r.course_id
                                 GROUP BY c.id''').fetchall()
    
    conn.close()
    return jsonify([dict(course) for course in courses])

@app.route('/api/courses/<int:course_id>', methods=['GET'])
def api_get_course(course_id):
    conn = get_db()
    
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    avg_rating, review_count = conn.execute('SELECT AVG(rating), COUNT(*) FROM reviews WHERE course_id = ?', (course_id,)).fetchone()
    
    reviews = conn.execute('''SELECT r.rating, r.review_text, r.created_at, u.email
                             FROM reviews r JOIN users u ON r.user_id = u.id
                             WHERE r.course_id = ? ORDER BY r.created_at DESC''', (course_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'course': dict(course),
        'avg_rating': avg_rating,
        'review_count': review_count,
        'reviews': [dict(review) for review in reviews]
    })

@app.route('/api/recommendations', methods=['GET'])
def api_get_recommendations():
    conn = get_db()
    
    top_rated = conn.execute('''SELECT c.id, c.course_name, c.provider, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
                               FROM courses c LEFT JOIN reviews r ON c.id = r.course_id
                               GROUP BY c.id ORDER BY avg_rating DESC LIMIT 5''').fetchall()
    
    most_reviewed = conn.execute('''SELECT c.id, c.course_name, c.provider, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
                                   FROM courses c LEFT JOIN reviews r ON c.id = r.course_id
                                   GROUP BY c.id ORDER BY review_count DESC LIMIT 5''').fetchall()
    
    conn.close()
    
    return jsonify({
        'top_rated': [dict(course) for course in top_rated],
        'most_reviewed': [dict(course) for course in most_reviewed]
    })

# Review APIs
@app.route('/api/reviews', methods=['POST'])
def api_submit_review():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    course_id = data.get('course_id')
    rating = data.get('rating')
    review_text = data.get('review_text')
    
    conn = get_db()
    conn.execute('INSERT INTO reviews (user_id, course_id, rating, review_text) VALUES (?, ?, ?, ?)',
                (session['user_id'], course_id, rating, review_text))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Review submitted successfully'})

@app.route('/api/user/reviews', methods=['GET'])
def api_get_user_reviews():
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db()
    reviews = conn.execute('''SELECT c.course_name, r.rating, r.review_text, r.created_at
                             FROM reviews r JOIN courses c ON r.course_id = c.id
                             WHERE r.user_id = ? ORDER BY r.created_at DESC''', (session['user_id'],)).fetchall()
    conn.close()
    
    return jsonify([dict(review) for review in reviews])

if __name__ == '__main__':
    init_db()
    seed_courses()
    app.run(debug=True, port=5001)