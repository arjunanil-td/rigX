# rigX Packaging Guide

This document explains the clean, organized structure of the rigX repository after cleanup and reorganization.

## 🏗️ Repository Structure

```
rigX/
├── src/                           # Source code (Python packages)
│   ├── rigging_pipeline/         # Core pipeline package
│   │   ├── __init__.py          # Package initialization
│   │   ├── bootstrap.py         # Maya integration bootstrap
│   │   ├── cli.py              # Command line interface
│   │   ├── main.py             # Main entry point
│   │   ├── tools/              # Rigging tools and utilities
│   │   ├── utils/              # Helper functions
│   │   ├── nodes/              # Custom Maya nodes
│   │   └── io/                 # Input/output operations
│   └── shows/                   # Show-specific configurations
│       └── Kantara/            # Example show package
│           ├── __init__.py
│           └── finalize/       # Character finalization tools
├── config/                       # Maya configuration files
│   ├── shelves/                 # Maya shelf files
│   └── icons/                   # Tool icons
├── docs/                         # Documentation
│   └── README.md               # Documentation index
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest configuration
│   └── test_bootstrap.py       # Bootstrap tests
├── scripts/                      # Utility scripts
│   └── install_maya.py         # Maya installation script
├── .gitignore                   # Git ignore patterns
├── pyproject.toml              # Modern Python packaging
├── README.md                    # Project overview
└── PACKAGING.md                # This file
```

## 🧹 What Was Cleaned Up

### Removed Files
- `rigX_git_reload_dialog.py` - Unused utility
- `test_rigx_tools.py` - Old test file
- `README_RIGX_TOOLS.md` - Redundant documentation
- `README_VALIDATOR_UPDATE.md` - Redundant documentation
- `install.py` - Replaced with better script
- `setup.cfg` - Replaced with pyproject.toml
- `test/` directory - Replaced with proper `tests/` structure
- All `__pycache__/` directories - Python cache files

### Reorganized Structure
- **Moved `shows/`** → `src/shows/` (proper package location)
- **Moved `shelves/`** → `config/shelves/` (configuration files)
- **Moved `icons/`** → `config/icons/` (configuration files)
- **Created `docs/`** - Proper documentation structure
- **Created `tests/`** - Proper test structure
- **Created `scripts/`** - Utility scripts

## 📦 Package Structure

### Core Package (`src/rigging_pipeline/`)
- **`__init__.py`** - Package metadata and imports
- **`bootstrap.py`** - Maya integration and module reloading
- **`cli.py`** - Command line interface
- **`main.py`** - Main entry point
- **`tools/`** - Rigging tools and utilities
- **`utils/`** - Helper functions and utilities
- **`nodes/`** - Custom Maya nodes
- **`io/`** - Input/output operations

### Show Packages (`src/shows/`)
- **`Kantara/`** - Example show package
  - **`finalize/`** - Character finalization tools

### Configuration (`config/`)
- **`shelves/`** - Maya shelf files (`.mel`)
- **`icons/`** - Tool icons (`.png`)

## 🚀 Installation and Usage

### Development Installation
```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Maya Integration
```bash
# Run Maya installation script
python scripts/install_maya.py
```

### In Maya
```python
# Add to Python path
import sys
sys.path.append('/path/to/rigX/src')

# Import and reload
from rigging_pipeline.bootstrap import reload_all
reload_all()
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=rigging_pipeline

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
```

## 📚 Documentation

- **`README.md`** - Project overview and quick start
- **`docs/`** - Comprehensive documentation
- **`PACKAGING.md`** - This packaging guide

## 🔧 Development Tools

- **`pyproject.toml`** - Modern Python packaging
- **`.gitignore`** - Comprehensive ignore patterns
- **`pre-commit`** - Code quality hooks (configured in pyproject.toml)

## ✅ Benefits of New Structure

1. **Clean Organization** - Logical separation of concerns
2. **Proper Packaging** - Follows Python packaging standards
3. **Easy Installation** - Simple pip install process
4. **Better Testing** - Proper test structure and configuration
5. **Documentation** - Organized documentation structure
6. **Configuration** - Maya configs in dedicated location
7. **Maintainability** - Easier to maintain and extend
8. **Professional** - Industry-standard project structure

## 🎯 Next Steps

1. **Add more tests** - Expand test coverage
2. **Document tools** - Document each tool and utility
3. **Add examples** - Create usage examples
4. **CI/CD setup** - Add automated testing and deployment
5. **Version management** - Implement proper versioning
6. **Release process** - Create release workflow

This clean structure makes rigX a professional, maintainable, and easy-to-use Maya rigging pipeline!
