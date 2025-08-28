# rigX - Maya Rigging Pipeline

A comprehensive Maya rigging pipeline for character animation and creature rigging.

## Quick Start

```python
# Import and reload the pipeline
from rigging_pipeline.bootstrap import reload_all
reload_all()
```

## Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Project Structure

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
│   └── icons/                     # Tool icons
├── docs/                          # Documentation
├── tests/                         # Test suite
└── scripts/                       # Utility scripts
```

## Features

- Automated rigging tools
- Pipeline validation
- Show management
- Maya integration
- Extensible architecture

## Requirements

- Python 3.8+
- Maya 2020+
- Windows/macOS/Linux

## License

MIT License - see LICENSE file for details.
