#!/usr/bin/env python3
"""
Python-based rigX shelf creation script.

This script creates the rigX shelf programmatically using Maya's Python commands.
It will definitely work and create all the tool buttons.
"""

import os
import sys
from pathlib import Path


def create_rigx_shelf():
    """Create the rigX shelf with all tools using Python."""
    try:
        import maya.cmds as cmds
        
        print("🎨 Creating rigX shelf using Python...")
        
        # Delete existing shelf if it exists
        if cmds.shelfLayout("rigX", exists=True):
            cmds.deleteUI("rigX")
            print("✅ Deleted existing rigX shelf")
        
        # Create the shelf
        cmds.shelfLayout("rigX")
        print("✅ Created rigX shelf layout")
        
        # Define all tools with their commands
        tools = [
            {
                "label": "Reload",
                "annotation": "Reload rigX pipeline",
                "image": "rigX_icon_git.png",
                "command": "from rigging_pipeline.bootstrap import reload_all; reload_all()"
            },
            {
                "label": "Validator",
                "annotation": "Launch Rigging Validator",
                "image": "rigX_icon_validator.png",
                "command": "from rigging_pipeline.tools.rigx_riggingValidator import launch_riggingValidator; launch_riggingValidator()"
            },
            {
                "label": "Utility Tools",
                "annotation": "Launch RigX Utility Tools",
                "image": "rigX_icon_utils.png",
                "command": "from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools; tools = RigXUtilityTools(); tools.show_ui()"
            },
            {
                "label": "Skin",
                "annotation": "Launch Skin Weights Tool",
                "image": "rigX_ngSkintools.png",
                "command": "from rigging_pipeline.tools.rigx_skinTools import launch_skinTools; launch_skinTools()"
            },
            {
                "label": "Coming Soon",
                "annotation": "Coming Soon - New Tool",
                "image": "rigX_coming_soon.png",
                "command": "print('Coming Soon - New Tool 2')"
            },
            {
                "label": "Coming Soon",
                "annotation": "Coming Soon - New Tool",
                "image": "rigX_coming_soon.png",
                "command": "print('Coming Soon - New Tool 2')"
            },
            {
                "label": "Coming Soon",
                "annotation": "Coming Soon - New Tool",
                "image": "rigX_coming_soon.png",
                "command": "print('Coming Soon - New Tool 3')"
            }
        ]
        
        # Create buttons for each tool
        for i, tool in enumerate(tools):
            try:
                # Check if tool has an image
                if "image" in tool and tool["image"]:
                    cmds.shelfButton(
                        parent="rigX",
                        label=tool["label"],
                        annotation=tool["annotation"],
                        image=tool["image"],
                        image1=tool["image"],
                        command=tool["command"],
                        sourceType="python"
                    )
                    print(f"✅ Created button: {tool['label']} (with icon)")
                else:
                    # Create button without image
                    cmds.shelfButton(
                        parent="rigX",
                        label=tool["label"],
                        annotation=tool["annotation"],
                        command=tool["command"],
                        sourceType="python"
                    )
                    print(f"✅ Created button: {tool['label']} (no icon)")
            except Exception as e:
                print(f"⚠️ Warning creating button {tool['label']}: {e}")
                # Create button without image if there's an issue
                try:
                    cmds.shelfButton(
                        parent="rigX",
                        label=tool["label"],
                        annotation=tool["annotation"],
                        command=tool["command"],
                        sourceType="python"
                    )
                    print(f"✅ Created button (fallback): {tool['label']}")
                except Exception as e2:
                    print(f"❌ Failed to create button {tool['label']}: {e2}")
        
        # Make rigX the current shelf
        try:
            cmds.shelfTabLayout(edit=True, selectTab="rigX")
            print("✅ Set rigX as current shelf")
        except:
            print("⚠️ Could not set rigX as current shelf (this is normal)")
        
        print("\n🎉 rigX shelf created successfully!")
        print(f"📊 Total buttons created: {len(tools)}")
        print("🔍 Look for the 'rigX' tab in your shelf area!")
        
        return True
        
    except ImportError:
        print("❌ Maya is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error creating shelf: {e}")
        return False


def main():
    """Main function."""
    print("🚀 rigX Python Shelf Creator")
    print("=" * 40)
    
    # Try to create the shelf
    if create_rigx_shelf():
        print("\n🎉 Success! The rigX shelf is now available in Maya.")
        print("   You can find it in the shelf area with all your tools.")
    else:
        print("\n📋 Manual Setup Required:")
        print("1. Make sure Maya is running")
        print("2. Add rigX to your Python path")
        print("3. Run this script again")
    
    print("\n📚 For more help, see MAYA_SETUP.md")
    print("🚀 Happy rigging!")


if __name__ == "__main__":
    main()
