#!/usr/bin/env python3
"""
Test script for Encryption Service
Verifies the functionality of the data encryption system
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.encryption_service import encryption_service, EncryptionLevel, DataCategory


def test_encryption_service_initialization():
    """Test encryption service initialization"""
    print("\n=== Testing Encryption Service Initialization ===")
    
    if encryption_service is None:
        print("X Encryption service failed to initialize")
        return False
    
    status = encryption_service.get_encryption_status()
    print(f"Encryption available: {status['encryption_available']}")
    print(f"Key version: {status['key_version']}")
    print(f"Master key exists: {status['master_key_exists']}")
    print(f"Keys initialized: {status['keys_initialized']}")
    print(f"Supported levels: {status['supported_levels']}")
    print(f"Supported categories: {status['supported_categories']}")
    
    if status['encryption_available'] and status['keys_initialized']:
        print("✓ Encryption service initialized successfully")
        return True
    else:
        print("X Encryption service initialization incomplete")
        return False


def test_basic_encryption_decryption():
    """Test basic encryption and decryption"""
    print("\n=== Testing Basic Encryption/Decryption ===")
    
    test_data = "This is a test message for encryption"
    
    try:
        # Test encryption
        encrypt_result = encryption_service.encrypt_data(
            test_data,
            DataCategory.PERSONAL_INFO,
            EncryptionLevel.BASIC
        )
        
        if not encrypt_result['success']:
            print(f"X Encryption failed: {encrypt_result.get('error')}")
            return False
        
        print("✓ Basic encryption successful")
        print(f"  Data ID: {encrypt_result['data_id']}")
        print(f"  Encryption level: {encrypt_result['encryption_level']}")
        
        # Test decryption
        decrypt_result = encryption_service.decrypt_data(
            encrypt_result['encrypted_data'],
            encrypt_result['metadata']
        )
        
        if not decrypt_result['success']:
            print(f"X Decryption failed: {decrypt_result.get('error')}")
            return False
        
        if decrypt_result['data'] == test_data:
            print("✓ Basic decryption successful - data matches original")
            return True
        else:
            print("X Decrypted data doesn't match original")
            return False
            
    except Exception as e:
        print(f"X Basic encryption test failed: {e}")
        return False


def test_different_encryption_levels():
    """Test different encryption levels"""
    print("\n=== Testing Different Encryption Levels ===")
    
    test_data = {"sensitive": "financial data", "amount": 50000}
    
    try:
        results = {}
        
        # Test all encryption levels
        for level in EncryptionLevel:
            print(f"Testing {level.value} encryption...")
            
            encrypt_result = encryption_service.encrypt_data(
                test_data,
                DataCategory.FINANCIAL_DATA,
                level
            )
            
            if not encrypt_result['success']:
                print(f"X {level.value} encryption failed: {encrypt_result.get('error')}")
                return False
            
            # Test decryption
            decrypt_result = encryption_service.decrypt_data(
                encrypt_result['encrypted_data'],
                encrypt_result['metadata']
            )
            
            if not decrypt_result['success']:
                print(f"X {level.value} decryption failed: {decrypt_result.get('error')}")
                return False
            
            if decrypt_result['data'] == test_data:
                print(f"✓ {level.value} encryption/decryption successful")
                results[level.value] = True
            else:
                print(f"X {level.value} data mismatch")
                return False
        
        print(f"✓ All encryption levels tested successfully: {list(results.keys())}")
        return True
        
    except Exception as e:
        print(f"X Encryption levels test failed: {e}")
        return False


def test_client_data_encryption():
    """Test client data encryption with mixed sensitivity levels"""
    print("\n=== Testing Client Data Encryption ===")
    
    # Sample client data
    test_client_data = {
        'clientId': 'test_client_123',
        'bioData': {
            'fullName': 'John Doe',
            'dateOfBirth': '1980-01-01',
            'idNumber': '12345678',
            'maritalStatus': 'Married'
        },
        'financialData': {
            'assets': [
                {
                    'type': 'Bank Account',
                    'value': 1000000,
                    'description': 'Savings account'
                },
                {
                    'type': 'Real Estate',
                    'value': 5000000,
                    'description': 'Family home'
                }
            ]
        },
        'economicContext': {
            'economicStanding': 'Middle Income'
        },
        'objectives': {
            'objective': 'Create Will',
            'details': 'Estate planning for family'
        },
        'savedAt': datetime.now().isoformat(),
        'submittedBy': 'test_user'
    }
    
    try:
        # Test encryption
        encrypt_result = encryption_service.encrypt_client_data(test_client_data)
        
        if not encrypt_result['success']:
            print(f"X Client data encryption failed: {encrypt_result.get('error')}")
            return False
        
        encrypted_data = encrypt_result['encrypted_client_data']
        encryption_summary = encrypt_result['encryption_summary']
        
        print("✓ Client data encrypted successfully")
        print(f"  Encrypted fields: {encryption_summary['encrypted_fields']}")
        print(f"  Total encrypted fields: {encryption_summary['total_fields']}")
        
        # Verify that sensitive data is encrypted
        if '_encryption_metadata' not in encrypted_data:
            print("X Encryption metadata missing")
            return False
        
        # Verify that clientId is not encrypted (should remain as-is)
        if encrypted_data.get('clientId') != test_client_data['clientId']:
            print("X Non-sensitive data was incorrectly modified")
            return False
        
        # Test decryption
        decrypt_result = encryption_service.decrypt_client_data(encrypted_data)
        
        if not decrypt_result['success']:
            print(f"X Client data decryption failed: {decrypt_result.get('error')}")
            return False
        
        decrypted_data = decrypt_result['decrypted_client_data']
        
        # Verify original data matches decrypted data
        for field in ['bioData', 'financialData', 'economicContext', 'objectives']:
            if decrypted_data.get(field) != test_client_data.get(field):
                print(f"X Field {field} doesn't match after decryption")
                return False
        
        print("✓ Client data decryption successful - all fields match")
        return True
        
    except Exception as e:
        print(f"X Client data encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test with invalid data category
        try:
            result = encryption_service.encrypt_data(
                "test",
                "invalid_category",  # Invalid category
                EncryptionLevel.STANDARD
            )
            print("X Should have failed with invalid category")
            return False
        except (ValueError, TypeError):
            print("✓ Correctly handled invalid data category")
        
        # Test decryption with corrupted data
        valid_encrypt = encryption_service.encrypt_data(
            "test data",
            DataCategory.PERSONAL_INFO,
            EncryptionLevel.STANDARD
        )
        
        # Corrupt the encrypted data
        corrupted_data = valid_encrypt['encrypted_data'][:-5] + "XXXXX"
        
        decrypt_result = encryption_service.decrypt_data(
            corrupted_data,
            valid_encrypt['metadata']
        )
        
        if not decrypt_result['success']:
            print("✓ Correctly handled corrupted encrypted data")
        else:
            print("X Should have failed with corrupted data")
            return False
        
        return True
        
    except Exception as e:
        print(f"X Error handling test failed: {e}")
        return False


def run_all_tests():
    """Run all test functions"""
    print("Encryption Service - Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # List of test functions
    tests = [
        ("Encryption Service Initialization", test_encryption_service_initialization),
        ("Basic Encryption/Decryption", test_basic_encryption_decryption),
        ("Different Encryption Levels", test_different_encryption_levels),
        ("Client Data Encryption", test_client_data_encryption),
        ("Error Handling", test_error_handling)
    ]
    
    # Run each test
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            test_results.append((test_name, result))
            if result:
                print(f"✓ {test_name} PASSED")
            else:
                print(f"X {test_name} FAILED")
        except Exception as e:
            print(f"X {test_name} FAILED with exception: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        success = True
    else:
        print(f"❌ {total - passed} tests failed")
        success = False
    
    # Save test results
    try:
        results_data = {
            "test_run_time": datetime.now().isoformat(),
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "test_results": [
                {"test_name": name, "passed": result}
                for name, result in test_results
            ],
            "overall_status": "PASSED" if success else "FAILED"
        }
        
        # Save to test results file
        results_file = os.path.join(os.path.dirname(__file__), "..", "data", "test_results_encryption.json")
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"Test results saved to: {results_file}")
        
    except Exception as e:
        print(f"Failed to save test results: {e}")
    
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)