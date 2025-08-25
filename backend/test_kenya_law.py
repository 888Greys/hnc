#!/usr/bin/env python3
"""
Test script for Kenya Law Database Service
Verifies the functionality of the legal database integration
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.kenya_law_service import kenya_law_db


def test_basic_search():
    """Test basic legal reference search"""
    print("\\n=== Testing Basic Legal Reference Search ===")
    
    # Test will-related search
    results = kenya_law_db.search_legal_references("will creation requirements")
    print(f"Search 'will creation requirements': Found {len(results)} results")
    
    for i, result in enumerate(results[:3]):
        ref = result['reference']
        print(f"  {i+1}. {ref.get('act_name')} ({ref.get('chapter')}) - {ref.get('title')}")
        print(f"     Score: {result['relevance_score']:.2f}")
    
    # Test trust-related search
    results = kenya_law_db.search_legal_references("trust creation")
    print(f"\\nSearch 'trust creation': Found {len(results)} results")
    
    for i, result in enumerate(results[:2]):
        ref = result['reference']
        print(f"  {i+1}. {ref.get('act_name')} ({ref.get('chapter')}) - {ref.get('title')}")


def test_context_based_search():
    """Test context-based legal reference retrieval"""
    print("\\n=== Testing Context-Based Legal References ===")
    
    # Mock client context for a married person wanting to create a will
    client_context = {
        'bioData': {
            'fullName': 'John Doe',
            'maritalStatus': 'Married',
            'children': '2 children'
        },
        'financialData': {
            'assets': [
                {'type': 'Real Estate', 'value': 10000000},
                {'type': 'Bank Account', 'value': 2000000}
            ]
        },
        'economicContext': {
            'economicStanding': 'Middle Income'
        },
        'objectives': {
            'objective': 'Create Will',
            'details': 'Want to ensure proper distribution to family'
        }
    }
    
    references = kenya_law_db.get_legal_references_for_context(client_context)
    print(f"Found {len(references)} relevant references for married person creating will")
    
    for i, ref in enumerate(references[:5]):
        formatted = kenya_law_db.format_legal_reference_for_ai(ref)
        print(f"  {i+1}. {formatted[:100]}...")


def test_tax_implications():
    """Test tax implication calculations"""
    print("\\n=== Testing Tax Implication Calculations ===")
    
    test_values = [3000000, 5000000, 8000000, 15000000]
    
    for value in test_values:
        tax_info = kenya_law_db.get_tax_implications(value)
        print(f"\\nAsset Value: KES {value:,}")
        print(f"  Tax Applicable: {tax_info['tax_applicable']}")
        print(f"  Advice: {tax_info['advice']}")
        if tax_info['tax_applicable']:
            print(f"  Estimated Tax: KES {tax_info['estimated_tax']:,.2f}")


def test_database_statistics():
    """Test database statistics"""
    print("\\n=== Testing Database Statistics ===")
    
    stats = kenya_law_db.get_database_statistics()
    print(f"Total Acts: {stats['total_acts']}")
    print(f"Total Cases: {stats['total_cases']}")
    print(f"Total Procedures: {stats['total_procedures']}")
    print(f"Coverage Areas: {', '.join(stats['coverage_areas'])}")


def test_search_with_areas():
    """Test search with specific legal areas"""
    print("\\n=== Testing Search with Legal Areas Filter ===")
    
    # Search for succession-related content
    results = kenya_law_db.search_legal_references("inheritance", ["succession", "estate_planning"])
    print(f"Succession area search: Found {len(results)} results")
    
    for result in results[:3]:
        ref = result['reference']
        print(f"  - {ref.get('title')} (Applicability: {', '.join(ref.get('applicability', []))})")


def test_ai_formatting():
    """Test AI-ready formatting of legal references"""
    print("\\n=== Testing AI-Ready Formatting ===")
    
    results = kenya_law_db.search_legal_references("will requirements")
    if results:
        formatted = kenya_law_db.format_legal_reference_for_ai(results[0])
        print("Sample AI-formatted reference:")
        print(f"  {formatted}")


def run_all_tests():
    """Run all test functions"""
    print("Kenya Law Database Service - Test Suite")
    print("=" * 50)
    
    try:
        test_basic_search()
        test_context_based_search()
        test_tax_implications()
        test_database_statistics()
        test_search_with_areas()
        test_ai_formatting()
        
        print("\\n" + "=" * 50)
        print("All tests completed successfully!")
        
        # Save test results
        test_results = {
            "test_run_time": datetime.now().isoformat(),
            "database_stats": kenya_law_db.get_database_statistics(),
            "test_status": "PASSED"
        }
        
        # Save to test results file
        results_file = os.path.join(os.path.dirname(__file__), "..", "data", "test_results_kenya_law.json")
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"Test results saved to: {results_file}")
        
    except Exception as e:
        print(f"\\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)