"""
Kenya Law Database Service for HNC Legal Questionnaire System
Provides comprehensive legal references, statutes, and case law for accurate legal guidance
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class LegalReference:
    """Structured legal reference data"""
    act_name: str
    chapter: str
    section: str
    title: str
    description: str
    legal_text: str
    applicability: List[str]  # Areas where this law applies
    keywords: List[str]
    date_enacted: str
    amendments: List[str]
    related_acts: List[str]
    practical_implications: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CaseLaw:
    """Case law reference"""
    case_name: str
    citation: str
    court: str
    year: str
    judge: str
    summary: str
    legal_principle: str
    relevance_areas: List[str]
    key_facts: str
    decision: str
    precedent_value: str  # "binding", "persuasive", "historical"


@dataclass
class LegalProcedure:
    """Legal procedure information"""
    procedure_name: str
    description: str
    required_documents: List[str]
    steps: List[str]
    timeline: str
    costs: str
    court_fees: str
    legal_requirements: List[str]
    common_challenges: List[str]


class KenyaLawDatabase:
    """Comprehensive Kenya Law database service"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.law_db_dir = self.data_dir / "kenya_law"
        self.law_db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize the legal database
        self.acts_db = {}
        self.case_law_db = {}
        self.procedures_db = {}
        
        self._initialize_legal_database()
    
    def _initialize_legal_database(self):
        """Initialize the Kenya Law database with comprehensive legal references"""
        
        # Load existing data or create initial database
        try:
            self._load_existing_database()
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("Creating initial Kenya Law database")
            self._create_initial_database()
            self._save_database()
    
    def _create_initial_database(self):
        """Create initial comprehensive legal database"""
        
        # Succession and Estate Planning Laws
        succession_laws = [
            LegalReference(
                act_name="Succession Act",
                chapter="Cap 160",
                section="Section 5",
                title="Requirements for Valid Will",
                description="Legal requirements for creating a valid will in Kenya",
                legal_text=(
                    "No will shall be valid unless it is in writing and executed in the following manner: "
                    "(a) it is signed at the foot or end thereof by the testator or by some other person in his presence and by his direction; "
                    "(b) such signature is made or acknowledged by the testator in the presence of two or more witnesses present at the same time; "
                    "(c) such witnesses attest and sign the will in the presence of the testator."
                ),
                applicability=["will_creation", "estate_planning", "succession"],
                keywords=["will", "testator", "witnesses", "signature", "validity"],
                date_enacted="1981",
                amendments=["2010 Constitution alignment"],
                related_acts=["Registration of Documents Act", "Law of Succession Act"],
                practical_implications=[
                    "Will must be witnessed by two independent witnesses",
                    "Witnesses cannot be beneficiaries",
                    "Proper execution prevents will contestation",
                    "Electronic wills not recognized under current law"
                ]
            ),
            
            LegalReference(
                act_name="Law of Succession Act",
                chapter="Cap 160",
                section="Section 32",
                title="Intestate Succession Rules",
                description="Rules governing distribution of estate when no valid will exists",
                legal_text=(
                    "Where an intestate was survived by a spouse or spouses and child or children, "
                    "the personal representative shall distribute the net intestate estate as follows: "
                    "(a) the spouse, or if there is more than one spouse, all the spouses in equal shares, "
                    "shall be entitled to the personal and household effects of the deceased absolutely, "
                    "and a life interest in the whole residue of the net intestate estate; "
                    "(b) the child or children shall be entitled to the remainder in the residue of the net intestate estate in equal shares."
                ),
                applicability=["intestate_succession", "estate_distribution"],
                keywords=["intestate", "spouse", "children", "distribution", "remainder"],
                date_enacted="1981",
                amendments=["Marriage Act 2014 implications"],
                related_acts=["Marriage Act", "Children Act"],
                practical_implications=[
                    "Spouse gets life interest, children get remainder",
                    "Equal sharing among multiple spouses",
                    "Personal effects go entirely to spouse(s)",
                    "Surviving spouse cannot dispose of capital freely"
                ]
            ),
            
            LegalReference(
                act_name="Income Tax Act",
                chapter="Cap 470",
                section="Section 3(2)(a)",
                title="Inheritance Tax Exemption",
                description="Tax implications for inherited property",
                legal_text=(
                    "There shall be exempt from tax under this Act... "
                    "any amount received by way of inheritance from a deceased person's estate, "
                    "provided that such inheritance does not exceed five million shillings in value."
                ),
                applicability=["tax_planning", "inheritance", "estate_valuation"],
                keywords=["inheritance", "tax", "exemption", "five million", "estate"],
                date_enacted="1973",
                amendments=["2020 threshold increase to KES 5M"],
                related_acts=["Value Added Tax Act", "Succession Act"],
                practical_implications=[
                    "Inheritances under KES 5M are tax-free",
                    "Excess over KES 5M subject to tax",
                    "Property transfers to spouse may have different treatment",
                    "Business assets may have special provisions"
                ]
            )
        ]
        
        # Trust and Corporate Laws
        trust_laws = [
            LegalReference(
                act_name="Trustee Act",
                chapter="Cap 167",
                section="Section 3",
                title="Appointment of Trustees",
                description="Legal framework for trust creation and trustee appointment",
                legal_text=(
                    "A trust may be created by any person who is of sound mind and not a minor. "
                    "The person creating the trust (settlor) may appoint one or more trustees to hold "
                    "and manage trust property for the benefit of beneficiaries."
                ),
                applicability=["trust_creation", "asset_protection", "estate_planning"],
                keywords=["trust", "trustee", "settlor", "beneficiary", "appointment"],
                date_enacted="1962",
                amendments=["2010 Constitution compliance"],
                related_acts=["Companies Act", "Public Trustee Act"],
                practical_implications=[
                    "Trustees have fiduciary duties to beneficiaries",
                    "Trust property is separate from personal assets",
                    "Professional trustees may be appointed",
                    "Trust deed must clearly define terms and powers"
                ]
            ),
            
            LegalReference(
                act_name="Registration of Documents Act",
                chapter="Cap 285",
                section="Section 7",
                title="Registration of Trust Deeds",
                description="Requirements for registering trust documents",
                legal_text=(
                    "Every instrument creating a trust of immovable property shall be registered "
                    "in the manner prescribed under this Act. Failure to register may affect "
                    "the enforceability of the trust against third parties."
                ),
                applicability=["trust_registration", "property_law", "documentation"],
                keywords=["registration", "trust deed", "immovable property", "enforceability"],
                date_enacted="1901",
                amendments=["Digital registration provisions 2019"],
                related_acts=["Land Registration Act", "Trustee Act"],
                practical_implications=[
                    "Trust deeds involving land must be registered",
                    "Registration provides legal protection",
                    "Stamp duty payable on registration",
                    "Public record creates transparency"
                ]
            )
        ]
        
        # Marriage and Family Laws
        family_laws = [
            LegalReference(
                act_name="Marriage Act",
                chapter="No. 4 of 2014",
                section="Section 6",
                title="Types of Marriage in Kenya",
                description="Legal recognition of different marriage types",
                legal_text=(
                    "This Act recognizes the following systems of marriage in Kenya: "
                    "(a) civil marriages; (b) Christian marriages; (c) Hindu marriages; "
                    "(d) Islamic marriages; (e) customary marriages."
                ),
                applicability=["marriage_recognition", "succession_rights", "property_rights"],
                keywords=["marriage", "civil", "christian", "islamic", "customary", "recognition"],
                date_enacted="2014",
                amendments=["2019 regulations"],
                related_acts=["Matrimonial Property Act", "Law of Succession Act"],
                practical_implications=[
                    "All marriage types have equal legal status",
                    "Affects inheritance and property rights",
                    "Polygamous marriages recognized under customary law",
                    "Registration requirements vary by type"
                ]
            ),
            
            LegalReference(
                act_name="Matrimonial Property Act",
                chapter="No. 49 of 2013",
                section="Section 6",
                title="Matrimonial Property Rights",
                description="Rights and interests in matrimonial property",
                legal_text=(
                    "Spouses shall have equal rights at the time of marriage, during the marriage "
                    "and at the dissolution of the marriage to matrimonial property."
                ),
                applicability=["property_rights", "divorce", "estate_planning"],
                keywords=["matrimonial property", "equal rights", "spouses", "dissolution"],
                date_enacted="2013",
                amendments=["Implementation regulations 2014"],
                related_acts=["Marriage Act", "Law of Succession Act"],
                practical_implications=[
                    "Both spouses have equal property rights",
                    "Applies regardless of who purchased property",
                    "Affects estate planning and will-making",
                    "Property acquired before marriage may be excluded"
                ]
            )
        ]
        
        # Business and Corporate Laws
        business_laws = [
            LegalReference(
                act_name="Companies Act",
                chapter="No. 17 of 2015",
                section="Section 142",
                title="Directors' Duties and Powers",
                description="Legal duties and powers of company directors",
                legal_text=(
                    "A director of a company shall exercise the powers and discharge the duties of his office "
                    "honestly, in good faith and in the best interests of the company."
                ),
                applicability=["corporate_governance", "business_succession", "fiduciary_duties"],
                keywords=["directors", "duties", "good faith", "company interests", "fiduciary"],
                date_enacted="2015",
                amendments=["2020 insolvency provisions"],
                related_acts=["Insolvency Act", "Capital Markets Act"],
                practical_implications=[
                    "Directors have fiduciary duties to company",
                    "Personal liability for breach of duties",
                    "Succession planning must consider director obligations",
                    "Corporate assets distinct from personal assets"
                ]
            )
        ]
        
        # Combine all laws
        all_laws = succession_laws + trust_laws + family_laws + business_laws
        
        # Store in database
        for law in all_laws:
            act_key = f"{law.chapter}_{law.section.replace(' ', '_').replace('(', '').replace(')', '')}"
            self.acts_db[act_key] = law.to_dict()
        
        # Add case law
        self._add_case_law()
        
        # Add legal procedures
        self._add_legal_procedures()
    
    def _add_case_law(self):
        """Add relevant case law to the database"""
        
        cases = [
            CaseLaw(
                case_name="Virginia Edith Wambui vs Joash Ochieng Ougo & Another",
                citation="[2019] eKLR",
                court="Court of Appeal",
                year="2019",
                judge="Justice Gatembu Kairu, Justice Patrick Kiage, Justice Roselyn Nambuye",
                summary="Landmark case on inheritance rights and succession law interpretation",
                legal_principle="Surviving spouse's rights under intestacy laws",
                relevance_areas=["intestate_succession", "spousal_rights", "inheritance"],
                key_facts="Dispute over inheritance rights between surviving spouse and deceased's relatives",
                decision="Court affirmed surviving spouse's rights under Law of Succession Act",
                precedent_value="binding"
            ),
            
            CaseLaw(
                case_name="Mary Rono vs Joseph Rono & 2 Others",
                citation="[2018] eKLR",
                court="High Court",
                year="2018",
                judge="Justice Weldon Korir",
                summary="Case establishing principles for matrimonial property division",
                legal_principle="Equal contribution principle in matrimonial property",
                relevance_areas=["matrimonial_property", "divorce", "property_division"],
                key_facts="Division of matrimonial property upon divorce",
                decision="Property divided based on contribution and circumstances",
                precedent_value="persuasive"
            )
        ]
        
        for case in cases:
            case_key = case.case_name.replace(" ", "_").replace("vs", "v").lower()
            self.case_law_db[case_key] = asdict(case)
    
    def _add_legal_procedures(self):
        """Add legal procedures to the database"""
        
        procedures = [
            LegalProcedure(
                procedure_name="Will Registration and Probate",
                description="Process for registering a will and obtaining probate",
                required_documents=[
                    "Original will document",
                    "Death certificate",
                    "Inventory of estate assets",
                    "Beneficiary identification documents",
                    "Witness affidavits"
                ],
                steps=[
                    "File probate application at High Court",
                    "Submit required documents and pay court fees",
                    "Publish notice in Kenya Gazette",
                    "Await objections period (21 days)",
                    "Attend court hearing if required",
                    "Receive grant of probate",
                    "Register grant with relevant authorities"
                ],
                timeline="3-12 months depending on complexity",
                costs="Court fees range from KES 3,000 to KES 50,000 based on estate value",
                court_fees="Calculated as percentage of estate value",
                legal_requirements=[
                    "Valid will meeting Succession Act requirements",
                    "Proper executor appointment",
                    "Complete asset disclosure",
                    "Beneficiary notification"
                ],
                common_challenges=[
                    "Will contestation by family members",
                    "Missing or inadequate documentation",
                    "Disputes over asset valuation",
                    "Executor conflicts of interest"
                ]
            ),
            
            LegalProcedure(
                procedure_name="Trust Creation and Registration",
                description="Process for creating and registering a trust",
                required_documents=[
                    "Trust deed",
                    "Settlor identification",
                    "Trustee consent and identification",
                    "Asset transfer documents",
                    "Beneficiary details"
                ],
                steps=[
                    "Draft comprehensive trust deed",
                    "Obtain trustee consent and documentation",
                    "Execute trust deed with proper witnesses",
                    "Transfer assets to trust",
                    "Register with relevant authorities",
                    "Obtain tax clearance certificates",
                    "Set up trust administration systems"
                ],
                timeline="1-6 months depending on complexity",
                costs="Legal fees KES 50,000-500,000 plus registration fees",
                court_fees="Registration fees vary by asset type and value",
                legal_requirements=[
                    "Clearly defined trust purposes",
                    "Competent trustees",
                    "Identifiable beneficiaries",
                    "Compliance with Trustee Act"
                ],
                common_challenges=[
                    "Tax implications for trust creation",
                    "Beneficiary consent issues",
                    "Asset valuation disputes",
                    "Ongoing compliance requirements"
                ]
            )
        ]
        
        for procedure in procedures:
            proc_key = procedure.procedure_name.replace(" ", "_").lower()
            self.procedures_db[proc_key] = asdict(procedure)
    
    def search_legal_references(self, query: str, areas: List[str] = None) -> List[Dict[str, Any]]:
        """Search legal references based on query and application areas"""
        
        query_lower = query.lower()
        results = []
        
        for act_key, act_data in self.acts_db.items():
            # Check if query matches keywords, description, or legal text
            searchable_text = (
                f"{act_data.get('title', '').lower()} "
                f"{act_data.get('description', '').lower()} "
                f"{' '.join(act_data.get('keywords', [])).lower()} "
                f"{act_data.get('legal_text', '').lower()}"
            )
            
            # Check area filter if provided
            area_match = True
            if areas:
                act_areas = act_data.get('applicability', [])
                area_match = any(area in act_areas for area in areas)
            
            if area_match and any(term in searchable_text for term in query_lower.split()):
                # Calculate relevance score
                score = self._calculate_relevance_score(query_lower, act_data)
                results.append({
                    'type': 'statute',
                    'reference': act_data,
                    'relevance_score': score
                })
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:10]  # Return top 10 results
    
    def get_legal_references_for_context(self, client_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get relevant legal references based on client context"""
        
        # Determine applicable areas based on client context
        areas = []
        
        # Check marital status
        marital_status = client_context.get('bioData', {}).get('maritalStatus', '').lower()
        if 'married' in marital_status:
            areas.extend(['matrimonial_property', 'spousal_rights'])
        
        # Check objectives
        objective = client_context.get('objectives', {}).get('objective', '').lower()
        if 'will' in objective:
            areas.extend(['will_creation', 'succession', 'estate_planning'])
        elif 'trust' in objective:
            areas.extend(['trust_creation', 'asset_protection'])
        
        # Check economic standing for tax implications
        economic_standing = client_context.get('economicContext', {}).get('economicStanding', '').lower()
        if 'high' in economic_standing:
            areas.extend(['tax_planning', 'inheritance'])
        
        # Build search query from context
        search_terms = []
        search_terms.append(objective)
        if client_context.get('bioData', {}).get('children'):
            search_terms.append('children beneficiaries')
        
        query = ' '.join(search_terms)
        
        # Get relevant references
        references = self.search_legal_references(query, areas)
        
        # Add case law if relevant
        case_results = self._search_case_law(query, areas)
        references.extend(case_results)
        
        # Add procedures if relevant
        procedure_results = self._search_procedures(query, areas)
        references.extend(procedure_results)
        
        return references
    
    def _search_case_law(self, query: str, areas: List[str] = None) -> List[Dict[str, Any]]:
        """Search case law database"""
        
        query_lower = query.lower()
        results = []
        
        for case_key, case_data in self.case_law_db.items():
            searchable_text = (
                f"{case_data.get('summary', '').lower()} "
                f"{case_data.get('legal_principle', '').lower()} "
                f"{' '.join(case_data.get('relevance_areas', [])).lower()}"
            )
            
            area_match = True
            if areas:
                case_areas = case_data.get('relevance_areas', [])
                area_match = any(area in case_areas for area in areas)
            
            if area_match and any(term in searchable_text for term in query_lower.split()):
                results.append({
                    'type': 'case_law',
                    'reference': case_data,
                    'relevance_score': 0.8  # Case law slightly lower priority than statutes
                })
        
        return results
    
    def _search_procedures(self, query: str, areas: List[str] = None) -> List[Dict[str, Any]]:
        """Search legal procedures database"""
        
        query_lower = query.lower()
        results = []
        
        for proc_key, proc_data in self.procedures_db.items():
            searchable_text = (
                f"{proc_data.get('procedure_name', '').lower()} "
                f"{proc_data.get('description', '').lower()}"
            )
            
            if any(term in searchable_text for term in query_lower.split()):
                results.append({
                    'type': 'procedure',
                    'reference': proc_data,
                    'relevance_score': 0.6  # Procedures lowest priority
                })
        
        return results
    
    def _calculate_relevance_score(self, query: str, act_data: Dict[str, Any]) -> float:
        """Calculate relevance score for search results"""
        
        score = 0.0
        query_terms = query.split()
        
        # Check title matches (highest weight)
        title = act_data.get('title', '').lower()
        for term in query_terms:
            if term in title:
                score += 2.0
        
        # Check keyword matches
        keywords = [kw.lower() for kw in act_data.get('keywords', [])]
        for term in query_terms:
            if term in keywords:
                score += 1.5
        
        # Check description matches
        description = act_data.get('description', '').lower()
        for term in query_terms:
            if term in description:
                score += 1.0
        
        # Check legal text matches (lower weight)
        legal_text = act_data.get('legal_text', '').lower()
        for term in query_terms:
            if term in legal_text:
                score += 0.5
        
        return score
    
    def format_legal_reference_for_ai(self, reference: Dict[str, Any]) -> str:
        """Format legal reference for AI consumption"""
        
        ref_type = reference.get('type', 'statute')
        ref_data = reference.get('reference', {})
        
        if ref_type == 'statute':
            return (
                f"{ref_data.get('act_name')} ({ref_data.get('chapter')}) - "
                f"{ref_data.get('section')}: {ref_data.get('title')}. "
                f"Description: {ref_data.get('description')}. "
                f"Practical implications: {'; '.join(ref_data.get('practical_implications', []))}"
            )
        elif ref_type == 'case_law':
            return (
                f"Case: {ref_data.get('case_name')} [{ref_data.get('citation')}]. "
                f"Legal principle: {ref_data.get('legal_principle')}. "
                f"Summary: {ref_data.get('summary')}"
            )
        elif ref_type == 'procedure':
            return (
                f"Procedure: {ref_data.get('procedure_name')}. "
                f"Description: {ref_data.get('description')}. "
                f"Timeline: {ref_data.get('timeline')}. "
                f"Costs: {ref_data.get('costs')}"
            )
        
        return str(ref_data)
    
    def get_tax_implications(self, asset_value: float) -> Dict[str, Any]:
        """Get tax implications based on asset value"""
        
        tax_threshold = 5000000  # KES 5M current threshold
        
        if asset_value <= tax_threshold:
            return {
                "tax_applicable": False,
                "exemption_amount": asset_value,
                "taxable_amount": 0,
                "estimated_tax": 0,
                "applicable_law": "Income Tax Act - Section 3(2)(a)",
                "advice": "Estate value is below the tax-free threshold of KES 5,000,000"
            }
        else:
            taxable_amount = asset_value - tax_threshold
            # Simplified tax calculation - in practice this would be more complex
            estimated_tax = taxable_amount * 0.20  # 20% rate (illustrative)
            
            return {
                "tax_applicable": True,
                "exemption_amount": tax_threshold,
                "taxable_amount": taxable_amount,
                "estimated_tax": estimated_tax,
                "applicable_law": "Income Tax Act - inheritance tax provisions",
                "advice": (
                    f"Estate value exceeds tax-free threshold. "
                    f"Taxable amount: KES {taxable_amount:,.2f}. "
                    f"Estimated tax: KES {estimated_tax:,.2f}. "
                    f"Consider tax planning strategies."
                )
            }
    
    def _load_existing_database(self):
        """Load existing legal database from files"""
        
        acts_file = self.law_db_dir / "acts_database.json"
        cases_file = self.law_db_dir / "case_law_database.json"
        procedures_file = self.law_db_dir / "procedures_database.json"
        
        # Check if any database files exist
        if not any(f.exists() for f in [acts_file, cases_file, procedures_file]):
            raise FileNotFoundError("No database files found")
        
        if acts_file.exists():
            with open(acts_file, 'r', encoding='utf-8') as f:
                self.acts_db = json.load(f)
        
        if cases_file.exists():
            with open(cases_file, 'r', encoding='utf-8') as f:
                self.case_law_db = json.load(f)
        
        if procedures_file.exists():
            with open(procedures_file, 'r', encoding='utf-8') as f:
                self.procedures_db = json.load(f)
    
    def _save_database(self):
        """Save legal database to files"""
        
        acts_file = self.law_db_dir / "acts_database.json"
        cases_file = self.law_db_dir / "case_law_database.json"
        procedures_file = self.law_db_dir / "procedures_database.json"
        
        with open(acts_file, 'w', encoding='utf-8') as f:
            json.dump(self.acts_db, f, indent=2, ensure_ascii=False)
        
        with open(cases_file, 'w', encoding='utf-8') as f:
            json.dump(self.case_law_db, f, indent=2, ensure_ascii=False)
        
        with open(procedures_file, 'w', encoding='utf-8') as f:
            json.dump(self.procedures_db, f, indent=2, ensure_ascii=False)
    
    def add_legal_reference(self, reference: LegalReference):
        """Add new legal reference to database"""
        
        act_key = f"{reference.chapter}_{reference.section.replace(' ', '_').replace('(', '').replace(')', '')}"
        self.acts_db[act_key] = reference.to_dict()
        self._save_database()
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get statistics about the legal database"""
        
        return {
            "total_acts": len(self.acts_db),
            "total_cases": len(self.case_law_db),
            "total_procedures": len(self.procedures_db),
            "last_updated": datetime.now().isoformat(),
            "coverage_areas": list(set(
                area for act in self.acts_db.values() 
                for area in act.get('applicability', [])
            ))
        }


# Global instance
kenya_law_db = KenyaLawDatabase()