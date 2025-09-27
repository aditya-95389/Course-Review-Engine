from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html>
<head><title>CourseHub</title></head>
<body>
<h1>🎓 CourseHub - Course Reviews</h1>
<p>Your Flask app is running on Vercel!</p>
</body>
</html>'''

if __name__ == '__main__':
    app.run()