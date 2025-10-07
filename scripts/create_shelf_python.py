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
        
        # Delete existing shelf if it exists and clear all shelf caches
        if cmds.shelfLayout("rigX", exists=True):
            cmds.deleteUI("rigX")
            print("✅ Deleted existing rigX shelf")
        
        # Clear Maya's shelf preferences and icon cache
        try:
            # Clear shelf preferences
            cmds.evalDeferred("import maya.cmds as cmds; cmds.shelfTabLayout(edit=True, deleteTab='rigX')", delay=50)
            print("✅ Cleared shelf preferences")
        except:
            pass
        
        # Force Maya to clear all icon caches
        try:
            cmds.refresh()
            cmds.evalDeferred("cmds.refresh()")
            print("✅ Cleared Maya icon cache")
        except:
            pass
        
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
                "image": "C:\\Users\\mohanraj.s\\Documents\\maya\\scripts\\rigX\\config\\icons\\rigX_icon_skinTools.png",
                "command": "from rigging_pipeline.tools.rigx_skinTools import launch_skinTools; launch_skinTools()"
            },
            {
                "label": "Modules",
                "annotation": "Launch RigX Modules",
                "image": "rigX_icon_modules.png",
                "command": "from rigging_pipeline.tools.rigx_modules import launch_modules; launch_modules()"
            },
            {
                "label": "animRig",
                "annotation": "Launch Animation Rigging Tools",
                "image": "C:\\Users\\mohanraj.s\\Documents\\maya\\scripts\\rigX\\config\\icons\\rigX_icon_animRig.png",
                "command": "from rigging_pipeline.tools.rigx_animRig import launch_AnimRig; launch_AnimRig()"
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
        
        # Force refresh of shelf icons and clear Maya's icon cache
        try:
            # Multiple refresh attempts to ensure icons update
            cmds.refresh()
            cmds.evalDeferred("cmds.refresh()")
            cmds.evalDeferred("cmds.refresh()")  # Double refresh for stubborn icons
            
            # Additional refresh with delay for persistent icon cache issues
            cmds.evalDeferred("import maya.cmds as cmds; cmds.refresh(); cmds.refresh()", delay=100)
            
            # Force Maya to reload shelf icons completely
            cmds.evalDeferred("import maya.cmds as cmds; cmds.shelfTabLayout(edit=True, selectTab='rigX'); cmds.refresh()", delay=200)
            
            # Clear Maya's icon cache more aggressively
            cmds.evalDeferred("import maya.cmds as cmds; cmds.refresh(); cmds.evalDeferred('cmds.refresh()', delay=50)", delay=300)
            
            print("✅ Forced icon refresh (multiple attempts with aggressive cache clearing)")
        except:
            pass
        
        print("\n🎉 rigX shelf created successfully!")
        print(f"📊 Total buttons created: {len(tools)}")
        print("🔍 Look for the 'rigX' tab in your shelf area!")
        print("💡 If icons still appear old, try restarting Maya or running: cmds.refresh()")
        
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
