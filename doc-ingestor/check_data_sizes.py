#!/usr/bin/env python3
import pandas as pd
import numpy as np

df = pd.read_pickle('your_data_file.pkl')

# Fields that should be in metadata table (after removing duplicates)
metadata_fields = [
    'Paper ID', 'Author Affiliations', 'Links', 'Categories', 
    'Primary Category', 'Comment', 'Journal Ref', 'DOI', 'category',
    'country of origin', 'country', 'Country2', 'title_Embedding'
]

print('Metadata table field sizes (first 3 records):')
for i in range(min(3, len(df))):
    print(f'\n--- Record {i+1} ---')
    total_size = 0
    for col in metadata_fields:
        if col in df.columns:
            val = df.iloc[i][col]
            if isinstance(val, (np.ndarray, list)):
                size = len(val)
                print(f'{col}: array/list of length {size}')
                total_size += size * 8  # assume float64 for rough estimate
            elif pd.notna(val):
                size = len(str(val))
                total_size += size
                print(f'{col}: {size} chars')
            else:
                print(f'{col}: None')
        else:
            print(f'{col}: Not found in DataFrame')
    
    print(f'Total estimated size: {total_size} bytes')
    if total_size > 8000:
        print(f'*** WARNING: Size exceeds 8KB limit! ***') 