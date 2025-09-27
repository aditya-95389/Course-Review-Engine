from flask import Flask, render_template, request, jsonify, session
import sqlite3
import hashlib
import secrets
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG, DEBUG_EMAIL

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key')

def db():
    c = sqlite3.connect('app.db')
    c.row_factory = sqlite3.Row
    return c

def init():
    with db() as c:
        c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,password TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY,name TEXT,provider TEXT,desc TEXT,url TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,user_id INTEGER,course_id INTEGER,rating INTEGER,text TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS reset_tokens(id INTEGER PRIMARY KEY,email TEXT,token TEXT,expires INTEGER)')
        
        if not c.execute('SELECT 1 FROM courses LIMIT 1').fetchone():
            c.executemany('INSERT INTO courses VALUES(?,?,?,?,?)', [
                (1,'Python Programming','Coursera','Complete Python course from basics to advanced','https://coursera.org/python'),
                (2,'React Development','Udemy','Build modern web apps with React and hooks','https://udemy.com/react'),
                (3,'Machine Learning','Stanford','Andrew Ng ML course with practical projects','https://coursera.org/ml'),
                (4,'Digital Marketing','Google','Complete digital marketing and SEO course','https://skillshop.withgoogle.com'),
                (5,'UI/UX Design','Adobe','Design thinking and user experience principles','https://adobe.com/education')
            ])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/courses')
def courses():
    s = request.args.get('search', '')
    with db() as c:
        if s:
            courses = c.execute('SELECT c.*, AVG(r.rating) avg, COUNT(r.id) cnt FROM courses c LEFT JOIN reviews r ON c.id=r.course_id WHERE c.name LIKE ? OR c.provider LIKE ? GROUP BY c.id', (f'%{s}%', f'%{s}%')).fetchall()
        else:
            courses = c.execute('SELECT c.*, AVG(r.rating) avg, COUNT(r.id) cnt FROM courses c LEFT JOIN reviews r ON c.id=r.course_id GROUP BY c.id').fetchall()
        return jsonify([dict(c) for c in courses])

@app.route('/api/courses/<int:id>')
def course(id):
    with db() as c:
        course = c.execute('SELECT * FROM courses WHERE id=?', (id,)).fetchone()
        if not course:
            return jsonify({'error': 'Course not found'}), 404
            
        reviews = c.execute('SELECT r.*, u.email FROM reviews r JOIN users u ON r.user_id=u.id WHERE r.course_id=?', (id,)).fetchall()
        avg_result = c.execute('SELECT AVG(rating) FROM reviews WHERE course_id=?', (id,)).fetchone()
        avg = avg_result[0] if avg_result and avg_result[0] else None
        
        return jsonify({
            'course': dict(course), 
            'reviews': [dict(r) for r in reviews], 
            'avg': avg,
            'current_user_id': session.get('uid')
        })

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
        c.execute('INSERT INTO reviews(user_id,course_id,rating,text)VALUES(?,?,?,?)', 
                 (session['uid'], d['course_id'], d['rating'], d['text']))
        return jsonify({'ok': 1})

@app.route('/api/reviews/<int:id>', methods=['PUT'])
def edit_review(id):
    if 'uid' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    d = request.json
    with db() as c:
        c.execute('UPDATE reviews SET rating=?, text=? WHERE id=? AND user_id=?', 
                 (d['rating'], d['text'], id, session['uid']))
        return jsonify({'ok': 1})

@app.route('/api/reviews/<int:id>', methods=['DELETE'])
def delete_review(id):
    if 'uid' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    with db() as c:
        c.execute('DELETE FROM reviews WHERE id=? AND user_id=?', (id, session['uid']))
        return jsonify({'ok': 1})

