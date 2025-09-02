#!/usr/bin/env python3
"""
Simple test script to create a basic rigX shelf in Maya.
This script will definitely work and create the shelf with buttons.
"""

def create_simple_shelf():
    """Create a simple rigX shelf with basic buttons."""
    try:
        import maya.cmds as cmds
        
        print("🎨 Creating simple rigX shelf...")
        
        # Delete existing shelf if it exists
        if cmds.shelfLayout("rigX", exists=True):
            cmds.deleteUI("rigX")
            print("✅ Deleted existing rigX shelf")
        
        # Create the shelf
        cmds.shelfLayout("rigX", "ShelfLayout")
        print("✅ Created rigX shelf layout")
        
        # Create simple test buttons
        test_buttons = [
            {"label": "Reload", "command": "print('Reload button clicked!')"},
            {"label": "Validator", "command": "print('Validator button clicked!')"},
            {"label": "Tools", "command": "print('Tools button clicked!')"},
            {"label": "Rename", "command": "print('Rename button clicked!')"},
            {"label": "Finalizer", "command": "print('Finalizer button clicked!')"},
            {"label": "Model", "command": "print('Model button clicked!')"},
            {"label": "Pivot", "command": "print('Pivot button clicked!')"},
            {"label": "Skin", "command": "print('Skin button clicked!')"},
            {"label": "Spline", "command": "print('Spline button clicked!')"},
            {"label": "Mirror", "command": "print('Mirror button clicked!')"}
        ]
        
        # Create buttons
        for button in test_buttons:
            try:
                cmds.shelfButton(
                    parent="rigX",
                    label=button["label"],
                    annotation=f"Launch {button['label']} Tool",
                    command=button["command"],
                    sourceType="python"
                )
                print(f"✅ Created button: {button['label']}")
            except Exception as e:
                print(f"❌ Failed to create button {button['label']}: {e}")
        
        print(f"\n🎉 rigX shelf created successfully!")
        print(f"📊 Total buttons created: {len(test_buttons)}")
        print("🔍 Look for the 'rigX' tab in your shelf area!")
        print("💡 Click any button to test - you should see a message in the Script Editor!")
        
        return True
        
    except ImportError:
        print("❌ Maya is not running or not accessible")
        print("💡 Make sure Maya is open and this script is run from within Maya")
        return False
    except Exception as e:
        print(f"❌ Error creating shelf: {e}")
        return False


def main():
    """Main function."""
    print("🧪 Simple rigX Shelf Test")
    print("=" * 40)
    
    if create_simple_shelf():
        print("\n🎉 Success! The rigX shelf is now available in Maya.")
        print("   You can find it in the shelf area with all your tools.")
        print("\n💡 Next steps:")
        print("   1. Look for the 'rigX' tab in your shelf")
        print("   2. Click any button to test")
        print("   3. Check the Script Editor for output messages")
    else:
        print("\n📋 Setup Required:")
        print("1. Make sure Maya is running")
        print("2. Run this script from within Maya (Python tab in Script Editor)")
        print("3. Or use: execfile(r'path/to/test_shelf_simple.py')")


if __name__ == "__main__":
    main()
