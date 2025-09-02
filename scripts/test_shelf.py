#!/usr/bin/env python3
"""
Test script to debug shelf creation in Maya.
"""

import os
import sys
from pathlib import Path


def test_maya_connection():
    """Test if we can connect to Maya."""
    try:
        import maya.cmds as cmds
        print("✅ Maya connection successful!")
        print(f"✅ Maya version: {cmds.about(version=True)}")
        return True
    except ImportError:
        print("❌ Maya is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Maya: {e}")
        return False


def test_shelf_creation():
    """Test creating a simple shelf in Maya."""
    try:
        import maya.cmds as cmds
        
        # Test if we can create a simple shelf
        test_shelf_name = "rigX_test"
        
        # Delete test shelf if it exists
        if cmds.shelfLayout(test_shelf_name, exists=True):
            cmds.deleteUI(test_shelf_name)
        
        # Create test shelf
        cmds.shelfLayout(test_shelf_name, "ShelfLayout")
        print(f"✅ Test shelf '{test_shelf_name}' created successfully!")
        
        # Create a test button
        cmds.shelfButton(
            parent=test_shelf_name,
            label="Test",
            annotation="Test button",
            command="print('Test button works!')"
        )
        print("✅ Test button created successfully!")
        
        # Clean up
        cmds.deleteUI(test_shelf_name)
        print("✅ Test shelf cleaned up!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test shelf: {e}")
        return False


def test_shelf_file():
    """Test if the shelf file exists and is readable."""
    script_dir = Path(__file__).parent
    rigx_root = script_dir.parent
    shelf_file = rigx_root / "config" / "shelves" / "shelf_RigX.mel"
    
    if shelf_file.exists():
        print(f"✅ Shelf file found: {shelf_file}")
        
        # Check file size
        file_size = shelf_file.stat().st_size
        print(f"✅ File size: {file_size} bytes")
        
        # Read first few lines
        try:
            with open(shelf_file, 'r') as f:
                first_lines = [next(f) for _ in range(5)]
            print("✅ File is readable. First 5 lines:")
            for i, line in enumerate(first_lines, 1):
                print(f"   {i}: {line.strip()}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
            
        return True
    else:
        print(f"❌ Shelf file not found: {shelf_file}")
        return False


def main():
    """Main test function."""
    print("🧪 rigX Shelf Debug Test")
    print("=" * 40)
    
    # Test 1: Maya connection
    print("\n1. Testing Maya connection...")
    maya_ok = test_maya_connection()
    
    # Test 2: Shelf file
    print("\n2. Testing shelf file...")
    file_ok = test_shelf_file()
    
    # Test 3: Shelf creation (if Maya is available)
    if maya_ok:
        print("\n3. Testing shelf creation...")
        shelf_ok = test_shelf_creation()
    else:
        print("\n3. Skipping shelf creation test (Maya not available)")
        shelf_ok = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS:")
    print(f"   Maya Connection: {'✅ PASS' if maya_ok else '❌ FAIL'}")
    print(f"   Shelf File: {'✅ PASS' if file_ok else '❌ FAIL'}")
    print(f"   Shelf Creation: {'✅ PASS' if shelf_ok else '❌ FAIL'}")
    
    if maya_ok and file_ok and shelf_ok:
        print("\n🎉 All tests passed! The shelf should work.")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")
    
    print("\n📚 For manual testing, try:")
    print("   source \"path/to/rigX/config/shelves/shelf_RigX.mel\";")


if __name__ == "__main__":
    main()
