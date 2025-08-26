#!/usr/bin/env python
"""
Test script for RigX Tools
This script demonstrates how to use the new RigX Tools functionality
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from rigging_pipeline.tools.rigx_tools import RigXTools
    
    def test_rigx_tools():
        """Test the RigX Tools functionality"""
        print("Testing RigX Tools...")
        
        # Create an instance of the tool
        tools = RigXTools()
        
        # Show the UI
        print("Opening RigX Tools UI...")
        tools.show_ui()
        
        print("RigX Tools test completed successfully!")
        
    if __name__ == "__main__":
        test_rigx_tools()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory")
except Exception as e:
    print(f"Error: {e}")
