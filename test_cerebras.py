#!/usr/bin/env python3
"""
Cerebras API Key Test Script
Tests if the Cerebras API key is working with proper SDK initialization
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_cerebras_api():
    """Test Cerebras API key and SDK functionality"""
    
    print("🔍 Testing Cerebras API Key...")
    print("=" * 50)
    
    # Check if API key is loaded
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("❌ CEREBRAS_API_KEY not found in environment variables")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")
    
    # Test SDK import
    try:
        from cerebras.cloud.sdk import Cerebras
        print("✅ Cerebras SDK imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Cerebras SDK: {e}")
        return False
    
    # Test client initialization with proper parameters
    print("\n🧪 Testing Cerebras client initialization...")
    
    try:
        # Initialize client with minimal parameters to avoid 'proxies' error
        client = Cerebras(api_key=api_key)
        print("✅ Cerebras client initialized successfully")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False
    
    # Test actual API call
    print("\n🚀 Testing actual API call...")
    
    # Try different model names that might be available
    model_names = [
        "gpt-oss-120b",
        "gpt-oss-70b", 
        "gpt-oss-8b",
        "gpt-4o",
        "gpt-4",
        "llama3.1-8b",
        "llama3.1-70b"
    ]
    
    for model_name in model_names:
        try:
            print(f"\n🧪 Trying model: {model_name}")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello! Can you respond with exactly: 'Cerebras API is working!'"
                    }
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            ai_response = response.choices[0].message.content
            print(f"✅ API call successful with model {model_name}!")
            print(f"📝 Response: {ai_response}")
            
            if "Cerebras API is working" in ai_response:
                print("🎉 Cerebras API is fully functional!")
                return True
            else:
                print("⚠️ API responded but with unexpected content")
                return True  # Still working, just different response
                
        except Exception as e:
            print(f"❌ Model {model_name} failed: {e}")
            continue
    
    print("❌ All model attempts failed")
    return False

if __name__ == "__main__":
    print("Cerebras API Test Tool")
    print("=" * 50)
    
    success = test_cerebras_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 RESULT: Cerebras API is working correctly!")
        sys.exit(0)
    else:
        print("❌ RESULT: Cerebras API test failed!")
        sys.exit(1)