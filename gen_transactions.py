import random
from datetime import datetime, timedelta
from gen_shared import BaseGenerator

class TransactionGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.txn_spec = self._load_spec('03_Spec_Fields_Transactions.txt')
        self.txn_types = self.loader.load_transaction_types('00_Spec_Transaction_Type.txt')
        
        # --- NEW LOOKUP MAP ---
        self.txn_type_map = {}
        for t in self.txn_types:
            self.txn_type_map[t['DESC'].upper()] = t['CODE']
        # ----------------------

        # ITEM 1: Load Channel Codes
        self.channel_map, self.channel_codes = self.loader.load_file('00_Spec_Transaction_Channel_Code.txt', key_idx=1, val_idx=0)

    def _get_counterparty(self):
        """Generates fake counterparty data (Fallback only)"""
        return {
            "NAME": self.fake.company(),
            "ADDRESS": self.fake.street_address(),
            "CITY": self.fake.city(),
            "COUNTRY": self.fake.country_code(),
            "IBAN": self.fake.iban(),
            "BIC": self.fake.swift(),
            "BANK": f"{self.fake.company()} Bank",
            "BANK_ADDRESS": self.fake.street_address(),
            "BANK_CITY": self.fake.city(),
            "BANK_COUNTRY": self.fake.country_code()
        }

    def generate_rows(self, account_contexts, run_date, global_blueprint=None):
        csv_rows = []
        
        # Simple Mock FX Rates
        fx_rates = {'USD': 1.0, 'EUR': 0.95, 'GBP': 0.80, 'JPY': 150.0, 'CNY': 7.2, 'CAD': 1.35}
        
        # Group Accounts by Customer ID
        accounts_by_cust = {}
        all_accounts_list = account_contexts # Reference for internal lookup
        
        for acc in account_contexts:
            cust_id = acc['CUSTOMER_SOURCE_UNIQUE_ID']
            if cust_id not in accounts_by_cust: accounts_by_cust[cust_id] = []
            accounts_by_cust[cust_id].append(acc)

        # Iterate through every Customer
        for cust_id, accounts in accounts_by_cust.items():
            if not accounts: continue

            txns_to_make = []
            if global_blueprint:
                for bp_item in global_blueprint:
                    count = int(bp_item.get('count', 1))
                    for _ in range(count):
                        txns_to_make.append(bp_item)
            else:
                for _ in range(random.randint(1, 5)):
                    txns_to_make.append({"TYPE_HINT": "Purchase"})

            for txn_req in txns_to_make:
                target_acc = random.choice(accounts)
                
