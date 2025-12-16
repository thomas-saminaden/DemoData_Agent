# =============================================================================
# KYC Data Generation Application
# 
# This Streamlit application serves as an interface for generating synthetic
# banking data with realistic KYC (Know Your Customer) profiles. It uses GPT-4
# to create detailed customer scenarios and generate corresponding transaction data.
# =============================================================================

import streamlit as st
import os
import json
import glob
from datetime import datetime
from openai import OpenAI
from gen_orchestrator import generate_custom_data 

# =============================================================================
# Configuration Settings
# - Defines core application settings and constants
# - Sets up file paths and basic Streamlit configuration
# =============================================================================

HISTORY_FILE = "chat_history.json"
BASE_OUTPUT_DIR = "generated_data"  

st.set_page_config(
    page_title="Senior Data Consultant", 
    page_icon="🧠", 
    layout="wide"
)

if not os.path.exists(BASE_OUTPUT_DIR):
    os.makedirs(BASE_OUTPUT_DIR)

# =============================================================================
# Data Loading and Management Functions
# - Handle chat history persistence
# - Load reference data from specification files
# =============================================================================

def load_chat_history():
    """Load previous chat interactions from JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_chat_history(messages):
    """Persist chat history to JSON file."""
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(messages, f, indent=4)
    except:
        pass

def get_valid_codes(file_path, key_idx=0, val_idx=1):
    """
    Load and parse specification files containing valid codes and descriptions.
    Returns formatted strings combining codes and descriptions.
    """
    items = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()[1:]
                for line in lines:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        items.append(f"{parts[key_idx].strip()} ({parts[val_idx].strip()})")
        except:
            pass
    return items

# Load reference data from specification files
ctx_countries = get_valid_codes('00_Spec_Country.txt')[:60]
ctx_industries = get_valid_codes('00_Spec_Business_Classification.txt')[:60]
ctx_txn_types = get_valid_codes('00_Spec_Transaction_Type.txt')

# =============================================================================
# Streamlit UI Components - Sidebar
# - API key input
# - System date configuration
# - History management
# =============================================================================

st.sidebar.title("KYC Data Consultant")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
run_date = st.sidebar.text_input("System Date (YYYYMMDD)", value="20251130")

if st.sidebar.button("Clear History"):
    st.session_state["messages"] = []
    st.session_state["blueprint"] = None
    save_chat_history([])
    st.rerun()

# =============================================================================
# GPT Tool Definitions
# - Defines the structure for scenario generation
# - Includes customer profiles and transaction specifications
# =============================================================================

tools = [{
    "type": "function",
    "function": {
        "name": "propose_scenario_blueprint",
        "description": "Proposes a detailed data plan.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Executive summary of the logic."
                },
                "customer_profiles": {
                    "type": "array",
                    "items": { 
                        "type": "object", 
                        "properties": { 
                            "type": {"enum": ["C", "P"]},
                            "country": {"type": "string"},
                            "phone_country_code": {
                                "type": "string",
                                "description": "Optional. Specific phone country code (e.g., '44' for UK). If not provided, uses country of residence code."
                            },
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "gender": {"enum": ["Male", "Female"]},
                            "legal_name": {"type": "string"},
                            "company_form": {"type": "string"},
                            "accounts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "product_code": {
                                            "type": "string",
                                            "description": "0004, 0011, 0002"
                                        },
                                        "count": {"type": "integer"},
                                        "overdraft_limit": {
                                            "type": "number",
                                            "description": "Overdraft limit amount. Default 0.00"
                                        }
                                    }
                                }
                            },
                            "industry": {"type": "string"},
                            "residence_flag": {"enum": ["Y", "N"]},
                            "special_attention_flag": {"enum": ["Y", "N"]},
                            
                            # Financial Activity Profile
                            "wire_in_volume": {
                                "type": "number",
                                "description": "Monthly Total Amount"
                            }, 
                            "wire_out_volume": {
                                "type": "number",
                                "description": "Monthly Total Amount"
                            },
                            "wire_in_number": {
                                "type": "integer",
                                "description": "Monthly Count"
                            }, 
                            "wire_out_number": {
                                "type": "integer",
                                "description": "Monthly Count"
                            },
                            "cash_in_volume": {
                                "type": "number",
                                "description": "Monthly Total Amount"
                            }, 
                            "cash_out_volume": {
                                "type": "number",
                                "description": "Monthly Total Amount"
                            },
                            "check_in_volume": {
                                "type": "number",
                                "description": "Monthly Total Amount"
                            }, 
                            "check_out_volume": {
                                "type": "number",
                                "description": "Monthly Total Amount"
                            },
                            
                            # Business Profile
                            "intended_product_usage": {
                                "type": "string", 
                                "description": "Purpose of relationship e.g. 'Salary Processing', 'Commercial Trading', 'Savings'"
                            },
                            "city": {"type": "string"},
                            "street_address": {"type": "string"},
                            "postal_code": {"type": "string"},
                            "tax_number": {"type": "string"}, 
                            "role": {"enum": ["STANDARD", "HUB", "FEEDER", "BENEFICIARY"]},
                            "network_id": {"type": "string"},
                        },
                        "required": [
                            "type", "country", 
                            "wire_in_number", "wire_out_number",
                            "wire_in_volume", "wire_out_volume",
                            "cash_in_volume", "cash_out_volume",
                            "check_in_volume", "check_out_volume",
                            "intended_product_usage"
                        ]
                    }
                },
                "transactions_per_customer": { 
                    "type": "array", 
                    "items": { 
                        "type": "object", 
                        "properties": { 
                            # Transaction Core Details
                            "type": {"type": "string"}, 
                            "amount_orig": {"type": "number"},
                            "currency_orig": {"type": "string"},
                            "date": {"type": "string"},
                            "credit_debit": {"enum": ["C", "D"]},
                            "description": {"type": "string"},
                            "channel_desc": {
                                "type": "string",
                                "description": "e.g. ATM, BRANCH, INTERNET, MOBILE"
                            },
                            "payment_mean": {
                                "type": "string",
                                "description": "Means of payment e.g. Wire Transfer, Cash, Debit Card"
                            },
                            "txn_type_desc": {
                                "type": "string",
                                "description": "Specific Type from Spec e.g. 'Cash', 'Wire Transfer', 'Direct Debit'"
                            },
                            
                            # Internal Transaction Logic
                            "is_internal": {
                                "type": "boolean",
                                "description": "If true, system links to another generated customer"
                            },
                            "internal_counterparty_role": {
                                "type": "string",
                                "description": "If internal, which role to target e.g. HUB"
                            },
                            
                            # Counterparty Details
                            "counterparty_name": {"type": "string"},
                            "counterparty_address": {
                                "type": "string",
                                "description": "Real address found on maps"
                            },
                            "counterparty_zone": {"type": "string"},
                            "counterparty_postal_code": {"type": "string"},
                            "counterparty_city": {"type": "string"},
                            "counterparty_country": {"type": "string"},
                            
                            # Counterparty Account Information
                            "counterparty_account_num": {"type": "string"},
                            "counterparty_account_name": {"type": "string"},
                            "counterparty_account_type": {
                                "type": "string",
                                "description": "e.g. Current, Savings"
                            },
                            "counterparty_account_iban": {"type": "string"},
                            "counterparty_account_bic": {"type": "string"},
                            
                            # Counterparty Bank Information
                            "counterparty_bank_name": {"type": "string"},
                            "counterparty_bank_code": {"type": "string"},
                            "counterparty_bank_address": {"type": "string"},
                            "counterparty_bank_city": {"type": "string"},
                            "counterparty_bank_zone": {"type": "string"},
                            "counterparty_bank_postal_code": {"type": "string"},
                            "counterparty_bank_country": {"type": "string"},
                            
                            "count": {"type": "integer"} 
                        } 
                    } 
                }
            },
            "required": ["summary", "customer_profiles"]
        }
    }
}]

# =============================================================================
# Chat Interface
# - Manages chat history and message display
# - Handles user input and API interactions
# =============================================================================

if "messages" not in st.session_state:
    st.session_state["messages"] = load_chat_history() or [{
        "role": "assistant",
        "content": "Hello. I am your KYC Data Consultant. I can generate precise account structures for specific customers."
    }]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not api_key:
        st.error("Enter API Key")
        st.stop()

    client = OpenAI(api_key=api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # =============================================================================
    # System Prompt - GPT Guidance
    # - Defines the AI's role and behavior
    # - Provides context and rules for data generation
    # =============================================================================
    
    system_prompt = """
