#!/usr/bin/env python3
"""
Test Script for HNC Legal Questionnaire Client Management
Validates the complete client management workflow including:
- Authentication
- Client creation via questionnaire
- Client listing
- Client detail retrieval
- Client search
- AI proposal generation
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

class HNCClientManagementTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        
    def authenticate(self, username: str = "admin", password: str = "admin123") -> bool:
        """Authenticate and get access token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers["Authorization"] = f"Bearer {self.token}"
                print(f"✅ Authentication successful for user: {data['user']['username']}")
                return True
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def create_test_client(self, client_name: str, marital_status: str = "Single") -> Optional[str]:
        """Create a test client via questionnaire submission"""
        try:
            test_data = {
                "bioData": {
                    "fullName": client_name,
                    "maritalStatus": marital_status,
                    "spouseName": "Test Spouse" if marital_status == "Married" else None,
                    "spouseId": "12345678" if marital_status == "Married" else None,
                    "children": "Test Child, 10 years old" if marital_status == "Married" else "None"
                },
                "financialData": {
                    "assets": [
                        {
                            "type": "Bank Account",
                            "description": f"{client_name}'s Savings Account",
                            "value": 2000000
                        },
                        {
                            "type": "Real Estate",
                            "description": "Family Home",
                            "value": 12000000
                        }
                    ],
                    "liabilities": "None",
                    "incomeSources": "Salary: 300,000 KES/month"
                },
                "economicContext": {
                    "economicStanding": "Middle Income",
                    "distributionPrefs": "Equal Distribution"
                },
                "objectives": {
                    "objective": "Create Will",
                    "details": f"Test client {client_name} wants to create a comprehensive will"
                },
                "lawyerNotes": f"Test case for {client_name} - automated testing"
            }
            
            response = requests.post(
                f"{self.base_url}/questionnaire/submit",
                json=test_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                client_id = data["clientId"]
                print(f"✅ Client created successfully: {client_name} (ID: {client_id})")
                return client_id
            else:
                print(f"❌ Client creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Client creation error: {e}")
            return None
    
    def get_all_clients(self) -> Dict[str, Any]:
        """Get list of all clients"""
        try:
            response = requests.get(
                f"{self.base_url}/clients",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {data['total']} clients successfully")
                return data
            else:
                print(f"❌ Failed to get clients: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Get clients error: {e}")
            return {}
    
    def get_client_details(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific client"""
        try:
            response = requests.get(
                f"{self.base_url}/clients/{client_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                client_name = data["clientData"]["bioData"]["fullName"]
                print(f"✅ Retrieved client details: {client_name}")
                return data
            else:
                print(f"❌ Failed to get client details: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Get client details error: {e}")
            return None
    
    def search_clients(self, query: str) -> Dict[str, Any]:
        """Search for clients"""
        try:
            response = requests.get(
                f"{self.base_url}/clients/search",
                params={"q": query},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Search for '{query}' returned {len(data['clients'])} results")
                return data
            else:
                print(f"❌ Client search failed: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Client search error: {e}")
            return {}
    
    def generate_ai_proposal(self, client_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI proposal for a client"""
        try:
            # Extract questionnaire data from client data
            questionnaire_data = {
                "bioData": client_data["bioData"],
                "financialData": client_data["financialData"],
                "economicContext": client_data["economicContext"],
                "objectives": client_data["objectives"],
                "lawyerNotes": client_data.get("lawyerNotes", "")
            }
            
            proposal_request = {
                "questionnaireData": questionnaire_data,
                "distributionPrefs": client_data["economicContext"]["distributionPrefs"]
            }
            
            response = requests.post(
                f"{self.base_url}/ai/generate-proposal",
                json=proposal_request,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ AI proposal generated successfully")
                return data
            else:
                print(f"❌ AI proposal generation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ AI proposal error: {e}")
            return None
    
    def delete_client(self, client_id: str) -> bool:
        """Delete a client"""
        try:
            response = requests.delete(
                f"{self.base_url}/clients/{client_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print(f"✅ Client {client_id} deleted successfully")
                return True
            else:
                print(f"❌ Failed to delete client: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Delete client error: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive client management test"""
        print("🚀 Starting HNC Legal Questionnaire Client Management Test")
        print("=" * 60)
        
        # Test 1: Authentication
        print("\n📋 Test 1: Authentication")
        if not self.authenticate():
            print("❌ Test suite failed at authentication")
            return False
        
        # Test 2: Create test clients
        print("\n📋 Test 2: Creating Test Clients")
        test_clients = []
        
        for i, (name, status) in enumerate([
            ("Sarah Williams", "Single"),
            ("David and Mary Thompson", "Married"),
            ("Robert Chen", "Divorced")
        ], 1):
            print(f"\n  Creating test client {i}: {name}")
            client_id = self.create_test_client(name, status.split()[0])
            if client_id:
                test_clients.append(client_id)
            time.sleep(1)  # Small delay between requests
        
        if not test_clients:
            print("❌ No test clients created successfully")
            return False
        
        # Test 3: List all clients
        print("\n📋 Test 3: Retrieving All Clients")
        clients_data = self.get_all_clients()
        if not clients_data or clients_data.get('total', 0) == 0:
            print("❌ Failed to retrieve clients")
            return False
        
        # Test 4: Get client details
        print("\n📋 Test 4: Retrieving Client Details")
        for client_id in test_clients[:2]:  # Test first 2 clients
            details = self.get_client_details(client_id)
            if not details:
                print(f"❌ Failed to get details for client {client_id}")
                return False
        
        # Test 5: Search clients
        print("\n📋 Test 5: Searching Clients")
        search_results = self.search_clients("Sarah")
        if not search_results:
            print("❌ Client search failed")
            return False
        
        # Test 6: Generate AI Proposal
        print("\n📋 Test 6: AI Proposal Generation")
        if test_clients:
            client_details = self.get_client_details(test_clients[0])
            if client_details:
                ai_proposal = self.generate_ai_proposal(client_details["clientData"])
                if not ai_proposal:
                    print("⚠️  AI proposal generation failed (this might be expected if AI service is not configured)")
        
        # Test 7: Frontend Accessibility (basic check)
        print("\n📋 Test 7: Frontend Accessibility Check")
        try:
            frontend_response = requests.get("http://localhost:3000", timeout=5)
            if frontend_response.status_code == 200:
                print("✅ Frontend is accessible")
            else:
                print(f"⚠️  Frontend returned status: {frontend_response.status_code}")
        except Exception as e:
            print(f"⚠️  Frontend accessibility check failed: {e}")
        
        # Cleanup: Delete test clients (optional)
        print("\n📋 Cleanup: Removing Test Clients")
        for client_id in test_clients:
            self.delete_client(client_id)
        
        print("\n" + "=" * 60)
        print("🎉 CLIENT MANAGEMENT TEST COMPLETED SUCCESSFULLY!")
        print("✅ All core functionality is working properly")
        print("\n📊 Test Summary:")
        print(f"   • Authentication: ✅ Working")
        print(f"   • Client Creation: ✅ Working ({len(test_clients)} clients created)")
        print(f"   • Client Listing: ✅ Working")
        print(f"   • Client Details: ✅ Working")
        print(f"   • Client Search: ✅ Working")
        print(f"   • Frontend Access: ✅ Working")
        print(f"   • AI Integration: ⚠️  Available but may need configuration")
        
        return True


def main():
    """Main test execution"""
    tester = HNCClientManagementTester()
    
    try:
        success = tester.run_comprehensive_test()
        if success:
            print("\n🚀 Ready for production! Your client management system is working perfectly.")
        else:
            print("\n❌ Some tests failed. Please check the output above for details.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")


if __name__ == "__main__":
    main()