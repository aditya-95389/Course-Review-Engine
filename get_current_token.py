#!/usr/bin/env python3
"""
Get current valid token for testing
"""
import sqlite3
import time

def get_current_token():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    
    email = 'adityaroyal5398@gmail.com'
    current_time = int(time.time())
    
    # Get current valid token
    result = conn.execute(
        'SELECT token, expires FROM reset_tokens WHERE email=? AND expires > ?', 
        (email, current_time)
    ).fetchone()
    
    if result:
        print(f"Current valid token for {email}:")
        print(f"Token: {result['token']}")
        print(f"Expires in: {result['expires'] - current_time} seconds")
        print(f"Copy this token to test password reset")
    else:
        print(f"No valid token found for {email}")
        print("Generate a new one using the forgot password feature")
    
    conn.close()

if __name__ == "__main__":
    get_current_token()