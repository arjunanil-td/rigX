"""
Tests for the bootstrap module.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestBootstrap:
    """Test cases for bootstrap functionality."""
    
    def test_reload_all_basic(self):
        """Test basic reload functionality."""
        from rigging_pipeline.bootstrap import reload_all
        
        # Mock Maya modules
        with patch('rigging_pipeline.bootstrap._show_simple_notification') as mock_notify:
            mock_notify.return_value = "maya_message"
            
            # This should not raise an error
            try:
                reload_all()
            except (ImportError, ModuleNotFoundError):
                # Expected in test environment
                pass
            
            # Verify notification was called
            mock_notify.assert_called_once()
    
    def test_show_notification(self):
        """Test notification function."""
        from rigging_pipeline.bootstrap import _show_simple_notification
        
        # Test without Maya
        result = _show_simple_notification()
        assert result is None
    
    def test_package_imports(self):
        """Test that package can be imported."""
        import rigging_pipeline
        assert hasattr(rigging_pipeline, '__version__')
        assert hasattr(rigging_pipeline, 'reload_all')
    
    def test_bootstrap_imports(self):
        """Test bootstrap module imports."""
        from rigging_pipeline import bootstrap
        assert hasattr(bootstrap, 'reload_all')
        assert callable(bootstrap.reload_all)
