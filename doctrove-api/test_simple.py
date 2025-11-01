#!/usr/bin/env python3
"""
Simple test to see if Flask works without UMAP dependencies.
"""

from flask import Flask

app = Flask('test')

@app.route('/test')
def test():
    """Test endpoint that should return OK."""
    return 'OK'

def test():
    """Test function for pytest."""
    assert True, "Simple test should always pass"

if __name__ == '__main__':
    print('Starting simple Flask test...')
    app.run(host='0.0.0.0', port=5004, debug=False) 
"""
Simple test to see if Flask works without UMAP dependencies.
"""
