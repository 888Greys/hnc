#!/usr/bin/env python3
"""
AI Service for HNC Legal Questionnaire System
Handles AI integration, proposal generation, and legal analysis
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Cerebras SDK
try:
    from cerebras.cloud.sdk import Cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    logger.warning("Cerebras SDK not available. Using mock responses.")
    Cerebras = None
    CEREBRAS_AVAILABLE = False


class AIService:
    """Service for AI-powered legal analysis and proposal generation"""
    
    def __init__(self):
        self.api_key = os.environ.get("CEREBRAS_API_KEY")
        self.client = None
        
        if CEREBRAS_AVAILABLE and self.api_key:
            try:
                self.client = Cerebras(api_key=self.api_key)
                logger.info("Cerebras AI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Cerebras client: {e}")
                self.client = None
        else:
            logger.info("AI service running in mock mode")
    
    def generate_ai_proposal(self, client_data: Dict[str, Any], distribution_prefs: str = "") -> Dict[str, Any]:
        """Generate AI-powered legal proposal"""
        try:
            # Build prompt from client data
            prompt = self.build_ai_prompt(client_data, distribution_prefs)
            
            if self.client:
                # Use real AI service
                response = self._call_cerebras_api(prompt)
                return {
                    "success": True,
                    "suggestion": response,
                    "legalReferences": self._extract_legal_references(response),
                    "consequences": self._extract_consequences(response),
                    "nextSteps": self._extract_next_steps(response),
                    "source": "cerebras_ai",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Use mock response
                return self._generate_mock_proposal(client_data, distribution_prefs)
                
        except Exception as e:
            logger.error(f"Failed to generate AI proposal: {e}")
            return {
                "success": False,
                "error": str(e),
                "suggestion": "AI analysis unavailable. Please consult with a legal professional.",
                "timestamp": datetime.now().isoformat()
            }
    
    def build_ai_prompt(self, client_data: Dict[str, Any], distribution_prefs: str) -> str:
        """Build AI prompt from client data"""
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        objectives = client_data.get('objectives', {})
        economic_context = client_data.get('economicContext', {})
        
        # Calculate total assets
        assets = financial_data.get('assets', [])
        total_assets = sum(asset.get('value', 0) for asset in assets)
        
        prompt = f"""
Based on Kenya Law, particularly the Succession Act Cap 160, analyze the following client situation and provide legal recommendations:

CLIENT INFORMATION:
- Name: {bio_data.get('fullName', 'Not specified')}
- Marital Status: {bio_data.get('maritalStatus', 'Not specified')}
- Children: {bio_data.get('children', 'Not specified')}
- Economic Standing: {economic_context.get('economicStanding', 'Not specified')}

FINANCIAL OVERVIEW:
- Total Assets: KES {total_assets:,.0f}
- Asset Types: {', '.join([asset.get('type', 'Unknown') for asset in assets])}
- Liabilities: {financial_data.get('liabilities', 'Not specified')}

PRIMARY OBJECTIVE: {objectives.get('objective', 'Not specified')}
OBJECTIVE DETAILS: {objectives.get('details', 'Not specified')}
DISTRIBUTION PREFERENCES: {distribution_prefs or 'Not specified'}

Please provide:
1. Legal recommendations specific to Kenyan law
2. Potential consequences and tax implications
3. Risk factors to consider
4. Next steps for implementation
5. Relevant statutory references

