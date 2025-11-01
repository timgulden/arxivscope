#!/usr/bin/env python3
"""
Utility script to switch between different visualization modes.
This allows easy comparison between title and abstract embeddings.
"""

import json
import os
from pathlib import Path

# Path to the settings file
SETTINGS_FILE = Path(__file__).parent.parent / "config" / "settings.py"

def update_visualization_config(embedding_type: str, show_connections: bool = False):
    """
    Update the visualization configuration in settings.py.
    
    Args:
        embedding_type: 'title', 'abstract', or 'both'
        show_connections: Whether to show lines connecting title and abstract points (only for 'both')
    """
    if embedding_type not in ['title', 'abstract', 'both']:
        raise ValueError("embedding_type must be 'title', 'abstract', or 'both'")
    
    # Read the current settings file
    with open(SETTINGS_FILE, 'r') as f:
        content = f.read()
    
    # Update the visualization configuration
    new_config = f"""# Visualization Configuration
VISUALIZATION_CONFIG = {{
    'embedding_type': '{embedding_type}',  # 'title', 'abstract', or 'both'
    'show_connections': {str(show_connections).title()},  # Whether to show lines connecting title and abstract points when using 'both'
    'connection_opacity': 0.3,  # Opacity of connection lines
    'point_size': 8,  # Size of scatter plot points
    'point_opacity': 0.8,  # Opacity of scatter plot points
}}"""
    
    # Find and replace the existing configuration
    import re
    pattern = r'# Visualization Configuration\s+VISUALIZATION_CONFIG = \{.*?\}'
    
    if re.search(pattern, content, re.DOTALL):
        # Replace existing configuration
        content = re.sub(pattern, new_config, content, flags=re.DOTALL)
    else:
        # Add new configuration after API_FIELDS
        api_fields_pattern = r'(API_FIELDS = .*?)\n\n'
        replacement = r'\1\n\n' + new_config + '\n\n'
        content = re.sub(api_fields_pattern, replacement, content, flags=re.DOTALL)
    
    # Write the updated content back
    with open(SETTINGS_FILE, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated visualization configuration:")
    print(f"   - Embedding type: {embedding_type}")
    print(f"   - Show connections: {show_connections}")
    print(f"   - Restart the frontend to see changes")

def switch_to_title_embeddings():
    """Switch to title embeddings visualization."""
    update_visualization_config('title', False)
    print("🎯 Switched to title embeddings")

def switch_to_abstract_embeddings():
    """Switch to abstract embeddings visualization."""
    update_visualization_config('abstract', False)
    print("📝 Switched to abstract embeddings")

def switch_to_both_embeddings(show_connections: bool = True):
    """Switch to both embeddings visualization with optional connections."""
    update_visualization_config('both', show_connections)
    if show_connections:
        print("🔗 Switched to both embeddings with connecting lines")
    else:
        print("⚫ Switched to both embeddings (title points only)")

def show_current_config():
    """Show the current visualization configuration."""
    with open(SETTINGS_FILE, 'r') as f:
        content = f.read()
    
    import re
    pattern = r'VISUALIZATION_CONFIG = \{.*?\}'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        config_str = match.group(0)
        print("📊 Current visualization configuration:")
        print(config_str)
    else:
        print("❌ No visualization configuration found")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python visualization_switcher.py title     # Switch to title embeddings")
        print("  python visualization_switcher.py abstract  # Switch to abstract embeddings")
        print("  python visualization_switcher.py both      # Switch to both embeddings with connections")
        print("  python visualization_switcher.py both-no   # Switch to both embeddings without connections")
        print("  python visualization_switcher.py show      # Show current configuration")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'title':
        switch_to_title_embeddings()
    elif command == 'abstract':
        switch_to_abstract_embeddings()
    elif command == 'both':
        switch_to_both_embeddings(True)
    elif command == 'both-no':
        switch_to_both_embeddings(False)
    elif command == 'show':
        show_current_config()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1) 