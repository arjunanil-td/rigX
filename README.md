# rigX - Maya Rigging Pipeline

A comprehensive Maya rigging pipeline for character animation and creature rigging.

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/arjunanil-td/rigX.git
cd rigX
```

### 2. Install Maya Shelf and Icons
```bash
# Run the Maya installation script
python scripts/install_maya.py
```

### 3. Use in Maya
```python
# Add to Python path in Maya
import sys
sys.path.append('/path/to/rigX/src')

# Import and reload the pipeline
from rigging_pipeline.bootstrap import reload_all
reload_all()
```

## 📦 Installation

### Development Installation
```bash
# Install in development mode
pip install -e .

# Install with development dependencies (optional)
pip install -e ".[dev]"
```

### Maya Integration
The `scripts/install_maya.py` script automatically:
- ✅ Detects your Maya version
- ✅ Installs the rigX shelf to Maya preferences
- ✅ Copies all tool icons to the correct location
- ✅ Works on Windows, macOS, and Linux

## 🎯 What Gets Installed

### Maya Shelf
- **File**: `config/shelves/shelf_RigX.mel`
- **Location**: `~/Documents/maya/[VERSION]/prefs/shelves/`
- **Contains**: All rigX tools organized in one shelf

### Tool Icons
- **Location**: `~/Documents/maya/[VERSION]/prefs/icons/`
- **Icons**: Validator, Utils, Git, and other tool icons
- **Format**: High-quality PNG files

## 🏗️ Project Structure

```
rigX/
├── src/
│   ├── rigging_pipeline/          # Core pipeline package
│   │   ├── tools/                 # Rigging tools and utilities
│   │   ├── utils/                 # Helper functions
│   │   ├── nodes/                 # Custom Maya nodes
│   │   └── io/                    # Input/output operations
│   └── shows/                     # Show-specific configurations
│       └── Kantara/              # Example show package
├── config/                        # Maya configuration files
│   ├── shelves/                   # Maya shelf files
│   │   └── shelf_RigX.mel        # Main rigX shelf with all tools
│   └── icons/                     # Tool icons
│       ├── rigX_icon_validator.png
│       ├── rigX_icon_utils.png
│       ├── rigX_icon_git.png
│       └── ... (other icons)
├── docs/                          # Documentation
└── scripts/                       # Utility scripts
│   └── install_maya.py           # Maya installation script
```

## ✨ Features

- 🎨 **Custom Maya Shelf** - All tools organized in one place
- 🖼️ **Professional Icons** - High-quality tool icons
- 🔧 **Automated Installation** - One-click Maya setup
- 🚀 **Pipeline Tools** - Rigging validation and automation
- 🎭 **Show Management** - Project-specific configurations
- 🔌 **Maya Integration** - Seamless Maya workflow
- 📚 **Extensible Architecture** - Easy to add new tools

## 📋 Requirements

- **Python**: 3.8 or higher
- **Maya**: 2020 or higher
- **OS**: Windows, macOS, or Linux
- **Git**: For cloning the repository

## 🆘 Troubleshooting

### Shelf Not Appearing?
1. Restart Maya after installation
2. Check Maya's shelf editor (Window → UI Elements → Shelf Editor)
3. Verify icons are in `~/Documents/maya/[VERSION]/prefs/icons/`

### Icons Missing?
1. Run `python scripts/install_maya.py` again
2. Check Maya preferences folder exists
3. Ensure you have write permissions

### Python Import Errors?
1. Verify path is added to `sys.path`
2. Check Python version compatibility
3. Install dependencies with `pip install -e .`

## 📖 Documentation

- **User Guide**: See `docs/` folder for detailed usage
- **Packaging Guide**: `PACKAGING.md` for development setup
- **Troubleshooting**: `docs/TROUBLESHOOTING.md` for common issues

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/arjunanil-td/rigX/issues)
- **Email**: arjunanil.online@gmail.com

## 📄 License

MIT License - see LICENSE file for details.

---

**🎉 Ready to rig!** After installation, you'll have a professional Maya shelf with all rigX tools at your fingertips.