Keep recommendations practical, legally sound, and specific to the Kenyan legal framework.
Do not provide direct legal advice - only informational guidance.
"""
        
        return prompt.strip()
    
    def _call_cerebras_api(self, prompt: str) -> str:
        """Call Cerebras API for AI response"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-oss-120b",
                max_tokens=500,
                temperature=0.7,
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Cerebras API call failed: {e}")
            raise
    
    def _generate_mock_proposal(self, client_data: Dict[str, Any], distribution_prefs: str) -> Dict[str, Any]:
        """Generate mock AI proposal when real AI is unavailable"""
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        objectives = client_data.get('objectives', {})
        
        # Calculate total assets
        assets = financial_data.get('assets', [])
        total_assets = sum(asset.get('value', 0) for asset in assets)
        
        objective = objectives.get('objective', 'General legal planning')
        
        mock_suggestions = {
            "Create Will": f"""
Based on Kenya Law (Succession Act Cap 160), for will creation with assets worth KES {total_assets:,.0f}:

RECOMMENDATIONS:
1. Will Creation: Essential for proper asset distribution
2. Executor Appointment: Designate a reliable executor
3. Beneficiary Designation: Clear identification of heirs
4. Asset Distribution: Follow specified preferences

TAX IMPLICATIONS:
- Estates above KES 5M may attract inheritance tax
- Property transfers require stamp duty
- Consider tax-efficient distribution strategies

NEXT STEPS:
1. Draft comprehensive will document
2. Obtain legal witness signatures
3. Register with relevant authorities
4. Regular review and updates
""",
            "Create Trust": f"""
Based on Kenya Law, for trust creation with assets worth KES {total_assets:,.0f}:

RECOMMENDATIONS:
1. Family Trust Structure: Suitable for asset protection
2. Trustee Selection: Choose experienced trustees
3. Beneficiary Rights: Define clear terms
4. Tax Planning: Consider trust tax implications

LEGAL FRAMEWORK:
- Trustee Act Cap 167
- Income Tax Act provisions
- Property transfer requirements

NEXT STEPS:
1. Draft trust deed
2. Transfer assets to trust
3. Register trust entity
4. Establish governance structure
""",
            "default": f"""
Based on Kenya Law analysis for {objective} with assets worth KES {total_assets:,.0f}:

GENERAL RECOMMENDATIONS:
1. Legal Documentation: Ensure proper documentation
2. Compliance: Meet regulatory requirements
3. Tax Planning: Consider tax implications
4. Professional Advice: Consult qualified legal counsel

LEGAL REFERENCES:
- Succession Act Cap 160
- Land Act 2012
- Income Tax Act

NEXT STEPS:
1. Detailed legal consultation
2. Document preparation
3. Regulatory compliance
4. Implementation planning
"""
        }
        
        suggestion = mock_suggestions.get(objective, mock_suggestions["default"])
        
        return {
            "success": True,
            "suggestion": suggestion.strip(),
            "legalReferences": [
                "Succession Act Cap 160",
                "Income Tax Act",
                "Land Act 2012",
                "Trustee Act Cap 167"
            ],
            "consequences": [
                "Tax implications for high-value estates",
                "Probate requirements for will execution",
                "Stamp duty on property transfers",
                "Compliance with statutory timelines"
            ],
            "nextSteps": [
                "Consult with qualified legal counsel",
                "Prepare necessary legal documents",
                "Complete regulatory filings",
                "Implement recommended structures"
            ],
            "source": "mock_ai",
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_legal_references(self, ai_response: str) -> List[str]:
        """Extract legal references from AI response"""
        references = []
        common_acts = [
            "Succession Act Cap 160",
            "Income Tax Act",
            "Land Act 2012",
            "Trustee Act Cap 167",
            "Companies Act 2015",
            "Marriage Act 2014"
        ]
        
        for act in common_acts:
            if act.lower() in ai_response.lower():
                references.append(act)
        
        return references or ["Succession Act Cap 160"]  # Default reference
    
    def _extract_consequences(self, ai_response: str) -> List[str]:
        """Extract consequences from AI response"""
        consequences = []
        
        # Look for common consequence indicators
        if "tax" in ai_response.lower():
            consequences.append("Tax implications may apply")
        if "probate" in ai_response.lower():
            consequences.append("Probate process required")
        if "stamp duty" in ai_response.lower():
            consequences.append("Stamp duty charges applicable")
        if "compliance" in ai_response.lower():
            consequences.append("Regulatory compliance required")
        
        return consequences or ["General legal implications apply"]
    
    def _extract_next_steps(self, ai_response: str) -> List[str]:
        """Extract next steps from AI response"""
        steps = []
        
        # Look for action items
        if "draft" in ai_response.lower():
            steps.append("Draft legal documents")
        if "consult" in ai_response.lower():
            steps.append("Consult legal professional")
        if "register" in ai_response.lower():
            steps.append("Complete registration process")
        if "review" in ai_response.lower():
            steps.append("Regular review and updates")
        
        return steps or ["Seek professional legal advice"]
    
    def analyze_client_complexity(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze client case complexity"""
        try:
            bio_data = client_data.get('bioData', {})
            financial_data = client_data.get('financialData', {})
            
            complexity_score = 0
            risk_factors = []
            
            # Asset complexity
            assets = financial_data.get('assets', [])
            total_assets = sum(asset.get('value', 0) for asset in assets)
            
            if total_assets > 10000000:  # 10M KES
                complexity_score += 3
                risk_factors.append("High net worth estate")
            elif total_assets > 5000000:  # 5M KES
                complexity_score += 2
                risk_factors.append("Significant asset value")
            
            # Marital complexity
            if bio_data.get('maritalStatus') == 'Married':
                complexity_score += 1
                if bio_data.get('children'):
                    complexity_score += 1
                    risk_factors.append("Multiple beneficiaries")
            
            # Asset type complexity
            asset_types = set(asset.get('type', '') for asset in assets)
            if len(asset_types) > 3:
                complexity_score += 2
                risk_factors.append("Diverse asset portfolio")
            
            if 'Business' in asset_types:
                complexity_score += 2
                risk_factors.append("Business assets involved")
            
            complexity_level = "Low"
            if complexity_score >= 6:
                complexity_level = "High"
            elif complexity_score >= 3:
                complexity_level = "Medium"
            
            return {
                "complexity_score": complexity_score,
                "complexity_level": complexity_level,
                "risk_factors": risk_factors,
                "total_assets": total_assets,
                "recommendations": self._get_complexity_recommendations(complexity_level)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze client complexity: {e}")
            return {
                "complexity_score": 0,
                "complexity_level": "Unknown",
                "error": str(e)
            }
    
    def _get_complexity_recommendations(self, complexity_level: str) -> List[str]:
        """Get recommendations based on complexity level"""
        recommendations = {
            "Low": [
                "Standard will creation",
                "Basic legal documentation",
                "Standard tax planning"
            ],
            "Medium": [
                "Comprehensive estate planning",
                "Tax optimization strategies",
                "Professional legal review"
            ],
            "High": [
                "Advanced estate structures",
                "Trust arrangements",
                "Specialized tax planning",
                "Multiple legal consultations"
            ]
        }
        
        return recommendations.get(complexity_level, ["Seek professional advice"])


# Global AI service instance
ai_service = AIService()


# Convenience functions for backwards compatibility
def generate_ai_proposal(client_data: dict, distribution_prefs: str = "") -> dict:
    """Generate AI proposal (backwards compatible)"""
    return ai_service.generate_ai_proposal(client_data, distribution_prefs)


def build_ai_prompt(client_data: dict, distribution_prefs: str) -> str:
    """Build AI prompt (backwards compatible)"""
    return ai_service.build_ai_prompt(client_data, distribution_prefs)