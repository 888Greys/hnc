"""
Advanced AI Prompt Engineering Service for HNC Legal Questionnaire System
Provides sophisticated prompt engineering, context analysis, and response optimization
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

from services.kenya_law_service import kenya_law_db

logger = logging.getLogger(__name__)


class ClientComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class LegalArea(Enum):
    WILLS = "wills"
    TRUSTS = "trusts"
    SUCCESSION = "succession"
    MATRIMONIAL = "matrimonial"
    BUSINESS = "business"
    TAX_PLANNING = "tax_planning"
    ESTATE_PLANNING = "estate_planning"


@dataclass
class ClientProfile:
    """Comprehensive client profile for AI analysis"""
    name: str
    marital_status: str
    children: Optional[str]
    economic_standing: str
    total_assets: float
    primary_objective: str
    complexity_score: float
    risk_factors: List[str]
    legal_areas: List[LegalArea]
    special_considerations: List[str]


@dataclass
class PromptContext:
    """Context information for prompt generation"""
    client_profile: ClientProfile
    legal_references: List[Dict[str, Any]]
    tax_implications: Dict[str, Any]
    precedent_cases: List[Dict[str, Any]]
    procedures: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]


class PromptTemplateManager:
    """Manages specialized prompt templates for different scenarios"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize prompt templates for different legal scenarios"""
        
        return {
            "basic_will": """
You are a specialized legal AI assistant with expertise in Kenyan succession law and estate planning.

## CLIENT ANALYSIS
**Client Profile**: {client_name}
- **Family Structure**: {marital_status}, {children}
- **Asset Portfolio**: KES {total_assets:,} ({economic_standing})
- **Primary Objective**: {primary_objective}
- **Complexity Assessment**: {complexity_level}

## LEGAL FRAMEWORK
{legal_references}

## TAX CONTEXT
{tax_analysis}

## RISK ASSESSMENT
{risk_factors}

## EXPERT ANALYSIS REQUIRED
Provide a comprehensive legal analysis addressing:

### 1. SUCCESSION STRATEGY
- **Recommended Approach**: Detail the most appropriate succession mechanism
- **Legal Basis**: Reference specific sections of Kenyan law
- **Implementation Steps**: Concrete procedural requirements

### 2. TAX OPTIMIZATION
- **Tax Implications**: Detailed tax analysis and planning opportunities
- **Compliance Requirements**: Statutory obligations and filing requirements
- **Optimization Strategies**: Legal methods to minimize tax burden

### 3. RISK MITIGATION
- **Identified Risks**: Potential legal and family challenges
- **Preventive Measures**: Specific clauses and provisions to include
- **Contingency Planning**: Alternative scenarios and responses

### 4. PROCEDURAL GUIDANCE
- **Documentation Requirements**: Complete list of required documents
- **Legal Procedures**: Step-by-step process with timelines
- **Cost Analysis**: Expected legal and administrative costs

### 5. COMPLIANCE FRAMEWORK
- **Regulatory Requirements**: All applicable laws and regulations
- **Filing Obligations**: Court filings, registrations, and notifications
- **Ongoing Compliance**: Post-implementation requirements

**IMPORTANT**: Provide specific statutory references, practical implementation guidance, and emphasize that this constitutes informational guidance requiring professional legal review.
            """,
            
            "complex_trust": """
You are an expert legal AI specializing in Kenyan trust law, tax planning, and sophisticated estate structures.

## SOPHISTICATED CLIENT PROFILE
**High Net Worth Client**: {client_name}
- **Asset Complexity**: KES {total_assets:,} across {asset_types}
- **Family Dynamics**: {family_structure}
- **Business Interests**: {business_context}
- **Succession Objectives**: {objectives_analysis}

## ADVANCED LEGAL FRAMEWORK
{comprehensive_legal_analysis}

## MULTI-JURISDICTIONAL CONSIDERATIONS
{jurisdiction_analysis}

## SOPHISTICATED ANALYSIS REQUIRED

### 1. TRUST STRUCTURE DESIGN
- **Optimal Trust Type**: Detailed analysis of trust options under Kenyan law
- **Governance Framework**: Trustee selection, powers, and oversight mechanisms
- **Beneficiary Arrangements**: Distribution mechanisms and beneficiary protections
- **Asset Protection**: Creditor protection and asset isolation strategies

### 2. TAX ENGINEERING
- **Trust Taxation**: Comprehensive tax analysis under Income Tax Act
- **Distribution Tax**: Beneficiary tax implications and optimization
- **International Tax**: Cross-border considerations if applicable
- **Estate Duty**: Future estate planning implications

### 3. BUSINESS SUCCESSION
- **Corporate Governance**: Director succession and business continuity
- **Shareholding Structures**: Voting rights and control mechanisms
- **Succession Planning**: Multi-generational transfer strategies
- **Exit Strategies**: Liquidity events and business disposal

### 4. REGULATORY COMPLIANCE
- **Trust Registration**: Registration requirements and procedures
- **Ongoing Compliance**: Annual filings and regulatory obligations
- **Foreign Investment**: Exchange control and foreign ownership rules
- **Anti-Money Laundering**: Compliance with financial regulations

### 5. IMPLEMENTATION ROADMAP
- **Phase 1**: Initial structure and documentation (Timeline: X months)
- **Phase 2**: Asset transfer and registration (Timeline: Y months)
- **Phase 3**: Operational implementation (Timeline: Z months)
- **Phase 4**: Ongoing management and review (Annual cycle)

**CRITICAL**: Address sophisticated legal concepts while maintaining clarity for practical implementation.
            """,
            
            "matrimonial_planning": """
You are a legal AI expert in Kenyan matrimonial property law and family succession planning.

## FAMILY LAW CONTEXT
**Matrimonial Analysis**: {client_name}
- **Marriage Type**: {marriage_type} under {applicable_law}
- **Property Rights**: {property_analysis}
- **Children's Interests**: {children_analysis}
- **Succession Planning**: {succession_context}

## MATRIMONIAL LEGAL FRAMEWORK
{matrimonial_laws}

## FAMILY PROTECTION ANALYSIS

### 1. MATRIMONIAL PROPERTY RIGHTS
- **Current Rights**: Analysis under Matrimonial Property Act 2013
- **Property Classification**: Matrimonial vs. separate property
- **Contribution Assessment**: Financial and non-financial contributions
- **Protection Mechanisms**: Safeguarding spouse and children's interests

### 2. SUCCESSION PLANNING WITHIN MARRIAGE
- **Spousal Rights**: Inheritance rights under different scenarios
- **Children's Protection**: Guardianship and inheritance provisions
- **Will Planning**: Coordinated estate planning for both spouses
- **Trust Considerations**: Family trust structures and matrimonial law

### 3. RISK SCENARIOS
- **Divorce Implications**: Property division and succession impacts
- **Death During Marriage**: Succession law and matrimonial property interaction
- **Business Assets**: Treatment of business interests in matrimonial context
- **Foreign Assets**: Cross-border matrimonial and succession issues

### 4. PROTECTIVE STRATEGIES
- **Pre/Post-Nuptial Agreements**: Feasibility under Kenyan law
- **Trust Structures**: Asset protection within matrimonial framework
- **Insurance Planning**: Life insurance and family protection
- **Succession Coordination**: Harmonizing individual and joint planning

**FOCUS**: Balance individual succession objectives with matrimonial property rights and family protection.
            """,
            
            "business_succession": """
You are a corporate legal AI specialist focusing on Kenyan business law and succession planning.

## BUSINESS SUCCESSION CONTEXT
**Business Owner**: {client_name}
- **Business Structure**: {business_type}
- **Ownership Interest**: {ownership_percentage}
- **Business Value**: KES {business_value:,}
- **Succession Objectives**: {succession_goals}

## CORPORATE LEGAL FRAMEWORK
{corporate_laws}

## BUSINESS SUCCESSION STRATEGY

### 1. CORPORATE GOVERNANCE
- **Current Structure**: Analysis of existing corporate arrangements
- **Succession Mechanisms**: Director succession and shareholder transfer
- **Control Mechanisms**: Voting agreements and control retention
- **Management Transition**: Operational succession planning

### 2. VALUATION AND TRANSFER
- **Business Valuation**: Methods and tax implications
- **Transfer Mechanisms**: Share transfer, sale, or succession
- **Financing Arrangements**: Funding succession transactions
- **Tax Optimization**: Minimizing transfer taxes and CGT

### 3. STAKEHOLDER MANAGEMENT
- **Family Members**: Involving family in business succession
- **Key Employees**: Retention and incentive structures
- **External Shareholders**: Managing minority interests
- **Creditors and Banks**: Continuity assurances and guarantees

### 4. LEGAL DOCUMENTATION
- **Shareholders' Agreements**: Updated succession provisions
- **Employment Contracts**: Key person arrangements
- **Corporate Documents**: Articles of association amendments
- **Succession Agreements**: Binding succession arrangements

### 5. IMPLEMENTATION TIMELINE
- **Immediate Actions**: Urgent documentation and planning steps
- **Medium-term Planning**: 1-3 year implementation phases
- **Long-term Strategy**: 5-10 year succession roadmap
- **Contingency Planning**: Emergency succession procedures

**EMPHASIS**: Ensure business continuity while achieving personal succession objectives.
            """,
            
            "tax_optimization": """
You are a tax law AI specialist with deep expertise in Kenyan tax legislation and estate planning.

## TAX PLANNING CONTEXT
**Tax Optimization for**: {client_name}
- **Asset Base**: KES {total_assets:,}
- **Tax Position**: {current_tax_status}
- **Planning Horizon**: {planning_timeframe}
- **Objectives**: {tax_objectives}

## TAX LEGAL FRAMEWORK
{tax_legislation}

## COMPREHENSIVE TAX STRATEGY

### 1. CURRENT TAX ANALYSIS
- **Income Tax**: Current liability and optimization opportunities
- **Capital Gains Tax**: CGT exposure and mitigation strategies
- **Inheritance Tax**: Estate duty and succession tax planning
- **Stamp Duty**: Transaction taxes and exemptions

### 2. ESTATE TAX PLANNING
- **Tax-Free Threshold**: Maximizing KES 5M exemption
- **Asset Structuring**: Optimal holding structures for tax efficiency
- **Timing Strategies**: Gift timing and succession scheduling
- **Valuation Planning**: Asset valuation and tax minimization

### 3. ADVANCED STRATEGIES
- **Trust Taxation**: Tax treatment of different trust structures
- **Corporate Structures**: Using companies for tax optimization
- **Charitable Planning**: Philanthropic strategies and tax benefits
- **International Planning**: Cross-border tax considerations

### 4. COMPLIANCE MANAGEMENT
- **Filing Requirements**: Annual compliance obligations
- **Record Keeping**: Documentation and audit preparation
- **Professional Support**: When to engage tax specialists
- **Risk Management**: Avoiding tax disputes and penalties

### 5. IMPLEMENTATION SCHEDULE
- **Immediate Actions**: Urgent tax planning steps
- **Annual Planning**: Regular tax optimization reviews
- **Succession Timing**: Tax-efficient succession implementation
- **Ongoing Management**: Continuous tax optimization

**CRITICAL**: Ensure all strategies comply with current tax legislation and KRA requirements.
            """
        }
    
    def get_template(self, scenario: str) -> str:
        """Get prompt template for specific scenario"""
        return self.templates.get(scenario, self.templates["basic_will"])
    
    def list_available_templates(self) -> List[str]:
        """List available prompt templates"""
        return list(self.templates.keys())


