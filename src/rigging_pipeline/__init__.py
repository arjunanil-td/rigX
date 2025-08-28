"""
rigX - Maya Rigging Pipeline

A comprehensive Maya rigging pipeline for character animation and creature rigging.
"""

__version__ = "0.1.0"
__author__ = "Arjun Anil"
__email__ = "arjunanil.online@gmail.com"
__description__ = "Maya Rigging Pipeline for character animation and creatures"

# Core imports
from . import bootstrap
from . import tools
from . import utils
from . import nodes
from . import io

# Main functions
from .bootstrap import reload_all

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "bootstrap",
    "tools",
    "utils",
    "nodes",
    "io",
    "reload_all",
]
