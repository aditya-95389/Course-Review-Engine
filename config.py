import os

# Email Configuration
# To use Gmail SMTP, you need to:
# 1. Enable 2-factor authentication on your Gmail account.
# 2. Generate an App Password: https://myaccount.google.com/apppasswords
# 3. Set SENDER_EMAIL and SENDER_PASSWORD as environment variables.

EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': os.environ.get('SENDER_EMAIL', 'your-email@gmail.com'),
    'SENDER_PASSWORD': os.environ.get('SENDER_PASSWORD', 'your-16-char-app-password'),
    'SENDER_NAME': 'CourseHub Team'
}

# Set to False to actually send emails, True for console debugging
DEBUG_EMAIL = os.environ.get('DEBUG_EMAIL', 'True') == 'True'
