import streamlit as st
import pandas as pd
import os
import json
import logging
# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)


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


def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'login_history' not in st.session_state:
        st.session_state.login_history = []
    if 'assets' not in st.session_state:
        st.session_state.assets = pd.DataFrame(columns=["Type", "Description", "Value (KES)"])


def login_widget():
    st.header("HNC - Login")
    username = st.text_input("Username", key="_username")
    password = st.text_input("Password", type="password", key="_password")
    if st.button("Login"):
        # Mock auth - in real, use secure hashing and proper auth backends
        if username and password:
            st.session_state.logged_in = True
            st.session_state.login_history.append(f"Login at {pd.Timestamp.now()}")
            st.rerun()
        else:
            st.error("Invalid credentials")


def save_client_data(data: dict, path: str = "client_data.json") -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.exception("Failed to save client data")
        return False


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
    init_session_state()

    Cerebras = safe_import_cerebras()

    if not st.session_state.logged_in:
        login_widget()
        return

    st.sidebar.title("HNC AI Questionnaire Prototype")
    st.sidebar.write("Logged in. History:", st.session_state.login_history)

    st.title("Digitized Client Questionnaire")

    # --- Client Bio Data ---
    with st.expander("1. Client Bio Data", expanded=True):
        full_name = st.text_input("Full Name", key="name")
        marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"], key="marital")
        spouse_name = ""
        spouse_id = ""
        if marital_status == "Married":
            spouse_name = st.text_input("Spouse Name", key="spouse_name")
            spouse_id = st.text_input("Spouse ID Number", key="spouse_id")
        children = st.text_area("Children's Details (Name, Age, Relationship - one per line)", key="children")

    # --- Financial Data ---
    with st.expander("2. Financial Data"):
        st.write("Assets:")
        asset_type = st.selectbox("Asset Type", ["Real Estate", "Bank Account", "Shares", "Other"], key="asset_type")
        asset_desc = st.text_input("Description", key="asset_desc")
        asset_value = st.number_input("Estimated Value (KES)", min_value=0, key="asset_value")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add Asset"):
                new_row = pd.DataFrame({"Type": [asset_type], "Description": [asset_desc], "Value (KES)": [asset_value]})
                st.session_state.assets = pd.concat([st.session_state.assets, new_row], ignore_index=True)
        with col2:
            if st.button("Clear Assets"):
                st.session_state.assets = pd.DataFrame(columns=["Type", "Description", "Value (KES)"])
        st.dataframe(st.session_state.assets)

        liabilities = st.text_area("Liabilities (Type, Amount, Creditor - one per line)", key="liabilities")
        income_sources = st.text_area("Income Sources (Type, Annual Amount KES - one per line)", key="income_sources")

    # --- Economic Context ---
    with st.expander("3. Economic Context"):
        economic_standing = st.selectbox("Economic Standing", ["High Net Worth", "Middle Income", "Low Income"], key="economic")
        distribution_prefs = st.text_area("Asset Distribution Preferences", key="distribution_prefs")

    # --- Client Objectives ---
    with st.expander("4. Client Objectives"):
        objective = st.selectbox("Primary Objective", ["Create Will", "Create Living Will", "Create Share Transfer Will", "Create Trust", "Sell Asset", "Other"], key="objective")
        objective_details = st.text_area("Details", key="objective_details")

    # --- Options & Consequences ---
    with st.expander("5. Options & Consequences"):
        lawyer_notes = st.text_area("Lawyer Notes", key="lawyer_notes")
        if st.button("Generate Options"):
            api_key = os.environ.get("CEREBRAS_API_KEY")
            input_data = {
                "Name": full_name,
                "Marital": marital_status,
                "Children": children,
                "Assets": st.session_state.assets.to_dict(orient="records"),
                "Liabilities": liabilities,
                "Income": income_sources,
                "Economic": economic_standing,
                "Prefs": distribution_prefs,
                "Objective": objective,
                "Details": objective_details,
                "Notes": lawyer_notes,
            }

            # Build prompt and attempt to call AI; fallback to mock when not available
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
                    st.write("AI Suggestion (from Cerebras):", response)
                except Exception as e:
                    st.error(f"API Error: {str(e)}. Falling back to mock.")
                    st.write(fallback_mock())
            else:
                if not api_key:
                    st.info("CEREBRAS_API_KEY not set. Using mock response.")
                st.write(fallback_mock())

    # Submit and save
    if st.button("Submit for Proposal"):
        if not full_name:
            st.error("Missing required fields: Full Name is required.")
        else:
            data = {
                "Name": full_name,
                "Marital": marital_status,
                "SpouseName": spouse_name,
                "SpouseID": spouse_id,
                "Children": children,
                "Assets": st.session_state.assets.to_dict(orient="records"),
                "Liabilities": liabilities,
                "Income": income_sources,
                "Economic": economic_standing,
                "Prefs": distribution_prefs,
                "Objective": objective,
                "Details": objective_details,
                "Notes": lawyer_notes,
                "SavedAt": str(pd.Timestamp.now()),
            }

            ok = save_client_data(data)
            if ok:
                st.success("Submitted! Proposal generated (mock). Data stored locally in client_data.json.")
            else:
                st.error("Failed to save client data. See logs for details.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()


if __name__ == "__main__":
    main()
