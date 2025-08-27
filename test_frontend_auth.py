#!/usr/bin/env python3
"""
Test frontend authentication flow
"""

import requests
import json

def test_frontend_auth():
    """Test if frontend can authenticate properly"""
    print("🔍 Testing frontend authentication flow...")
    
    try:
        # Test login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post("http://localhost:8000/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        login_result = response.json()
        print("✅ Login successful!")
        print(f"Access token present: {bool(login_result.get('access_token'))}")
        print(f"User: {login_result.get('user', {}).get('username')}")
        
        # Test authenticated endpoint
        token = login_result.get('access_token')
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the chat endpoint
        chat_data = {
            "message": "What is the succession law in Kenya?",
            "context": "general"
        }
        
        chat_response = requests.post(
            "http://localhost:8000/ai/chat",
            json=chat_data,
            headers=headers
        )
        
        if chat_response.status_code != 200:
            print(f"❌ Chat endpoint failed: {chat_response.status_code}")
            print(f"Response: {chat_response.text}")
            return False
            
        chat_result = chat_response.json()
        print("✅ Chat endpoint working!")
        print(f"AI Response preview: {chat_result.get('response', '')[:100]}...")
        print(f"Is Real AI: {chat_result.get('isRealAI')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_frontend_auth()