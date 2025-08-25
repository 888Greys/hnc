import streamlit as st
import pandas as pd
import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Tuple, Optional
# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)


def load_css():
    """Load custom CSS for enhanced UI/UX"""
    css_file = os.path.join(os.path.dirname(__file__), "static", "style.css")
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        # Fallback inline CSS
        st.markdown("""
        <style>
        .main { font-family: 'Inter', sans-serif; }
        .stButton > button { border-radius: 8px; transition: all 0.2s ease; }
        .stButton > button[kind="primary"] { background: linear-gradient(135deg, #3b82f6, #2563eb); }
        .streamlit-expanderHeader { font-weight: 600; padding: 1rem; }
        .stAlert { border-radius: 8px; }
        hr { background: linear-gradient(90deg, transparent, #e5e7eb, transparent); height: 2px; border: none; }
        </style>
        """, unsafe_allow_html=True)


def display_header():
    """Display enhanced header with branding"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); margin: -1rem -1rem 2rem -1rem; border-radius: 0 0 16px 16px;">
        <h1 style="color: #1f2937; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">📋 HNC Legal Questionnaire</h1>
        <p style="color: #6b7280; font-size: 1.1rem; margin: 0;">Professional Client Data Collection System</p>
    </div>
    """, unsafe_allow_html=True)


def safe_import_cerebras():
    try:
        from cerebras.cloud.sdk import Cerebras

        return Cerebras
    except Exception:
        logging.info("Cerebras SDK not available; AI calls will fallback to mock.")
        return None


def fallback_mock():
    return (
        "AI Suggestion (Mock): Based on Kenya Law (Succession Act Cap 160), for a Will: "
        "Direct transfer to heirs; consequences include potential inheritance tax if value > KES 5M, probate required."
    )


def mock_kenya_law_search(query: str) -> str:
    # Mock search for Kenya Law - replace with real requests.get() and BeautifulSoup in prod
    return f"Mock Kenya Law Data: {query} - Succession Act Cap 160: Wills require probate, tax-free threshold KES 5M."


def generate_client_id(name: str) -> str:
    """Generate unique client ID based on name and timestamp"""
    return f"client_{hashlib.md5(f'{name}_{time.time()}'.encode()).hexdigest()[:8]}"


def validate_client_data(data: dict) -> Tuple[bool, List[str]]:
    """Validate client data and return validation status and error list"""
    errors = []
    
    # Required field validation
    if not data.get('Name', '').strip():
        errors.append("Full name is required")
    
    # Marital status specific validation
    if data.get('Marital') == 'Married':
        if not data.get('SpouseName', '').strip():
            errors.append("Spouse name is required for married status")
        if not data.get('SpouseID', '').strip():
            errors.append("Spouse ID is required for married status")
    
    # Financial data validation
    if not data.get('Assets') or len(data.get('Assets', [])) == 0:
        errors.append("At least one asset must be specified")
    
    # Objective validation
    if not data.get('Objective', '').strip():
        errors.append("Primary objective is required")
    
    return len(errors) == 0, errors


def init_user_session(user_id: str):
    """Initialize user-specific session data"""
    session_key = f"user_{user_id}"
    if session_key not in st.session_state:
        st.session_state[session_key] = {
            'assets': pd.DataFrame(columns=["Type", "Description", "Value (KES)"]),
            'form_data': {},
            'client_id': None
        }
    return session_key


def get_user_session_data(user_id: str, key: str):
    """Get user-specific session data"""
    session_key = f"user_{user_id}"
    if session_key in st.session_state:
        return st.session_state[session_key].get(key)
    return None


def set_user_session_data(user_id: str, key: str, value):
    """Set user-specific session data"""
    session_key = f"user_{user_id}"
    if session_key not in st.session_state:
        init_user_session(user_id)
    st.session_state[session_key][key] = value


def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'login_history' not in st.session_state:
        st.session_state.login_history = []
    if 'assets' not in st.session_state:
        st.session_state.assets = pd.DataFrame(columns=["Type", "Description", "Value (KES)"])


def authenticate_user(username: str, password: str) -> Tuple[bool, str, str]:
    """Authenticate user with demo credentials (replace with proper auth in production)"""
    # Demo users - replace with proper authentication system
    demo_users = {
        "lawyer1": {"password": "demo123", "role": "lawyer"},
        "admin": {"password": "admin123", "role": "admin"},
        "clerk": {"password": "clerk123", "role": "clerk"}
    }
    
    if not username or not password:
        return False, "Username and password are required", ""
    
    user = demo_users.get(username.lower())
    if user and user["password"] == password:
        return True, "Login successful", user["role"]
    
    return False, "Invalid username or password", ""


