#!/usr/bin/env python3
"""
Gmail Setup Helper for CourseHub Password Reset
"""

def setup_gmail():
    print("=== Gmail SMTP Setup for CourseHub ===\n")
    
    print("Steps to set up Gmail SMTP:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification if not already enabled")
    print("3. Go to https://myaccount.google.com/apppasswords")
    print("4. Generate a new App Password for 'Mail'")
    print("5. Copy the 16-character password (spaces will be removed)\n")
    
    email = input("Enter your Gmail address: ").strip()
    password = input("Enter your Gmail App Password (16 characters): ").strip().replace(" ", "")
    
    if len(password) != 16:
        print(f"Warning: App password should be 16 characters, got {len(password)}")
    
    # Update config.py
    config_content = f'''# Email Configuration
# Gmail SMTP setup completed

EMAIL_CONFIG = {{
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': '{email}',
    'SENDER_PASSWORD': '{password}',
    'SENDER_NAME': 'CourseHub Team'
}}

# Set to False to send real emails, True for console debugging
DEBUG_EMAIL = False
'''
    
    with open('config.py', 'w') as f:
        f.write(config_content)
    
    print(f"\n✅ Configuration saved!")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print("\nYou can now test the forgot password feature!")

if __name__ == "__main__":
    setup_gmail()