You are a Senior Banking Data Architect & KYC Specialist.

### CORE DIRECTIVE: REALISTIC BEHAVIOR SIMULATION
Do not use hardcoded rules. Instead, apply **Common Sense Banking Logic** to every specific scenario. 
Look at the Customer's Country, Legal Form, Industry, Occupation, and any other relevant characteristics 
to determine their financial behavior.

### 1. DERIVE USAGE VOLUMES (The "KYC Profile")
You MUST estimate realistic **MONTHLY** averages for ALL the following fields. Do NOT leave them blank.

**Required Fields:**
- **Count (`_NUMBER`):** `wire_in_number`, `wire_out_number`
- **Volume/Amount (`_VOLUME`):** 
  - `wire_in_volume`, `wire_out_volume`
  - `cash_in_volume`, `cash_out_volume`
  - `check_in_volume`, `check_out_volume`

**Thinking Process (Simulate, Don't just Lookup):**
1. **Contextualize Cash Usage:**
   - **Intersect Business & Region:** 
     - A Bakery in Germany typically uses high cash
     - A Bakery in Sweden typically uses cards/apps (low cash)
     - A Software firm ANYWHERE uses zero cash
   - **Derive:** `cash_in_volume` must reflect this specific intersection

2. **Determine Payment Methods (Checks vs Wires):**
   - **Analyze Banking Maturity:** 
     - Some countries still use checks (e.g., US, FR)
     - Fully digital regions (Northern Europe, developed Asia) use zero checks
   - **Default to Wire:** Most modern B2B flows through `wire_in/out`

3. **Scale & Frequency:**
   - **Volume vs Count:** 
     - High Net Worth: Few transactions (Low Count), high values
     - Retailers: Many transactions (High Count), lower values
   - **Consistency:** `wire_out_volume` should match entity's estimated costs

### 2. ACCOUNT STRUCTURE
Define the `accounts` list INSIDE each customer profile based on needs:
- **Corp:** Business, Trading, or Currency accounts
- **Indiv:** Current, Savings, or Joint accounts

### 3. TRANSACTIONS (The "Brain" Logic)
Define specific transactions in `transactions_per_customer`.

**A. DATES & CURRENCY**
- **Dates:** Use `date` (YYYYMMDD). Sequential dates. Avoid Sundays for B2B/Retail in EU
- **Currency:** Set `currency_orig` based on use case (Oil=USD, Local Groceries=Local)
- **Amount:** Set `amount_orig` realistically per currency scale

**B. DIRECTION & MEANS**
- **Credit/Debit:** Use "C" (Credit/Deposit) or "D" (Debit/Withdrawal)
- **Payment Mean:** Select realistic mean (Wire, Cash, Card)
- **Channel:** Match to payment (ATM=Cash, INTERNET=Wires)

**C. COUNTERPARTIES (Crucial)**
- **Internal:** 
  - Between generated customers: set `is_internal` = True
  - Do NOT invent details; Engine will link them
- **External:** 
  - Third party: set `is_internal` = False
  - MUST provide:
    - `counterparty_name`: Realistic name
    - `counterparty_address`: REAL address from maps
    - `counterparty_bank_name`: Realistic bank
    - Address must match entity type

### DATA QUALITY
- **Address:** Must be real location in specified City/Country
- **Consistency:** Occupation should match Age and Wealth level
- **Phone Numbers:**
  - Default: Uses country of residence's phone code
  - Can specify different phone_country_code if customer has foreign phone number
  - Example: German resident with UK phone would use phone_country_code="44"

### CONTEXT
Supported Countries: {ctx_countries_str}

Valid Transaction Types (Pick for txn_type_desc):
{ctx_txn_types_str}
""".format(
    ctx_countries_str=', '.join(ctx_countries[:15]) + '...',
    ctx_txn_types_str=', '.join(ctx_txn_types)
)

    messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
    
    # =============================================================================
    # GPT Interaction and Response Handling
    # - Processes GPT responses
    # - Updates UI with results
    # =============================================================================
    
    with st.chat_message("assistant"):
        with st.spinner("Architecture in progress..."):
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            tool_calls = response.choices[0].message.tool_calls
            content = response.choices[0].message.content

            if tool_calls:
                args = json.loads(tool_calls[0].function.arguments)
                st.session_state["blueprint"] = args
                
                st.info(f"📋 **Proposal:** {args.get('summary')}")
                with st.expander("Review Account Structure"):
                    st.json(args)
                
                msg_content = (
                    f"I have proposed a plan: {args.get('summary')}. "
                    "Check the 'accounts' section for each customer. Click 'Generate' to proceed."
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg_content
                })
                st.write(msg_content)
            
            elif content:
                st.write(content)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": content
                })
                
            save_chat_history(st.session_state["messages"])

# =============================================================================
# Data Generation Execution
# - Handles the actual data generation process
# - Creates output files in the specified directory
# =============================================================================

if "blueprint" in st.session_state and st.session_state["blueprint"]:
    st.divider()
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Generate Files Now", type="primary"):
            bp = st.session_state["blueprint"]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_folder = f"run_{timestamp}"
            full_path = os.path.join(BASE_OUTPUT_DIR, run_folder)
            
            with st.spinner("Generating High-Fidelity Data..."):
                files = generate_custom_data(
                    bp.get("customer_profiles", []), 
                    run_date, 
                    None,  # No global account blueprint anymore
                    bp.get("transactions_per_customer", []),
                    output_dir=full_path
                )
            
            st.success(f"Files saved to `{run_folder}`")
            st.session_state["blueprint"] = None
            st.rerun()