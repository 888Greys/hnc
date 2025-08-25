#!/usr/bin/env python3
"""
Test script for Document Template Service
Verifies the functionality of the document generation system
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.document_template_service import document_template_manager, DocumentType, DocumentFormat


def test_template_initialization():
    """Test template initialization and file creation"""
    print("\n=== Testing Template Initialization ===")
    
    try:
        # Check if template manager initialized correctly
        print(f"Templates directory: {document_template_manager.templates_dir}")
        print(f"Documents directory: {document_template_manager.documents_dir}")
        print(f"Jinja2 available: {document_template_manager.jinja_env is not None}")
        
        # Check if template files were created
        template_files = list(document_template_manager.templates_dir.glob("*.jinja2"))
        print(f"Template files created: {len(template_files)}")
        
        for template_file in template_files:
            print(f"  - {template_file.name}")
        
        return True
        
    except Exception as e:
        print(f"Template initialization failed: {e}")
        return False


def test_document_types_and_formats():
    """Test document types and formats enum"""
    print("\n=== Testing Document Types and Formats ===")
    
    document_types = [dt.value for dt in DocumentType]
    document_formats = [df.value for df in DocumentFormat]
    
    print(f"Available Document Types ({len(document_types)}):")
    for doc_type in document_types:
        print(f"  - {doc_type}")
    
    print(f"\nAvailable Document Formats ({len(document_formats)}):")
    for doc_format in document_formats:
        print(f"  - {doc_format}")
    
    return True


def test_will_generation():
    """Test will document generation"""
    print("\n=== Testing Will Document Generation ===")
    
    # Sample client data for will generation
    test_client_data = {
        'bioData': {
            'fullName': 'John Doe',
            'address': '123 Main Street, Nairobi, Kenya',
            'dateOfBirth': '1980-05-15',
            'idNumber': '12345678',
            'maritalStatus': 'Married',
            'children': '2 children: Jane (10), Jack (8)'
        },
        'financialData': {
            'assets': [
                {
                    'type': 'Real Estate',
                    'description': 'Family home in Nairobi',
                    'value': 5000000,
                    'location': 'Nairobi'
                },
                {
                    'type': 'Bank Account',
                    'description': 'Savings account',
                    'value': 1000000
                },
                {
                    'type': 'Investments',
                    'description': 'Stock portfolio',
                    'value': 2000000
                }
            ]
        },
        'economicContext': {
            'economicStanding': 'Middle Income'
        },
        'objectives': {
            'objective': 'Create Will',
            'details': 'Want to ensure proper distribution to family members'
        }
    }
    
    try:
        # Generate will document
        result = document_template_manager.generate_document(
            document_type=DocumentType.WILL,
            client_data=test_client_data,
            format_type=DocumentFormat.HTML
        )
        
        if result.get('success'):
            print("✓ Will document generated successfully")
            print(f"  Document ID: {result['document_id']}")
            print(f"  Format: {result['format']}")
            print(f"  Content length: {result['content_length']} characters")
            print(f"  File path: {result['file_path']}")
            
            # Test document retrieval
            retrieved = document_template_manager.get_document(result['document_id'])
            if retrieved.get('success'):
                print("✓ Document retrieval successful")
                print(f"  Retrieved content length: {len(retrieved['content'])}")
            else:
                print(f"✗ Document retrieval failed: {retrieved.get('error')}")
                return False
            
            return True
        else:
            print(f"✗ Will generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Will generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trust_deed_generation():
    """Test trust deed generation"""
    print("\n=== Testing Trust Deed Generation ===")
    
    test_client_data = {
        'bioData': {
            'fullName': 'Mary Williams',
            'address': '456 Oak Avenue, Mombasa, Kenya',
            'maritalStatus': 'Married',
            'children': '3 children'
        },
        'financialData': {
            'assets': [
                {
                    'type': 'Business',
                    'description': 'Import/Export Business',
                    'value': 15000000
                },
                {
                    'type': 'Real Estate',
                    'description': 'Commercial property',
                    'value': 10000000
                }
            ]
        },
        'objectives': {
            'objective': 'Create Trust',
            'details': 'Family trust for asset protection'
        }
    }
    
    try:
        result = document_template_manager.generate_document(
            document_type=DocumentType.TRUST_DEED,
            client_data=test_client_data,
            format_type=DocumentFormat.HTML
        )
        
        if result.get('success'):
            print("✓ Trust deed generated successfully")
            print(f"  Document ID: {result['document_id']}")
            return True
        else:
            print(f"✗ Trust deed generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Trust deed test failed: {e}")
        return False


def test_asset_declaration_generation():
    """Test asset declaration generation"""
    print("\n=== Testing Asset Declaration Generation ===")
    
    test_client_data = {
        'bioData': {
            'fullName': 'Robert Johnson',
            'idNumber': '87654321',
            'address': '789 Pine Street, Kisumu, Kenya'
        },
        'financialData': {
            'assets': [
                {
                    'type': 'Real Estate',
                    'description': 'Residential property',
                    'value': 8000000,
                    'location': 'Kisumu'
                },
                {
                    'type': 'Bank Account',
                    'description': 'Current account',
                    'value': 500000
                },
                {
                    'type': 'Vehicle',
                    'description': 'Toyota Land Cruiser',
                    'value': 3000000
                }
            ]
        },
        'objectives': {
            'objective': 'Asset Declaration',
            'details': 'Complete asset disclosure for legal purposes'
        }
    }
    
    try:
        result = document_template_manager.generate_document(
            document_type=DocumentType.ASSET_DECLARATION,
            client_data=test_client_data,
            format_type=DocumentFormat.HTML
        )
        
        if result.get('success'):
            print("✓ Asset declaration generated successfully")
            print(f"  Document ID: {result['document_id']}")
            
            # Check if asset categorization worked
            retrieved = document_template_manager.get_document(result['document_id'])
            if retrieved.get('success'):
                content = retrieved['content']
                if 'Real Estate' in content and 'Bank Account' in content:
                    print("✓ Asset categorization working correctly")
                else:
                    print("⚠ Asset categorization may have issues")
            
            return True
        else:
            print(f"✗ Asset declaration generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Asset declaration test failed: {e}")
        return False


def test_document_listing_and_management():
    """Test document listing and management features"""
    print("\n=== Testing Document Management ===")
    
    try:
        # List all documents
        documents = document_template_manager.list_documents()
        print(f"Total documents in system: {len(documents)}")
        
        if documents:
            print("Recent documents:")
            for i, doc in enumerate(documents[:3]):
                print(f"  {i+1}. {doc.get('document_type')} for {doc.get('client_name')} - {doc.get('document_id')}")
        
        # Test filtering by client name
        filtered_docs = document_template_manager.list_documents("John Doe")
        print(f"Documents for 'John Doe': {len(filtered_docs)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Document management test failed: {e}")
        return False


def test_legal_reference_integration():
    """Test integration with Kenya Law database"""
    print("\n=== Testing Legal Reference Integration ===")
    
    test_client_data = {
        'objectives': {
            'objective': 'Create Will'
        }
    }
    
    try:
        # Test getting legal references for will creation
        legal_refs = document_template_manager._get_relevant_legal_references(
            DocumentType.WILL, test_client_data
        )
        
        print(f"Legal references found: {len(legal_refs)}")
        if legal_refs:
            print("Sample legal references:")
            for i, ref in enumerate(legal_refs[:2]):
                print(f"  {i+1}. {ref[:100]}...")
        
        return len(legal_refs) > 0
        
    except Exception as e:
        print(f"✗ Legal reference integration test failed: {e}")
        return False


def test_template_data_preparation():
    """Test template data preparation for different document types"""
    print("\n=== Testing Template Data Preparation ===")
    
    test_client_data = {
        'bioData': {
            'fullName': 'Test Client',
            'maritalStatus': 'Single',
            'address': 'Test Address'
        },
        'financialData': {
            'assets': [
                {'type': 'Bank Account', 'value': 1000000},
                {'type': 'Real Estate', 'value': 5000000}
            ]
        },
        'objectives': {
            'objective': 'Create Will'
        }
    }
    
    try:
        # Test will data preparation
        will_data = document_template_manager._prepare_template_data(
            DocumentType.WILL, test_client_data
        )
        
        print("Will template data prepared:")
        print(f"  Client name: {will_data.get('client_name')}")
        print(f"  Total assets: {will_data.get('total_assets'):,}")
        print(f"  Has executor: {'executor_name' in will_data}")
        print(f"  Has legal references: {'legal_references' in will_data}")
        
        # Test asset declaration data preparation
        asset_data = document_template_manager._prepare_template_data(
            DocumentType.ASSET_DECLARATION, test_client_data
        )
        
        print("\nAsset declaration data prepared:")
        print(f"  Bank accounts: {len(asset_data.get('bank_accounts', []))}")
        print(f"  Real estate: {len(asset_data.get('real_estate_assets', []))}")
        print(f"  Net worth: {asset_data.get('net_worth', 0):,}")
        
        return True
        
    except Exception as e:
        print(f"✗ Template data preparation test failed: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test with invalid document type
        try:
            result = document_template_manager.generate_document(
                document_type="invalid_type",  # This should fail
                client_data={},
                format_type=DocumentFormat.HTML
            )
            print("✗ Should have failed with invalid document type")
            return False
        except (ValueError, AttributeError):
            print("✓ Correctly handled invalid document type")
        
        # Test with empty client data
        result = document_template_manager.generate_document(
            document_type=DocumentType.WILL,
            client_data={},  # Empty data
            format_type=DocumentFormat.HTML
        )
        
        if result.get('success'):
            print("✓ Handled empty client data gracefully")
        else:
            print(f"Document generation with empty data: {result.get('error', 'Failed')}")
        
        # Test retrieving non-existent document
        result = document_template_manager.get_document("non_existent_doc_id")
        if not result.get('success'):
            print("✓ Correctly handled non-existent document request")
        else:
            print("✗ Should have failed for non-existent document")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def run_all_tests():
    """Run all test functions"""
    print("Document Template Service - Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # List of test functions
    tests = [
        ("Template Initialization", test_template_initialization),
        ("Document Types and Formats", test_document_types_and_formats),
        ("Will Generation", test_will_generation),
        ("Trust Deed Generation", test_trust_deed_generation),
        ("Asset Declaration Generation", test_asset_declaration_generation),
        ("Document Management", test_document_listing_and_management),
        ("Legal Reference Integration", test_legal_reference_integration),
        ("Template Data Preparation", test_template_data_preparation),
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
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
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
        results_file = os.path.join(os.path.dirname(__file__), "..", "data", "test_results_document_templates.json")
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