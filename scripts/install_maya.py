#!/usr/bin/env python3
"""
Maya installation script for rigX pipeline.

This script installs the rigX shelf and icons into Maya's preferences folder.
"""

import os
import shutil
import sys
from pathlib import Path


def get_maya_prefs_path():
    """Get Maya preferences path based on OS."""
    if sys.platform == "win32":
        # Windows
        maya_docs = os.path.expanduser("~/Documents/maya")
    elif sys.platform == "darwin":
        # macOS
        maya_docs = os.path.expanduser("~/Library/Preferences/Autodesk/maya")
    else:
        # Linux
        maya_docs = os.path.expanduser("~/maya")
    
    return maya_docs


def install_to_maya(rigx_root, maya_version=None):
    """Install rigX components to Maya preferences."""
    rigx_root = Path(rigx_root)
    
    # Maya prefs folder
    maya_prefs = Path(get_maya_prefs_path())
    
    if not maya_prefs.exists():
        print(f"⚠️ Maya preferences folder not found: {maya_prefs}")
        return False
    
    # Find Maya version folders
    maya_versions = [d for d in maya_prefs.iterdir() 
                    if d.is_dir() and d.name.isdigit()]
    
    if not maya_versions:
        print(f"⚠️ No Maya version folders found in: {maya_prefs}")
        return False
    
    # Use specified version or latest
    if maya_version:
        target_version = maya_prefs / maya_version
        if not target_version.exists():
            print(f"⚠️ Maya version {maya_version} not found")
            return False
        maya_versions = [target_version]
    
    # Install to each Maya version
    for maya_ver_path in maya_versions:
        print(f"📁 Installing to Maya {maya_ver_path.name}...")
        
        # Install shelf
        shelf_src = rigx_root / "config" / "shelves" / "shelf_rigX.mel"
        shelf_dst = maya_ver_path / "prefs" / "shelves" / "shelf_rigX.mel"
        
        if shelf_src.exists():
            shelf_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(shelf_src, shelf_dst)
            print(f"✅ Shelf installed: {shelf_dst}")
        else:
            print(f"⚠️ Shelf not found: {shelf_src}")
        
        # Install icons
        icons_src = rigx_root / "config" / "icons"
        icons_dst = maya_ver_path / "prefs" / "icons"
        
        if icons_src.exists():
            icons_dst.mkdir(parents=True, exist_ok=True)
            for icon_file in icons_src.glob("*.png"):
                shutil.copy2(icon_file, icons_dst)
                print(f"✅ Icon installed: {icon_file.name}")
        else:
            print(f"⚠️ Icons folder not found: {icons_src}")
    
    return True


def main():
    """Main installation function."""
    print("🚀 rigX Maya Installation")
    print("=" * 40)
    
    # Get rigX root directory
    script_dir = Path(__file__).parent
    rigx_root = script_dir.parent
    
    print(f"📁 rigX root: {rigx_root}")
    
    # Check if we're in the right place
    if not (rigx_root / "src" / "rigging_pipeline").exists():
        print("❌ Error: rigX source not found. Please run from rigX root directory.")
        return 1
    
    # Install to Maya
    success = install_to_maya(rigx_root)
    
    if success:
        print("\n🎉 rigX installation completed!")
        print("\nTo use rigX in Maya:")
        print("1. Add to Python path: sys.path.append(r'{}')".format(rigx_root / "src"))
        print("2. Import and reload: from rigging_pipeline.bootstrap import reload_all")
        print("3. Run: reload_all()")
    else:
        print("\n❌ Installation failed. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
