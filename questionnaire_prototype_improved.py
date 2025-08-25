import streamlit as st
import pandas as pd
import os
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import re

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def safe_import_cerebras():
    """Safely import Cerebras SDK with fallback handling."""
    try:
        from cerebras.cloud.sdk import Cerebras
        return Cerebras
    except ImportError:
        logger.info("Cerebras SDK not available; AI calls will fallback to mock.")
        return None
    except Exception as e:
        logger.error(f"Error importing Cerebras SDK: {e}")
        return None


def generate_client_id(full_name: str) -> str:
    """Generate a unique client ID from full name and timestamp."""
    # Create a unique identifier
    unique_string = f"{full_name.lower().replace(' ', '_')}_{int(time.time())}"
    # Generate short hash for uniqueness
    hash_obj = hashlib.md5(unique_string.encode())
    return f"client_{hash_obj.hexdigest()[:8]}"


def validate_client_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate client data and return validation status and error list."""
    errors = []
    
    # Required fields validation
    if not data.get('Name', '').strip():
        errors.append("Full name is required and cannot be empty")
    
    # Name format validation
    name = data.get('Name', '').strip()
    if name and not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
        errors.append("Full name contains invalid characters")
    
    # Marital status specific validation
    if data.get('Marital') == 'Married':
        if not data.get('SpouseName', '').strip():
            errors.append("Spouse name is required when marital status is 'Married'")
        if not data.get('SpouseID', '').strip():
            errors.append("Spouse ID is required when marital status is 'Married'")
    
    # Asset validation
    assets = data.get('Assets', [])
    total_asset_value = 0
    for i, asset in enumerate(assets):
        if not asset.get('Type'):
            errors.append(f"Asset {i+1}: Type is required")
        if not asset.get('Description', '').strip():
            errors.append(f"Asset {i+1}: Description is required")
        
        try:
            value = float(asset.get('Value (KES)', 0))
            if value < 0:
                errors.append(f"Asset {i+1}: Value cannot be negative")
            total_asset_value += value
        except (ValueError, TypeError):
            errors.append(f"Asset {i+1}: Invalid value format")
    
    # Objective validation
    if not data.get('Objective'):
        errors.append("Primary objective is required")
    
    return len(errors) == 0, errors


def sanitize_input(text: str) -> str:
    """Sanitize text input to prevent basic injection attacks."""
    if not isinstance(text, str):
        return ""
    
    # Remove potential script tags and suspicious patterns
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    # Limit length to prevent DoS
    return text[:5000]


def save_client_data(data: Dict[str, Any], client_id: str = None) -> Tuple[bool, str]:
    """Save client data to individual client file with improved error handling."""
    try:
        # Generate client ID if not provided
        if not client_id:
            client_id = generate_client_id(data.get('Name', 'unknown'))
        
        # Ensure data directory exists
        data_dir = os.getenv("DATA_DIR", "data")
        clients_dir = os.path.join(data_dir, "clients")
        os.makedirs(clients_dir, exist_ok=True)
        
        # Create unique file path
        file_path = os.path.join(clients_dir, f"{client_id}.json")
        
        # Add metadata
        data_with_metadata = {
            **data,
            "clientId": client_id,
            "savedAt": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Atomic write operation using temporary file
        temp_path = f"{file_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data_with_metadata, f, ensure_ascii=False, indent=2)
        
        # Rename temp file to actual file (atomic operation)
        os.rename(temp_path, file_path)
        
        logger.info(f"Client data saved successfully: {client_id}")
        return True, client_id
        
    except PermissionError:
        error_msg = "Permission denied: Cannot write to data directory"
        logger.error(error_msg)
        return False, error_msg
    except OSError as e:
        error_msg = f"File system error: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error saving data: {e}"
        logger.exception(error_msg)
        return False, error_msg


def build_enhanced_prompt(input_data: Dict[str, Any], distribution_prefs: str) -> str:
    """Build enhanced AI prompt with better structure and validation."""
    # Validate input data
    if not input_data:
        return "Invalid input data provided"
    
    # Calculate total asset value
    assets = input_data.get('Assets', [])
    total_value = sum(asset.get('Value (KES)', 0) for asset in assets)
    
    # Build structured prompt
    prompt_parts = [
        "You are a legal information assistant specializing in Kenyan law.",
        f"Client Information: {input_data.get('Name', 'Unknown')} ({input_data.get('Marital', 'Unknown')} status)",
        f"Primary Objective: {input_data.get('Objective', 'Not specified')}",
        f"Total Asset Value: KES {total_value:,.2f}",
        f"Distribution Preferences: {distribution_prefs or 'Not specified'}",
        "",
        "Based on Kenyan law, particularly the Succession Act (Cap 160), provide:",
        "1. Relevant legal options for the stated objective",
        "2. Potential legal consequences and considerations", 
        "3. Tax implications (inheritance tax threshold: KES 5,000,000)",
        "4. Required legal procedures and documentation",
        "",
        "IMPORTANT: Provide informational guidance only. This does not constitute legal advice.",
        "Always recommend consulting with a qualified legal practitioner.",
        "",
        f"Context: {mock_kenya_law_search(input_data.get('Objective', ''))}"
    ]
    
    return "\n".join(prompt_parts)


def mock_kenya_law_search(query: str) -> str:
    """Enhanced mock search for Kenya Law with more detailed information."""
    query_lower = query.lower()
    
    if 'will' in query_lower:
        return ("Succession Act (Cap 160): Wills must be in writing, signed by testator, "
                "witnessed by two independent witnesses. Probate required. "
                "Tax-free threshold: KES 5,000,000.")
    elif 'trust' in query_lower:
        return ("Trustee Act (Cap 167): Trusts require written trust deed, "
                "appointment of trustees, clear beneficiary designation. "
                "Registration may be required for certain assets.")
    elif 'sell' in query_lower or 'transfer' in query_lower:
        return ("Transfer of Property Act: Requires proper documentation, "
                "stamp duty payment, registration with relevant authorities. "
                "Capital gains tax may apply.")
    else:
        return ("General Kenya Law: Consult Succession Act (Cap 160), "
                "Registration of Documents Act, and relevant statutes. "
                "Professional legal advice recommended.")


def get_fallback_response(objective: str) -> str:
    """Provide enhanced fallback response when AI is unavailable."""
    base_response = (
        "Legal Information (System Generated):\n\n"
        f"For your objective '{objective}', here are key considerations under Kenyan law:\n\n"
    )
    
    if 'will' in objective.lower():
        base_response += (
            "• Will Creation: Must comply with Succession Act (Cap 160)\n"
            "• Requirements: Written document, testator signature, two independent witnesses\n"
            "• Tax Implications: Inheritance tax applies if estate value exceeds KES 5,000,000\n"
            "• Process: Probate application required after death\n"
            "• Timeline: 3-12 months depending on complexity\n\n"
        )
    elif 'trust' in objective.lower():
        base_response += (
            "• Trust Creation: Governed by Trustee Act (Cap 167)\n"
            "• Requirements: Written trust deed, trustee appointment, beneficiary designation\n"
            "• Benefits: Asset protection, tax planning, succession planning\n"
            "• Registration: Required for certain types of assets\n"
            "• Management: Ongoing trustee duties and compliance\n\n"
        )
    else:
        base_response += (
            "• Legal Framework: Multiple statutes may apply\n"
            "• Documentation: Proper legal documentation required\n"
            "• Compliance: Must adhere to Kenyan legal requirements\n"
            "• Professional Advice: Strongly recommended\n\n"
        )
    
    base_response += (
        "⚠️ IMPORTANT: This information is for educational purposes only. "
        "Please consult with a qualified legal practitioner for specific legal advice."
    )
    
    return base_response


def init_user_session():
    """Initialize user-specific session state with proper isolation."""
    required_keys = [
        'logged_in', 'current_user', 'login_attempts', 'last_login',
        'form_errors', 'client_id', 'last_save_time'
    ]
    
    for key in required_keys:
        if key not in st.session_state:
            if key == 'logged_in':
                st.session_state[key] = False
            elif key == 'login_attempts':
                st.session_state[key] = 0
            elif key == 'form_errors':
                st.session_state[key] = []
            else:
                st.session_state[key] = None


def get_user_assets_key() -> str:
    """Get user-specific assets key for session isolation."""
    user = st.session_state.get('current_user', 'anonymous')
    return f"assets_{user}"


def init_user_assets():
    """Initialize user-specific assets dataframe."""
    assets_key = get_user_assets_key()
    if assets_key not in st.session_state:
        st.session_state[assets_key] = pd.DataFrame(
            columns=["Type", "Description", "Value (KES)"]
        )


def enhanced_login_widget():
    """Enhanced login widget with basic security features."""
    st.header("🏛️ HNC Legal Services - Secure Login")
    
    # Check login attempts
    if st.session_state.get('login_attempts', 0) >= 5:
        st.error("⚠️ Too many failed login attempts. Please contact administrator.")
        return False
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # Basic validation (in production, use proper authentication)
            username = sanitize_input(username)
            
            if len(username) < 3:
                st.error("Username must be at least 3 characters")
                return False
            
            if len(password) < 6:
                st.error("Password must be at least 6 characters")
                return False
            
            # Mock authentication (replace with real auth in production)
            if username and password:
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.session_state.last_login = datetime.now()
                st.session_state.login_attempts = 0
                logger.info(f"User logged in: {username}")
                st.rerun()
            else:
                st.session_state.login_attempts = st.session_state.get('login_attempts', 0) + 1
                st.error("Invalid credentials")
                return False
    
    return st.session_state.get('logged_in', False)


def display_form_errors(errors: List[str]):
    """Display form validation errors in a user-friendly way."""
    if errors:
        st.error("Please correct the following errors:")
        for error in errors:
            st.error(f"• {error}")


def auto_save_form_data(data: Dict[str, Any]):
    """Auto-save form data to prevent data loss."""
    try:
        auto_save_dir = os.path.join(os.getenv("DATA_DIR", "data"), "auto_save")
        os.makedirs(auto_save_dir, exist_ok=True)
        
        user = st.session_state.get('current_user', 'anonymous')
        file_path = os.path.join(auto_save_dir, f"{user}_autosave.json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        st.session_state.last_save_time = datetime.now()
        
    except Exception as e:
        logger.error(f"Auto-save failed: {e}")


def main():
    """Main application function with improved structure and error handling."""
    # Page configuration
    st.set_page_config(
        page_title="HNC Legal Questionnaire",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session
    init_user_session()
    
    # Authentication check
    if not st.session_state.get('logged_in', False):
        enhanced_login_widget()
        return
    
    # Initialize user-specific data
    init_user_assets()
    assets_key = get_user_assets_key()
    
    # Sidebar
    with st.sidebar:
        st.title("🏛️ HNC Legal Services")
        st.write(f"👤 Logged in as: {st.session_state.get('current_user')}")
        st.write(f"🕒 Login time: {st.session_state.get('last_login', 'Unknown')}")
        
        if st.button("🚪 Logout", type="secondary"):
            # Clear user session
            keys_to_clear = [k for k in st.session_state.keys() if k.startswith(f"assets_{st.session_state.get('current_user')}")]
            for key in keys_to_clear:
                del st.session_state[key]
            
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()
        
        # Auto-save indicator
        if st.session_state.get('last_save_time'):
            st.caption(f"Last auto-save: {st.session_state.last_save_time.strftime('%H:%M:%S')}")
    
    # Main content
    st.title("📋 Comprehensive Legal Questionnaire")
    st.markdown("Please provide accurate information for legal consultation and document preparation.")
    
    # Display any form errors
    display_form_errors(st.session_state.get('form_errors', []))
    
    # Form sections
    with st.form("client_questionnaire", clear_on_submit=False):
        # --- Section 1: Client Bio Data ---
        st.header("1. 👤 Client Information")
        
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input(
                "Full Name *", 
                key="name",
                help="Enter your complete legal name as it appears on official documents"
            )
            date_of_birth = st.date_input(
                "Date of Birth",
                key="dob",
                help="Your date of birth for identification purposes"
            )
            id_number = st.text_input(
                "ID/Passport Number",
                key="id_number",
                help="National ID or passport number"
            )
        
        with col2:
            marital_status = st.selectbox(
                "Marital Status *",
                ["Single", "Married", "Divorced", "Widowed"],
                key="marital",
                help="Your current marital status"
            )
            
            # Conditional spouse information
            spouse_name = ""
            spouse_id = ""
            if marital_status == "Married":
                spouse_name = st.text_input(
                    "Spouse Name *",
                    key="spouse_name",
                    help="Full name of your spouse"
                )
                spouse_id = st.text_input(
                    "Spouse ID Number *",
                    key="spouse_id",
                    help="Your spouse's ID or passport number"
                )
        
        children = st.text_area(
            "Children's Details",
            key="children",
            help="List children's names, ages, and relationships (one per line)",
            placeholder="Example:\nJohn Doe, 25, Son\nJane Doe, 22, Daughter"
        )
        
        # --- Section 2: Financial Information ---
        st.header("2. 💰 Financial Information")
        
        st.subheader("Assets")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            asset_type = st.selectbox(
                "Asset Type",
                ["Real Estate", "Bank Account", "Shares", "Business", "Vehicle", "Investment", "Other"],
                key="asset_type"
            )
        
        with col2:
            asset_desc = st.text_input(
                "Description",
                key="asset_desc",
                help="Brief description of the asset"
            )
        
        with col3:
            asset_value = st.number_input(
                "Estimated Value (KES)",
                min_value=0,
                key="asset_value",
                help="Current estimated value in Kenyan Shillings"
            )
        
        # Asset management buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            add_asset = st.form_submit_button("➕ Add Asset", type="secondary")
        with col2:
            clear_assets = st.form_submit_button("🗑️ Clear All", type="secondary")
        
        # Handle asset operations
        if add_asset and asset_desc and asset_value >= 0:
            new_row = pd.DataFrame({
                "Type": [asset_type],
                "Description": [asset_desc],
                "Value (KES)": [asset_value]
            })
            st.session_state[assets_key] = pd.concat([st.session_state[assets_key], new_row], ignore_index=True)
            st.rerun()
        
        if clear_assets:
            st.session_state[assets_key] = pd.DataFrame(columns=["Type", "Description", "Value (KES)"])
            st.rerun()
        
        # Display assets table
        if not st.session_state[assets_key].empty:
            st.subheader("📊 Your Assets")
            st.dataframe(st.session_state[assets_key], use_container_width=True)
            
            total_value = st.session_state[assets_key]["Value (KES)"].sum()
            st.metric("Total Asset Value", f"KES {total_value:,.2f}")
            
            if total_value > 5000000:
                st.warning("⚠️ Your estate value exceeds KES 5,000,000. Inheritance tax may apply.")
        
        # Liabilities and Income
        st.subheader("Liabilities and Income")
        col1, col2 = st.columns(2)
        
        with col1:
            liabilities = st.text_area(
                "Liabilities",
                key="liabilities",
                help="List debts, loans, and other liabilities",
                placeholder="Example:\nHome Loan - KES 2,000,000 - ABC Bank\nCar Loan - KES 500,000 - XYZ Bank"
            )
        
        with col2:
            income_sources = st.text_area(
                "Income Sources",
                key="income_sources",
                help="List your sources of income",
                placeholder="Example:\nSalary - KES 100,000/month - ABC Company\nRental Income - KES 50,000/month"
            )
        
        # --- Section 3: Economic Context ---
        st.header("3. 📈 Economic Context")
        
        col1, col2 = st.columns(2)
        with col1:
            economic_standing = st.selectbox(
                "Economic Standing",
                ["High Net Worth", "Upper Middle Income", "Middle Income", "Lower Middle Income", "Low Income"],
                key="economic",
                help="Your overall economic classification"
            )
        
        with col2:
            annual_income = st.number_input(
                "Annual Income (KES)",
                min_value=0,
                key="annual_income",
                help="Your total annual income from all sources"
            )
        
        distribution_prefs = st.text_area(
            "Asset Distribution Preferences",
            key="distribution_prefs",
            help="Describe how you would like your assets distributed",
            placeholder="Example: 50% to spouse, 50% equally among children"
        )
        
        # --- Section 4: Legal Objectives ---
        st.header("4. ⚖️ Legal Objectives")
        
        col1, col2 = st.columns(2)
        with col1:
            objective = st.selectbox(
                "Primary Objective *",
                [
                    "Create Will",
                    "Create Living Will",
                    "Create Trust",
                    "Business Succession Planning",
                    "Asset Transfer",
                    "Estate Planning",
                    "Other"
                ],
                key="objective",
                help="Select your primary legal objective"
            )
        
        with col2:
            urgency = st.selectbox(
                "Urgency Level",
                ["Low", "Medium", "High", "Critical"],
                key="urgency",
                help="How urgent is this matter?"
            )
        
        objective_details = st.text_area(
            "Objective Details",
            key="objective_details",
            help="Provide additional details about your objectives and specific requirements",
            placeholder="Please describe your specific goals, concerns, and any special circumstances..."
        )
        
        # --- Section 5: Additional Information ---
        st.header("5. 📝 Additional Information")
        
        special_circumstances = st.text_area(
            "Special Circumstances",
            key="special_circumstances",
            help="Any special circumstances, health issues, or unique situations",
            placeholder="Example: Health concerns, family disputes, business complexities, etc."
        )
        
        lawyer_notes = st.text_area(
            "Additional Notes",
            key="lawyer_notes",
            help="Any other information you think is relevant"
        )
        
        # --- AI Analysis Section ---
        st.header("6. 🤖 Legal Analysis")
        
        generate_analysis = st.form_submit_button(
            "🔍 Generate Legal Analysis",
            type="secondary"
        )
        
        # --- Form Submission ---
        st.header("7. 📤 Submit Information")
        
        submitted = st.form_submit_button(
            "📋 Submit for Legal Consultation",
            type="primary"
        )
    
    # Handle AI analysis generation
    if generate_analysis:
        if not full_name:
            st.error("Please provide your full name before generating analysis.")
        else:
            with st.spinner("Generating legal analysis..."):
                # Prepare data for analysis
                analysis_data = {
                    "Name": sanitize_input(full_name),
                    "Marital": marital_status,
                    "Assets": st.session_state[assets_key].to_dict(orient="records"),
                    "Economic": economic_standing,
                    "Objective": objective,
                    "Details": sanitize_input(objective_details)
                }
                
                # Generate AI analysis
                Cerebras = safe_import_cerebras()
                api_key = os.environ.get("CEREBRAS_API_KEY")
                
                if Cerebras and api_key:
                    try:
                        client = Cerebras(api_key=api_key)
                        prompt = build_enhanced_prompt(analysis_data, distribution_prefs)
                        
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="gpt-oss-120b",
                            max_tokens=500,
                            temperature=0.7,
                        )
                        
                        response = chat_completion.choices[0].message.content
                        
                        st.success("🎯 AI Legal Analysis Complete")
                        st.markdown("### 📋 Analysis Results")
                        st.markdown(response)
                        
                    except Exception as e:
                        st.error(f"AI Analysis Error: {str(e)}")
                        st.markdown("### 📋 Fallback Legal Information")
                        st.markdown(get_fallback_response(objective))
                else:
                    st.info("🤖 AI service unavailable. Showing standard legal information.")
                    st.markdown("### 📋 Legal Information")
                    st.markdown(get_fallback_response(objective))
    
    # Handle form submission
    if submitted:
        # Collect all form data
        form_data = {
            "Name": sanitize_input(full_name),
            "DateOfBirth": str(date_of_birth) if 'date_of_birth' in locals() else "",
            "IDNumber": sanitize_input(id_number) if 'id_number' in locals() else "",
            "Marital": marital_status,
            "SpouseName": sanitize_input(spouse_name),
            "SpouseID": sanitize_input(spouse_id),
            "Children": sanitize_input(children),
            "Assets": st.session_state[assets_key].to_dict(orient="records"),
            "Liabilities": sanitize_input(liabilities),
            "Income": sanitize_input(income_sources),
            "AnnualIncome": annual_income if 'annual_income' in locals() else 0,
            "Economic": economic_standing,
            "DistributionPrefs": sanitize_input(distribution_prefs),
            "Objective": objective,
            "ObjectiveDetails": sanitize_input(objective_details),
            "Urgency": urgency if 'urgency' in locals() else "Medium",
            "SpecialCircumstances": sanitize_input(special_circumstances) if 'special_circumstances' in locals() else "",
            "LawyerNotes": sanitize_input(lawyer_notes),
            "SubmittedBy": st.session_state.get('current_user', 'unknown'),
        }
        
        # Validate form data
        is_valid, validation_errors = validate_client_data(form_data)
        
        if not is_valid:
            st.session_state.form_errors = validation_errors
            st.rerun()
        else:
            # Clear previous errors
            st.session_state.form_errors = []
            
            # Save client data
            success, result = save_client_data(form_data)
            
            if success:
                st.session_state.client_id = result
                st.success(f"✅ Information submitted successfully! Client ID: {result}")
                st.balloons()
                
                # Show summary
                with st.expander("📋 Submission Summary", expanded=True):
                    total_assets = sum(asset.get('Value (KES)', 0) for asset in form_data['Assets'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Client", form_data['Name'])
                    with col2:
                        st.metric("Total Assets", f"KES {total_assets:,.2f}")
                    with col3:
                        st.metric("Primary Objective", form_data['Objective'])
                    
                    st.info("📧 A legal practitioner will review your information and contact you within 2-3 business days.")
                
            else:
                st.error(f"❌ Failed to save information: {result}")
                st.error("Please try again or contact support if the problem persists.")


if __name__ == "__main__":
    main()