from gen_shared import BaseGenerator

class LinkGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.link_spec = self._load_spec('04_Spec_Fields_CustomerAccountLink.txt')

    def generate_rows(self, customer_contexts, account_contexts):
        csv_rows = []
        
        # Create a lookup for customers to easily find them by ID
        # (Though in this flow, we usually just iterate accounts, this is safer)
        cust_map = {c['ID']: c for c in customer_contexts}

        for acc in account_contexts:
            cust_id = acc['CUSTOMER_SOURCE_UNIQUE_ID']
            
            # Context for Link is simple, we mostly just map to CSV
            row = []
            for i, col in enumerate(self.link_spec['columns']):
                col_name = col.upper()
                col_type = self.link_spec['types'][i] if i < len(self.link_spec['types']) else "STRING"
                val = ""
                
                if col_name == 'ACCOUNT_SOURCE_UNIQUE_ID': val = acc['ACCOUNT_SOURCE_UNIQUE_ID']
                elif col_name == 'CUSTOMER_SOURCE_UNIQUE_ID': val = cust_id
                elif col_name == 'CUSTOMER_ROLE': val = 'PRIMARY'
                elif col_name == 'FROM_DATE': val = acc['DATE_OPENED']
                
                is_mandatory = self.link_spec['mandatory'][i] if i < len(self.link_spec['mandatory']) else 'NO'
                if is_mandatory == 'YES' and not val: val = "N"
                row.append(self._enforce_length(val, col_type))
            
            csv_rows.append(row)
            
        return csv_rows