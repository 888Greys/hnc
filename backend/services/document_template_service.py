"""
Document Template Service for HNC Legal Questionnaire System
Provides comprehensive document generation for various legal document types
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, date
from pathlib import Path
import logging

try:
    from jinja2 import Environment, FileSystemLoader, Template
    from jinja2.exceptions import TemplateError
    JINJA2_AVAILABLE = True
except ImportError:
    # Fallback for basic template functionality
    JINJA2_AVAILABLE = False
    Environment = None
    FileSystemLoader = None
    Template = None
    TemplateError = Exception

from services.kenya_law_service import kenya_law_db
from services.ai_prompt_service import advanced_prompt_engine

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    WILL = "will"
    TRUST_DEED = "trust_deed"
    POWER_OF_ATTORNEY = "power_of_attorney"
    LEGAL_OPINION = "legal_opinion"
    ASSET_DECLARATION = "asset_declaration"
    SUCCESSION_CERTIFICATE = "succession_certificate"
    MARRIAGE_CONTRACT = "marriage_contract"
    BUSINESS_SUCCESSION_PLAN = "business_succession_plan"


class DocumentFormat(Enum):
    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"
    TXT = "txt"


@dataclass
class DocumentMetadata:
    """Metadata for generated documents"""
    document_id: str
    document_type: DocumentType
    client_name: str
    created_at: datetime
    created_by: str
    version: str
    template_version: str
    legal_references: List[str]
    ai_generated: bool
    review_status: str  # "draft", "reviewed", "approved"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'document_type': self.document_type.value,
            'created_at': self.created_at.isoformat()
        }


class DocumentTemplateManager:
    """Manages legal document templates and generation"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment if available
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            self.jinja_env = None
            logger.warning("Jinja2 not available, using basic template functionality")
        
        # Document storage
        self.documents_dir = Path("generated_documents")
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize templates
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize legal document templates"""
        
        # Create template files if they don't exist
        templates = {
            DocumentType.WILL: self._get_will_template(),
            DocumentType.TRUST_DEED: self._get_trust_deed_template(),
            DocumentType.POWER_OF_ATTORNEY: self._get_power_of_attorney_template(),
            DocumentType.LEGAL_OPINION: self._get_legal_opinion_template(),
            DocumentType.ASSET_DECLARATION: self._get_asset_declaration_template(),
            DocumentType.SUCCESSION_CERTIFICATE: self._get_succession_certificate_template(),
            DocumentType.MARRIAGE_CONTRACT: self._get_marriage_contract_template(),
            DocumentType.BUSINESS_SUCCESSION_PLAN: self._get_business_succession_plan_template()
        }
        
        for doc_type, template_content in templates.items():
            template_file = self.templates_dir / f"{doc_type.value}.jinja2"
            if not template_file.exists():
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(template_content)
                logger.info(f"Created template file: {template_file}")
    
    def _get_will_template(self) -> str:
        """Get will document template"""
        return '''
# LAST WILL AND TESTAMENT

**IN THE MATTER OF THE ESTATE OF {{ client_name|upper }}**

---

## PERSONAL DETAILS

I, **{{ client_name }}**, of {{ client_address }}, being of sound mind and disposing memory, do hereby make, publish and declare this to be my Last Will and Testament, hereby revoking all former wills and codicils by me at any time heretofore made.

**Date of Birth:** {{ date_of_birth }}  
**ID/Passport Number:** {{ id_number }}  
**Marital Status:** {{ marital_status }}

---

## APPOINTMENT OF EXECUTOR

I hereby nominate and appoint **{{ executor_name }}** of {{ executor_address }} to be the Executor of this my Will, and in the event of their death, incapacity, or inability to act, I appoint **{{ alternate_executor }}** as alternate Executor.

I direct that no bond or other security shall be required of any Executor appointed hereunder.

---

## REVOCATION OF PREVIOUS WILLS

I hereby revoke all wills, codicils, and other testamentary dispositions heretofore made by me.

---

## DEBTS AND FUNERAL EXPENSES

I direct my Executor to pay all my just debts, funeral expenses, and the expenses of administering my estate as soon as practicable after my death.

---

## SPECIFIC BEQUESTS

{% if specific_bequests %}
### Specific Gifts and Bequests

{% for bequest in specific_bequests %}
**{{ loop.index }}.** I give and bequeath {{ bequest.description }} to {{ bequest.beneficiary }}.
{% if bequest.condition %}
*Condition:* {{ bequest.condition }}
{% endif %}

{% endfor %}
{% endif %}

---

## DISPOSITION OF RESIDUARY ESTATE

{% if residuary_disposition %}
### Distribution of Remaining Estate

After payment of all debts, expenses, and specific bequests above, I give, devise, and bequeath the rest, residue, and remainder of my estate as follows:

{% for disposition in residuary_disposition %}
**{{ loop.index }}.** {{ disposition.percentage }}% to {{ disposition.beneficiary }}
{% if disposition.description %}
   *{{ disposition.description }}*
{% endif %}

{% endfor %}
{% endif %}

---

## GUARDIANSHIP OF MINOR CHILDREN

{% if minor_children %}
In the event that I die while any of my children are minors, I nominate and appoint **{{ guardian_name }}** as Guardian of the person and property of such minor children. In the event of their inability to serve, I nominate **{{ alternate_guardian }}** as alternate Guardian.
{% endif %}

---

## TRUST PROVISIONS

{% if trust_provisions %}
### Trust for Minor Beneficiaries

Any bequest to a beneficiary who is under the age of {{ trust_age|default(18) }} years at the time of my death shall be held in trust by my Executor until such beneficiary attains the age of {{ trust_age|default(18) }} years.

The Trustee shall have the discretionary power to apply the whole or any part of the income and capital of the trust fund for the maintenance, education, advancement, or benefit of the beneficiary.
{% endif %}

---

## GENERAL POWERS

I grant to my Executor full power and authority to:

1. Sell, mortgage, lease, or otherwise dispose of any part of my estate
2. Invest and reinvest estate funds in any form of investment
3. Carry on any business that forms part of my estate
4. Settle any claims against my estate
5. Exercise all powers necessary for the proper administration of my estate

---

## LEGAL REFERENCES

This Will is made in accordance with the following Kenyan laws:

{% for reference in legal_references %}
- {{ reference }}
{% endfor %}

---

## EXECUTION

IN WITNESS WHEREOF, I have hereunto set my hand this {{ execution_date }} day of {{ execution_month }}, {{ execution_year }}.

**SIGNED:** _______________________________  
{{ client_name|upper }} (Testator)

**WITNESSES:**

We, the undersigned, do hereby certify that the above-named Testator signed this Will in our presence, and we, at their request and in their presence, and in the presence of each other, have signed our names as witnesses.

**Witness 1:**  
Name: _______________________________  
Signature: _______________________________  
Address: _______________________________  
Date: _______________________________

**Witness 2:**  
Name: _______________________________  
Signature: _______________________________  
Address: _______________________________  
Date: _______________________________

---

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Legal Review Required:** Yes

*This document is generated for informational purposes and requires professional legal review before execution.*
        '''
    
    def _get_trust_deed_template(self) -> str:
        """Get trust deed template"""
        return '''
# TRUST DEED

**{{ trust_name|upper }}**

---

## PARTIES

**SETTLOR:** {{ settlor_name }} of {{ settlor_address }}

**TRUSTEE(S):** 
{% for trustee in trustees %}
- {{ trustee.name }} of {{ trustee.address }}
{% endfor %}

**BENEFICIARIES:** 
{% for beneficiary in beneficiaries %}
- {{ beneficiary.name }} ({{ beneficiary.relationship }})
{% endfor %}

---

## TRUST CREATION

This Trust Deed is made this {{ execution_date }} day of {{ execution_month }}, {{ execution_year }}, between the Settlor and the Trustee(s) named above.

## TRUST PROPERTY

The Settlor hereby transfers to the Trustee(s) the following property to be held in trust:

{% for asset in trust_assets %}
**{{ loop.index }}.** {{ asset.description }}
   - Type: {{ asset.type }}
   - Value: KES {{ asset.value|number_format }}
   {% if asset.location %}
   - Location: {{ asset.location }}
   {% endif %}

{% endfor %}

**Total Trust Value:** KES {{ total_trust_value|number_format }}

---

## TRUST PURPOSES

This Trust is established for the following purposes:

{% for purpose in trust_purposes %}
{{ loop.index }}. {{ purpose }}
{% endfor %}

---

## POWERS OF TRUSTEES

The Trustees shall have the following powers:

1. **Investment Powers:** To invest trust funds in any form of investment deemed appropriate
2. **Management Powers:** To manage, maintain, and preserve trust property
3. **Distribution Powers:** To distribute income and capital to beneficiaries according to this deed
4. **Sale Powers:** To sell, mortgage, or dispose of trust property when necessary
5. **Professional Advice:** To engage professional advisors including lawyers, accountants, and investment managers

---

## DISTRIBUTION PROVISIONS

### Income Distribution
{% if income_distribution %}
{{ income_distribution }}
{% else %}
Income shall be distributed annually among beneficiaries in equal shares unless otherwise directed by the Trustees.
{% endif %}

### Capital Distribution
{% if capital_distribution %}
{{ capital_distribution }}
{% else %}
Capital may be distributed at the discretion of the Trustees for the benefit, advancement, or maintenance of beneficiaries.
{% endif %}

---

## TRUSTEE DUTIES

The Trustees shall:

1. Act in the best interests of the beneficiaries
2. Exercise reasonable care and skill in managing trust property
3. Keep proper accounts and records
4. Provide annual statements to beneficiaries
5. Act impartially between beneficiaries
6. Not profit from their position without proper authorization

---

## LEGAL COMPLIANCE

This Trust is established in accordance with:

{% for reference in legal_references %}
- {{ reference }}
{% endfor %}

---

## EXECUTION

IN WITNESS WHEREOF the parties have executed this Trust Deed on the date first written above.

**SETTLOR:**  
Signed: _______________________________  
{{ settlor_name }}

**TRUSTEES:**  
{% for trustee in trustees %}
Signed: _______________________________  
{{ trustee.name }}

{% endfor %}

**WITNESSES:**  
Signed: _______________________________  
Witness 1

Signed: _______________________________  
Witness 2

---

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Legal Review Required:** Yes

*This document requires professional legal review and proper registration.*
        '''
    
    def _get_power_of_attorney_template(self) -> str:
        """Get power of attorney template"""
        return '''
# POWER OF ATTORNEY

---

## PRINCIPAL

I, **{{ principal_name }}** of {{ principal_address }}, being of sound mind, do hereby make, constitute and appoint {{ attorney_name }} of {{ attorney_address }} as my true and lawful Attorney-in-Fact.

**Principal ID:** {{ principal_id }}  
**Date of Birth:** {{ principal_dob }}

---

## ATTORNEY-IN-FACT

**Name:** {{ attorney_name }}  
**Address:** {{ attorney_address }}  
**ID Number:** {{ attorney_id }}  
**Relationship:** {{ attorney_relationship }}

---

## SCOPE OF AUTHORITY

{% if power_type == "general" %}
I hereby grant to my Attorney-in-Fact full power and authority to act on my behalf in all matters, including but not limited to:

1. **Financial Matters:** Banking, investments, tax matters, and financial transactions
2. **Property Matters:** Real estate transactions, property management, and rentals
3. **Legal Matters:** Signing contracts, legal documents, and representing me in legal proceedings
4. **Business Matters:** Operating business interests and making business decisions
5. **Government Matters:** Dealing with government agencies and departments

{% elif power_type == "specific" %}
I hereby grant to my Attorney-in-Fact the following specific powers:

{% for power in specific_powers %}
{{ loop.index }}. {{ power }}
{% endfor %}

{% elif power_type == "limited" %}
This Power of Attorney is limited to the following matters:

{% for limitation in limitations %}
{{ loop.index }}. {{ limitation }}
{% endfor %}

**Duration:** {{ duration }}
{% endif %}

---

## LIMITATIONS AND RESTRICTIONS

{% if restrictions %}
The following limitations apply to this Power of Attorney:

{% for restriction in restrictions %}
- {{ restriction }}
{% endfor %}
{% endif %}

My Attorney-in-Fact shall NOT have the power to:
1. Make or change a will
2. Make gifts exceeding KES {{ gift_limit|default(100000) }} per year
3. Create or change beneficiary designations
4. Delegate this authority to another person

---

## EFFECTIVE PERIOD

{% if effective_type == "immediate" %}
This Power of Attorney shall be effective immediately upon execution and shall remain in effect until revoked.

{% elif effective_type == "springing" %}
This Power of Attorney shall become effective only upon my incapacity as certified by {{ incapacity_certifier|default("a licensed physician") }}.

{% elif effective_type == "limited_time" %}
This Power of Attorney shall be effective from {{ start_date }} to {{ end_date }}.
{% endif %}

---

## REVOCATION

I reserve the right to revoke this Power of Attorney at any time by providing written notice to my Attorney-in-Fact and any third parties who may be relying on this document.

---

## INDEMNIFICATION

I agree to indemnify and hold harmless my Attorney-in-Fact from any claims, damages, or expenses arising from their good faith exercise of the powers granted herein.

---

## LEGAL COMPLIANCE

This Power of Attorney is executed in accordance with Kenyan law, specifically:

{% for reference in legal_references %}
- {{ reference }}
{% endfor %}

---

## EXECUTION

IN WITNESS WHEREOF, I have executed this Power of Attorney this {{ execution_date }} day of {{ execution_month }}, {{ execution_year }}.

**PRINCIPAL:**  
Signed: _______________________________  
{{ principal_name }}

**ATTORNEY-IN-FACT ACCEPTANCE:**  
I accept the appointment as Attorney-in-Fact and agree to act in the best interests of the Principal.

Signed: _______________________________  
{{ attorney_name }}

**WITNESSES:**  
Signed: _______________________________  
Witness 1: {{ witness1_name }}

Signed: _______________________________  
Witness 2: {{ witness2_name }}

**NOTARIZATION:**  
Sworn to and subscribed before me this {{ execution_date }} day of {{ execution_month }}, {{ execution_year }}.

_______________________________  
Notary Public

---

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Legal Review Required:** Yes

*This document requires notarization and professional legal review.*
        '''
    
    def _get_legal_opinion_template(self) -> str:
        """Get legal opinion template"""
        return '''
# LEGAL OPINION

**{{ law_firm_name }}**  
{{ law_firm_address }}

---

## CLIENT INFORMATION

**Client:** {{ client_name }}  
**Matter:** {{ matter_description }}  
**Date:** {{ opinion_date }}  
**Reference:** {{ reference_number }}

---

## EXECUTIVE SUMMARY

{{ executive_summary }}

---

## FACTUAL BACKGROUND

{{ factual_background }}

---

## LEGAL ANALYSIS

### Applicable Law

The following Kenyan laws are relevant to this matter:

{% for law in applicable_laws %}
#### {{ law.title }}
{{ law.description }}

**Relevant Provisions:**
{% for provision in law.provisions %}
- {{ provision }}
{% endfor %}

{% endfor %}

### Legal Assessment

{{ legal_assessment }}

---

## RECOMMENDATIONS

Based on our analysis, we recommend the following:

{% for recommendation in recommendations %}
### {{ loop.index }}. {{ recommendation.title }}

{{ recommendation.description }}

**Priority:** {{ recommendation.priority }}  
**Timeline:** {{ recommendation.timeline }}  
**Estimated Cost:** {{ recommendation.cost }}

{% endfor %}

---

## RISK ANALYSIS

{% for risk in risks %}
### {{ risk.category }} Risk: {{ risk.level }}

**Description:** {{ risk.description }}  
**Mitigation:** {{ risk.mitigation }}

{% endfor %}

---

## CONCLUSION

{{ conclusion }}

---

## DISCLAIMERS

1. This opinion is based on current Kenyan law as of {{ opinion_date }}
2. This opinion is specific to the facts presented and may not apply to different circumstances
3. Legal developments may affect the validity of this opinion
4. This opinion does not constitute a guarantee of outcome
5. Professional legal representation is recommended for implementation

---

**Prepared by:** {{ lawyer_name }}  
**Admitted Advocate:** {{ admission_number }}  
**Law Society of Kenya Member**

**Signature:** _______________________________  
**Date:** {{ opinion_date }}

---

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Legal Review Status:** {{ review_status }}
        '''
    
    def _get_asset_declaration_template(self) -> str:
        """Get asset declaration template"""
        return '''
# COMPREHENSIVE ASSET DECLARATION

**Declaration by:** {{ declarant_name }}  
**Date:** {{ declaration_date }}  
**ID/Passport:** {{ declarant_id }}

---

## DECLARATION STATEMENT

I, {{ declarant_name }}, do hereby solemnly declare that the following is a true and complete statement of all my assets and liabilities as of {{ valuation_date }}.

---

## REAL ESTATE ASSETS

{% if real_estate_assets %}
{% for property in real_estate_assets %}
### Property {{ loop.index }}

**Type:** {{ property.type }}  
**Location:** {{ property.location }}  
**Title/Deed Number:** {{ property.title_number }}  
**Size:** {{ property.size }}  
**Current Value:** KES {{ property.value|number_format }}  
**Acquisition Date:** {{ property.acquisition_date|default('Not provided') }}  
**Acquisition Cost:** KES {{ property.acquisition_cost|default(0)|number_format }}  
**Outstanding Mortgage:** KES {{ property.mortgage_balance|default(0)|number_format }}

{% endfor %}

**Total Real Estate Value:** KES {{ total_real_estate_value|number_format }}
{% else %}
No real estate assets declared.
{% endif %}

---

## FINANCIAL ASSETS

### Bank Accounts
{% if bank_accounts %}
{% for account in bank_accounts %}
**{{ account.bank_name }}**  
Account Number: {{ account.account_number }}  
Account Type: {{ account.account_type }}  
Current Balance: KES {{ account.balance|number_format }}

{% endfor %}
**Total Bank Balances:** KES {{ total_bank_balances|number_format }}
{% else %}
No bank accounts declared.
{% endif %}

### Investment Accounts
{% if investments %}
{% for investment in investments %}
**{{ investment.type }}**  
Institution: {{ investment.institution }}  
Account/Policy Number: {{ investment.account_number }}  
Current Value: KES {{ investment.value|number_format }}  
Maturity Date: {{ investment.maturity_date }}

{% endfor %}
**Total Investment Value:** KES {{ total_investment_value|number_format }}
{% else %}
No investments declared.
{% endif %}

---

## BUSINESS INTERESTS

{% if business_interests %}
{% for business in business_interests %}
### {{ business.business_name }}

**Type:** {{ business.business_type }}  
**Registration Number:** {{ business.registration_number }}  
**Ownership Percentage:** {{ business.ownership_percentage }}%  
**Estimated Value:** KES {{ business.estimated_value|number_format }}  
**Annual Revenue:** KES {{ business.annual_revenue|number_format }}  
**Role:** {{ business.role }}

{% endfor %}

**Total Business Value:** KES {{ total_business_value|number_format }}
{% else %}
No business interests declared.
{% endif %}

---

## PERSONAL PROPERTY

{% if personal_property %}
{% for item in personal_property %}
**{{ item.category }}**  
Description: {{ item.description }}  
Estimated Value: KES {{ item.value|number_format }}  
Acquisition Date: {{ item.acquisition_date|default('Not provided') }}

{% endfor %}

**Total Personal Property Value:** KES {{ total_personal_property_value|number_format }}
{% else %}
No significant personal property declared.
{% endif %}

---

## LIABILITIES

### Loans and Mortgages
{% if loans %}
{% for loan in loans %}
**{{ loan.lender }}**  
Loan Type: {{ loan.type }}  
Original Amount: KES {{ loan.original_amount|number_format }}  
Outstanding Balance: KES {{ loan.outstanding_balance|number_format }}  
Monthly Payment: KES {{ loan.monthly_payment|number_format }}  
Maturity Date: {{ loan.maturity_date }}

{% endfor %}

**Total Outstanding Loans:** KES {{ total_outstanding_loans|number_format }}
{% else %}
No outstanding loans declared.
{% endif %}

### Other Liabilities
{% if other_liabilities %}
{% for liability in other_liabilities %}
**{{ liability.type }}**  
Creditor: {{ liability.creditor }}  
Amount: KES {{ liability.amount|number_format }}  
Due Date: {{ liability.due_date }}

{% endfor %}

**Total Other Liabilities:** KES {{ total_other_liabilities|number_format }}
{% else %}
No other liabilities declared.
{% endif %}

---

## SUMMARY

### Asset Summary
- Real Estate: KES {{ total_real_estate_value|number_format }}
- Financial Assets: KES {{ (total_bank_balances + total_investment_value)|number_format }}
- Business Interests: KES {{ total_business_value|number_format }}
- Personal Property: KES {{ total_personal_property_value|number_format }}

**TOTAL ASSETS:** KES {{ total_assets|number_format }}

### Liability Summary
- Outstanding Loans: KES {{ total_outstanding_loans|number_format }}
- Other Liabilities: KES {{ total_other_liabilities|number_format }}

**TOTAL LIABILITIES:** KES {{ total_liabilities|number_format }}

### Net Worth
**NET WORTH:** KES {{ net_worth|number_format }}

---

## DECLARATION

I solemnly declare that:

1. The information provided above is true and complete to the best of my knowledge
2. I have not deliberately omitted any assets or liabilities
3. All valuations are based on current market estimates or professional assessments
4. I understand that false declaration may have legal consequences

**Declarant Signature:** _______________________________  
{{ declarant_name }}  
Date: {{ declaration_date }}

**Witness:**  
Name: _______________________________  
Signature: _______________________________  
Date: _______________________________

---

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Purpose:** {{ declaration_purpose }}

*This declaration is prepared for {{ declaration_purpose }} and may require professional verification.*
        '''
    
    def _get_succession_certificate_template(self) -> str:
        """Get succession certificate template"""
        return '''
# APPLICATION FOR SUCCESSION CERTIFICATE

**HIGH COURT OF KENYA**  
**{{ court_station }} REGISTRY**

**IN THE MATTER OF THE ESTATE OF {{ deceased_name|upper }} (DECEASED)**

---

## APPLICANT INFORMATION

**Name:** {{ applicant_name }}  
**ID Number:** {{ applicant_id }}  
**Address:** {{ applicant_address }}  
**Telephone:** {{ applicant_phone }}  
**Relationship to Deceased:** {{ relationship_to_deceased }}

---

## DECEASED INFORMATION

**Full Name:** {{ deceased_name }}  
**Date of Birth:** {{ deceased_dob }}  
**Date of Death:** {{ deceased_date_of_death }}  
**Place of Death:** {{ place_of_death }}  
**Last Known Address:** {{ deceased_address }}  
**Occupation:** {{ deceased_occupation }}

---

## FAMILY INFORMATION

### Surviving Spouse(s)
{% if surviving_spouses %}
{% for spouse in surviving_spouses %}
**Name:** {{ spouse.name }}  
**ID Number:** {{ spouse.id_number }}  
**Marriage Date:** {{ spouse.marriage_date }}  
**Marriage Type:** {{ spouse.marriage_type }}

{% endfor %}
{% else %}
No surviving spouse.
{% endif %}

### Surviving Children
{% if surviving_children %}
{% for child in surviving_children %}
**Name:** {{ child.name }}  
**Date of Birth:** {{ child.dob }}  
**ID Number:** {{ child.id_number }}  
**Relationship:** {{ child.relationship }}

{% endfor %}
{% else %}
No surviving children.
{% endif %}

---

## ESTATE INFORMATION

### Assets of the Deceased

{% for asset in estate_assets %}
**{{ loop.index }}. {{ asset.type }}**  
Description: {{ asset.description }}  
Location: {{ asset.location }}  
Estimated Value: KES {{ asset.value|number_format }}  

{% endfor %}

**Total Estate Value:** KES {{ total_estate_value|number_format }}

### Liabilities
{% if estate_liabilities %}
{% for liability in estate_liabilities %}
**{{ liability.type }}**  
Creditor: {{ liability.creditor }}  
Amount: KES {{ liability.amount|number_format }}  

{% endfor %}

**Total Liabilities:** KES {{ total_liabilities|number_format }}
{% else %}
No known liabilities.
{% endif %}

**Net Estate Value:** KES {{ net_estate_value|number_format }}

---

## GROUNDS FOR APPLICATION

The Applicant seeks a Succession Certificate on the following grounds:

{% for ground in application_grounds %}
{{ loop.index }}. {{ ground }}
{% endfor %}

---

## PRAYERS

WHEREFORE, the Applicant humbly prays that this Honourable Court may be pleased to:

1. Grant a Succession Certificate in respect of the estate of the deceased
2. Declare the Applicant as the lawful {{ succession_role }}
3. Grant such other relief as this Honourable Court may deem fit
4. Grant costs of this application

---

## SUPPORTING DOCUMENTS

The following documents are attached in support of this application:

{% for document in supporting_documents %}
{{ loop.index }}. {{ document }}
{% endfor %}

---

## VERIFICATION

I, {{ applicant_name }}, do hereby verify that the contents of this application are true to the best of my knowledge, information and belief.

**Signature:** _______________________________  
{{ applicant_name }}  
**Date:** {{ application_date }}

**SWORN BEFORE ME:**  

_______________________________  
Magistrate/Commissioner for Oaths  
**Date:** {{ verification_date }}

---

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Court Filing Required:** Yes

*This application must be filed with the appropriate High Court registry.*
        '''
    
    def _get_marriage_contract_template(self) -> str:
        """Get marriage contract template"""
        return '''
# MARRIAGE CONTRACT

{% if contract_type == "prenuptial" %}
## PRE-NUPTIAL AGREEMENT
{% elif contract_type == "postnuptial" %}
## POST-NUPTIAL AGREEMENT
{% else %}
## MARRIAGE CONTRACT
{% endif %}

---

## PARTIES

**FIRST PARTY:** {{ party1_name }}  
ID Number: {{ party1_id }}  
Address: {{ party1_address }}  
Occupation: {{ party1_occupation }}

**SECOND PARTY:** {{ party2_name }}  
ID Number: {{ party2_id }}  
Address: {{ party2_address }}  
Occupation: {{ party2_occupation }}

{% if contract_type == "prenuptial" %}
**Intended Marriage Date:** {{ intended_marriage_date }}
{% elif contract_type == "postnuptial" %}
**Marriage Date:** {{ marriage_date }}  
**Marriage Certificate Number:** {{ marriage_cert_number }}
{% endif %}

---

## PREAMBLE

WHEREAS the parties intend to enter into marriage and wish to define their respective rights and obligations regarding property and financial matters;

WHEREAS both parties have made full disclosure of their assets and liabilities;

WHEREAS both parties have had the opportunity to seek independent legal advice;

NOW THEREFORE, the parties agree as follows:

---

## SEPARATE PROPERTY

### Property of {{ party1_name }}
The following shall remain the separate property of {{ party1_name }}:

{% for asset in party1_separate_assets %}
{{ loop.index }}. {{ asset.description }} (Value: KES {{ asset.value|number_format }})
{% endfor %}

### Property of {{ party2_name }}
The following shall remain the separate property of {{ party2_name }}:

{% for asset in party2_separate_assets %}
{{ loop.index }}. {{ asset.description }} (Value: KES {{ asset.value|number_format }})
{% endfor %}

---

## MATRIMONIAL PROPERTY

{% if matrimonial_property_regime == "community" %}
### Community Property Regime
All property acquired during the marriage (except separate property above) shall be owned jointly in equal shares.

{% elif matrimonial_property_regime == "separate" %}
### Separate Property Regime
Each party shall retain ownership of property acquired in their own name during marriage.

{% elif matrimonial_property_regime == "deferred_community" %}
### Deferred Community Property
Property acquired during marriage shall be subject to sharing upon dissolution of marriage according to contribution.
{% endif %}

---

## FINANCIAL OBLIGATIONS

### Living Expenses
{{ living_expenses_arrangement }}

### Debt Responsibility
{{ debt_responsibility_arrangement }}

### Children's Expenses
{{ children_expenses_arrangement }}

---

## SUCCESSION RIGHTS

{% if succession_waiver %}
### Waiver of Succession Rights
{{ succession_waiver_details }}
{% else %}
### Succession Rights Preserved
Both parties retain their succession rights under the Law of Succession Act.
{% endif %}

---

## DISPUTE RESOLUTION

Any disputes arising from this contract shall be resolved through:
1. Mediation by a qualified mediator
2. If mediation fails, arbitration under the Arbitration Act
3. As a last resort, court proceedings in Kenya

---

## MODIFICATION AND TERMINATION

This contract may only be modified by mutual written agreement of both parties. The contract shall terminate upon:
1. Mutual agreement of the parties
2. Divorce or annulment of the marriage
3. Death of either party

---

## LEGAL COMPLIANCE

This contract is made in accordance with:
{% for reference in legal_references %}
- {{ reference }}
{% endfor %}

---

## EXECUTION

IN WITNESS WHEREOF, the parties have executed this agreement on {{ execution_date }}.

**{{ party1_name }}:**  
Signature: _______________________________  
Date: _______________________________

**{{ party2_name }}:**  
Signature: _______________________________  
Date: _______________________________

**WITNESSES:**  
Witness 1: _______________________________  
Witness 2: _______________________________

---

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Legal Review Required:** Yes

*This contract requires independent legal advice for both parties.*
        '''
    
    def _get_business_succession_plan_template(self) -> str:
        """Get business succession plan template"""
        return '''
# BUSINESS SUCCESSION PLAN

**{{ business_name|upper }}**  
**Registration Number:** {{ business_registration_number }}

---

## EXECUTIVE SUMMARY

{{ executive_summary }}

---

## BUSINESS INFORMATION

**Business Name:** {{ business_name }}  
**Type:** {{ business_type }}  
**Registration Number:** {{ business_registration_number }}  
**Date Established:** {{ establishment_date }}  
**Current Value:** KES {{ business_value|number_format }}  
**Annual Revenue:** KES {{ annual_revenue|number_format }}  
**Number of Employees:** {{ employee_count }}

### Key Business Assets
{% for asset in key_assets %}
**{{ asset.type }}**  
Description: {{ asset.description }}  
Value: KES {{ asset.value|number_format }}  
Critical to Operations: {{ asset.critical|default("Yes") }}

{% endfor %}

---

## CURRENT OWNERSHIP STRUCTURE

{% for owner in current_owners %}
**{{ owner.name }}**  
Ownership Percentage: {{ owner.percentage }}%  
Role: {{ owner.role }}  
Age: {{ owner.age }}  
Succession Priority: {{ owner.succession_priority }}

{% endfor %}

---

## SUCCESSION OBJECTIVES

{% for objective in succession_objectives %}
{{ loop.index }}. {{ objective }}
{% endfor %}

---

## SUCCESSION STRATEGY

### Management Succession

#### Key Positions
{% for position in key_positions %}
**{{ position.title }}**  
Current Holder: {{ position.current_holder }}  
Age: {{ position.age }}  
Retirement Timeline: {{ position.retirement_timeline }}  
Successor: {{ position.successor }}  
Development Plan: {{ position.development_plan }}

{% endfor %}

### Ownership Succession

{{ ownership_succession_strategy }}

#### Succession Options Considered
{% for option in succession_options %}
**{{ option.type }}**  
Description: {{ option.description }}  
Advantages: {{ option.advantages }}  
Disadvantages: {{ option.disadvantages }}  
Selected: {{ option.selected }}

{% endfor %}

---

## VALUATION AND FINANCING

### Business Valuation
**Current Valuation Method:** {{ valuation_method }}  
**Current Value:** KES {{ current_business_value|number_format }}  
**Valuation Date:** {{ valuation_date }}  
**Valuation Frequency:** {{ valuation_frequency }}

### Financing Strategy
{{ financing_strategy }}

#### Funding Sources
{% for source in funding_sources %}
**{{ source.type }}**  
Amount: KES {{ source.amount|number_format }}  
Terms: {{ source.terms }}  
Approval Status: {{ source.status }}

{% endfor %}

---

## IMPLEMENTATION TIMELINE

{% for phase in implementation_phases %}
### Phase {{ loop.index }}: {{ phase.name }}
**Timeline:** {{ phase.timeline }}  
**Objectives:** {{ phase.objectives }}  
**Key Actions:**
{% for action in phase.actions %}
- {{ action }}
{% endfor %}
**Success Metrics:** {{ phase.success_metrics }}

{% endfor %}

---

## RISK MANAGEMENT

{% for risk in identified_risks %}
### {{ risk.category }} Risk: {{ risk.level }}
**Description:** {{ risk.description }}  
**Impact:** {{ risk.impact }}  
**Mitigation Strategy:** {{ risk.mitigation }}  
**Contingency Plan:** {{ risk.contingency }}

{% endfor %}

---

## LEGAL AND TAX CONSIDERATIONS

### Corporate Governance
{{ corporate_governance_plan }}

### Tax Planning
{{ tax_planning_strategy }}

### Legal Documentation Required
{% for document in required_documents %}
{{ loop.index }}. {{ document.type }} - {{ document.description }}
   Status: {{ document.status }}
   Deadline: {{ document.deadline }}

{% endfor %}

---

## COMMUNICATION PLAN

### Stakeholder Communication
{{ stakeholder_communication_plan }}

### Key Stakeholders
{% for stakeholder in key_stakeholders %}
**{{ stakeholder.name }}**  
Role: {{ stakeholder.role }}  
Communication Frequency: {{ stakeholder.communication_frequency }}  
Communication Method: {{ stakeholder.communication_method }}

{% endfor %}

---

## MONITORING AND REVIEW

**Review Frequency:** {{ review_frequency }}  
**Review Committee:** {{ review_committee }}  
**Key Performance Indicators:**

{% for kpi in key_performance_indicators %}
- {{ kpi.metric }}: {{ kpi.target }}
{% endfor %}

---

## CONTINGENCY PLANS

### Emergency Succession
{{ emergency_succession_plan }}

### Business Continuity
{{ business_continuity_plan }}

---

## APPROVAL AND AUTHORIZATION

This Business Succession Plan has been reviewed and approved by:

{% for approver in plan_approvers %}
**{{ approver.name }}**  
Title: {{ approver.title }}  
Signature: _______________________________  
Date: _______________________________

{% endfor %}

---

**Document Prepared by:** {{ prepared_by }}  
**Date Prepared:** {{ preparation_date }}  
**Next Review Date:** {{ next_review_date }}

**Document Generated:** {{ generation_date }}  
**Template Version:** {{ template_version }}  
**Implementation Status:** {{ implementation_status }}

*This plan should be reviewed annually and updated as business circumstances change.*
        '''
    
    def generate_document(self, document_type: DocumentType, 
                         client_data: Dict[str, Any],
                         additional_data: Dict[str, Any] = None,
                         format_type: DocumentFormat = DocumentFormat.HTML) -> Dict[str, Any]:
        """Generate a document based on client data and template"""
        
        try:
            # Prepare template data
            template_data = self._prepare_template_data(document_type, client_data, additional_data)
            
            # Get legal references
            legal_references = self._get_relevant_legal_references(document_type, client_data)
            template_data['legal_references'] = legal_references
            
            # Generate document content
            if self.jinja_env:
                content = self._generate_with_jinja(document_type, template_data)
            else:
                content = self._generate_with_basic_template(document_type, template_data)
            
            # Create document metadata
            metadata = self._create_document_metadata(document_type, client_data)
            
            # Save document
            document_id = self._save_document(content, metadata, format_type)
            
            return {
                "success": True,
                "document_id": document_id,
                "document_type": document_type.value,
                "format": format_type.value,
                "metadata": metadata.to_dict(),
                "content_length": len(content),
                "file_path": str(self.documents_dir / f"{document_id}.{format_type.value}")
            }
            
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_type": document_type.value
            }
    
    def _prepare_template_data(self, document_type: DocumentType, 
                              client_data: Dict[str, Any],
                              additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        
        # Extract base client information
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        objectives = client_data.get('objectives', {})
        
        # Base template data
        template_data = {
            # Client information
            'client_name': bio_data.get('fullName', 'Unknown'),
            'client_address': bio_data.get('address', 'Address not provided'),
            'date_of_birth': bio_data.get('dateOfBirth', 'Not provided'),
            'id_number': bio_data.get('idNumber', 'Not provided'),
            'marital_status': bio_data.get('maritalStatus', 'Not specified'),
            'children': bio_data.get('children', 'None specified'),
            
            # Financial information
            'assets': financial_data.get('assets', []),
            'total_assets': sum(asset.get('value', 0) for asset in financial_data.get('assets', [])),
            
            # Objectives
            'primary_objective': objectives.get('objective', 'Not specified'),
            'objective_details': objectives.get('details', 'No details provided'),
            
            # Document metadata
            'generation_date': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            'template_version': '1.0',
            'execution_date': datetime.now().strftime('%d'),
            'execution_month': datetime.now().strftime('%B'),
            'execution_year': datetime.now().strftime('%Y')
        }
        
        # Add document-specific data
        if document_type == DocumentType.WILL:
            template_data.update(self._prepare_will_data(client_data, additional_data))
        elif document_type == DocumentType.TRUST_DEED:
            template_data.update(self._prepare_trust_data(client_data, additional_data))
        elif document_type == DocumentType.POWER_OF_ATTORNEY:
            template_data.update(self._prepare_poa_data(client_data, additional_data))
        elif document_type == DocumentType.ASSET_DECLARATION:
            template_data.update(self._prepare_asset_declaration_data(client_data, additional_data))
        elif document_type == DocumentType.LEGAL_OPINION:
            template_data.update(self._prepare_legal_opinion_data(client_data, additional_data))
        
        # Merge additional data if provided
        if additional_data:
            template_data.update(additional_data)
        
        return template_data
    
    def _prepare_will_data(self, client_data: Dict[str, Any], 
                          additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare will-specific template data"""
        
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        distribution_prefs = client_data.get('distributionPreferences', {})
        
        # Default executor (can be overridden in additional_data)
        executor_name = bio_data.get('spouse', 'To be appointed')
        if bio_data.get('maritalStatus') != 'Married':
            executor_name = 'To be appointed'
        
        will_data = {
            'executor_name': executor_name,
            'executor_address': 'Address to be provided',
            'alternate_executor': 'To be appointed',
            'specific_bequests': [],
            'residuary_disposition': [],
            'minor_children': bio_data.get('children', '').lower() in ['minor', 'young', 'children'],
            'guardian_name': 'To be appointed',
            'alternate_guardian': 'To be appointed',
            'trust_provisions': True if bio_data.get('children') else False,
            'trust_age': 18
        }
        
        # Process distribution preferences
        if distribution_prefs:
            will_data['residuary_disposition'] = self._process_distribution_preferences(distribution_prefs)
        
        # Process assets for specific bequests
        assets = financial_data.get('assets', [])
        for asset in assets:
            if asset.get('specific_beneficiary'):
                will_data['specific_bequests'].append({
                    'description': asset.get('type', 'Asset'),
                    'beneficiary': asset.get('specific_beneficiary'),
                    'condition': asset.get('condition', '')
                })
        
        return will_data
    
    def _prepare_trust_data(self, client_data: Dict[str, Any], 
                           additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare trust-specific template data"""
        
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        
        trust_data = {
            'trust_name': f"{bio_data.get('fullName', 'Family')} Trust",
            'settlor_name': bio_data.get('fullName', 'Unknown'),
            'settlor_address': bio_data.get('address', 'Address not provided'),
            'trustees': [
                {
                    'name': 'Professional Trustee to be appointed',
                    'address': 'Address to be provided'
                }
            ],
            'beneficiaries': [],
            'trust_assets': [],
            'total_trust_value': 0,
            'trust_purposes': [
                'Asset protection and preservation',
                'Tax efficient wealth transfer',
                'Beneficiary welfare and advancement'
            ],
            'income_distribution': 'Annual distribution at trustees discretion',
            'capital_distribution': 'Capital distributions for beneficiary advancement'
        }
        
        # Process beneficiaries
        if bio_data.get('maritalStatus') == 'Married':
            trust_data['beneficiaries'].append({
                'name': bio_data.get('spouse', 'Spouse'),
                'relationship': 'Spouse'
            })
        
        if bio_data.get('children'):
            trust_data['beneficiaries'].append({
                'name': bio_data.get('children', 'Children'),
                'relationship': 'Children'
            })
        
        # Process trust assets
        for asset in financial_data.get('assets', []):
            trust_data['trust_assets'].append({
                'description': f"{asset.get('type', 'Asset')} - {asset.get('description', 'No description')}",
                'type': asset.get('type', 'Unknown'),
                'value': asset.get('value', 0),
                'location': asset.get('location', 'Not specified')
            })
        
        trust_data['total_trust_value'] = sum(
            asset.get('value', 0) for asset in trust_data['trust_assets']
        )
        
        return trust_data
    
    def _prepare_poa_data(self, client_data: Dict[str, Any], 
                         additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare power of attorney specific data"""
        
        bio_data = client_data.get('bioData', {})
        
        poa_data = {
            'principal_name': bio_data.get('fullName', 'Unknown'),
            'principal_address': bio_data.get('address', 'Address not provided'),
            'principal_id': bio_data.get('idNumber', 'Not provided'),
            'principal_dob': bio_data.get('dateOfBirth', 'Not provided'),
            'attorney_name': 'To be appointed',
            'attorney_address': 'Address to be provided',
            'attorney_id': 'To be provided',
            'attorney_relationship': 'To be specified',
            'power_type': 'general',  # general, specific, limited
            'effective_type': 'immediate',  # immediate, springing, limited_time
            'gift_limit': 100000,
            'restrictions': [
                'Cannot make or change a will',
                'Cannot make gifts exceeding specified limit',
                'Cannot delegate authority to others'
            ],
            'witness1_name': 'Witness 1 Name',
            'witness2_name': 'Witness 2 Name'
        }
        
        return poa_data
    
    def _prepare_asset_declaration_data(self, client_data: Dict[str, Any], 
                                       additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare asset declaration specific data"""
        
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        assets = financial_data.get('assets', [])
        
        # Initialize asset categories
        real_estate_assets = []
        bank_accounts = []
        investments = []
        business_interests = []
        personal_property = []
        
        # Process real estate assets
        for asset in financial_data.get('assets', []):
            processed_asset = {
                'type': asset.get('type', 'Unknown'),
                'description': asset.get('description', 'No description'),
                'value': asset.get('value', 0),
                'location': asset.get('location', 'Not specified'),
                'acquisition_date': asset.get('acquisition_date', 'Not provided'),
                'acquisition_cost': asset.get('acquisition_cost', 0),
                'mortgage_balance': asset.get('mortgage_balance', 0)
            }
            
            if 'property' in asset.get('type', '').lower() or 'real estate' in asset.get('type', '').lower():
                real_estate_assets.append(processed_asset)
            elif 'bank' in asset.get('type', '').lower() or 'account' in asset.get('type', '').lower():
                bank_accounts.append({
                    'bank_name': asset.get('bank_name', 'Bank'),
                    'account_number': asset.get('account_number', 'Not provided'),
                    'account_type': asset.get('account_type', 'Account'),
                    'balance': asset.get('value', 0)
                })
            elif 'investment' in asset.get('type', '').lower() or 'shares' in asset.get('type', '').lower():
                investments.append({
                    'type': asset.get('type', 'Investment'),
                    'institution': asset.get('institution', 'Not specified'),
                    'account_number': asset.get('account_number', 'Not provided'),
                    'value': asset.get('value', 0),
                    'maturity_date': asset.get('maturity_date', 'Not specified')
                })
            elif 'business' in asset.get('type', '').lower():
                business_interests.append({
                    'business_name': asset.get('business_name', asset.get('description', 'Business')),
                    'business_type': asset.get('business_type', 'Private Company'),
                    'registration_number': asset.get('registration_number', 'Not provided'),
                    'ownership_percentage': asset.get('ownership_percentage', 'Not specified'),
                    'estimated_value': asset.get('value', 0),
                    'annual_revenue': asset.get('annual_revenue', 0),
                    'role': asset.get('role', 'Owner')
                })
            else:
                personal_property.append({
                    'category': asset.get('type', 'Personal Property'),
                    'description': asset.get('description', 'No description'),
                    'value': asset.get('value', 0),
                    'acquisition_date': asset.get('acquisition_date', 'Not provided')
                })
        
        # Calculate totals
        total_real_estate = sum(a.get('value', 0) for a in real_estate_assets)
        total_bank_balances = sum(a.get('value', 0) for a in bank_accounts)
        total_investment_value = sum(a.get('value', 0) for a in investments)
        total_business_value = sum(a.get('value', 0) for a in business_interests)
        total_personal_property_value = sum(a.get('value', 0) for a in personal_property)
        total_assets = total_real_estate + total_bank_balances + total_investment_value + total_business_value + total_personal_property_value
        
        declaration_data = {
            'declarant_name': bio_data.get('fullName', 'Unknown'),
            'declaration_date': datetime.now().strftime('%B %d, %Y'),
            'declarant_id': bio_data.get('idNumber', 'Not provided'),
            'valuation_date': datetime.now().strftime('%B %d, %Y'),
            
            # Asset categories
            'real_estate_assets': real_estate_assets,
            'bank_accounts': bank_accounts,
            'investments': investments,
            'business_interests': business_interests,
            'personal_property': personal_property,
            
            # Totals
            'total_real_estate_value': total_real_estate,
            'total_bank_balances': total_bank_balances,
            'total_investment_value': total_investment_value,
            'total_business_value': total_business_value,
            'total_personal_property_value': total_personal_property_value,
            'total_assets': total_assets,
            
            # Liabilities (placeholder)
            'loans': [],
            'other_liabilities': [],
            'total_outstanding_loans': 0,
            'total_other_liabilities': 0,
            'total_liabilities': 0,
            'net_worth': total_assets,
            
            'declaration_purpose': 'Estate planning and legal documentation'
        }
        
        return declaration_data
    
    def _prepare_legal_opinion_data(self, client_data: Dict[str, Any], 
                                   additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare legal opinion specific data"""
        
        bio_data = client_data.get('bioData', {})
        objectives = client_data.get('objectives', {})
        
        opinion_data = {
            'law_firm_name': 'HNC Legal Services',
            'law_firm_address': 'Nairobi, Kenya',
            'client_name': bio_data.get('fullName', 'Unknown'),
            'matter_description': objectives.get('objective', 'Legal consultation'),
            'opinion_date': datetime.now().strftime('%B %d, %Y'),
            'reference_number': f"HNC-{datetime.now().strftime('%Y%m%d')}-{bio_data.get('fullName', 'Unknown')[:3].upper()}",
            'executive_summary': 'Comprehensive legal analysis and recommendations based on client objectives and applicable Kenyan law.',
            'factual_background': f"Client seeks legal guidance regarding {objectives.get('objective', 'legal matters')}.",
            'applicable_laws': [],
            'legal_assessment': 'Detailed legal analysis based on applicable statutes and case law.',
            'recommendations': [],
            'risks': [],
            'conclusion': 'Professional legal guidance and implementation recommended.',
            'lawyer_name': 'Legal Practitioner',
            'admission_number': 'To be provided',
            'review_status': 'Draft'
        }
        
        return opinion_data
    
    def _process_distribution_preferences(self, distribution_prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process distribution preferences into residuary disposition format"""
        
        dispositions = []
        
        # This would process actual distribution preferences
        # For now, return a default structure
        dispositions.append({
            'percentage': 50,
            'beneficiary': 'Spouse',
            'description': 'To surviving spouse'
        })
        
        dispositions.append({
            'percentage': 50,
            'beneficiary': 'Children',
            'description': 'To children in equal shares'
        })
        
        return dispositions
    
    def _get_relevant_legal_references(self, document_type: DocumentType, 
                                     client_data: Dict[str, Any]) -> List[str]:
        """Get relevant legal references for the document type"""
        
        # Get legal references based on document type and client context
        search_query = self._get_search_query_for_document_type(document_type)
        legal_refs = kenya_law_db.search_legal_references(search_query)
        
        formatted_refs = []
        for ref in legal_refs[:5]:  # Top 5 most relevant
            formatted_ref = kenya_law_db.format_legal_reference_for_ai(ref)
            formatted_refs.append(formatted_ref)
        
        # Add document-specific legal references
        if document_type == DocumentType.WILL:
            formatted_refs.insert(0, "Succession Act (Cap 160) - Requirements for Valid Will")
        elif document_type == DocumentType.TRUST_DEED:
            formatted_refs.insert(0, "Trustee Act (Cap 167) - Trust Creation and Management")
        elif document_type == DocumentType.POWER_OF_ATTORNEY:
            formatted_refs.insert(0, "Powers of Attorney Act - Legal Framework for POA")
        
        return formatted_refs
    
    def _get_search_query_for_document_type(self, document_type: DocumentType) -> str:
        """Get appropriate search query for legal references"""
        
        queries = {
            DocumentType.WILL: "will creation requirements succession",
            DocumentType.TRUST_DEED: "trust creation trustee duties",
            DocumentType.POWER_OF_ATTORNEY: "power of attorney legal requirements",
            DocumentType.LEGAL_OPINION: "legal analysis statutory requirements",
            DocumentType.ASSET_DECLARATION: "asset disclosure inheritance tax",
            DocumentType.SUCCESSION_CERTIFICATE: "succession certificate probate",
            DocumentType.MARRIAGE_CONTRACT: "matrimonial property marriage rights",
            DocumentType.BUSINESS_SUCCESSION_PLAN: "business succession corporate governance"
        }
        
        return queries.get(document_type, "legal requirements")
    
    def _generate_with_jinja(self, document_type: DocumentType, 
                            template_data: Dict[str, Any]) -> str:
        """Generate document using Jinja2 template engine"""
        
        template_file = f"{document_type.value}.jinja2"
        
        try:
            template = self.jinja_env.get_template(template_file)
            
            # Add custom filters
            self.jinja_env.filters['number_format'] = self._number_format_filter
            
            content = template.render(**template_data)
            return content
            
        except TemplateError as e:
            logger.error(f"Jinja2 template error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            raise
    
    def _generate_with_basic_template(self, document_type: DocumentType, 
                                     template_data: Dict[str, Any]) -> str:
        """Generate document using basic string template (fallback)"""
        
        # Get template content
        template_methods = {
            DocumentType.WILL: self._get_will_template,
            DocumentType.TRUST_DEED: self._get_trust_deed_template,
            DocumentType.POWER_OF_ATTORNEY: self._get_power_of_attorney_template,
            DocumentType.LEGAL_OPINION: self._get_legal_opinion_template,
            DocumentType.ASSET_DECLARATION: self._get_asset_declaration_template
        }
        
        template_method = template_methods.get(document_type)
        if not template_method:
            raise ValueError(f"No template available for document type: {document_type.value}")
        
        template_content = template_method()
        
        # Basic variable substitution (very limited compared to Jinja2)
        try:
            content = template_content.format(**template_data)
            return content
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}. Using placeholder.")
            # Create a version with missing variables replaced
            import re
            content = re.sub(r'\{\{[^}]*\}\}', '[TO BE COMPLETED]', template_content)
            return content
    
    def _number_format_filter(self, value: Any) -> str:
        """Format numbers with commas for Jinja2 templates"""
        try:
            return f"{float(value):,.0f}"
        except (ValueError, TypeError):
            return str(value)
    
    def _create_document_metadata(self, document_type: DocumentType, 
                                 client_data: Dict[str, Any]) -> DocumentMetadata:
        """Create document metadata"""
        
        bio_data = client_data.get('bioData', {})
        
        return DocumentMetadata(
            document_id=f"{document_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            document_type=document_type,
            client_name=bio_data.get('fullName', 'Unknown'),
            created_at=datetime.now(),
            created_by='System',
            version='1.0',
            template_version='1.0',
            legal_references=[],  # Will be populated
            ai_generated=True,
            review_status='draft'
        )
    
    def _save_document(self, content: str, metadata: DocumentMetadata, 
                      format_type: DocumentFormat) -> str:
        """Save generated document to file"""
        
        document_id = metadata.document_id
        file_path = self.documents_dir / f"{document_id}.{format_type.value}"
        
        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save metadata
        metadata_path = self.documents_dir / f"{document_id}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Document saved: {file_path}")
        return document_id
    
    def get_document(self, document_id: str, format_type: DocumentFormat = DocumentFormat.HTML) -> Dict[str, Any]:
        """Retrieve a generated document"""
        
        file_path = self.documents_dir / f"{document_id}.{format_type.value}"
        metadata_path = self.documents_dir / f"{document_id}_metadata.json"
        
        if not file_path.exists():
            return {"success": False, "error": "Document not found"}
        
        try:
            # Read content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Read metadata
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return {
                "success": True,
                "document_id": document_id,
                "content": content,
                "metadata": metadata,
                "format": format_type.value
            }
            
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def list_documents(self, client_name: str = None) -> List[Dict[str, Any]]:
        """List all generated documents"""
        
        documents = []
        
        for metadata_file in self.documents_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Filter by client name if provided
                if client_name and metadata.get('client_name', '').lower() != client_name.lower():
                    continue
                
                documents.append(metadata)
                
            except Exception as e:
                logger.error(f"Error reading metadata file {metadata_file}: {str(e)}")
                continue
        
        # Sort by creation date (newest first)
        documents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return documents
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a generated document"""
        
        try:
            deleted_files = []
            
            # Delete all format versions of the document
            for format_type in DocumentFormat:
                file_path = self.documents_dir / f"{document_id}.{format_type.value}"
                if file_path.exists():
                    file_path.unlink()
                    deleted_files.append(str(file_path))
            
            # Delete metadata
            metadata_path = self.documents_dir / f"{document_id}_metadata.json"
            if metadata_path.exists():
                metadata_path.unlink()
                deleted_files.append(str(metadata_path))
            
            if deleted_files:
                return {
                    "success": True,
                    "message": f"Deleted {len(deleted_files)} files",
                    "deleted_files": deleted_files
                }
            else:
                return {
                    "success": False,
                    "error": "Document not found"
                }
                
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return {"success": False, "error": str(e)}


# Global instance
document_template_manager = DocumentTemplateManager()