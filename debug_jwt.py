#!/usr/bin/env python3
"""
Debug JWT token validation for the chat endpoint
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

from jose import jwt, JWTError
from datetime import datetime, timezone

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent / "backend" / ".env")

def test_jwt_validation():
    """Test JWT validation with current configuration"""
    
    # Get JWT secret from environment
    jwt_secret = os.getenv("JWT_SECRET_KEY", "your_super_secret_jwt_key_here_change_in_production")
    algorithm = "HS256"
    
    print("=== JWT Debug Information ===")
    print(f"JWT Secret Key: {'*' * (len(jwt_secret) - 8) + jwt_secret[-8:] if jwt_secret else 'NOT SET'}")
    print(f"Algorithm: {algorithm}")
    print()
    
    # Test creating a token like the auth service does
    print("=== Creating Test Token ===")
    test_payload = {
        "sub": "admin",
        "role": "admin", 
        "exp": int((datetime.now(timezone.utc).timestamp())) + 1800,  # 30 minutes
        "type": "access"
    }
    
    try:
        test_token = jwt.encode(test_payload, jwt_secret, algorithm=algorithm)
        print(f"Created token: {test_token[:50]}...")
        print()
        
        # Test decoding the token
        print("=== Validating Test Token ===")
        decoded = jwt.decode(test_token, jwt_secret, algorithms=[algorithm])
        print(f"Decoded payload: {json.dumps(decoded, indent=2)}")
        print("✅ Token validation successful!")
        print()
        
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        return False
    
    # Test with a potentially malformed token format
    print("=== Testing Token Format Issues ===")
    
    # Common issues that could cause validation failure:
    malformed_tests = [
        ("Empty secret", ""),
        ("Wrong algorithm", "HS512"),
        ("Expired token", test_payload.copy())
    ]
    
    for test_name, test_config in malformed_tests:
        try:
            if test_name == "Empty secret":
                jwt.decode(test_token, test_config, algorithms=[algorithm])
            elif test_name == "Wrong algorithm":
                jwt.decode(test_token, jwt_secret, algorithms=[test_config])
            elif test_name == "Expired token":
                # Create expired token
                expired_payload = test_config.copy()
                expired_payload["exp"] = int(datetime.now(timezone.utc).timestamp()) - 3600  # 1 hour ago
                expired_token = jwt.encode(expired_payload, jwt_secret, algorithm=algorithm)
                jwt.decode(expired_token, jwt_secret, algorithms=[algorithm])
                
            print(f"⚠️  {test_name}: Should have failed but didn't")
            
        except JWTError as e:
            print(f"✅ {test_name}: Failed as expected - {e}")
    
    return True

if __name__ == "__main__":
    test_jwt_validation()