#!/usr/bin/env python3
import pandas as pd

df = pd.read_pickle('../final_df_country.pkl')
sample = df.iloc[0]

print('Sample data sizes:')
total_size = 0
for col in df.columns:
    if pd.notna(sample[col]):
        size = len(str(sample[col]))
        total_size += size
        print(f'{col}: {size} chars')
    else:
        print(f'{col}: None')

print(f'\nTotal size: {total_size} chars')
print(f'Total size in bytes: {total_size} bytes') 