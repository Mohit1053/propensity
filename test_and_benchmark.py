"""
Utility script for testing and benchmarking the Unique ID Generator
Includes performance tests and comparison with different approaches
"""

import time
import pandas as pd
import numpy as np
from typing import List, Dict
import matplotlib.pyplot as plt
import seaborn as sns
from unique_id_generator import UniqueIDGenerator
from advanced_unique_id_generator import LargeScaleUniqueIDGenerator
import random
import string


def generate_test_data(num_users: int = 1000, overlap_ratio: float = 0.3) -> pd.DataFrame:
    """
    Generate synthetic test data for benchmarking
    
    Args:
        num_users: Number of base users
        overlap_ratio: Ratio of users that share emails/phones with others
    """
    
    def random_email():
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com']
        name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
        return f"{name}@{random.choice(domains)}"
    
    def random_phone():
        return ''.join(random.choices(string.digits, k=10))
    
    # Generate base data
    data = []
    unique_emails = [random_email() for _ in range(num_users)]
    unique_phones = [random_phone() for _ in range(num_users)]
    
    # Create base user records
    for i in range(num_users):
        data.append({
            'email': unique_emails[i],
            'mobile': unique_phones[i],
            'user_id': i  # True user ID for validation
        })
    
    # Add overlapping records to simulate real-world scenarios
    num_overlaps = int(num_users * overlap_ratio)
    for _ in range(num_overlaps):
        # Pick two random users and create cross-connections
        user1, user2 = random.sample(range(num_users), 2)
        
        # User1's email with User2's phone
        data.append({
            'email': unique_emails[user1],
            'mobile': unique_phones[user2],
            'user_id': min(user1, user2)  # Should map to same group
        })
        
        # User2's email with User1's phone
        data.append({
            'email': unique_emails[user2],
            'mobile': unique_phones[user1],
            'user_id': min(user1, user2)  # Should map to same group
        })
    
    return pd.DataFrame(data)


