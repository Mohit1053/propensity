"""
Optimized Unique ID Generator for User Identification
Uses Union-Find (Disjoint Set Union) algorithm for efficient connected component detection.
Time Complexity: O(n * α(n)) where α is the inverse Ackermann function (practically constant)
Space Complexity: O(n) where n is the number of unique nodes (emails + phones)
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
import hashlib


class UnionFind:
    """
    Optimized Union-Find data structure with path compression and union by rank.
    This provides near-constant time operations for finding connected components.
    """
    
    def __init__(self):
        self.parent = {}
        self.rank = {}
    
    def find(self, x) -> int:
        """Find root with path compression optimization"""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            return x
        
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x, y) -> None:
        """Union by rank optimization"""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return
        
        # Union by rank - attach smaller tree under root of larger tree
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
    
    def get_groups(self) -> Dict[int, int]:
        """Get mapping of each node to its group representative (minimum node in component)"""
        groups = {}
        for node in self.parent:
            root = self.find(node)
            if root not in groups:
                groups[root] = []
            groups[root].append(node)
        
        # Return mapping where each node maps to minimum node in its component
        node_to_min = {}
        for group_nodes in groups.values():
            min_node = min(group_nodes)
            for node in group_nodes:
                node_to_min[node] = min_node
        
        return node_to_min


class UniqueIDGenerator:
    """
    Main class for generating unique user IDs based on email and phone connections.
    Efficiently handles large datasets with minimal memory overhead.
    """
    
    def __init__(self):
        self.union_find = UnionFind()
        self.email_to_id = {}
        self.phone_to_id = {}
        self.id_counter = 1
    
    def _get_hash_id(self, value: str, prefix: str = "") -> int:
        """Generate consistent hash-based ID for emails/phones"""
        # Using a simple hash for demonstration - you can replace with FARM_FINGERPRINT equivalent
        hash_obj = hashlib.md5(f"{prefix}{value}".encode())
        return int(hash_obj.hexdigest()[:8], 16)  # Use first 8 hex chars as integer
    
    def _get_or_create_id(self, value: str, value_type: str) -> int:
        """Get or create ID for email/phone with consistent hashing"""
        if value_type == "email":
            if value not in self.email_to_id:
                self.email_to_id[value] = self._get_hash_id(value, "e_")
            return self.email_to_id[value]
        else:  # phone
            if value not in self.phone_to_id:
                self.phone_to_id[value] = self._get_hash_id(value, "p_")
            return self.phone_to_id[value]
    
    def _normalize_phone(self, phone: str) -> str:
        """Extract last 10 digits from phone (similar to SQL substring logic)"""
        if pd.isna(phone) or phone is None:
            return None
        
        phone_str = str(phone).strip()
        # For test data, if it's alphanumeric (like P1, P2), keep as is
        if phone_str and not phone_str.isdigit():
            return phone_str
        
        # Remove non-digit characters for real phone numbers
        digits_only = ''.join(filter(str.isdigit, phone_str))
        
        if len(digits_only) >= 10:
            return digits_only[-10:]  # Last 10 digits
        elif len(digits_only) > 0:
            return digits_only
        elif phone_str:  # Keep non-empty strings as test data
            return phone_str
        return None
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        if pd.isna(email) or email is None:
            return False
        return '@' in str(email).strip()
    
    def _filter_spam_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out spam patterns based on your SQL logic:
        Remove emails/phones that appear with too many different counterparts
        """
        # Count unique phones per email and unique emails per phone
        email_phone_counts = df.groupby('email')['mobile'].nunique().reset_index()
        email_phone_counts.columns = ['email', 'phone_cnt']
        
        phone_email_counts = df.groupby('mobile')['email'].nunique().reset_index()
        phone_email_counts.columns = ['mobile', 'email_cnt']
        
        # Identify spam patterns (emails with >4 phones or phones with >4 emails)
        spam_emails = set(email_phone_counts[email_phone_counts['phone_cnt'] > 4]['email'])
        spam_phones = set(phone_email_counts[phone_email_counts['email_cnt'] > 4]['mobile'])
        
        # Filter out spam patterns
        filtered_df = df[
            (~df['email'].isin(spam_emails)) & 
            (~df['mobile'].isin(spam_phones))
        ].copy()
        
        return filtered_df
    
    def generate_unique_ids(self, data: List[Dict]) -> pd.DataFrame:
        """
        Main method to generate unique IDs for user data.
        
        Args:
            data: List of dictionaries with 'email' and 'mobile' keys
            
        Returns:
            DataFrame with original data plus e_id, p_id, and unique_id columns
        """
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data)
        
        # Normalize and validate data
        df['email'] = df['email'].apply(lambda x: str(x).strip().lower() if self._is_valid_email(x) else None)
        df['mobile'] = df['mobile'].apply(self._normalize_phone)
        
        # Remove rows where both email and phone are invalid
        df = df.dropna(subset=['email', 'mobile'], how='all')
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['email', 'mobile'])
        
        # Filter spam patterns
        df_filtered = self._filter_spam_patterns(df)
        
        # Generate e_id and p_id
        df_filtered['e_id'] = df_filtered['email'].apply(
            lambda x: self._get_or_create_id(x, "email") if x is not None else None
        )
        df_filtered['p_id'] = df_filtered['mobile'].apply(
            lambda x: self._get_or_create_id(x, "phone") if x is not None else None
        )
        
        # Build Union-Find structure for connected components
        for _, row in df_filtered.iterrows():
            e_id = row['e_id']
            p_id = row['p_id']
            
            if e_id is not None and p_id is not None:
                self.union_find.union(e_id, p_id)
        
        # Get group mappings (each node maps to minimum node in its component)
        group_mapping = self.union_find.get_groups()
        
        # Assign unique_id based on connected components
        def get_unique_id(row):
            e_id = row['e_id']
            p_id = row['p_id']
            
            # Get the minimum ID from the connected component
            candidates = []
            if e_id is not None and e_id in group_mapping:
                candidates.append(group_mapping[e_id])
            if p_id is not None and p_id in group_mapping:
                candidates.append(group_mapping[p_id])
            
            if candidates:
                return min(candidates)
            elif e_id is not None:
                return e_id
            elif p_id is not None:
                return p_id
            else:
                return None
        
        df_filtered['unique_id'] = df_filtered.apply(get_unique_id, axis=1)
        
        return df_filtered
    
    def process_from_dataframe(self, df: pd.DataFrame, email_col: str = 'email', 
                              phone_col: str = 'mobile') -> pd.DataFrame:
        """Process data directly from a pandas DataFrame"""
        data = df[[email_col, phone_col]].rename(
            columns={email_col: 'email', phone_col: 'mobile'}
        ).to_dict('records')
        
        result = self.generate_unique_ids(data)
        
        # Merge back with original data
        original_cols = [col for col in df.columns if col not in ['email', 'mobile']]
        if original_cols:
            result = result.merge(
                df[[email_col, phone_col] + original_cols],
                left_on=['email', 'mobile'],
                right_on=[email_col, phone_col],
                how='left'
            )
        
        return result


def main():
    """Example usage with the provided sample data"""
    
    # Sample input data
    sample_data = [
        {'email': 'A@gmail', 'mobile': 'P1'},
        {'email': 'B@gmail', 'mobile': 'P1'},
        {'email': 'C@gmail', 'mobile': 'P1'},
        {'email': 'D@gmail', 'mobile': 'P2'},
        {'email': 'E@gmail', 'mobile': 'P2'},
        {'email': 'A@gmail', 'mobile': 'P4'},
    ]
    
    # Generate unique IDs
    generator = UniqueIDGenerator()
    result = generator.generate_unique_ids(sample_data)
    
    print("Input Data:")
    input_df = pd.DataFrame(sample_data)
    print(input_df.to_string(index=False))
    
    print("\nOutput with Unique IDs:")
    print(result[['email', 'mobile', 'e_id', 'p_id', 'unique_id']].to_string(index=False))
    
    # Verify the logic
    print("\nUnique ID Groups:")
    for unique_id in result['unique_id'].unique():
        group_data = result[result['unique_id'] == unique_id][['email', 'mobile']]
        print(f"Group {unique_id}:")
        print(group_data.to_string(index=False))
        print()


if __name__ == "__main__":
    main()
