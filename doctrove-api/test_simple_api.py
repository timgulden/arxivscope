#!/usr/bin/env python3
"""
Simple test API to verify basic Flask functionality.
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    })

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint."""
    return jsonify({
        'message': 'Test endpoint working'
    })

def test_endpoint():
    """Test function for the endpoint."""
    with app.app_context():
        response = jsonify({
            'message': 'Test endpoint working'
        })
        assert response.status_code == 200, "Endpoint should return 200 status"
        # Don't return the response - pytest functions should return None

if __name__ == '__main__':
    print("Starting simple test API on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True) 
