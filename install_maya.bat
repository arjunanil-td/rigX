@echo off
echo.
echo ========================================
echo    rigX Maya Installation Script
echo ========================================
echo.
echo This script will install the rigX shelf and icons to Maya.
echo.
echo Press any key to continue...
pause >nul

echo.
echo 📁 Installing rigX files to Maya...
python scripts/install_maya.py

echo.
echo 🎨 Creating rigX shelf using MEL script...
echo.
echo ========================================
echo IMPORTANT: You need to run this in Maya!
echo ========================================
echo.
echo To create the shelf in Maya:
echo 1. Open Maya
echo 2. Go to Window ^> General Editors ^> Script Editor
echo 3. In the MEL tab, copy and paste this command:
echo.
echo ========================================
echo source "%~dp0config\shelves\shelf_RigX.mel"; shelf_rigX();
echo ========================================
echo.
echo Or use the Python version in the Python tab:
echo ========================================
echo exec(open(r"%~dp0scripts\create_shelf_python.py").read())
echo ========================================
echo.
echo Next steps:
echo 1. Add to Python path: sys.path.append(r'%~dp0src')
echo 2. Import: from rigging_pipeline.bootstrap import reload_all
echo.
echo Press any key to exit...
pause >nul