class ClientAnalyzer:
    """Analyzes client context to determine appropriate prompt strategy"""
    
    def analyze_client_profile(self, client_data: Dict[str, Any]) -> ClientProfile:
        """Analyze client data and create comprehensive profile"""
        
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        economic_context = client_data.get('economicContext', {})
        objectives = client_data.get('objectives', {})
        
        # Calculate total assets
        total_assets = sum(
            asset.get('value', 0) 
            for asset in financial_data.get('assets', [])
        )
        
        # Determine complexity score
        complexity_score = self._calculate_complexity_score(client_data, total_assets)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(client_data, total_assets)
        
        # Determine legal areas
        legal_areas = self._determine_legal_areas(client_data)
        
        # Special considerations
        special_considerations = self._identify_special_considerations(client_data)
        
        return ClientProfile(
            name=bio_data.get('fullName', 'Unknown'),
            marital_status=bio_data.get('maritalStatus', 'Unknown'),
            children=bio_data.get('children'),
            economic_standing=economic_context.get('economicStanding', 'Unknown'),
            total_assets=total_assets,
            primary_objective=objectives.get('objective', 'Unknown'),
            complexity_score=complexity_score,
            risk_factors=risk_factors,
            legal_areas=legal_areas,
            special_considerations=special_considerations
        )
    
    def _calculate_complexity_score(self, client_data: Dict[str, Any], total_assets: float) -> float:
        """Calculate complexity score based on various factors"""
        
        score = 0.0
        
        # Asset value complexity
        if total_assets > 50000000:  # 50M+
            score += 3.0
        elif total_assets > 20000000:  # 20M+
            score += 2.0
        elif total_assets > 5000000:  # 5M+
            score += 1.0
        
        # Family complexity
        bio_data = client_data.get('bioData', {})
        if bio_data.get('maritalStatus') in ['Married', 'Divorced']:
            score += 1.0
        if bio_data.get('children'):
            score += 0.5
        
        # Asset diversity
        assets = client_data.get('financialData', {}).get('assets', [])
        asset_types = set(asset.get('type', '') for asset in assets)
        if len(asset_types) > 3:
            score += 1.0
        elif len(asset_types) > 1:
            score += 0.5
        
        # Business interests
        business_assets = [a for a in assets if 'business' in a.get('type', '').lower()]
        if business_assets:
            score += 1.5
        
        # Objective complexity
        objective = client_data.get('objectives', {}).get('objective', '').lower()
        if 'trust' in objective:
            score += 1.5
        elif 'business' in objective:
            score += 1.0
        
        return min(score, 10.0)  # Cap at 10
    
    def _identify_risk_factors(self, client_data: Dict[str, Any], total_assets: float) -> List[str]:
        """Identify potential risk factors"""
        
        risks = []
        
        # High value estate risks
        if total_assets > 5000000:
            risks.append("Estate exceeds tax-free threshold - tax planning required")
        
        # Family structure risks
        bio_data = client_data.get('bioData', {})
        if bio_data.get('maritalStatus') == 'Married' and bio_data.get('children'):
            risks.append("Complex family structure - matrimonial and succession law interaction")
        
        if bio_data.get('maritalStatus') == 'Divorced':
            risks.append("Previous marriage - potential claims and complications")
        
        # Asset concentration risks
        assets = client_data.get('financialData', {}).get('assets', [])
        if len(assets) == 1 and assets[0].get('value', 0) > total_assets * 0.8:
            risks.append("Asset concentration risk - single major asset")
        
        # Business risks
        business_assets = [a for a in assets if 'business' in a.get('type', '').lower()]
        if business_assets:
            risks.append("Business succession complexity - corporate governance required")
        
        # Liquidity risks
        liquid_assets = [a for a in assets if a.get('type', '').lower() in ['cash', 'bank account', 'investments']]
        liquid_value = sum(a.get('value', 0) for a in liquid_assets)
        if liquid_value < total_assets * 0.1:
            risks.append("Liquidity risk - limited liquid assets for tax obligations")
        
        return risks
    
    def _determine_legal_areas(self, client_data: Dict[str, Any]) -> List[LegalArea]:
        """Determine relevant legal areas"""
        
        areas = []
        
        objective = client_data.get('objectives', {}).get('objective', '').lower()
        
        if 'will' in objective:
            areas.extend([LegalArea.WILLS, LegalArea.SUCCESSION])
        
        if 'trust' in objective:
            areas.extend([LegalArea.TRUSTS, LegalArea.ESTATE_PLANNING])
        
        if 'business' in objective:
            areas.append(LegalArea.BUSINESS)
        
        bio_data = client_data.get('bioData', {})
        if bio_data.get('maritalStatus') in ['Married', 'Divorced']:
            areas.append(LegalArea.MATRIMONIAL)
        
        # Always include tax planning for significant estates
        total_assets = sum(
            asset.get('value', 0) 
            for asset in client_data.get('financialData', {}).get('assets', [])
        )
        if total_assets > 2000000:  # 2M+
            areas.append(LegalArea.TAX_PLANNING)
        
        return list(set(areas))  # Remove duplicates
    
    def _identify_special_considerations(self, client_data: Dict[str, Any]) -> List[str]:
        """Identify special considerations"""
        
        considerations = []
        
        # High net worth considerations
        total_assets = sum(
            asset.get('value', 0) 
            for asset in client_data.get('financialData', {}).get('assets', [])
        )
        
        if total_assets > 20000000:
            considerations.append("High net worth estate - consider international structures")
        
        # Business ownership
        assets = client_data.get('financialData', {}).get('assets', [])
        business_assets = [a for a in assets if 'business' in a.get('type', '').lower()]
        if business_assets:
            considerations.append("Business ownership - succession planning for business continuity")
        
        # Multiple properties
        property_assets = [a for a in assets if 'property' in a.get('type', '').lower() or 'real estate' in a.get('type', '').lower()]
        if len(property_assets) > 2:
            considerations.append("Multiple properties - consider trust structures for management")
        
        # Young children
        bio_data = client_data.get('bioData', {})
        children_info = bio_data.get('children', '').lower()
        if any(age_word in children_info for age_word in ['young', 'minor', 'child']):
            considerations.append("Minor children - guardianship and trust arrangements required")
        
        return considerations


