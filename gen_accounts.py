import random
from gen_shared import BaseGenerator

class AccountGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.acct_spec = self._load_spec('02_Spec_Fields_Accounts.txt')
        
        # Load Reference Maps
        self.country_currency_map = {
            'US': 'USD', 'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR', 'FI': 'EUR',
            'GB': 'GBP', 'JP': 'JPY', 'CN': 'CNY', 'CH': 'CHF', 'CA': 'CAD', 'AU': 'AUD', 'TR': 'TRY', 'RO': 'RON'
        }
        
    def generate_rows(self, customer_contexts, run_date):
        """
        Generates Account rows based on Customer Specific Instructions.
        """
        account_contexts = []
        csv_rows = []
        
        for cust in customer_contexts:
            # 1. READ CUSTOMER SPECIFIC INSTRUCTIONS
            # We look for the blueprint attached to this specific customer
            cust_bp = cust.get('ACCOUNTS_BLUEPRINT', [])
            
            types_to_generate = []
            
            if cust_bp and isinstance(cust_bp, list):
                for item in cust_bp:
                    if isinstance(item, dict):
                        qty = int(item.get('count', 1))
                        # Pass the whole item (dict) to preserve product_code
                        for _ in range(qty): types_to_generate.append(item) 
                    elif isinstance(item, str):
                        types_to_generate.append(item)
            
            # Default Logic (Fallback if Agent said nothing)
            if not types_to_generate:
                if cust['CUSTOMER_TYPE_CODE'] == 'C':
                    types_to_generate = ['Business']
                else:
                    types_to_generate = ['Current']

            # 2. Generate Account Objects
            for acc_request in types_to_generate:
                
                # Logic to handle both old string list and new dict object from tool
                if isinstance(acc_request, dict):
                    acc_type_desc = acc_request.get('type', 'Current')
                    bp_product_code = acc_request.get('product_code')
                    bp_overdraft = float(acc_request.get('overdraft_limit', 0.00))
                else:
                    acc_type_desc = str(acc_request)
                    bp_product_code = None
                    bp_overdraft = 0.00

                product_code_map = {"Current": "0004", "Savings": "0011", "Business": "0002", "Trading": "PRD003", "Loan": "0007", "Mortgage": "0008"}
                
                # Use Code from Agent if available, else derive
                if bp_product_code:
                    product_code = bp_product_code
                else:
                    clean_type = "Current"
                    for k in product_code_map:
                        if k.upper() in acc_type_desc.upper(): clean_type = k
                    product_code = product_code_map.get(clean_type, "0013")
                
                acc_id = f"ACC-{random.randint(10000000,99999999)}"
                # Use Currency from instruction if available, else derive from Country
                currency = self.country_currency_map.get(cust['COUNTRY_CODE'], 'USD')
                
                balance = f"{random.uniform(50000, 5000000):.2f}" if cust['CUSTOMER_TYPE_CODE'] == 'C' else f"{random.uniform(0, 15000):.2f}"
                
                acc_ctx = {
                    "ACCOUNT_SOURCE_UNIQUE_ID": acc_id,
                    "ACCOUNT_SOURCE_REF_ID": acc_id,
                    "ACCOUNT_NAME": f"{cust['CUSTOMER_NAME']} {acc_type_desc}",
                    "CUSTOMER_SOURCE_UNIQUE_ID": cust['ID'],
                    "ACCOUNT_STATUS_CODE": "ACTIVE",
                    "CREDIT_DEBIT_CODE": "C",
                    "CURRENCY_CODE": currency,
                    "DATE_OPENED": cust['ACQUISITION_DATE'],
                    "ACCOUNT_BALANCE": balance,
                    "BRANCH_ID": cust['PRIME_BRANCH_ID'],
                    "RELATIONSHIP_MGR_ID": cust['RELATIONSHIP_MGR_ID'],
                    "IBAN": f"{cust['COUNTRY_CODE']}99{random.randint(1000000000,9999999999)}",
                    "BIC": self.fake.swift(),
                    "BALANCE_DATE": run_date,
                    "ORG_UNIT_CODE": cust['ORG_UNIT'],
                    "PRIMARY_CUSTOMER_CATEGORY_CODE": cust['CUSTOMER_CATEGORY_CODE'],
                    "PRODUCT_SOURCE_TYPE_CODE": product_code,
                    "ADDRESS": cust.get('OVERRIDE_ADDRESS'), 
                    "CITY": cust.get('OVERRIDE_CITY'),
                    "POSTAL_CODE": cust.get('POSTAL_CODE'),
                    "COUNTRY_CODE": cust['COUNTRY_CODE'],
                    "ADDRESS_VALID_FROM": cust['ACQUISITION_DATE'],
                    "OVERDRAFT_LIMIT": f"{bp_overdraft:.2f}",
                    "ACCOUNT_CHANNEL_REMOTE_FLAG": "N"
                }
                
                account_contexts.append(acc_ctx)

                row = []
                for i, col in enumerate(self.acct_spec['columns']):
                    col_name = col.upper()
                    col_type = self.acct_spec['types'][i]
                    val = ""
                    if col_name in acc_ctx: val = acc_ctx[col_name]
                    if self.acct_spec['mandatory'][i] == 'YES' and not val: val = "0" if 'NUMBER' in col_type else "N"
                    row.append(self._enforce_length(val, col_type))
                csv_rows.append(row)

        return account_contexts, csv_rows