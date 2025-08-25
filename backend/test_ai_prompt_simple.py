#!/usr/bin/env python3
"""
Simple test script for AI Prompt Engineering Service
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.ai_prompt_service import advanced_prompt_engine


def test_basic_functionality():
    """Test basic AI prompt engineering functionality"""
    print("Testing AI Prompt Engineering Service")
    print("=" * 40)
    
    # Test client data
    test_client = {
        'bioData': {
            'fullName': 'Test Client',
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
            'economicStanding': 'High Net Worth'
        },
        'objectives': {
            'objective': 'Create Will',
            'details': 'Estate planning for family'
        }
    }
    
    print("\\n1. Testing Client Analysis...")
    try:
        client_profile = advanced_prompt_engine.client_analyzer.analyze_client_profile(test_client)
        print(f"   ✓ Client analyzed successfully")
        print(f"   ✓ Complexity Score: {client_profile.complexity_score:.2f}")
        print(f"   ✓ Legal Areas: {len(client_profile.legal_areas)} identified")
        print(f"   ✓ Risk Factors: {len(client_profile.risk_factors)} identified")
    except Exception as e:
        print(f"   ✗ Client analysis failed: {e}")
        return False
    
    print("\\n2. Testing Template Selection...")
    try:
        template_type = advanced_prompt_engine._select_optimal_template(client_profile)
        print(f"   ✓ Template selected: {template_type}")
        
        templates = advanced_prompt_engine.template_manager.list_available_templates()
        print(f"   ✓ Available templates: {len(templates)}")
    except Exception as e:
        print(f"   ✗ Template selection failed: {e}")
        return False
    
    print("\\n3. Testing Prompt Generation...")
    try:
        enhanced_prompt = advanced_prompt_engine.generate_enhanced_prompt(
            test_client, "Equal distribution with tax optimization"
        )
        print(f"   ✓ Enhanced prompt generated")
        print(f"   ✓ Prompt length: {len(enhanced_prompt)} characters")
        print(f"   ✓ Word count: {len(enhanced_prompt.split())} words")
        
        # Check for key elements
        key_elements = ["CLIENT", "LEGAL", "TAX", "KENYAN", "law"]
        found = sum(1 for element in key_elements if element.lower() in enhanced_prompt.lower())
        print(f"   ✓ Key elements found: {found}/{len(key_elements)}")
        
    except Exception as e:
        print(f"   ✗ Prompt generation failed: {e}")
        return False
    
    print("\\n4. Testing Different Complexity Levels...")
    
    # Simple client
    simple_client = {
        'bioData': {'fullName': 'Simple Client', 'maritalStatus': 'Single'},
        'financialData': {'assets': [{'type': 'Bank Account', 'value': 1000000}]},
        'economicContext': {'economicStanding': 'Middle Income'},
        'objectives': {'objective': 'Create Will'}
    }
    
    # Complex client
    complex_client = {
        'bioData': {'fullName': 'Complex Client', 'maritalStatus': 'Married', 'children': '3 children'},
        'financialData': {'assets': [
            {'type': 'Business', 'value': 50000000},
            {'type': 'Real Estate', 'value': 30000000},
            {'type': 'Investments', 'value': 20000000}
        ]},
        'economicContext': {'economicStanding': 'High Net Worth'},
        'objectives': {'objective': 'Business Succession Planning'}
    }
    
    try:
        simple_profile = advanced_prompt_engine.client_analyzer.analyze_client_profile(simple_client)
        complex_profile = advanced_prompt_engine.client_analyzer.analyze_client_profile(complex_client)
        
        print(f"   ✓ Simple client complexity: {simple_profile.complexity_score:.2f}")
        print(f"   ✓ Complex client complexity: {complex_profile.complexity_score:.2f}")
        
        simple_template = advanced_prompt_engine._select_optimal_template(simple_profile)
        complex_template = advanced_prompt_engine._select_optimal_template(complex_profile)
        
        print(f"   ✓ Simple client template: {simple_template}")
        print(f"   ✓ Complex client template: {complex_template}")
        
    except Exception as e:
        print(f"   ✗ Complexity testing failed: {e}")
        return False
    
    print("\\n" + "=" * 40)
    print("All tests completed successfully!")
    
    # Save test results
    test_results = {
        "test_run_time": datetime.now().isoformat(),
        "test_status": "PASSED",
        "templates_available": advanced_prompt_engine.template_manager.list_available_templates(),
        "simple_complexity": simple_profile.complexity_score,
        "complex_complexity": complex_profile.complexity_score
    }
    
    results_file = os.path.join(os.path.dirname(__file__), "..", "data", "test_results_ai_prompt.json")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"Test results saved to: {results_file}")
    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)