class AdvancedPromptEngine:
    """Advanced AI prompt engineering engine"""
    
    def __init__(self):
        self.template_manager = PromptTemplateManager()
        self.client_analyzer = ClientAnalyzer()
    
    def generate_enhanced_prompt(self, client_data: Dict[str, Any], distribution_prefs: str = "") -> str:
        """Generate enhanced AI prompt based on client analysis"""
        
        # Analyze client profile
        client_profile = self.client_analyzer.analyze_client_profile(client_data)
        
        # Get relevant legal references
        legal_references = kenya_law_db.get_legal_references_for_context(client_data)
        
        # Get tax implications
        tax_implications = kenya_law_db.get_tax_implications(client_profile.total_assets)
        
        # Determine prompt template based on analysis
        template_type = self._select_optimal_template(client_profile)
        template = self.template_manager.get_template(template_type)
        
        # Build context
        context = self._build_prompt_context(client_profile, legal_references, tax_implications)
        
        # Format the prompt
        formatted_prompt = self._format_prompt(template, context, client_data, distribution_prefs)
        
        return formatted_prompt
    
    def _select_optimal_template(self, client_profile: ClientProfile) -> str:
        """Select the most appropriate prompt template"""
        
        # High complexity business scenarios
        if (client_profile.complexity_score > 6.0 and 
            LegalArea.BUSINESS in client_profile.legal_areas):
            return "business_succession"
        
        # Complex trust scenarios
        if (client_profile.complexity_score > 5.0 and 
            LegalArea.TRUSTS in client_profile.legal_areas):
            return "complex_trust"
        
        # Tax optimization focus
        if (client_profile.total_assets > 10000000 and 
            LegalArea.TAX_PLANNING in client_profile.legal_areas):
            return "tax_optimization"
        
        # Matrimonial considerations
        if (LegalArea.MATRIMONIAL in client_profile.legal_areas and 
            client_profile.marital_status in ['Married', 'Divorced']):
            return "matrimonial_planning"
        
        # Default to basic will
        return "basic_will"
    
    def _build_prompt_context(self, client_profile: ClientProfile, 
                             legal_references: List[Dict], 
                             tax_implications: Dict) -> PromptContext:
        """Build comprehensive prompt context"""
        
        # Format legal references
        formatted_refs = []
        for ref in legal_references[:7]:  # Top 7 most relevant
            formatted_ref = kenya_law_db.format_legal_reference_for_ai(ref)
            formatted_refs.append(formatted_ref)
        
        # Assess risks
        risk_assessment = {
            "complexity_level": self._get_complexity_level(client_profile.complexity_score),
            "primary_risks": client_profile.risk_factors,
            "mitigation_required": len(client_profile.risk_factors) > 2
        }
        
        return PromptContext(
            client_profile=client_profile,
            legal_references=formatted_refs,
            tax_implications=tax_implications,
            precedent_cases=[],  # Could be expanded
            procedures=[],  # Could be expanded
            risk_assessment=risk_assessment
        )
    
    def _get_complexity_level(self, score: float) -> str:
        """Convert complexity score to descriptive level"""
        if score >= 7.0:
            return "Very Complex"
        elif score >= 5.0:
            return "Complex"
        elif score >= 3.0:
            return "Moderate"
        else:
            return "Simple"
    
    def _format_prompt(self, template: str, context: PromptContext, 
                      client_data: Dict[str, Any], distribution_prefs: str) -> str:
        """Format the prompt template with context data"""
        
        # Extract data for formatting
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        assets = financial_data.get('assets', [])
        
        # Asset analysis
        asset_types = list(set(asset.get('type', '') for asset in assets))
        asset_types_str = ', '.join(asset_types) if asset_types else 'Various'
        
        # Business context
        business_assets = [a for a in assets if 'business' in a.get('type', '').lower()]
        business_context = "Multiple business interests" if len(business_assets) > 1 else "Single business" if business_assets else "No business interests"
        
        # Family structure
        children_info = bio_data.get('children', 'No children specified')
        family_structure = f"{bio_data.get('maritalStatus', 'Unknown')}, {children_info}"
        
        # Legal references formatting
        legal_refs_formatted = "\\n".join([f"• {ref}" for ref in context.legal_references])
        
        # Tax analysis formatting
        tax_analysis = f"""
**Tax Status**: {'Tax applicable' if context.tax_implications['tax_applicable'] else 'Tax-free estate'}
**Assessment**: {context.tax_implications['advice']}
**Applicable Law**: {context.tax_implications['applicable_law']}
"""
        
        # Risk factors formatting
        risk_factors_formatted = "\\n".join([f"⚠️ {risk}" for risk in context.client_profile.risk_factors])
        
        # Format the template
        try:
            formatted_prompt = template.format(
                client_name=context.client_profile.name,
                marital_status=context.client_profile.marital_status,
                children=context.client_profile.children or 'No children specified',
                total_assets=context.client_profile.total_assets,
                economic_standing=context.client_profile.economic_standing,
                primary_objective=context.client_profile.primary_objective,
                complexity_level=context.risk_assessment['complexity_level'],
                legal_references=legal_refs_formatted,
                tax_analysis=tax_analysis,
                risk_factors=risk_factors_formatted,
                asset_types=asset_types_str,
                family_structure=family_structure,
                business_context=business_context,
                objectives_analysis=client_data.get('objectives', {}).get('details', 'Standard succession planning'),
                comprehensive_legal_analysis=legal_refs_formatted,
                jurisdiction_analysis="Kenya (primary jurisdiction)",
                matrimonial_laws=legal_refs_formatted,
                marriage_type=bio_data.get('maritalStatus', 'Unknown'),
                applicable_law="Marriage Act 2014" if bio_data.get('maritalStatus') == 'Married' else 'N/A',
                property_analysis="Joint matrimonial property" if bio_data.get('maritalStatus') == 'Married' else 'Individual property',
                children_analysis=children_info,
                succession_context=context.client_profile.primary_objective,
                corporate_laws=legal_refs_formatted,
                business_type="Private company" if business_assets else 'N/A',
                ownership_percentage="Majority" if business_assets else 'N/A',
                business_value=sum(a.get('value', 0) for a in business_assets),
                succession_goals=context.client_profile.primary_objective,
                tax_legislation=legal_refs_formatted,
                current_tax_status="Under review",
                planning_timeframe="5-10 years",
                tax_objectives="Tax optimization and compliance"
            )
        except KeyError as e:
            logger.warning(f"Template formatting error: {e}. Using fallback.")
            formatted_prompt = self._get_fallback_prompt(context, client_data, distribution_prefs)
        
        return formatted_prompt
    
    def _get_fallback_prompt(self, context: PromptContext, 
                           client_data: Dict[str, Any], distribution_prefs: str) -> str:
        """Generate fallback prompt if template formatting fails"""
        
        legal_refs_formatted = "\\n".join([f"• {ref}" for ref in context.legal_references])
        
        return f"""
You are a specialized legal AI assistant with expertise in Kenyan law and estate planning.

**CLIENT**: {context.client_profile.name}
**ASSETS**: KES {context.client_profile.total_assets:,}
**OBJECTIVE**: {context.client_profile.primary_objective}
**COMPLEXITY**: {context.risk_assessment['complexity_level']}

**RELEVANT KENYAN LAWS**:
{legal_refs_formatted}

**TAX IMPLICATIONS**:
{context.tax_implications['advice']}

**ANALYSIS REQUIRED**:
1. Provide comprehensive legal recommendations for achieving the client's objectives
2. Address all relevant Kenyan law requirements and procedures
3. Identify potential risks and mitigation strategies
4. Provide specific next steps with legal references
5. Consider tax implications and optimization opportunities

**IMPORTANT**: Provide informational guidance only, emphasizing the need for professional legal consultation.
        """


# Global instance
advanced_prompt_engine = AdvancedPromptEngine()