def benchmark_algorithms(test_sizes: List[int] = [100, 500, 1000, 5000]):
    """Benchmark different algorithm implementations"""
    
    results = []
    
    for size in test_sizes:
        print(f"\nTesting with {size} users...")
        
        # Generate test data
        test_data = generate_test_data(size, overlap_ratio=0.2)
        
        # Test basic algorithm
        start_time = time.time()
        basic_generator = UniqueIDGenerator()
        basic_result = basic_generator.process_from_dataframe(test_data)
        basic_time = time.time() - start_time
        
        # Test advanced algorithm
        start_time = time.time()
        advanced_generator = LargeScaleUniqueIDGenerator(batch_size=max(100, size//10))
        advanced_result = advanced_generator.process_large_dataset(test_data)
        advanced_time = time.time() - start_time
        
        # Calculate unique users found
        basic_unique_count = basic_result['unique_id'].nunique()
        advanced_unique_count = advanced_result['unique_id'].nunique()
        
        results.append({
            'dataset_size': size,
            'input_rows': len(test_data),
            'basic_time': basic_time,
            'advanced_time': advanced_time,
            'basic_unique_users': basic_unique_count,
            'advanced_unique_users': advanced_unique_count,
            'speedup': basic_time / advanced_time if advanced_time > 0 else 0
        })
        
        print(f"Basic algorithm: {basic_time:.3f}s, {basic_unique_count} unique users")
        print(f"Advanced algorithm: {advanced_time:.3f}s, {advanced_unique_count} unique users")
        print(f"Speedup: {basic_time / advanced_time:.2f}x" if advanced_time > 0 else "N/A")
    
    return pd.DataFrame(results)


def validate_algorithm_correctness():
    """Validate that the algorithm produces correct results"""
    
    print("Validating algorithm correctness...")
    
    # Test case 1: Simple connections
    test_data_1 = [
        {'email': 'user1@test.com', 'mobile': 'phone1'},
        {'email': 'user2@test.com', 'mobile': 'phone1'},  # Same phone -> same group
        {'email': 'user1@test.com', 'mobile': 'phone2'},  # Same email -> extends group
        {'email': 'user3@test.com', 'mobile': 'phone3'},  # Isolated user
    ]
    
    generator = UniqueIDGenerator()
    result_1 = generator.generate_unique_ids(test_data_1)
    
    # Validate: user1 and user2 should have same unique_id due to shared phone
    # user1 with phone2 should also be in the same group
    # user3 should be separate
    
    unique_ids = result_1['unique_id'].tolist()
    assert unique_ids[0] == unique_ids[1] == unique_ids[2], "Connected users should have same unique_id"
    assert unique_ids[3] not in unique_ids[:3], "Isolated user should have different unique_id"
    
    print("✓ Test case 1 passed")
    
    # Test case 2: Chain connections (A-B-C where A connects to B, B connects to C)
    test_data_2 = [
        {'email': 'A@test.com', 'mobile': 'phone1'},
        {'email': 'B@test.com', 'mobile': 'phone1'},  # A and B connected via phone1
        {'email': 'B@test.com', 'mobile': 'phone2'},  # B also has phone2
        {'email': 'C@test.com', 'mobile': 'phone2'},  # C connected to B via phone2
    ]
    
    generator = UniqueIDGenerator()
    result_2 = generator.generate_unique_ids(test_data_2)
    
    # All should be in same group (transitive connection)
    unique_ids = result_2['unique_id'].unique()
    assert len(unique_ids) == 1, "All transitively connected users should have same unique_id"
    
    print("✓ Test case 2 passed")
    
    # Test case 3: Spam filtering
    test_data_3 = []
    
    # Create a spam email that connects to many phones
    for i in range(6):
        test_data_3.append({'email': 'spam@test.com', 'mobile': f'phone{i}'})
    
    # Add legitimate users
    test_data_3.extend([
        {'email': 'legit1@test.com', 'mobile': 'legitphone1'},
        {'email': 'legit2@test.com', 'mobile': 'legitphone2'},
    ])
    
    generator = UniqueIDGenerator()
    result_3 = generator.generate_unique_ids(test_data_3)
    
    # Spam patterns should be filtered out
    assert 'spam@test.com' not in result_3['email'].values, "Spam email should be filtered out"
    assert len(result_3) == 2, "Only legitimate users should remain"
    
    print("✓ Test case 3 passed")
    
    print("All validation tests passed! ✓")


def analyze_results(df: pd.DataFrame, title: str = "Unique ID Analysis"):
    """Analyze and visualize the results"""
    
    print(f"\n{title}")
    print("=" * len(title))
    
    # Basic statistics
    print(f"Total records: {len(df)}")
    print(f"Unique users identified: {df['unique_id'].nunique()}")
    print(f"Reduction ratio: {len(df) / df['unique_id'].nunique():.2f}:1")
    
    # Group size distribution
    group_sizes = df.groupby('unique_id').size()
    print(f"\nGroup size distribution:")
    print(f"  Single-record users: {(group_sizes == 1).sum()}")
    print(f"  Multi-record users: {(group_sizes > 1).sum()}")
    print(f"  Largest group size: {group_sizes.max()}")
    print(f"  Average group size: {group_sizes.mean():.2f}")
    
    # Show largest groups
    if group_sizes.max() > 1:
        print(f"\nLargest user groups:")
        top_groups = group_sizes.nlargest(5)
        for unique_id, size in top_groups.items():
            if size > 1:
                group_data = df[df['unique_id'] == unique_id][['email', 'mobile']]
                print(f"\nGroup {unique_id} ({size} records):")
                print(group_data.to_string(index=False))


def create_performance_plots(benchmark_results: pd.DataFrame):
    """Create performance visualization plots"""
    
    try:
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Execution time comparison
        axes[0, 0].plot(benchmark_results['dataset_size'], benchmark_results['basic_time'], 
                       marker='o', label='Basic Algorithm', linewidth=2)
        axes[0, 0].plot(benchmark_results['dataset_size'], benchmark_results['advanced_time'], 
                       marker='s', label='Advanced Algorithm', linewidth=2)
        axes[0, 0].set_xlabel('Dataset Size')
        axes[0, 0].set_ylabel('Execution Time (seconds)')
        axes[0, 0].set_title('Algorithm Performance Comparison')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Speedup
        axes[0, 1].bar(range(len(benchmark_results)), benchmark_results['speedup'])
        axes[0, 1].set_xlabel('Test Case')
        axes[0, 1].set_ylabel('Speedup Factor')
        axes[0, 1].set_title('Advanced Algorithm Speedup')
        axes[0, 1].set_xticks(range(len(benchmark_results)))
        axes[0, 1].set_xticklabels([f"{size}" for size in benchmark_results['dataset_size']])
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Memory efficiency (input vs output rows)
        axes[1, 0].scatter(benchmark_results['input_rows'], benchmark_results['basic_unique_users'], 
                          label='Basic Algorithm', alpha=0.7, s=60)
        axes[1, 0].scatter(benchmark_results['input_rows'], benchmark_results['advanced_unique_users'], 
                          label='Advanced Algorithm', alpha=0.7, s=60)
        axes[1, 0].plot([0, benchmark_results['input_rows'].max()], 
                       [0, benchmark_results['input_rows'].max()], 
                       'k--', alpha=0.5, label='1:1 ratio')
        axes[1, 0].set_xlabel('Input Rows')
        axes[1, 0].set_ylabel('Unique Users Identified')
        axes[1, 0].set_title('Data Reduction Effectiveness')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Time complexity analysis
        axes[1, 1].loglog(benchmark_results['dataset_size'], benchmark_results['basic_time'], 
                         marker='o', label='Basic Algorithm')
        axes[1, 1].loglog(benchmark_results['dataset_size'], benchmark_results['advanced_time'], 
                         marker='s', label='Advanced Algorithm')
        axes[1, 1].set_xlabel('Dataset Size (log scale)')
        axes[1, 1].set_ylabel('Time (seconds, log scale)')
        axes[1, 1].set_title('Time Complexity Analysis')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('c:\\Users\\98765\\OneDrive\\Desktop\\Propensity\\performance_analysis.png', 
                    dpi=300, bbox_inches='tight')
        plt.show()
        
        print("Performance plots saved as 'performance_analysis.png'")
        
    except ImportError:
        print("Matplotlib not available. Skipping visualization.")
        print("Install with: pip install matplotlib seaborn")


def main():
    """Main function to run all tests and demonstrations"""
    
    print("Unique ID Generator - Comprehensive Testing Suite")
    print("=" * 50)
    
    # 1. Validate correctness
    validate_algorithm_correctness()
    
    # 2. Run example with provided sample data
    print("\n" + "=" * 50)
    print("SAMPLE DATA DEMONSTRATION")
    
    sample_data = [
        {'email': 'A@gmail', 'mobile': 'P1'},
        {'email': 'B@gmail', 'mobile': 'P1'},
        {'email': 'C@gmail', 'mobile': 'P1'},
        {'email': 'D@gmail', 'mobile': 'P2'},
        {'email': 'E@gmail', 'mobile': 'P2'},
        {'email': 'A@gmail', 'mobile': 'P4'},
    ]
    
    generator = UniqueIDGenerator()
    result = generator.generate_unique_ids(sample_data)
    
    print("\nInput:")
    input_df = pd.DataFrame(sample_data)
    print(input_df.to_string(index=False))
    
    print("\nOutput:")
    print(result[['email', 'mobile', 'e_id', 'p_id', 'unique_id']].to_string(index=False))
    
    analyze_results(result, "Sample Data Analysis")
    
    # 3. Performance benchmarking
    print("\n" + "=" * 50)
    print("PERFORMANCE BENCHMARKING")
    
    benchmark_results = benchmark_algorithms([100, 500, 1000])
    print("\nBenchmark Results:")
    print(benchmark_results.to_string(index=False))
    
    # 4. Create visualizations
    create_performance_plots(benchmark_results)
    
    # 5. Large dataset demonstration
    print("\n" + "=" * 50)
    print("LARGE DATASET DEMONSTRATION")
    
    large_data = generate_test_data(2000, overlap_ratio=0.25)
    print(f"Generated test dataset with {len(large_data)} records")
    
    advanced_generator = LargeScaleUniqueIDGenerator(batch_size=500)
    large_result = advanced_generator.process_large_dataset(large_data)
    
    analyze_results(large_result, "Large Dataset Analysis")
    
    # Export results
    large_result.to_csv('c:\\Users\\98765\\OneDrive\\Desktop\\Propensity\\large_dataset_results.csv', index=False)
    print("\nLarge dataset results saved to 'large_dataset_results.csv'")
    
    print("\n" + "=" * 50)
    print("TESTING COMPLETE!")
    print("\nKey Files Created:")
    print("- unique_id_generator.py (Basic implementation)")
    print("- advanced_unique_id_generator.py (Production-ready version)")
    print("- performance_analysis.png (Performance charts)")
    print("- large_dataset_results.csv (Sample output)")


if __name__ == "__main__":
    main()
