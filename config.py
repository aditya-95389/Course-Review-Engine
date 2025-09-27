# Email Configuration
# To use Gmail SMTP, you need to:
# 1. Enable 2-factor authentication on your Gmail account
# 2. Generate an App Password: https://myaccount.google.com/apppasswords
# 3. Replace the values below with your actual credentials

EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': 'adityaroyal5398@gmail.com',
    'SENDER_PASSWORD': 'vxmcpbudkmjfbrjt',
    'SENDER_NAME': 'CourseHub Team'
}

# Set to False to actually send emails, True for console debugging
DEBUG_EMAIL = False