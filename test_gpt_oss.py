#!/usr/bin/env python3
"""
GPT-OSS Model Test Script
Specifically tests the GPT-OSS model with different parameters
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gpt_oss_detailed():
    """Test GPT-OSS model with various parameter combinations"""
    
    print("🧪 Testing GPT-OSS Model in Detail...")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("❌ CEREBRAS_API_KEY not found")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Import SDK
    try:
        from cerebras.cloud.sdk import Cerebras
        client = Cerebras(api_key=api_key)
        print("✅ Cerebras client initialized")
    except Exception as e:
        print(f"❌ Client init failed: {e}")
        return False
    
    # Test different parameter combinations for GPT-OSS
    test_cases = [
        {
            "name": "Basic GPT-OSS Test",
            "params": {
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": "Say 'Hello from GPT-OSS!'"}],
                "max_tokens": 50,
                "temperature": 0.1
            }
        },
        {
            "name": "GPT-OSS with System Message",
            "params": {
                "model": "gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Respond with exactly: 'GPT-OSS is working correctly!'"}
                ],
                "max_tokens": 50,
                "temperature": 0.0
            }
        },
        {
            "name": "GPT-OSS Higher Token Limit",
            "params": {
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": "Write a short sentence about AI."}],
                "max_tokens": 100,
                "temperature": 0.7
            }
        },
        {
            "name": "GPT-OSS Legal Question",
            "params": {
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": "What is a will in legal terms? Give a brief answer."}],
                "max_tokens": 200,
                "temperature": 0.3
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            response = client.chat.completions.create(**test_case['params'])
            
            # Debug the response structure
            print(f"📊 Response type: {type(response)}")
            print(f"📊 Response object: {response}")
            
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                print(f"📊 Choice type: {type(choice)}")
                print(f"📊 Choice object: {choice}")
                
                if hasattr(choice, 'message'):
                    message = choice.message
                    print(f"📊 Message type: {type(message)}")
                    print(f"📊 Message object: {message}")
                    
                    if hasattr(message, 'content'):
                        content = message.content
                        print(f"📊 Content type: {type(content)}")
                        print(f"✅ Response content: '{content}'")
                        
                        if content and content.strip():
                            print("🎉 Success: Got valid response!")
                            success_count += 1
                        else:
                            print("⚠️  Warning: Content is empty or None")
                    else:
                        print("❌ No 'content' attribute in message")
                else:
                    print("❌ No 'message' attribute in choice")
            else:
                print("❌ No 'choices' in response")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        print()
    
    print("=" * 60)
    print(f"📈 Results: {success_count}/{len(test_cases)} tests successful")
    
    return success_count > 0

if __name__ == "__main__":
    print("GPT-OSS Detailed Test Tool")
    print("=" * 60)
    
    success = test_gpt_oss_detailed()
    
    if success:
        print("🎉 GPT-OSS model is working!")
        sys.exit(0)
    else:
        print("❌ GPT-OSS tests failed!")
        sys.exit(1)