def send_reset_email(email, token):
    if DEBUG_EMAIL:
        print(f'\n=== DEBUG MODE: Email would be sent to {email} ===')
        print(f'Reset Token: {token}')
        print('=== Copy this token to use in the reset form ===')
        return True
    
    # Validate email configuration
    if (EMAIL_CONFIG['SENDER_EMAIL'] == 'your-email@gmail.com' or 
        EMAIL_CONFIG['SENDER_PASSWORD'] == 'your-16-char-app-password'):
        print('ERROR: Please configure your Gmail credentials in config.py')
        return False
    
    try:
        print(f'Attempting to send email to {email}...')
        
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        msg['To'] = email
        msg['Subject'] = 'Password Reset - CourseHub'
        
        body = f'''Hello,

You requested a password reset for your CourseHub account.

Your reset token is: {token}

This token will expire in 1 hour.

If you didn't request this reset, please ignore this email.

Best regards,
CourseHub Team'''
        
        msg.attach(MIMEText(body, 'plain'))
        
        print('Connecting to Gmail SMTP...')
        server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
        server.set_debuglevel(0)  # Disable SMTP debugging for cleaner output
        server.starttls()
        
        print('Logging in...')
        server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['SENDER_PASSWORD'])
        
        print('Sending email...')
        server.send_message(msg)
        server.quit()
        
        print(f'Email sent successfully to {email}')
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f'Gmail authentication failed: {e}')
        print('Make sure you have:')
        print('1. Enabled 2-factor authentication')
        print('2. Generated an App Password (not your regular password)')
        print('3. Used the correct Gmail address')
        return False
    except Exception as e:
        print(f'Email sending failed: {e}')
        return False

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    d = request.json
    email = d['email']
    
    with db() as c:
        user = c.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
        if not user:
            return jsonify({'ok': 0, 'msg': 'Email not found'}), 404
        
        token = secrets.token_urlsafe(32)
        expires = int(time.time()) + 3600  # 1 hour
        
        print(f'Generated token for {email}: {token}')
        print(f'Token expires at: {expires} (current: {int(time.time())})')
        
        c.execute('DELETE FROM reset_tokens WHERE email=?', (email,))
        c.execute('INSERT INTO reset_tokens(email,token,expires)VALUES(?,?,?)', (email, token, expires))
        c.commit()  # Ensure the transaction is committed
        
        if send_reset_email(email, token):
            return jsonify({'ok': 1, 'msg': 'Reset token sent to your email'})
        else:
            # Fallback: show token in response for testing
            print(f'\n=== EMAIL FAILED - SHOWING TOKEN FOR TESTING ===')
            print(f'Reset Token for {email}: {token}')
            print('=== Use this token in the reset form ===')
            return jsonify({'ok': 1, 'token': token, 'msg': 'Email service unavailable. Token shown in console.'})

@app.route('/api/check-token', methods=['POST'])
def check_token():
    d = request.json
    token = d['token']
    
    with db() as c:
        reset = c.execute('SELECT email,expires FROM reset_tokens WHERE token=?', (token,)).fetchone()
        current_time = int(time.time())
        
        if not reset:
            return jsonify({'valid': False, 'msg': 'Token not found'})
        
        if reset[1] < current_time:
            return jsonify({'valid': False, 'msg': f'Token expired. Current time: {current_time}, Token expires: {reset[1]}'})
        
        return jsonify({'valid': True, 'email': reset[0], 'expires_in': reset[1] - current_time})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    d = request.json
    token = d.get('token', '').strip()
    new_password = d.get('password', '')
    
    print(f'Reset attempt - Token: "{token}" (length: {len(token)})')
    print(f'Password length: {len(new_password)}')
    
    with db() as c:
        # First, let's see all tokens in the database
        all_tokens = c.execute('SELECT token, email, expires FROM reset_tokens').fetchall()
        print(f'All tokens in database: {[dict(t) for t in all_tokens]}')
        
        reset = c.execute('SELECT email,expires FROM reset_tokens WHERE token=?', (token,)).fetchone()
        current_time = int(time.time())
        
        print(f'Token lookup result: {reset}')
        print(f'Current time: {current_time}')
        
        if not reset:
            print('Token not found in database')
            # Let's check if there's a similar token (maybe whitespace issue)
            similar = c.execute('SELECT token FROM reset_tokens WHERE token LIKE ?', (f'%{token[:10]}%',)).fetchall()
            print(f'Similar tokens found: {[dict(s) for s in similar]}')
            return jsonify({'ok': 0, 'msg': 'Invalid token - not found'}), 400
        
        if reset[1] < current_time:
            print(f'Token expired. Expires: {reset[1]}, Current: {current_time}')
            return jsonify({'ok': 0, 'msg': 'Token has expired'}), 400
        
        pwd_hash = hashlib.sha256(new_password.encode()).hexdigest()
        c.execute('UPDATE users SET password=? WHERE email=?', (pwd_hash, reset[0]))
        c.execute('DELETE FROM reset_tokens WHERE token=?', (token,))
        
        print(f'Password reset successful for {reset[0]}')
        return jsonify({'ok': 1, 'msg': 'Password reset successful'})

@app.route('/api/permissions', methods=['POST'])
def save_permissions():
    if 'uid' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    d = request.json
    permissions = d.get('permissions', {})
    session['permissions'] = permissions
    
    print(f'User {session["email"]} granted permissions: {permissions}')
    return jsonify({'ok': 1, 'msg': 'Permissions saved'})

@app.route('/api/debug/tokens')
def debug_tokens():
    with db() as c:
        tokens = c.execute('SELECT * FROM reset_tokens').fetchall()
        return jsonify([dict(t) for t in tokens])

@app.route('/api/user')
def user():
    user_data = None
    if 'uid' in session:
        user_data = {
            'id': session.get('uid'), 
            'email': session.get('email'),
            'permissions': session.get('permissions', {})
        }
    return jsonify({'user': user_data})

if __name__ == '__main__':
    init()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)