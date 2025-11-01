"""
Test script for ArXiv data ingestion.
Generates sample ArXiv data and tests the ingestion pipeline.
"""

import json
import tempfile
import os
from datetime import datetime, timedelta
import random

def generate_sample_arxiv_data(num_records: int = 10) -> list:
    """
    Generate sample ArXiv data for testing.
    
    Args:
        num_records: Number of sample records to generate
        
    Returns:
        List of sample ArXiv records
    """
    categories = [
        "cs.AI", "cs.LG", "cs.CV", "cs.NE", "cs.CL", "cs.IR", "cs.SE", "cs.DC",
        "math.NA", "math.OC", "stat.ML", "stat.TH", "physics.comp-ph"
    ]
    
    sample_data = []
    
    for i in range(num_records):
        # Generate ArXiv ID
        year = random.randint(2020, 2024)
        month = random.randint(1, 12)
        paper_num = random.randint(1, 99999)
        arxiv_id = f"{year:04d}.{month:05d}"
        
        # Generate dates
        created_date = datetime(year, month, random.randint(1, 28))
        updated_date = created_date + timedelta(days=random.randint(0, 30))
        
        record = {
            "id": arxiv_id,
            "title": f"Sample Paper {i+1}: A Study in Machine Learning",
            "abstract": f"This is a sample abstract for paper {i+1}. It discusses various aspects of machine learning and artificial intelligence.",
            "authors": [f"Author {j+1}" for j in range(random.randint(1, 4))],
            "categories": random.sample(categories, random.randint(1, 3)),
            "created": created_date.strftime("%Y-%m-%d"),
            "updated": updated_date.strftime("%Y-%m-%d"),
            "doi": f"10.1234/arxiv.{arxiv_id}",
            "journal_ref": f"Journal of AI Research {year}",
            "report_no": f"arXiv:{arxiv_id}",
            "license": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
            "submitter": f"Researcher {i+1}"
        }
        
        sample_data.append(record)
    
    return sample_data

def create_test_json_file(data: list, filename: str = None) -> str:
    """
    Create a temporary JSON file with test data.
    
    Args:
        data: List of data records
        filename: Optional filename (if None, creates temp file)
        
    Returns:
        Path to the created JSON file
    """
    if filename is None:
        # Create temporary file
        fd, filename = tempfile.mkstemp(suffix='.json')
        os.close(fd)
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

def test_json_ingestor():
    """Test the JSON ingestor functions."""
    print("Testing JSON ingestor...")
    
    # Generate sample data
    sample_data = generate_sample_arxiv_data(5)
    
    # Create test file
    test_file = create_test_json_file(sample_data)
    
    try:
        from json_ingestor import (
            load_json_to_dict_list, 
            validate_json_structure, 
            get_json_field_names,
            sample_json_data
        )
        
        # Test loading
        loaded_data = load_json_to_dict_list(test_file)
        print(f"✓ Loaded {len(loaded_data)} records from JSON")
        
        # Test field detection
        fields = get_json_field_names(test_file)
        print(f"✓ Detected fields: {fields}")
        
        # Test validation
        required_fields = ['id', 'title', 'abstract']
        errors = validate_json_structure(loaded_data, required_fields)
        if errors:
            print(f"✗ Validation errors: {errors}")
        else:
            print("✓ JSON structure validation passed")
        
        # Test sampling
        sample = sample_json_data(test_file, 2)
        print(f"✓ Sampled {len(sample)} records")
        
    finally:
        # Clean up
        os.unlink(test_file)
    
    print("JSON ingestor tests completed\n")

def test_source_config():
    """Test the source configuration system."""
    print("Testing source configuration...")
    
    from source_configs import get_source_config, validate_source_config, ARXIV_CONFIG
    
    # Test ArXiv config
    arxiv_config = get_source_config('arxiv')
    print(f"✓ Loaded ArXiv config: {arxiv_config['source_name']}")
    
    # Test validation
    errors = validate_source_config(arxiv_config)
    if errors:
        print(f"✗ Config validation errors: {errors}")
    else:
        print("✓ ArXiv config validation passed")
    
    # Test field mappings
    field_mappings = arxiv_config['field_mappings']
    print(f"✓ Field mappings: {list(field_mappings.keys())}")
    
    print("Source configuration tests completed\n")

