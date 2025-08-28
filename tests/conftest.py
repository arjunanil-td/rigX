"""
Pytest configuration for rigX tests.
"""

import os
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)

# Maya mock setup
def pytest_configure(config):
    """Configure pytest with Maya mocks."""
    # Mock Maya modules if not available
    try:
        import maya.cmds
    except ImportError:
        # Create mock Maya modules
        import types
        
        # Mock maya.cmds
        mock_cmds = types.ModuleType("maya.cmds")
        mock_cmds.about = lambda version: "2024"
        sys.modules["maya.cmds"] = mock_cmds
        
        # Mock maya.utils
        mock_utils = types.ModuleType("maya.utils")
        mock_utils.executeDeferred = lambda func: func()
        sys.modules["maya.utils"] = mock_utils
        
        # Mock maya
        mock_maya = types.ModuleType("maya")
        mock_maya.cmds = mock_cmds
        mock_maya.utils = mock_utils
        sys.modules["maya"] = mock_maya
