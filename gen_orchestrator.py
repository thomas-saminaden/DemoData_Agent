import os
import csv
from gen_customers import CustomerGenerator
from gen_accounts import AccountGenerator
from gen_links import LinkGenerator
from gen_transactions import TransactionGenerator

def generate_custom_data(customer_profiles, run_date, account_blueprint=None, transaction_blueprint=None, output_dir="output"):
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    # 1. Initialize Engines
    gen_cust = CustomerGenerator()
    gen_acct = AccountGenerator()
    gen_link = LinkGenerator()
    gen_txn = TransactionGenerator()
    
    # 2. EXECUTE SEQUENCE
    
    # Step A: Customers
    print("--- Step 1: Generating Customers ---")
    customer_contexts, customer_rows = gen_cust.generate_rows(customer_profiles, run_date)
    
    # Step B: Accounts
    print("--- Step 2: Generating Accounts ---")
    account_contexts, account_rows = gen_acct.generate_rows(customer_contexts, run_date)
    
    # Step C: Links
    print("--- Step 3: Generating Links ---")
    link_rows = gen_link.generate_rows(customer_contexts, account_contexts)
    
    # Step D: Transactions
    print("--- Step 4: Generating Transactions ---")
    transaction_rows = gen_txn.generate_rows(account_contexts, run_date, transaction_blueprint)

    # 3. WRITE FILES
    files_created = []
    
    # Write Customers
    c_file = os.path.join(output_dir, f"CUSTOMERS_{run_date}.txt")
    with open(c_file, 'w', newline='', encoding='utf-8') as f: 
        csv.writer(f, delimiter='|', quoting=csv.QUOTE_MINIMAL).writerows(customer_rows)
    files_created.append(c_file)
    
    # Write Accounts
    a_file = os.path.join(output_dir, f"ACCOUNTS_{run_date}.txt")
    with open(a_file, 'w', newline='', encoding='utf-8') as f: 
        csv.writer(f, delimiter='|', quoting=csv.QUOTE_MINIMAL).writerows(account_rows)
    files_created.append(a_file)

    # Write Links
    l_file = os.path.join(output_dir, f"CUSTOMER_ACCOUNT_LINK_{run_date}.txt")
    with open(l_file, 'w', newline='', encoding='utf-8') as f: 
        csv.writer(f, delimiter='|', quoting=csv.QUOTE_MINIMAL).writerows(link_rows)
    files_created.append(l_file)
    
    # Write Transactions
    t_file = os.path.join(output_dir, f"TRANSACTIONS_{run_date}.txt")
    with open(t_file, 'w', newline='', encoding='utf-8') as f: 
        csv.writer(f, delimiter='|', quoting=csv.QUOTE_MINIMAL).writerows(transaction_rows)
    files_created.append(t_file)
        
    return files_created