# --- LOGIC START ---

                # 1. ORG UNIT
                org_unit = target_acc.get('ORG_UNIT_CODE', '')

                # 2. CHANNEL
                chan_desc = txn_req.get('channel_desc', 'INTERNET').upper()
                chan_code = self.channel_map.get(chan_desc, 'CH001') # Default
                if not chan_code and self.channel_codes: chan_code = self.channel_codes[0]

                # 3. CREDIT/DEBIT
                cd_code = txn_req.get('credit_debit')
                if not cd_code: cd_code = 'D' if txn_req.get('TYPE_HINT') == 'Purchase' else 'C'

                # --- NEW LOGIC FOR REQ 14-18 & 9 (Source Type) ---
                
                # Payment Mean & Source Type
                pay_mean = txn_req.get('payment_mean', 'Wire Transfer')
                bp_type_desc = txn_req.get('txn_type_desc', '').upper()
                txn_source_type_code = self.txn_type_map.get(bp_type_desc, "TT0013") # Default to Other if missing

                # Internal/External Scope
                is_internal = txn_req.get('is_internal', False)
                scope_desc = "INTERNAL" if is_internal else "EXTERNAL"

                # Instrument Mapping (Simple keyword check)
                pm_upper = pay_mean.upper()
                if "CARD" in pm_upper: instrument = "CARD"
                elif "CASH" in pm_upper or "CURRENCY" in pm_upper: instrument = "CASH"
                elif "CHECK" in pm_upper or "CHEQUE" in pm_upper: instrument = "CHEQUE"
                else: instrument = "WIRE"

                # 4. COUNTERPARTY RESOLUTION (Expanded)
                cpty_data = {}

                if is_internal:
                    candidates = [a for a in all_accounts_list if a['CUSTOMER_SOURCE_UNIQUE_ID'] != cust_id]
                    if candidates:
                        int_acc = random.choice(candidates)
                        cpty_data = {
                            "NAME": int_acc['ACCOUNT_NAME'],
                            "ADDRESS": int_acc.get('ADDRESS', ''),
                            "ZONE": "",
                            "CITY": int_acc.get('CITY', ''),
                            "POSTAL_CODE": int_acc.get('POSTAL_CODE', ''),
                            "COUNTRY": int_acc.get('COUNTRY_CODE', ''),
                            "ACCOUNT_NUM": int_acc['ACCOUNT_SOURCE_UNIQUE_ID'],
                            "ACCOUNT_NAME": int_acc['ACCOUNT_NAME'],
                            "ACCOUNT_TYPE": "Current",
                            "IBAN": int_acc.get('IBAN', ''),
                            "BIC": int_acc.get('BIC', ''),
                            "BANK_NAME": "INTERNAL BANK",
                            "BANK_CODE": "BNK_INT",
                            "BANK_ADDRESS": "Internal HQ",
                            "BANK_CITY": int_acc.get('CITY', ''),
                            "BANK_ZONE": "",
                            "BANK_POSTAL_CODE": "",
                            "BANK_COUNTRY": int_acc.get('COUNTRY_CODE', '')
                        }
                    else:
                        cpty_data = self._get_counterparty()
                else:
                    # External: Map all new Brain fields
                    fallback = self._get_counterparty()
                    cpty_data = {
                        "NAME": txn_req.get('counterparty_name') or fallback['NAME'],
                        "ADDRESS": txn_req.get('counterparty_address') or fallback['ADDRESS'],
                        "ZONE": txn_req.get('counterparty_zone', ''),
                        "CITY": txn_req.get('counterparty_city') or fallback['CITY'],
                        "POSTAL_CODE": txn_req.get('counterparty_postal_code', ''),
                        "COUNTRY": txn_req.get('counterparty_country') or fallback['COUNTRY'],
                        
                        "ACCOUNT_NUM": txn_req.get('counterparty_account_num') or f"ACC-{random.randint(1000,9999)}",
                        "ACCOUNT_NAME": txn_req.get('counterparty_account_name') or fallback['NAME'],
                        "ACCOUNT_TYPE": txn_req.get('counterparty_account_type', 'Current'),
                        "IBAN": txn_req.get('counterparty_account_iban') or fallback['IBAN'],
                        "BIC": txn_req.get('counterparty_account_bic') or fallback['BIC'],
                        
                        "BANK_NAME": txn_req.get('counterparty_bank_name') or fallback['BANK'],
                        "BANK_CODE": txn_req.get('counterparty_bank_code', 'BNK001'),
                        "BANK_ADDRESS": txn_req.get('counterparty_bank_address') or fallback['BANK_ADDRESS'],
                        "BANK_CITY": txn_req.get('counterparty_bank_city') or fallback['BANK_CITY'],
                        "BANK_ZONE": txn_req.get('counterparty_bank_zone', ''),
                        "BANK_POSTAL_CODE": txn_req.get('counterparty_bank_postal_code', ''),
                        "BANK_COUNTRY": txn_req.get('counterparty_bank_country') or fallback['BANK_COUNTRY']
                    }
                    
                # Geo Scope
                geo_scope = "DOMESTIC" if target_acc['COUNTRY_CODE'] == cpty_data['COUNTRY'] else "INTERNATIONAL"

                # 5. ORIGINATOR vs BENEFICIARY (Logic 5)
                # If Debit (Out): Originator = Account Holder, Beneficiary = Cpty
                # If Credit (In): Originator = Cpty, Beneficiary = Account Holder
                
                my_name = target_acc['ACCOUNT_NAME']
                my_bank = "My Bank" # Simplified, usually derived from Branch/Org
                
                if cd_code == 'D':
                    orig_name = my_name
                    orig_bank = my_bank
                    ben_name = cpty_data['NAME']
                    ben_bank = cpty_data['BANK_NAME']
                else:
                    orig_name = cpty_data['NAME']
                    orig_bank = cpty_data['BANK_NAME']
                    ben_name = my_name
                    ben_bank = my_bank

                # Currency & Amounts (Previous Logic)
                curr_orig = txn_req.get('currency_orig', target_acc['CURRENCY_CODE'])
                curr_base = target_acc['CURRENCY_CODE']
                
                amt_orig = float(txn_req.get('amount_orig') or txn_req.get('AMOUNT') or random.uniform(10.0, 1000.0))
                if curr_orig == curr_base:
                    amt_base = amt_orig
                else:
                    rate_orig = fx_rates.get(curr_orig, 1.0)
                    rate_base = fx_rates.get(curr_base, 1.0)
                    amt_base = amt_orig * (rate_base / rate_orig)

                # Date Logic
                specified_date = txn_req.get('date')
                if specified_date:
                    orig_date = specified_date
                else:
                    dt_obj = datetime.strptime(run_date, "%Y%m%d") - timedelta(days=random.randint(0, 30))
                    orig_date = dt_obj.strftime("%Y%m%d")

                txn_unique_id = f"TXN-{random.randint(10000000, 99999999)}"

                txn_ctx = {
                    "RUN_TIMESTAMP": f"{run_date}000000",
                    "SOURCE_TXN_NUM": txn_unique_id,
                    "SOURCE_TXN_UNIQUE_ID": txn_unique_id,
                    "ACCOUNT_SOURCE_UNIQUE_ID": target_acc['ACCOUNT_SOURCE_UNIQUE_ID'],
                    "ACCOUNT_SOURCE_REF_ID": target_acc['ACCOUNT_SOURCE_UNIQUE_ID'],
                    "CUSTOMER_SOURCE_UNIQUE_ID": cust_id,
                    "PRIMARY_CUST_SRCE_REF_ID": cust_id,
                    "BRANCH_ID": target_acc['BRANCH_ID'],
                    
                    "CURRENCY_CODE_ORIG": curr_orig,
                    "CURRENCY_CODE_BASE": curr_base,
                    "TXN_AMOUNT_ORIG": f"{amt_orig:.2f}",
                    "TXN_AMOUNT_BASE": f"{amt_base:.2f}",
                    "CREDIT_DEBIT_CODE": cd_code,
                    "ORIGINATION_DATE": orig_date,
                    "POSTING_DATE": orig_date,
                    "VALUE_DATE": orig_date,
                    "TRANS_REF_DESC": txn_req.get('description', 'Generic'),
                    "TRANS_REF_DESC_2": pay_mean, 
                    "TRANS_REF_DESC_3": scope_desc,
                    "TRANS_REF_DESC_4": instrument,
                    "TRANS_REF_DESC_5": geo_scope,
                    "TRANS_REF_DESC_6": pay_mean,

                    "TXN_SOURCE_TYPE_CODE": txn_source_type_code,
                    "TXN_CHANNEL_CODE": chan_code,
                    
                    # ITEM 1: Channel
                    "TXN_CHANNEL_CODE": chan_code,
                    
                    # ITEM 2: Org Unit
                    "ORG_UNIT_CODE": org_unit,
                    
                    # ITEM 4: Counterparty Fields (a-r)
"COUNTER_PARTY_NAME": cpty_data['NAME'],
                    "COUNTER_PARTY_ADDRESS": cpty_data['ADDRESS'],
                    "COUNTER_PARTY_ZONE": cpty_data['ZONE'],
                    "COUNTER_PARTY_POSTAL_CODE": cpty_data['POSTAL_CODE'],
                    "COUNTER_PARTY_CITY": cpty_data['CITY'],
                    "COUNTER_PARTY_COUNTRY_CODE": cpty_data['COUNTRY'],
                    "COUNTER_PARTY_ACCOUNT_NUM": cpty_data['ACCOUNT_NUM'],
                    "COUNTER_PARTY_ACCOUNT_NAME": cpty_data['ACCOUNT_NAME'],
                    "COUNTER_PARTY_ACCOUNT_TYPE": cpty_data['ACCOUNT_TYPE'],
                    "COUNTER_PARTY_ACCOUNT_IBAN": cpty_data['IBAN'],
                    "COUNTER_PARTY_ACCOUNT_BIC": cpty_data['BIC'],
                    "COUNTER_PARTY_BANK_NAME": cpty_data['BANK_NAME'],
                    "COUNTER_PARTY_BANK_CODE": cpty_data['BANK_CODE'],
                    "COUNTER_PARTY_BANK_ADDRESS": cpty_data['BANK_ADDRESS'],
                    "COUNTER_PARTY_BANK_CITY": cpty_data['BANK_CITY'],
                    "COUNTER_PARTY_BANK_ZONE": cpty_data['BANK_ZONE'],
                    "COUNTER_PARTY_BANK_POSTAL_CODE": cpty_data['BANK_POSTAL_CODE'],
                    "COUNTER_PARTY_BNK_CNTRY_CD": cpty_data['BANK_COUNTRY'],

                    # ITEM 5: Originator/Beneficiary
                    "ORIGINATOR_NAME": orig_name,
                    "BENEFICIARY_NAME": ben_name,
                    "ORIGINATOR_BANK_NAME": orig_bank,
                    "BENEFICIARY_BANK_NAME": ben_bank,
                    
                    # ITEM 6: Cashback
                    "CASHBACK_AMT": "0"
                }

                # Map to CSV
                row = []
                for i, col in enumerate(self.txn_spec['columns']):
                    col_name = col.upper()
                    col_type = self.txn_spec['types'][i]
                    val = ""
                    if col_name in txn_ctx: val = txn_ctx[col_name]
                    if self.txn_spec['mandatory'][i] == 'YES' and not val: 
                        val = "0" if 'NUMBER' in col_type or 'DECIMAL' in col_type else "N"
                    row.append(self._enforce_length(val, col_type))
                csv_rows.append(row)

        return csv_rows