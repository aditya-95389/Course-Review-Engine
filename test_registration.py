#!/usr/bin/env python3

import requests
import json

# Test registration endpoint
def test_registration():
    url = "http://localhost:5000/api/auth"
    
    # Test data
    test_cases = [
        {
            "email": "testuser1@example.com",
            "password": "password123",
            "register": True
        },
        {
            "email": "testuser2@gmail.com", 
            "password": "mypassword",
            "register": True
        },
        {
            "email": "invalid-email",  # Invalid format
            "password": "password123",
            "register": True
        },
        {
            "email": "shortpass@test.com",
            "password": "123",  # Too short
            "register": True
        }
    ]
    
    print("Testing registration endpoint...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['email']}")
        print("-" * 30)
        
        try:
            response = requests.post(url, 
                                   json=test_case, 
                                   headers={'Content-Type': 'application/json'})
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - Make sure the server is running on localhost:5000")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True

if __name__ == "__main__":
    test_registration()
