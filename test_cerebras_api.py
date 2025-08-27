#!/usr/bin/env python3
"""
Test Cerebras AI API directly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_cerebras_api():
    """Test Cerebras API directly"""
    try:
        from cerebras.cloud.sdk import Cerebras
        
        api_key = os.getenv("CEREBRAS_API_KEY")
        print(f"API Key present: {bool(api_key)}")
        print(f"API Key length: {len(api_key) if api_key else 0}")
        
        if not api_key:
            print("❌ No API key found")
            return False
            
        print("🔍 Testing Cerebras API connection...")
        
        client = Cerebras(api_key=api_key)
        
        # Test with a simple legal question
        response = client.chat.completions.create(
            model="gpt-oss-120b",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a legal AI assistant specializing in Kenyan law."
                },
                {
                    "role": "user",
                    "content": "What are the basic requirements for creating a will under Kenyan law?"
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        print("✅ Cerebras API connection successful!")
        print(f"Response: {response.choices[0].message.content[:200]}...")
        return True
        
    except ImportError as e:
        print(f"❌ Cerebras SDK not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Cerebras API test failed: {e}")
        return False

if __name__ == "__main__":
    test_cerebras_api()