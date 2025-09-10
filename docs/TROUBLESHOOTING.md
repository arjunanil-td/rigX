# Maya Loading Troubleshooting Guide

If Maya is not loading after running the batch file, follow these steps:

## 🔍 **Step 1: Check Maya Script Editor**

1. Open Maya
2. Go to **Window → General Editors → Script Editor**
3. Look for any error messages in the **History** tab
4. Copy any error messages and check them against the solutions below

## 🛠️ **Step 2: Common Issues & Solutions**

### **Import Errors**
If you see errors like:
```
ImportError: No module named 'rigging_pipeline'
```

**Solution:**
1. Make sure the rigX `src` directory is in your Python path
2. In Maya's script editor, run:
```python
import sys
sys.path.append(r'C:\path\to\your\rigX\src')
```

### **Missing Dependencies**
If you see errors like:
```
ImportError: No module named 'PySide2'
```

**Solution:**
1. Install PySide2: `pip install PySide2`
2. Or use Maya's built-in Qt: Replace `from PySide2` with `from maya.app.general.mayaMixin import *`

### **File Not Found Errors**
If you see errors like:
```
FileNotFoundError: [Errno 2] No such file or directory
```

**Solution:**
1. Check that all rigX files are in the correct locations
2. Verify the installation script copied files to the right Maya preferences folder

## 🧪 **Step 3: Test Imports**

Run this test script in Maya's script editor:

```python
# Test script to verify imports
try:
    from rigging_pipeline.bootstrap import reload_all
    print("✅ Bootstrap import successful")
    
    from rigging_pipeline.tools.rigx_riggingValidator import launch_riggingValidator
    print("✅ Validator import successful")
    
    from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
    print("✅ Utility tools import successful")
    
         from rigging_pipeline.tools.rigx_skinTools import launch_skinTools
     print("✅ Skin tools import successful")
     
     # Note: Model tools removed to avoid circular imports
     print("⚠️ Model tools import skipped (removed to avoid circular imports)")
     
     print("🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
```

## 🔧 **Step 4: Manual Installation**

If the batch file isn't working:

1. **Copy the shelf manually:**
   - Copy `config/shelves/shelf_RigX.mel` to `~/Documents/maya/[VERSION]/prefs/shelves/`

2. **Copy icons manually:**
   - Copy all files from `config/icons/` to `~/Documents/maya/[VERSION]/prefs/icons/`

3. **Add to Python path:**
   - In Maya's script editor, run:
   ```python
   import sys
   sys.path.append(r'C:\path\to\your\rigX\src')
   ```

4. **Test the shelf:**
   - In Maya's script editor, run:
   ```python
   source "~/Documents/maya/[VERSION]/prefs/shelves/shelf_RigX.mel";
   shelf_rigX();
   ```

## 📋 **Step 5: Verify Installation**

After fixing issues, verify the installation:

1. **Check shelf exists:**
   - Look for "rigX" tab in Maya's shelf area

2. **Test a tool:**
   - Click the "Reload" button in the rigX shelf
   - Should see a success message

3. **Check icons:**
   - All buttons should have proper icons
   - If icons are missing, check the icons folder

## 🆘 **Still Having Issues?**

If you're still experiencing problems:

1. **Check Maya version compatibility**
2. **Verify Python version** (rigX requires Python 3.8+)
3. **Run the test script:** `python scripts/test_imports.py`
4. **Check file permissions** (ensure you can write to Maya preferences)
5. **Restart Maya** after making changes

## 📞 **Getting Help**

If none of the above solutions work:

1. **Collect error information:**
   - Copy all error messages from Maya's script editor
   - Note your Maya version and Python version
   - Describe what happens when you try to load rigX

2. **Check the logs:**
   - Look in Maya's script editor history
   - Check Windows Event Viewer for any Maya-related errors

3. **Contact support:**
   - Provide the error information collected above
   - Include your system specifications
