#!/usr/bin/env python3
"""
Quick script to update Gmail App Password
"""

def update_gmail_password():
    print("Enter your Gmail App Password (16 characters from Google Account settings):")
    app_password = input("App Password: ").strip().replace(" ", "")
    
    if len(app_password) != 16:
        print(f"Warning: App password should be 16 characters, you entered {len(app_password)}")
        if input("Continue anyway? (y/n): ").lower() != 'y':
            return
    
    # Read current config
    with open('config.py', 'r') as f:
        content = f.read()
    
    # Replace the password
    updated_content = content.replace(
        "'SENDER_PASSWORD': 'your-app-password-here',",
        f"'SENDER_PASSWORD': '{app_password}',"
    )
    
    # Write back
    with open('config.py', 'w') as f:
        f.write(updated_content)
    
    print("✅ Gmail App Password updated successfully!")
    print("You can now test the forgot password feature.")

if __name__ == "__main__":
    update_gmail_password()