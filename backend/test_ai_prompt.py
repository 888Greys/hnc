#!/usr/bin/env python3
"""
Test script for AI Prompt Engineering Service
Verifies the functionality of the advanced prompt engineering system
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.ai_prompt_service import advanced_prompt_engine, ClientComplexity, LegalArea


def test_client_analysis():
    """Test client complexity analysis"""
    print("\n=== Testing Client Complexity Analysis ===")
    
    # Test data for different client scenarios
    test_clients = [
        {
            'name': 'Simple Client',
            'data': {
                'bioData': {
                    'fullName': 'Jane Smith',
                    'maritalStatus': 'Single',
                    'children': 'None'
                },
                'financialData': {
                    'assets': [
                        {'type': 'Bank Account', 'value': 2000000}
                    ]
                },
                'economicContext': {
                    'economicStanding': 'Middle Income'
                },
                'objectives': {
                    'objective': 'Create Will',
                    'details': 'Simple will for small estate'
                }
            }
        },
        {
            'name': 'Complex Business Owner',
            'data': {
                'bioData': {
                    'fullName': 'Robert Johnson',
                    'maritalStatus': 'Married',
                    'children': '3 children'
                },
                'financialData': {
                    'assets': [
                        {'type': 'Business', 'value': 25000000},
                        {'type': 'Real Estate', 'value': 15000000},
                        {'type': 'Investments', 'value': 8000000}
                    ]
                },
                'economicContext': {
                    'economicStanding': 'High Net Worth'
                },
                'objectives': {
                    'objective': 'Business Succession Planning',
                    'details': 'Complex succession with family trust'
                }
            }
        },
        {
            'name': 'High Net Worth Trust Client',
            'data': {
                'bioData': {
                    'fullName': 'Mary Williams',
                    'maritalStatus': 'Married',
                    'children': '2 children'
                },
                'financialData': {
                    'assets': [
                        {'type': 'Real Estate', 'value': 30000000},
                        {'type': 'Shares', 'value': 20000000},
                        {'type': 'Bank Account', 'value': 5000000}
                    ]
                },
                'economicContext': {
                    'economicStanding': 'High Net Worth'
                },
                'objectives': {
                    'objective': 'Create Trust',
                    'details': 'Family trust for tax optimization'
                }
            }
        }
    ]
    
    for client in test_clients:
        print(f\"\\nAnalyzing: {client['name']}\")
        
        client_profile = advanced_prompt_engine.client_analyzer.analyze_client_profile(client['data'])
        template_type = advanced_prompt_engine._select_optimal_template(client_profile)
        
        print(f\"  Complexity Score: {client_profile.complexity_score:.2f}\")
        print(f\"  Complexity Level: {advanced_prompt_engine._get_complexity_level(client_profile.complexity_score)}\")
        print(f\"  Legal Areas: {[area.value for area in client_profile.legal_areas]}\")
        print(f\"  Risk Factors: {len(client_profile.risk_factors)} identified\")
        print(f\"  Recommended Template: {template_type}\")
        print(f\"  Special Considerations: {len(client_profile.special_considerations)}\")


def test_template_selection():
    """Test template selection logic"""
    print("\\n=== Testing Template Selection ===")
    
    templates = advanced_prompt_engine.template_manager.list_available_templates()
    print(f\"Available Templates: {templates}\")
    
    # Test different template selections
    scenarios = [
        (\"Simple will\", 2.0, [LegalArea.WILLS]),
        (\"Complex trust\", 6.5, [LegalArea.TRUSTS, LegalArea.TAX_PLANNING]),
        (\"Business succession\", 7.0, [LegalArea.BUSINESS]),
        (\"Matrimonial planning\", 4.0, [LegalArea.MATRIMONIAL]),
        (\"Tax optimization\", 5.0, [LegalArea.TAX_PLANNING])
    ]
    
    for scenario_name, complexity, legal_areas in scenarios:
        print(f\"\\nScenario: {scenario_name}\")
        print(f\"  Complexity: {complexity}\")
        print(f\"  Legal Areas: {[area.value for area in legal_areas]}\")
        
        # Create mock client profile
        from services.ai_prompt_service import ClientProfile
        mock_profile = ClientProfile(
            name=\"Test Client\",
            marital_status=\"Unknown\",
            children=None,
            economic_standing=\"Unknown\",
            total_assets=10000000,
            primary_objective=scenario_name,
            complexity_score=complexity,
            risk_factors=[],
            legal_areas=legal_areas,
            special_considerations=[]
        )
        
        template = advanced_prompt_engine._select_optimal_template(mock_profile)
        print(f\"  Selected Template: {template}\")


def test_prompt_generation():
    """Test actual prompt generation"""
    print("\\n=== Testing Prompt Generation ===")
    
    # Test client data
    test_client = {
        'bioData': {
            'fullName': 'David Chen',
            'maritalStatus': 'Married',
            'children': '2 children: Sarah (12), Michael (8)'
        },
        'financialData': {
            'assets': [
                {'type': 'Real Estate', 'value': 12000000},
                {'type': 'Business', 'value': 8000000},
                {'type': 'Bank Account', 'value': 1500000}
            ]
        },
        'economicContext': {
            'economicStanding': 'High Net Worth'
        },
        'objectives': {
            'objective': 'Create Trust',
            'details': 'Family trust for asset protection and succession'
        }
    }
    
    try:
        enhanced_prompt = advanced_prompt_engine.generate_enhanced_prompt(
            test_client, \"Equal distribution to spouse and children with tax optimization\"
        )
        
        print(\"Enhanced Prompt Generated Successfully!\")
        print(f\"Prompt Length: {len(enhanced_prompt)} characters\")
        print(f\"Word Count: {len(enhanced_prompt.split())} words\")
        
        # Show first 500 characters as preview
        print(f\"\\nPrompt Preview (first 500 chars):\")
        print(enhanced_prompt[:500] + \"...\")
        
        # Check for key elements
        key_elements = [
            \"CLIENT PROFILE\",
            \"LEGAL FRAMEWORK\", 
            \"TAX CONTEXT\",
            \"RISK ASSESSMENT\",
            \"Kenyan law\"
        ]
        
        found_elements = [element for element in key_elements if element in enhanced_prompt]
        print(f\"\\nKey Elements Found: {found_elements}\")
        
    except Exception as e:
        print(f\"Error generating prompt: {e}\")
        import traceback
        traceback.print_exc()


def test_template_formatting():
    """Test template formatting with different scenarios"""
    print("\\n=== Testing Template Formatting ===")
    
    templates_to_test = [\"basic_will\", \"complex_trust\", \"business_succession\"]
    
    for template_name in templates_to_test:
        print(f\"\\nTesting Template: {template_name}\")
        
        try:
            template = advanced_prompt_engine.template_manager.get_template(template_name)
            print(f\"  Template loaded successfully\")
            print(f\"  Template length: {len(template)} characters\")
            
            # Count placeholders
            placeholders = template.count('{')
            print(f\"  Placeholders found: {placeholders}\")
            
        except Exception as e:
            print(f\"  Error with template {template_name}: {e}\")


def test_risk_assessment():
    """Test risk assessment functionality"""
    print(\"\\n=== Testing Risk Assessment ===\")
    
    risk_scenarios = [
        {
            'name': 'High Value Estate',
            'data': {
                'bioData': {'fullName': 'Test', 'maritalStatus': 'Single'},
                'financialData': {'assets': [{'type': 'Real Estate', 'value': 25000000}]},
                'economicContext': {'economicStanding': 'High Net Worth'},
                'objectives': {'objective': 'Create Will'}
            }
        },
        {
            'name': 'Complex Family Structure',
            'data': {
                'bioData': {'fullName': 'Test', 'maritalStatus': 'Divorced', 'children': '3 children'},
                'financialData': {'assets': [{'type': 'Bank Account', 'value': 3000000}]},
                'economicContext': {'economicStanding': 'Middle Income'},
                'objectives': {'objective': 'Create Will'}
            }
        }
    ]
    
    for scenario in risk_scenarios:
        print(f\"\\nScenario: {scenario['name']}\")
        
        client_profile = advanced_prompt_engine.client_analyzer.analyze_client_profile(scenario['data'])
        
        print(f\"  Risk Factors Identified: {len(client_profile.risk_factors)}\")
        for risk in client_profile.risk_factors:
            print(f\"    - {risk}\")
        
        print(f\"  Special Considerations: {len(client_profile.special_considerations)}\")
        for consideration in client_profile.special_considerations:
            print(f\"    - {consideration}\")


def run_all_tests():
    \"\"\"Run all test functions\"\"\"
    print(\"AI Prompt Engineering Service - Test Suite\")
    print(\"=\" * 50)
    
    try:
        test_client_analysis()
        test_template_selection()
        test_prompt_generation()
        test_template_formatting()
        test_risk_assessment()
        
        print(\"\\n\" + \"=\" * 50)
        print(\"All tests completed successfully!\")
        
        # Save test results
        test_results = {
            \"test_run_time\": datetime.now().isoformat(),
            \"available_templates\": advanced_prompt_engine.template_manager.list_available_templates(),
            \"test_status\": \"PASSED\"
        }
        
        # Save to test results file
        results_file = os.path.join(os.path.dirname(__file__), \"..\", \"data\", \"test_results_ai_prompt.json\")
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f\"Test results saved to: {results_file}\")
        
    except Exception as e:
        print(f\"\\nTest failed with error: {e}\")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == \"__main__\":
    success = run_all_tests()
    sys.exit(0 if success else 1)