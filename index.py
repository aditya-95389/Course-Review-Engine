from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html>
<head>
<title>CourseHub</title>
<style>
body{font:16px Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;color:white;text-align:center;padding:2rem}
h1{font-size:3rem;margin:2rem 0}
</style>
</head>
<body>
<h1>🎓 CourseHub</h1>
<p>Course Review Platform - Running on Vercel!</p>
</body>
</html>'''

if __name__ == '__main__':
    app.run()