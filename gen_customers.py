import random
import re
from faker import Faker
from gen_shared import BaseGenerator

class CustomerGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.cust_spec = self._load_spec('01_Spec_Fields_customers.txt')
        
        # Load Maps
        self.country_map, self.country_codes = self.loader.load_file('00_Spec_Country.txt')
        self.org_map, self.org_codes = self.loader.load_file('00_Spec_Organization_Units.txt')
        self.gender_map, self.gender_codes = self.loader.load_file('00_Spec_Gender.txt')
        self.cust_type_map, self.cust_type_codes = self.loader.load_file('00_Spec_Customer_Type.txt')
        self.cust_seg_map, self.cust_seg_codes = self.loader.load_file('00_Spec_Customer_Segment.txt')
        self.cat_map, self.cat_codes = self.loader.load_file('00_Spec_Customer_Category.txt')
        _, self.branch_ids = self.loader.load_file('00_Spec_Branch.txt', key_idx=0, val_idx=1)
        _, self.employee_ids = self.loader.load_file('00_Spec_Employee.txt', key_idx=0, val_idx=1)
        self.phone_codes = {
            'US': '1', 'CA': '1', 'GB': '44', 'DE': '49', 'FR': '33', 'IT': '39',
            'ES': '34', 'NL': '31', 'CH': '41', 'AU': '61', 'JP': '81', 'CN': '86',
            'BR': '55', 'MX': '52', 'IN': '91', 'TR': '90', 'RO': '40', 'RU': '7'
        }
        self.fakers = {}

    def _get_faker_for_country(self, country_code):
        if country_code in self.fakers: return self.fakers[country_code]
        locale_map = {
            'US': 'en_US', 'GB': 'en_GB', 'DE': 'de_DE', 'FR': 'fr_FR',
            'IT': 'it_IT', 'ES': 'es_ES', 'NL': 'nl_NL', 'FI': 'fi_FI',
            'PL': 'pl_PL', 'RU': 'ru_RU', 'JP': 'ja_JP', 'CN': 'zh_CN',
            'BR': 'pt_BR', 'MX': 'es_MX', 'TR': 'tr_TR', 'RO': 'ro_RO'
        }
        locale = locale_map.get(country_code, 'en_US')
        try:
            fake = Faker(locale)
            self.fakers[country_code] = fake
            return fake
        except: return self.fake

    def _generate_smart_email(self, first, last, company, is_company):
        if is_company and company:
            clean_comp = re.sub(r'[^a-zA-Z]', '', company.split(' ')[0]).lower()
            return f"contact@{clean_comp}.com"
        else:
            f = re.sub(r'[^a-zA-Z]', '', first).lower()
            l = re.sub(r'[^a-zA-Z]', '', last).lower()
            return f"{f}.{l}@example.com"

    def _resolve_flag(self, val, default_val):
        if not val: return default_val
        clean = str(val).strip().upper()
        return clean if clean in ['Y', 'N'] else default_val

    def generate_single_profile(self, profile):
        # 1. RESOLVE COUNTRY & FAKER
        country_code = self._resolve_value(profile.get('country'), self.country_map, self.country_codes, default='US')
        local_fake = self._get_faker_for_country(country_code)

        raw_type = profile.get('type')
        
        # --- FIX START ---
        # 1. Trust the Input for the Logic Flag (C vs P) to prevent defaulting to Corporate
        is_company = (raw_type == 'C')

        # 2. Resolve the Code for the CSV (Allows fallback to 'C' code if P is missing in spec, without breaking logic)
        cust_type = self._resolve_value(raw_type, self.cust_type_map, self.cust_type_codes, default='C')
        # --- FIX END ---
        
        # 2. IDENTITY LOGIC
        legal_name = ""
        first_name = ""
        last_name = ""
        gender_code = ""
        person_title = ""
        company_form = ""
        registered_number = ""
        incorp_date = ""
        incorp_country = ""
        
        if is_company:
            legal_name = profile.get('legal_name') or profile.get('name') or local_fake.company()
            company_form = profile.get('company_form', '') 
            if company_form and company_form.lower() not in legal_name.lower():
                legal_name = f"{legal_name} {company_form}"
            
            registered_number = profile.get('registered_number') or f"REG-{random.randint(10000,99999)}"
            incorp_date = profile.get('incorporation_date') or self._get_random_date(start_year=-10, end_year=-1)
            incorp_country = country_code
        else:
            first_name = profile.get('first_name') or local_fake.first_name()
            last_name = profile.get('last_name') or local_fake.last_name()
            legal_name = f"{first_name} {last_name}"
            
            gender_input = profile.get('gender', 'Male' if random.random() > 0.5 else 'Female')
            gender_code = self._resolve_value(gender_input, self.gender_map, self.gender_codes)
            
            if gender_code == 'GN0001': person_title = "Mr"
            elif gender_code == 'GN0002': person_title = "Ms"

        # 3. SEGMENTATION
        biz_seg_desc = str(profile.get('business_segment', ''))[:50]
        email = self._generate_smart_email(first_name, last_name, legal_name, is_company)
        
        # 4. Phone Details
        # First check for explicit phone_country_code, then fall back to country of residence
        phone_country = (
            profile.get('phone_country_code') or
            self.phone_codes.get(country_code, '1')
        )
        phone_area = f"{random.randint(10, 999):03d}"
        phone_num = f"{random.randint(1000000, 9999999)}"
        phone_ext = ""

        # 5. Tax Number Type (Deterministic based on Country & Type)
        tax_type = "TIN" # Default
        if country_code == 'US':
            tax_type = "EIN" if is_company else "SSN"
        elif country_code == 'GB':
            tax_type = "UTR" if is_company else "NINO"
        elif country_code == 'DE':
            tax_type = "STEUERNUMMER" if is_company else "STEUERID"
        elif country_code == 'FR':
            tax_type = "SIREN" if is_company else "SPI"
        elif country_code == 'IT':
             tax_type = "PIVA" if is_company else "CF"
        elif country_code == 'ES':
             tax_type = "CIF" if is_company else "NIF"
        
        # 6. CONSTRUCT CONTEXT
        ctx = {
            "ID": f"CUST-{random.randint(100000,999999)}",
            # Pass the SPECIFIC accounts for this customer to the next step
            "ACCOUNTS_BLUEPRINT": profile.get('accounts', []), 

            "ORG_UNIT": self._resolve_value(profile.get('org_unit'), self.org_map, self.org_codes, default='EUR'),
            "CUSTOMER_TYPE_CODE": cust_type,
            "CUSTOMER_CATEGORY_CODE": self._resolve_value(profile.get('category'), self.cat_map, self.cat_codes, default='RETAIL'),
            "CUSTOMER_SEGMENT_1": self._resolve_value(profile.get('segment'), self.cust_seg_map, self.cust_seg_codes, default='SME' if is_company else 'PERS'),
            
            "BUSINESS_SEGMENT_1": biz_seg_desc, 
            
            "COUNTRY_CODE": country_code,
            "CUSTOMER_NAME": legal_name,
            "COMPANY_NAME": legal_name if is_company else "",
            "FIRST_NAME": first_name,
            "LAST_NAME": last_name,
            "MIDDLE_NAMES": profile.get('middle_names', ''),
            "GENDER_CODE": gender_code,
            "PRIME_BRANCH_ID": str(random.choice(self.branch_ids) if self.branch_ids else "8").zfill(6),
            "RELATIONSHIP_MGR_ID": str(random.choice(self.employee_ids) if self.employee_ids else "000001").zfill(6),
            "ACQUISITION_DATE": self._get_random_date(),
            
            "REGISTERED_NUMBER": registered_number,
            "INCORPORATION_DATE": incorp_date,
            "INCORPORATION_COUNTRY_CODE": incorp_country,
            "MARITAL_STATUS": profile.get('marital_status', 'Single' if not is_company else ''),
            "OCCUPATION": profile.get('occupation', 'Employed' if not is_company else ''),
            "EMPLOYMENT_STATUS": "EMPLOYED" if not is_company else "",
            "DATE_OF_BIRTH": profile.get('date_of_birth') or (self.fake.date_of_birth(minimum_age=18).strftime('%Y%m%d') if not is_company else ""),
            "PLACE_OF_BIRTH": profile.get('place_of_birth') or (local_fake.city() if not is_company else ""),
            
            # FLAGS
            "RESIDENCE_FLAG": self._resolve_flag(profile.get('residence_flag'), 'Y'),
            "SPECIAL_ATTENTION_FLAG": self._resolve_flag(profile.get('special_attention_flag'), 'N'),
            "DECEASED_FLAG": self._resolve_flag(profile.get('deceased_flag'), 'N'),
            "BANKRUPT_FLAG": self._resolve_flag(profile.get('bankrupt_flag'), 'N'),
            "FACE_TO_FACE_FLAG": self._resolve_flag(profile.get('face_to_face_flag'), 'N'),
            "CUSTOMER_CHANNEL_REMOTE_FLAG": "N",
            "ADVERSE_MEDIA_FLAG_INGESTED": "N",

            # USAGE
            "WIRE_IN_NUMBER": profile.get('wire_in_number', ''),
            "WIRE_OUT_NUMBER": profile.get('wire_out_number', ''),
            "WIRE_IN_VOLUME": profile.get('wire_in_volume', ''),
            "WIRE_OUT_VOLUME": profile.get('wire_out_volume', ''),
            "CASH_IN_VOLUME": profile.get('cash_in_volume', ''),
            "CASH_OUT_VOLUME": profile.get('cash_out_volume', ''),
            "CHECK_IN_VOLUME": profile.get('check_in_volume', ''),
            "CHECK_OUT_VOLUME": profile.get('check_out_volume', ''),

            "SOURCE_OF_FUNDS": profile.get('source_of_funds', 'TRADING' if is_company else 'EMPLOYMENT'),
            "TAX_NUMBER": profile.get('tax_number') or f"{country_code}-{self.fake.random_number(digits=9)}",
            "TAX_NUMBER_ISSUED_BY": profile.get('tax_number_issued_by', country_code),
            "COMPANY_FORM": company_form,
            "BUSINESS_TYPE": profile.get('industry', "Trading") if is_company else "",
            "VAT_NUMBER": profile.get('vat_number', ""),
            "PERSON_TITLE": person_title,
            "TAX_NUMBER_TYPE": tax_type,

            
            # ADDRESS 
            "OVERRIDE_CITY": profile.get('city') or local_fake.city(),
            "OVERRIDE_ADDRESS": profile.get('street_address') or local_fake.street_address(),
            "POSTAL_CODE": profile.get('postal_code') or local_fake.postcode(),
            "IS_COMPANY": is_company,
            "EMAIL_ADDRESS": email,
            "PHONE_COUNTRY_CODE": phone_country,
            "PHONE_AREA_CODE": phone_area,
            "PHONE_NUMBER": phone_num,
            "PHONE_EXTENSION": phone_ext,

            
            "ROLE": profile.get('role', 'STANDARD'),
            "NETWORK_ID": profile.get('network_id', None)
        }
        return ctx

    def generate_rows(self, profiles, run_date):
        run_timestamp_val = f"{run_date}000000"
        context_list, csv_rows = [], []

        for p in profiles:
            ctx = self.generate_single_profile(p)
            context_list.append(ctx) 
            
            row = []
            for i, col in enumerate(self.cust_spec['columns']):
                col_name = col.upper()
                col_type = self.cust_spec['types'][i]
                val = ""
                
                if col_name == 'ORGUNIT_CODE': val = ctx['ORG_UNIT']
                elif col_name == 'RUN_TIMESTAMP' or 'TIMESTAMP' in col_type: val = run_timestamp_val
                elif col_name == 'CUSTOMER_STATUS_CODE': val = 'ACTIVE'
                elif col_name == 'EMPLOYEE_FLAG': val = 'N'
                elif col_name in ['CUSTOMER_SOURCE_UNIQUE_ID', 'CUSTOMER_SOURCE_REF_ID']: val = ctx['ID']
                elif col_name == 'ADDRESS': val = ctx.get('OVERRIDE_ADDRESS')
                elif col_name == 'CITY': val = ctx.get('OVERRIDE_CITY')
                elif col_name == 'POSTAL_CODE': val = ctx.get('POSTAL_CODE')
                elif col_name in ctx: val = ctx[col_name]
                elif 'EMAIL' in col_name: val = ctx.get('EMAIL_ADDRESS')
                elif col_name in ['COUNTRY_OF_RESIDENCE', 'COUNTRY_OF_ORIGIN', 'NATIONALITY_CODE']: val = ctx['COUNTRY_CODE']
                
                if self.cust_spec['mandatory'][i] == 'YES' and not val: val = "0" if 'NUMBER' in col_type else "N"
                row.append(self._enforce_length(val, col_type))
            csv_rows.append(row)
            
        return context_list, csv_rows