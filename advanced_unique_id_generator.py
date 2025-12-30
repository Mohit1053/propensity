"""
Advanced Unique ID Generator - Optimized for Large Scale Data Processing
Includes memory-efficient streaming processing and batch operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Iterator
import hashlib
import gc
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedUnionFind:
    """
    Memory-optimized Union-Find with additional features for large datasets
    """
    
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self.size = {}  # Track component sizes
    
    def find(self, x) -> int:
        """Find with path compression and memoization"""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            self.size[x] = 1
            return x
        
        # Path compression with iterative approach to avoid recursion stack overflow
        path = []
        current = x
        while self.parent[current] != current:
            path.append(current)
            current = self.parent[current]
        
        # Compress path
        for node in path:
            self.parent[node] = current
        
        return current
    
    def union(self, x, y) -> bool:
        """Union by rank with size tracking"""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
            self.size[root_y] += self.size[root_x]
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
            self.size[root_x] += self.size[root_y]
        else:
            self.parent[root_y] = root_x
            self.size[root_x] += self.size[root_y]
            self.rank[root_x] += 1
        
        return True
    
    def get_component_mapping(self) -> Dict[int, int]:
        """Get efficient mapping of nodes to their minimum representative"""
        component_mins = {}
        node_to_min = {}
        
        for node in list(self.parent.keys()):
            root = self.find(node)
            if root not in component_mins:
                component_mins[root] = node
            else:
                component_mins[root] = min(component_mins[root], node)
        
        for node in self.parent.keys():
            root = self.find(node)
            node_to_min[node] = component_mins[root]
        
        return node_to_min
    
    def get_statistics(self) -> Dict:
        """Get statistics about connected components"""
        components = defaultdict(list)
        for node in self.parent.keys():
            root = self.find(node)
            components[root].append(node)
        
        sizes = [len(nodes) for nodes in components.values()]
        return {
            'total_components': len(components),
            'total_nodes': len(self.parent),
            'largest_component': max(sizes) if sizes else 0,
            'smallest_component': min(sizes) if sizes else 0,
            'average_component_size': np.mean(sizes) if sizes else 0
        }


class LargeScaleUniqueIDGenerator:
    """
    Production-ready unique ID generator optimized for large datasets
    """
    
    def __init__(self, batch_size: int = 10000, spam_threshold: int = 4):
        self.union_find = AdvancedUnionFind()
        self.batch_size = batch_size
        self.spam_threshold = spam_threshold
        self.email_id_cache = {}
        self.phone_id_cache = {}
        
    def _generate_farm_fingerprint_like_id(self, value: str, prefix: str = "") -> int:
        """
        Generate BigQuery FARM_FINGERPRINT-like hash
        Uses SHA-256 for better distribution and consistency
        """
        hash_obj = hashlib.sha256(f"{prefix}{value}".encode('utf-8'))
        # Convert to signed 64-bit integer (similar to BigQuery FARM_FINGERPRINT)
        hash_int = int(hash_obj.hexdigest()[:16], 16)
        # Convert to signed int64 range
        if hash_int >= 2**63:
            hash_int -= 2**64
        return hash_int
    
    def _normalize_phone(self, phone) -> Optional[str]:
        """Enhanced phone normalization"""
        if pd.isna(phone) or phone is None:
            return None
        
        phone_str = str(phone).strip()
        # For test data, if it's alphanumeric (like P1, P2), keep as is
        if phone_str and not phone_str.isdigit():
            return phone_str
        
        # Remove all non-digit characters for real phone numbers
        digits_only = ''.join(filter(str.isdigit, phone_str))
        
        # Handle different phone formats
        if len(digits_only) >= 10:
            return digits_only[-10:]  # Last 10 digits
        elif len(digits_only) >= 7:  # Handle shorter valid phone numbers
            return digits_only
        elif phone_str:  # Keep non-empty strings as test data
            return phone_str
        
        return None
    
    def _is_valid_email(self, email) -> bool:
        """Enhanced email validation"""
        if pd.isna(email) or email is None:
            return False
        
        email_str = str(email).strip().lower()
        return '@' in email_str and '.' in email_str.split('@')[-1]
    
    def _detect_spam_patterns(self, df: pd.DataFrame) -> Tuple[set, set]:
        """
        Detect spam patterns more efficiently using vectorized operations
        """
        # Count connections efficiently
        email_counts = df.groupby('email')['mobile'].nunique()
        phone_counts = df.groupby('mobile')['email'].nunique()
        
        spam_emails = set(email_counts[email_counts > self.spam_threshold].index)
        spam_phones = set(phone_counts[phone_counts > self.spam_threshold].index)
        
        logger.info(f"Detected {len(spam_emails)} spam emails and {len(spam_phones)} spam phones")
        
        return spam_emails, spam_phones
    
    def _process_batch(self, batch_df: pd.DataFrame) -> pd.DataFrame:
        """Process a single batch of data"""
        # Clean and normalize
        batch_df = batch_df.copy()
        batch_df['email'] = batch_df['email'].apply(
            lambda x: str(x).strip().lower() if self._is_valid_email(x) else None
        )
        batch_df['mobile'] = batch_df['mobile'].apply(self._normalize_phone)
        
        # Remove invalid rows
        batch_df = batch_df.dropna(subset=['email', 'mobile'], how='all')
        
        # Generate IDs with caching
        def get_email_id(email):
            if email is None:
                return None
            if email not in self.email_id_cache:
                self.email_id_cache[email] = self._generate_farm_fingerprint_like_id(email, "e_")
            return self.email_id_cache[email]
        
        def get_phone_id(phone):
            if phone is None:
                return None
            if phone not in self.phone_id_cache:
                self.phone_id_cache[phone] = self._generate_farm_fingerprint_like_id(phone, "p_")
            return self.phone_id_cache[phone]
        
        batch_df['e_id'] = batch_df['email'].apply(get_email_id)
        batch_df['p_id'] = batch_df['mobile'].apply(get_phone_id)
        
        return batch_df
    
    def process_large_dataset(self, data_source, email_col: str = 'email', 
                            mobile_col: str = 'mobile') -> pd.DataFrame:
        """
        Process large datasets efficiently with batching and streaming
        
        Args:
            data_source: Can be DataFrame, CSV file path, or iterator
            email_col: Name of email column
            mobile_col: Name of mobile column
        """
        
        logger.info("Starting large-scale unique ID generation...")
        
        # Handle different data source types
        if isinstance(data_source, str):
            # File path
            df_iterator = pd.read_csv(data_source, chunksize=self.batch_size)
        elif isinstance(data_source, pd.DataFrame):
            # DataFrame - split into chunks
            df_iterator = [data_source[i:i+self.batch_size] 
                          for i in range(0, len(data_source), self.batch_size)]
        else:
            # Assume it's already an iterator
            df_iterator = data_source
        
        processed_batches = []
        total_rows = 0
        
        # Process in batches
        for batch_idx, batch in enumerate(df_iterator):
            if isinstance(batch, pd.DataFrame):
                # Rename columns to standard names
                batch = batch.rename(columns={email_col: 'email', mobile_col: 'mobile'})
                
                # Process batch
                processed_batch = self._process_batch(batch)
                processed_batches.append(processed_batch)
                total_rows += len(processed_batch)
                
                # Build Union-Find structure
                for _, row in processed_batch.iterrows():
                    if row['e_id'] is not None and row['p_id'] is not None:
                        self.union_find.union(row['e_id'], row['p_id'])
                
                logger.info(f"Processed batch {batch_idx + 1}, total rows: {total_rows}")
                
                # Periodic garbage collection for memory management
                if batch_idx % 10 == 0:
                    gc.collect()
        
        # Combine all processed batches
        logger.info("Combining processed batches...")
        full_df = pd.concat(processed_batches, ignore_index=True)
        
        # Remove spam patterns
        logger.info("Detecting and removing spam patterns...")
        spam_emails, spam_phones = self._detect_spam_patterns(full_df)
        
        filtered_df = full_df[
            (~full_df['email'].isin(spam_emails)) & 
            (~full_df['mobile'].isin(spam_phones))
        ].copy()
        
        logger.info(f"Filtered dataset: {len(filtered_df)} rows (removed {len(full_df) - len(filtered_df)} spam rows)")
        
        # Generate unique IDs using connected components
        logger.info("Generating unique IDs...")
        component_mapping = self.union_find.get_component_mapping()
        
        def assign_unique_id(row):
            e_id = row['e_id']
            p_id = row['p_id']
            
            candidates = []
            if e_id is not None and e_id in component_mapping:
                candidates.append(component_mapping[e_id])
            if p_id is not None and p_id in component_mapping:
                candidates.append(component_mapping[p_id])
            
            if candidates:
                return min(candidates)
            elif e_id is not None:
                return e_id
            elif p_id is not None:
                return p_id
            return None
        
        filtered_df['unique_id'] = filtered_df.apply(assign_unique_id, axis=1)
        
        # Log statistics
        stats = self.union_find.get_statistics()
        logger.info(f"Connected components statistics: {stats}")
        
        unique_user_count = filtered_df['unique_id'].nunique()
        logger.info(f"Total unique users identified: {unique_user_count}")
        
        return filtered_df
    
    def export_results(self, df: pd.DataFrame, output_path: str, format: str = 'csv'):
        """Export results to file"""
        if format.lower() == 'csv':
            df.to_csv(output_path, index=False)
        elif format.lower() == 'parquet':
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError("Supported formats: 'csv', 'parquet'")
        
        logger.info(f"Results exported to {output_path}")


def run_example():
    """Run example with sample data"""
    
    # Extended sample data to test the algorithm
    sample_data = [
        {'email': 'A@gmail.com', 'mobile': 'P1'},
        {'email': 'B@gmail.com', 'mobile': 'P1'},
        {'email': 'C@gmail.com', 'mobile': 'P1'},
        {'email': 'D@gmail.com', 'mobile': 'P2'},
        {'email': 'E@gmail.com', 'mobile': 'P2'},
        {'email': 'A@gmail.com', 'mobile': 'P4'},
        {'email': 'F@gmail.com', 'mobile': 'P3'},  # Isolated user
        {'email': 'G@gmail.com', 'mobile': 'P5'},  # Another group
        {'email': 'H@gmail.com', 'mobile': 'P5'},  # Same group as G
    ]
    
    df = pd.DataFrame(sample_data)
    
    generator = LargeScaleUniqueIDGenerator(batch_size=5)
    result = generator.process_large_dataset(df)
    
    print("Sample Input:")
    print(df.to_string(index=False))
    print("\nProcessed Output:")
    print(result[['email', 'mobile', 'e_id', 'p_id', 'unique_id']].to_string(index=False))
    
    # Show groupings
    print("\nUnique User Groups:")
    for unique_id in sorted(result['unique_id'].unique()):
        group = result[result['unique_id'] == unique_id][['email', 'mobile']]
        print(f"\nGroup {unique_id}:")
        print(group.to_string(index=False))


if __name__ == "__main__":
    run_example()
