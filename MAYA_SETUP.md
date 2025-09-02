# 🎨 Maya Setup Guide - Getting rigX Shelf and Icons Working

This guide will help you get the rigX shelf and icons working in Maya on your system.

## 🚀 Quick Installation (Recommended)

### Windows Users
1. **Double-click** `install_maya.bat`
2. **Follow the prompts** - the script will do everything automatically
3. **Restart Maya** when installation is complete

### macOS/Linux Users
1. **Open Terminal** in the rigX folder
2. **Run**: `./install_maya.sh`
3. **Follow the prompts** - the script will do everything automatically
4. **Restart Maya** when installation is complete

## 🔧 Manual Installation

If the automatic scripts don't work, here's how to do it manually:

### Step 1: Find Your Maya Preferences Folder

**Windows:**
```
C:\Users\[USERNAME]\Documents\maya\[VERSION]\prefs\
```

**macOS:**
```
~/Library/Preferences/Autodesk/maya/[VERSION]/
```

**Linux:**
```
~/maya/[VERSION]/
```

Replace `[VERSION]` with your Maya version (e.g., `2024`, `2023`, etc.)

### Step 2: Install the Shelf

1. **Copy** `config/shelves/shelf_RigX.mel`
2. **Paste** into `[MAYA_PREFS]/shelves/`
3. **Create folders** if they don't exist

### Step 3: Install the Icons

1. **Copy** all files from `config/icons/`
2. **Paste** into `[MAYA_PREFS]/icons/`
3. **Skip** the `backUp/` folder (it's not needed)

## 🎯 What You'll Get

### The rigX Shelf
- **Appears in Maya** as a new shelf tab
- **Contains all tools** organized by category
- **Professional layout** with proper spacing

### Tool Icons
- **High-quality PNG** icons for each tool
- **Consistent style** across all tools
- **Proper sizing** for Maya's interface

## 🔍 Troubleshooting

### Shelf Not Visible?
1. **Restart Maya** completely
2. **Check Shelf Editor**: Window → UI Elements → Shelf Editor
3. **Look for "rigX"** in the shelf list
4. **Right-click** on shelf area → "rigX" should appear

### Icons Missing?
1. **Verify path**: Check if icons are in the right Maya folder
2. **Permissions**: Ensure you can write to Maya preferences
3. **Reinstall**: Run the installation script again

### Python Errors?
1. **Add to path**: `sys.path.append('/path/to/rigX/src')`
2. **Check Python version**: Must be 3.8 or higher
3. **Install dependencies**: `pip install -e .`

## 📱 Using rigX in Maya

### 1. Add to Python Path
```python
import sys
sys.path.append('/path/to/rigX/src')
```

### 2. Import and Reload
```python
from rigging_pipeline.bootstrap import reload_all
reload_all()
```

### 3. Access Tools
- **From Shelf**: Click any tool button
- **From Python**: Import specific modules
- **From Menu**: Tools should appear in Maya menus

## 🎨 Customizing the Shelf

### Adding Your Own Tools
1. **Edit** `config/shelves/shelf_RigX.mel`
2. **Add** your tool commands
3. **Place** your icons in `config/icons/`
4. **Reinstall** to update Maya

### Changing Icon Colors
1. **Modify** the PNG files in `config/icons/`
2. **Keep** the same dimensions
3. **Reinstall** to see changes

## 🆘 Still Having Issues?

### Check These Common Problems:
- ✅ Maya version compatibility (2020+)
- ✅ Python version (3.8+)
- ✅ File permissions
- ✅ Path separators (use `/` not `\` in Python)

### Get Help:
- **Email**: arjunanil.online@gmail.com
- **Issues**: [GitHub Issues](https://github.com/arjunanil-td/rigX/issues)
- **Documentation**: Check the `docs/` folder

---

**🎉 Success!** Once everything is working, you'll have a professional Maya shelf with all rigX tools at your fingertips. The shelf will automatically appear every time you start Maya!