def login_widget():
    st.header("HNC - Login")
    
    # Show demo credentials info
    with st.expander("Demo Credentials"):
        st.write("**Demo Users:**")
        st.write("- lawyer1 / demo123 (Lawyer role)")
        st.write("- admin / admin123 (Admin role)")
        st.write("- clerk / clerk123 (Clerk role)")
    
    username = st.text_input("Username", key="_username")
    password = st.text_input("Password", type="password", key="_password")
    
    if st.button("Login"):
        success, message, role = authenticate_user(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.current_user = {
                "username": username,
                "role": role,
                "login_time": str(pd.Timestamp.now())
            }
            st.session_state.login_history.append(f"Login: {username} ({role}) at {pd.Timestamp.now()}")
            
            # Initialize user session
            init_user_session(username)
            
            st.success(f"{message}. Welcome, {username} ({role})!")
            st.rerun()
        else:
            st.error(message)


def save_client_data(data: dict, client_id: str = None) -> Tuple[bool, str, str]:
    """Save client data with unique filename and proper error handling"""
    try:
        # Validate input data
        is_valid, errors = validate_client_data(data)
        if not is_valid:
            return False, f"Validation failed: {'; '.join(errors)}", ""
        
        # Generate unique client ID if not provided
        if not client_id:
            client_id = generate_client_id(data.get('Name', 'unknown'))
        
        # Use data directory for better Docker volume mounting
        data_dir = os.getenv("DATA_DIR", "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Create unique filename with client ID and timestamp
        timestamp = str(int(time.time()))
        filename = f"client_{client_id}_{timestamp}.json"
        path = os.path.join(data_dir, filename)
        
        # Add metadata to data
        data_with_metadata = {
            **data,
            "clientId": client_id,
            "fileName": filename,
            "savedAt": str(pd.Timestamp.now()),
            "version": "1.0"
        }
        
        # Atomic write operation
        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data_with_metadata, f, ensure_ascii=False, indent=2)
        
        # Move temp file to final location (atomic operation)
        os.rename(temp_path, path)
        
        logging.info(f"Client data saved successfully: {filename}")
        return True, f"Data saved successfully as {filename}", path
        
    except PermissionError as e:
        error_msg = f"Permission denied: Cannot write to data directory. {str(e)}"
        logging.error(error_msg)
        return False, error_msg, ""
    except OSError as e:
        error_msg = f"File system error: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, ""
    except json.JSONEncodeError as e:
        error_msg = f"Data serialization error: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, ""
    except Exception as e:
        error_msg = f"Unexpected error while saving data: {str(e)}"
        logging.exception(error_msg)
        return False, error_msg, ""


def build_prompt(input_data: dict, distribution_prefs: str) -> str:
    prompt = (
        f"Based on Kenya Law, particularly Succession Act Cap 160, suggest legal options and consequences "
        f"for {input_data.get('Objective')} with assets: {input_data.get('Assets')}. Include implications for distribution: "
        f"{distribution_prefs}. Reference specific statutes if applicable. Do not provide legal advice; "
        f"offer informational suggestions only. Keep it concise, accurate, and relevant to Kenyan law."
    )
    law_context = mock_kenya_law_search(input_data.get('Objective', ''))
    prompt += f"\nContext from Kenya Law: {law_context}"
    return prompt


def main():
    # Load custom CSS and display header
    load_css()
    
    init_session_state()

    Cerebras = safe_import_cerebras()

    if not st.session_state.logged_in:
        display_header()
        login_widget()
        return

    # Display header for logged-in users
    display_header()
    
    # Get current user info
    current_user = st.session_state.current_user
    username = current_user["username"]
    user_role = current_user["role"]
    
    # Initialize user-specific session
    session_key = init_user_session(username)
    
    # Get user-specific assets dataframe
    user_assets = get_user_session_data(username, 'assets')
    if user_assets is None:
        user_assets = pd.DataFrame(columns=["Type", "Description", "Value (KES)"])
        set_user_session_data(username, 'assets', user_assets)

    # Enhanced sidebar with user info
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1f2937, #374151); color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; text-align: center;">
            <h2 style="margin: 0; color: white;">💼 HNC Dashboard</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**👤 User:** {username}")
        st.markdown(f"**🎯 Role:** {user_role.title()}")
        st.markdown(f"**⏰ Login:** {current_user['login_time'][:16]}")
        
        st.markdown("---")
        
        # Progress indicator
        client_id = get_user_session_data(username, 'client_id')
        if client_id:
            st.markdown(f"**🎯 Current Client:** {client_id[:8]}...")
        
        if not user_assets.empty:
            total_value = user_assets["Value (KES)"].sum()
            st.metric("💰 Total Assets", f"KES {total_value:,.0f}")
        
        # Show recent login history
        if st.session_state.login_history:
            with st.expander("📅 Recent Activity"):
                for entry in st.session_state.login_history[-3:]:
                    st.write(f"• {entry}")

    # Welcome message with user context
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #dbeafe, #bfdbfe); padding: 1rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid #3b82f6;">
        <p style="margin: 0; color: #1e40af;"><strong>👋 Welcome back, {username}!</strong> Please complete the client questionnaire below.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Client Bio Data ---
    with st.expander("1. Client Bio Data", expanded=True):
        full_name = st.text_input("Full Name *", key="name", help="Required field")
        marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"], key="marital")
        spouse_name = ""
        spouse_id = ""
        if marital_status == "Married":
            spouse_name = st.text_input("Spouse Name *", key="spouse_name", help="Required for married status")
            spouse_id = st.text_input("Spouse ID Number *", key="spouse_id", help="Required for married status")
        children = st.text_area("Children's Details (Name, Age, Relationship - one per line)", key="children")

    # --- Financial Data ---
    with st.expander("2. Financial Data"):
        st.write("**Assets:**")
        
        # Asset input form
        col1, col2 = st.columns(2)
        with col1:
            asset_type = st.selectbox("Asset Type", ["Real Estate", "Bank Account", "Shares", "Business", "Investments", "Vehicle", "Other"], key="asset_type")
            asset_desc = st.text_input("Description", key="asset_desc", help="Provide detailed description")
        with col2:
            asset_value = st.number_input("Estimated Value (KES)", min_value=0, step=1000, key="asset_value")
            if asset_type == "Real Estate":
                asset_location = st.text_input("Location", key="asset_location")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Add Asset"):
                if asset_desc.strip() and asset_value > 0:
                    new_asset_data = {
                        "Type": asset_type, 
                        "Description": asset_desc, 
                        "Value (KES)": asset_value
                    }
                    if asset_type == "Real Estate" and 'asset_location' in st.session_state:
                        new_asset_data["Location"] = st.session_state.asset_location
                    
                    new_row = pd.DataFrame([new_asset_data])
                    user_assets = pd.concat([user_assets, new_row], ignore_index=True)
                    set_user_session_data(username, 'assets', user_assets)
                    st.success(f"Added {asset_type}: {asset_desc}")
                    st.rerun()
                else:
                    st.error("Please provide asset description and value > 0")
        
        with col2:
            if st.button("Clear Assets"):
                user_assets = pd.DataFrame(columns=["Type", "Description", "Value (KES)"])
                set_user_session_data(username, 'assets', user_assets)
                st.success("Assets cleared")
                st.rerun()
        
        with col3:
            if not user_assets.empty:
                total_value = user_assets["Value (KES)"].sum()
                st.metric("Total Assets", f"KES {total_value:,.0f}")
        
        # Display assets table
        if not user_assets.empty:
            st.dataframe(user_assets, use_container_width=True)
        else:
            st.info("No assets added yet. Please add at least one asset.")

        liabilities = st.text_area("Liabilities (Type, Amount, Creditor - one per line)", key="liabilities")
        income_sources = st.text_area("Income Sources (Type, Annual Amount KES - one per line)", key="income_sources")

    # --- Economic Context ---
    with st.expander("3. Economic Context"):
        economic_standing = st.selectbox("Economic Standing", ["High Net Worth", "Middle Income", "Low Income"], key="economic")
        distribution_prefs = st.text_area("Asset Distribution Preferences", key="distribution_prefs", help="Specify how you want your assets distributed")

    # --- Client Objectives ---
    with st.expander("4. Client Objectives"):
        objective = st.selectbox("Primary Objective *", ["Create Will", "Create Living Will", "Create Share Transfer Will", "Create Trust", "Sell Asset", "Other"], key="objective", help="Required field")
        objective_details = st.text_area("Details", key="objective_details", help="Provide specific details about your objectives")

    # --- Options & Consequences ---
    with st.expander("5. Options & Consequences"):
        lawyer_notes = st.text_area("Lawyer Notes", key="lawyer_notes", help="Additional notes from lawyer consultation")
        
        col1, col2 = st.columns(2)
        with col1:
            generate_button = st.button("Generate AI Options", type="primary")
        with col2:
            if not user_assets.empty:
                st.metric("Assets to Analyze", len(user_assets))
        
        if generate_button:
            # Validate required fields before generating
            if not full_name or not objective:
                st.error("Please fill in required fields: Full Name and Primary Objective")
            elif user_assets.empty:
                st.error("Please add at least one asset before generating options")
            else:
                api_key = os.environ.get("CEREBRAS_API_KEY")
                input_data = {
                    "Name": full_name,
                    "Marital": marital_status,
                    "SpouseName": spouse_name,
                    "SpouseID": spouse_id,
                    "Children": children,
                    "Assets": user_assets.to_dict(orient="records"),
                    "Liabilities": liabilities,
                    "Income": income_sources,
                    "Economic": economic_standing,
                    "Prefs": distribution_prefs,
                    "Objective": objective,
                    "Details": objective_details,
                    "Notes": lawyer_notes,
                }

                # Build prompt and attempt to call AI; fallback to mock when not available
                with st.spinner("Generating AI suggestions..."):
                    prompt = build_prompt(input_data, distribution_prefs)

                    if Cerebras and api_key:
                        try:
                            client = Cerebras(api_key=api_key)
                            chat_completion = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="gpt-oss-120b",
                                max_tokens=300,
                                temperature=0.7,
                            )
                            response = chat_completion.choices[0].message.content
                            st.success("AI suggestions generated successfully!")
                            st.write("**AI Suggestion (from Cerebras):**", response)
                        except Exception as e:
                            st.error(f"API Error: {str(e)}. Falling back to mock response.")
                            st.write("**AI Suggestion (Mock Fallback):**", fallback_mock())
                    else:
                        if not api_key:
                            st.info("CEREBRAS_API_KEY not set. Using mock response.")
                        st.write("**AI Suggestion (Mock):**", fallback_mock())

    # Submit and save
    st.markdown("---")
    st.subheader("Submit Questionnaire")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        submit_button = st.button("Submit for Proposal", type="primary", use_container_width=True)
    
    with col2:
        preview_button = st.button("Preview Data", use_container_width=True)
    
    with col3:
        logout_button = st.button("Logout", use_container_width=True)
    
    if preview_button:
        # Show data preview
        st.subheader("Data Preview")
        preview_data = {
            "Client Name": full_name,
            "Marital Status": marital_status,
            "Total Assets": len(user_assets) if not user_assets.empty else 0,
            "Total Asset Value": f"KES {user_assets['Value (KES)'].sum():,.0f}" if not user_assets.empty else "KES 0",
            "Primary Objective": objective
        }
        st.json(preview_data)
    
    if submit_button:
        # Validate all required fields
        if not full_name:
            st.error("❌ Full Name is required")
        elif marital_status == "Married" and (not spouse_name or not spouse_id):
            st.error("❌ Spouse Name and ID are required for married status")
        elif user_assets.empty:
            st.error("❌ At least one asset must be added")
        elif not objective:
            st.error("❌ Primary Objective is required")
        else:
            # Prepare data for submission
            submission_data = {
                "Name": full_name,
                "Marital": marital_status,
                "SpouseName": spouse_name,
                "SpouseID": spouse_id,
                "Children": children,
                "Assets": user_assets.to_dict(orient="records"),
                "Liabilities": liabilities,
                "Income": income_sources,
                "Economic": economic_standing,
                "Prefs": distribution_prefs,
                "Objective": objective,
                "Details": objective_details,
                "Notes": lawyer_notes,
                "SubmittedBy": username,
                "UserRole": user_role,
                "SavedAt": str(pd.Timestamp.now()),
            }
            
            # Generate client ID
            client_id = generate_client_id(full_name)
            
            with st.spinner("Saving client data..."):
                success, message, file_path = save_client_data(submission_data, client_id)
                
                if success:
                    st.success(f"✅ {message}")
                    st.success("📋 Proposal will be generated and sent to client.")
                    
                    # Store client ID in user session
                    set_user_session_data(username, 'client_id', client_id)
                    
                    # Show success details
                    with st.expander("Submission Details"):
                        st.write(f"**Client ID:** {client_id}")
                        st.write(f"**File:** {os.path.basename(file_path)}")
                        st.write(f"**Submitted by:** {username} ({user_role})")
                        st.write(f"**Total Assets:** KES {user_assets['Value (KES)'].sum():,.0f}")
                        st.write(f"**Asset Count:** {len(user_assets)}")
                    
                    # Option to clear form for new client
                    if st.button("Start New Client Form"):
                        # Clear user session data
                        set_user_session_data(username, 'assets', pd.DataFrame(columns=["Type", "Description", "Value (KES)"]))
                        set_user_session_data(username, 'client_id', None)
                        st.rerun()
                        
                else:
                    st.error(f"❌ Failed to save data: {message}")
                    
                    # Show troubleshooting info
                    with st.expander("Troubleshooting"):
                        st.write("**Possible solutions:**")
                        st.write("- Check if the data directory exists and is writable")
                        st.write("- Verify disk space availability")
                        st.write("- Contact system administrator if problem persists")
                        st.write(f"**Data directory:** {os.getenv('DATA_DIR', 'data')}")
    
    if logout_button:
        # Clear session and logout
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.success("Logged out successfully")
        st.rerun()


if __name__ == "__main__":
    main()
