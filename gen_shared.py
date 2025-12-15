import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import os
import re

class ReferenceLoader:
    """Shared Loader for all Spec files"""
    def __init__(self):
        self.maps = {}

    def load_file(self, file_path, key_idx=0, val_idx=1):
        """Standard Key-Value Loader"""
        data_map = {}
        valid_keys = []
        if not os.path.exists(file_path):
            return {}, []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()[1:] 
                for line in lines:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        key = parts[key_idx].strip()
                        val = parts[val_idx].strip()
                        data_map[key] = val
                        data_map[val.upper()] = key 
                        valid_keys.append(key)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return data_map, valid_keys

    def load_transaction_types(self, file_path):
        """Special Loader for Transaction Types (Complex Structure)"""
        data = []
        if not os.path.exists(file_path): return []
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()[1:]
                for line in lines:
                    parts = line.strip().split('|')
                    if len(parts) >= 4: 
                        data.append({
                            'CODE': parts[0].strip(),
                            'DESC': parts[1].strip(),
                            'SCOPE': parts[2].strip(), 
                            'INSTRUMENT': parts[3].strip()
                        })
        except: pass
        return data

class BaseGenerator:
    """Shared Helper methods for all Generators"""
    def __init__(self):
        self.fake = Faker()
        self.loader = ReferenceLoader()
    
    def _resolve_value(self, input_val, mapping, valid_list, default=None):
        """Strict Enum Enforcer"""
        if not input_val: return default if default else (random.choice(valid_list) if valid_list else "")
        clean_input = str(input_val).strip().upper()
        if clean_input in valid_list: return clean_input
        if clean_input in mapping: return mapping[clean_input]
        return default if default else (random.choice(valid_list) if valid_list else "")

    def _get_random_date(self, start_year=-5, end_year=0, fmt='%Y%m%d'):
        end = datetime.now() + timedelta(days=end_year*365)
        start = datetime.now() + timedelta(days=start_year*365)
        return self.fake.date_between(start_date=start, end_date=end).strftime(fmt)

    def _enforce_length(self, value, col_type):
        val_str = str(value)
        if 'STRING' in col_type and '(' in col_type:
            try:
                max_len = int(col_type.split('(')[1].split(')')[0])
                return val_str[:max_len]
            except: pass
        return val_str

    def _load_spec(self, file_path):
        """Generic Spec Loader"""
        if not os.path.exists(file_path): return {'columns': [], 'types': [], 'mandatory': []}
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if len(lines) < 3: return {'columns': [], 'types': [], 'mandatory': []}
                cols = lines[1].split('|')
                line2_upper = lines[2].upper()
                if 'STRING' in line2_upper or 'DATE' in line2_upper:
                    types = lines[2].split('|')
                    mandatory = lines[3].split('|') if len(lines) > 3 else []
                else: 
                    types = lines[3].split('|') if len(lines) > 3 else []
                    mandatory = lines[4].split('|') if len(lines) > 4 else []
                
                while len(types) < len(cols): types.append('STRING')
                while len(mandatory) < len(cols): mandatory.append('N')
                return {'columns': cols, 'types': types[:len(cols)], 'mandatory': mandatory[:len(cols)]}
        except: return {'columns': [], 'types': [], 'mandatory': []}