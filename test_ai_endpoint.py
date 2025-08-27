#!/usr/bin/env python3
"""
Test to verify FastAPI backend is using real Cerebras AI
"""

import requests
import json

def test_ai_endpoint():
    """Test the AI generation endpoint"""
    
    # Sample questionnaire data
    test_data = {
        "questionnaireData": {
            "bioData": {
                "fullName": "John Doe",
                "maritalStatus": "Married",
                "spouseName": "Jane Doe",
                "spouseId": "12345678",
                "children": "2 children: Mary (10), Peter (8)"
            },
            "financialData": {
                "assets": [
                    {
                        "type": "Real Estate",
                        "description": "Family home in Nairobi",
                        "value": 8000000
                    },
                    {
                        "type": "Savings",
                        "description": "Bank savings account",
                        "value": 2000000
                    }
                ],
                "liabilities": "Mortgage of KES 3,000,000",
                "incomeSources": "Monthly salary KES 150,000"
            },
            "economicContext": {
                "economicStanding": "Upper middle class",
                "distributionPrefs": "Equal distribution to children, with spouse as executor"
            },
            "objectives": {
                "objective": "Create Will",
                "details": "Need to create a comprehensive will to protect family assets"
            },
            "lawyerNotes": "Client wants immediate action due to health concerns"
        },
        "distributionPrefs": "Equal distribution to children, with spouse as executor"
    }
    
    # Test the AI endpoint
    try:
        print("🔍 Testing AI proposal generation endpoint...")
        
        # First, we need to login to get a token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = requests.post("http://localhost:8000/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Now test the AI endpoint
        response = requests.post(
            "http://localhost:8000/ai/generate-proposal",
            json=test_data,
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ AI endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        result = response.json()
        
        print("✅ AI endpoint responded successfully!")
        print(f"Suggestion preview: {result['suggestion'][:200]}...")
        
        # Check if it's using real AI (should be much more detailed than mock)
        if len(result['suggestion']) > 500 and "Kenyan law" in result['suggestion']:
            print("✅ Appears to be using real Cerebras AI (detailed response)")
        else:
            print("⚠️  Might still be using mock response (short/generic response)")
            
        print(f"Legal references: {len(result.get('legalReferences', []))} found")
        print(f"Consequences: {len(result.get('consequences', []))} found")
        print(f"Next steps: {len(result.get('nextSteps', []))} found")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_ai_endpoint()