from flask import Flask, render_template, request, jsonify, session
import hashlib
import secrets
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG, DEBUG_EMAIL
from vercel_db import get_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/courses')
def courses():
    db = get_db()
    search_term = request.args.get('search', '')
    
    if search_term:
        courses_list = db.search_courses(search_term)
    else:
        courses_list = db.get_all_courses()
    
    return jsonify(courses_list)

@app.route('/api/courses/<int:id>')
def course(id):
    db = get_db()
    course = db.get_course_by_id(id)
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    reviews = db.get_course_reviews(id)
    
    # Calculate average rating
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
    else:
        avg_rating = None
    
    return jsonify({
        'course': course,
        'reviews': reviews,
        'avg': avg_rating,
        'current_user_id': session.get('uid')
    })

@app.route('/api/auth', methods=['POST'])
def auth():
    db = get_db()
    d = request.json
    email = d['email']
    password = d['password']
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if d.get('register'):
        # Validate email format
        if not email or '@' not in email:
            return jsonify({'ok': 0, 'msg': 'Invalid email format'}), 400
        
        # Validate password
        if not password or len(password) < 6:
            return jsonify({'ok': 0, 'msg': 'Password must be at least 6 characters'}), 400
        
        # Check if email already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return jsonify({'ok': 0, 'msg': 'Email already registered'}), 400
        
        try:
            user = db.create_user(email, pwd_hash)
            print(f'Successfully registered new user: {email}')
            return jsonify({'ok': 1, 'msg': 'Registration successful'})
        except Exception as e:
            print(f'Registration error: {e}')
            return jsonify({'ok': 0, 'msg': 'Registration failed'}), 500
    
    else:  # Login
        # Validate login input
        if not email or not password:
            return jsonify({'ok': 0, 'msg': 'Email and password required'}), 400
        
        print(f'Login attempt for email: {email}')
        user = db.get_user_by_email(email)
        
        if user and user['password'] == pwd_hash:
            session.update({'uid': user['id'], 'email': user['email']})
            print(f'Login successful for user: {email}')
            return jsonify({'ok': 1, 'user': {'id': user['id'], 'email': user['email']}})
        elif user:
            print(f'Login failed - wrong password for: {email}')
            return jsonify({'ok': 0, 'msg': 'Invalid password'}), 401
        else:
            print(f'Login failed - email not found: {email}')
            return jsonify({'ok': 0, 'msg': 'Email not registered'}), 401

@app.route('/api/reviews', methods=['POST'])
def review():
    if 'uid' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    db = get_db()
    d = request.json
    
    try:
        review = db.create_review(
            user_id=session['uid'],
            course_id=d['course_id'],
            rating=d['rating'],
            text=d['text']
        )
        return jsonify({'ok': 1})
    except Exception as e:
        print(f'Review creation error: {e}')
        return jsonify({'ok': 0, 'msg': 'Failed to create review'}), 500

@app.route('/api/reviews/<int:id>', methods=['PUT'])
def edit_review(id):
    if 'uid' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    db = get_db()
    d = request.json
    
    success = db.update_review(id, d['rating'], d['text'], session['uid'])
    
    if success:
        return jsonify({'ok': 1})
    else:
        return jsonify({'ok': 0, 'msg': 'Review not found or permission denied'}), 403

@app.route('/api/reviews/<int:id>', methods=['DELETE'])
def delete_review(id):
    if 'uid' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    db = get_db()
    success = db.delete_review(id, session['uid'])
    
    if success:
        return jsonify({'ok': 1})
    else:
        return jsonify({'ok': 0, 'msg': 'Review not found or permission denied'}), 403

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
        server.set_debuglevel(0)
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
        return False
    except Exception as e:
        print(f'Email sending failed: {e}')
        return False

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    db = get_db()
    d = request.json
    email = d['email']
    
    user = db.get_user_by_email(email)
    if not user:
        return jsonify({'ok': 0, 'msg': 'Email not found'}), 404
    
    token = secrets.token_urlsafe(32)
    expires = int(time.time()) + 3600  # 1 hour
    
    print(f'Generated token for {email}: {token}')
    print(f'Token expires at: {expires} (current: {int(time.time())})')
    
    db.store_reset_token(email, token, expires)
    
    if send_reset_email(email, token):
        return jsonify({'ok': 1, 'msg': 'Reset token sent to your email'})
    else:
        print(f'\n=== EMAIL FAILED - SHOWING TOKEN FOR TESTING ===')
        print(f'Reset Token for {email}: {token}')
        print('=== Use this token in the reset form ===')
        return jsonify({'ok': 1, 'token': token, 'msg': 'Email service unavailable. Token shown in console.'})

@app.route('/api/check-token', methods=['POST'])
def check_token():
    db = get_db()
    d = request.json
    token = d['token']
    
    reset_data = db.get_reset_token(token)
    current_time = int(time.time())
    
    if not reset_data:
        return jsonify({'valid': False, 'msg': 'Token not found'})
    
    if reset_data['expires'] < current_time:
        return jsonify({'valid': False, 'msg': f'Token expired. Current time: {current_time}, Token expires: {reset_data["expires"]}'})
    
    return jsonify({'valid': True, 'email': reset_data['email'], 'expires_in': reset_data['expires'] - current_time})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    db = get_db()
    d = request.json
    token = d.get('token', '').strip()
    new_password = d.get('password', '')
    
    print(f'Reset attempt - Token: "{token}" (length: {len(token)})')
    print(f'Password length: {len(new_password)}')
    
    reset_data = db.get_reset_token(token)
    current_time = int(time.time())
    
    if not reset_data:
        print('Token not found in database')
        return jsonify({'ok': 0, 'msg': 'Invalid token - not found'}), 400
    
    if reset_data['expires'] < current_time:
        print(f'Token expired. Expires: {reset_data["expires"]}, Current: {current_time}')
        return jsonify({'ok': 0, 'msg': 'Token has expired'}), 400
    
    pwd_hash = hashlib.sha256(new_password.encode()).hexdigest()
    success = db.update_user_password(reset_data['email'], pwd_hash)
    
    if success:
        db.delete_reset_token(token)
        print(f'Password reset successful for {reset_data["email"]}')
        return jsonify({'ok': 1, 'msg': 'Password reset successful'})
    else:
        return jsonify({'ok': 0, 'msg': 'Failed to update password'}), 500

@app.route('/api/debug/tokens')
def debug_tokens():
    db = get_db()
    return jsonify(list(db.reset_tokens.items()))

@app.route('/api/user')
def user():
    user_data = None
    if 'uid' in session:
        user_data = {
            'id': session.get('uid'), 
            'email': session.get('email')
        }
    return jsonify({'user': user_data})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
