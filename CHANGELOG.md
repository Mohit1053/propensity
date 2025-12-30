# Changelog

All notable changes to the Unique ID Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- PyPI package distribution
- Async processing support
- Database connectors (PostgreSQL, MySQL)
- REST API wrapper

## [1.0.0] - 2025-12-30

### Added
- Initial release of Unique ID Generator
- Core implementations:
  - `unique_id_generator.py` - Basic Union-Find implementation
  - `advanced_unique_id_generator.py` - Production-ready optimized version
  - `test_and_benchmark.py` - Comprehensive test suite
  - `final_demonstration.py` - Usage demonstration

### Features
- Union-Find algorithm with path compression
- Spam detection for excessive connections
- Batch processing for large datasets
- Memory-efficient streaming processing
- BigQuery FARM_FINGERPRINT compatibility
- Configurable thresholds

### Performance
- O(n * α(n)) time complexity
- Linear space complexity
- Up to 12x speedup over basic algorithms

### Documentation
- Comprehensive README with examples
- Performance benchmarks
- Algorithm explanation
- Sample output files