def test_generic_transformers():
    """Test the generic transformers."""
    print("Testing generic transformers...")
    
    from generic_transformers import transform_json_to_papers, count_papers_by_source_generic
    from source_configs import get_source_config
    
    # Generate sample data
    sample_data = generate_sample_arxiv_data(3)
    
    # Get ArXiv config
    arxiv_config = get_source_config('arxiv')
    
    # Test transformation
    common_papers, source_metadata_list = transform_json_to_papers(sample_data, arxiv_config)
    
    print(f"✓ Transformed {len(common_papers)} papers")
    print(f"✓ Generated {len(source_metadata_list)} metadata records")
    
    # Test counting
    counts = count_papers_by_source_generic(common_papers)
    print(f"✓ Paper counts by source: {counts}")
    
    # Show sample transformed paper
    if common_papers:
        sample_paper = common_papers[0]
        print(f"✓ Sample paper ID: {sample_paper['doctrove_paper_id']}")
        print(f"✓ Sample paper title: {sample_paper['doctrove_title']}")
        print(f"✓ Sample paper source: {sample_paper['doctrove_source']}")
    
    print("Generic transformers tests completed\n")

def test_full_pipeline():
    """Test the full ingestion pipeline (without database)."""
    print("Testing full pipeline (without database)...")
    
    # Generate sample data
    sample_data = generate_sample_arxiv_data(5)
    
    # Create test file
    test_file = create_test_json_file(sample_data)
    
    try:
        from main_ingestor import validate_data_interceptor, load_papers_interceptor
        
        # Create context
        from source_configs import get_source_config
        source_config = get_source_config('arxiv')
        
        context = {
            'json_path': test_file,
            'source_config': source_config
        }
        
        # Test validation
        context = validate_data_interceptor(context)
        print("✓ Data validation passed")
        
        # Test loading
        context = load_papers_interceptor(context)
        print(f"✓ Loaded {len(context['common_papers'])} papers")
        
    finally:
        # Clean up
        os.unlink(test_file)
    
    print("Full pipeline tests completed\n")

def test_arxiv_link_builder_unit():
    """Unit-test arXiv link generation (arXiv, PDF, DOI, Journal URL)."""
    print("Testing arXiv link builder (unit)...")
    import arxiv_ingester as ai
    # Case 1: full URL id with DOI and journal URL
    record1 = {
        'id': 'http://arxiv.org/abs/2501.01234v2',
        'title': 'X',
        'abstract': 'Y',
        'authors': ['A'],
        'created': '2025-01-02',
        'doi': '10.1234/abc.def',
        'journal_ref': 'https://journal.example.com/paper/abc'
    }
    md1 = ai.extract_arxiv_metadata(record1, record1['id'])
    assert 'links' in md1, 'links missing in metadata'
    links1 = json.loads(md1['links'])
    labels1 = [l.get('title') for l in links1]
    assert labels1[:2] == ['arXiv', 'PDF'], 'arXiv/PDF ordering wrong'
    assert 'DOI' in labels1, 'DOI link missing'
    assert 'Journal' in labels1, 'Journal link missing when URL present'
    assert links1[0]['href'].startswith('https://arxiv.org/abs/2501.01234'), 'abs URL malformed'
    assert links1[1]['href'].startswith('https://arxiv.org/pdf/2501.01234.pdf'), 'pdf URL malformed'
    # Case 2: bare ID, no DOI, non-URL journal ref
    record2 = {
        'id': '2502.00001',
        'title': 'X',
        'abstract': 'Y',
        'authors': ['A'],
        'created': '2025-02-03',
        'journal_ref': 'Phys.Rev.D76:013009,2007'
    }
    md2 = ai.extract_arxiv_metadata(record2, record2['id'])
    links2 = json.loads(md2.get('links', '[]'))
    labels2 = [l.get('title') for l in links2]
    assert labels2 == ['arXiv', 'PDF'], 'Unexpected extra links when DOI/journal URL absent'
    print("✓ arXiv link builder unit tests passed")


def main():
    """Run all tests."""
    print("Running ArXiv ingestion tests...\n")
    
    try:
        test_json_ingestor()
        test_source_config()
        test_generic_transformers()
        test_full_pipeline()
        # Unit: arXiv link builder
        test_arxiv_link_builder_unit()
        
        print("All tests passed! ✅")
        print("\nTo test with real data:")
        print("python main_ingestor.py your_arxiv_data.json --limit 100")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()