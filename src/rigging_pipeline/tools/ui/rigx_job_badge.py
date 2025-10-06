# -*- coding: utf-8 -*-
"""
RigX Context Badge — a tiny dockable text widget for Maya 2024 (PySide2).
Usage (from Maya Script Editor or shelf):
    import rigx_context_badge as rcb
    rcb.show_badge("Kantara | charTiger | SH010")

You can update the text later with:
    rcb.set_badge_text("Kantara | SH020 | v012")

If RIGX_SHOW is defined, show_badge() with no arg will use it by default.
"""
from __future__ import annotations
import os
from functools import partial
from pathlib import Path

# Import the module and create a working get_job_info function
from rigging_pipeline.io import rigx_buildInfo
from PySide2 import QtCore, QtGui, QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as cmds

WC_NAME = "rigxContextBadgeWC"
WC_LABEL = "Job Context"
WIDGET_OBJECT_NAME = "rigxContextBadgeWidget"
# Handle case where JOB_PATH environment variable is not set
job_path_env = os.environ.get("JOB_PATH")
JOB_PATH = Path(job_path_env) if job_path_env else None

def get_job_info():
    """Get job information from JOB_PATH environment variable."""
    if JOB_PATH is None:
        # Return default values when JOB_PATH is not set
        return {
            "show": "unknown",
            "asset": "unknown", 
            "shot": "unknown",
            "department": "unknown",
            "path": None
        }
    
    try:
        data = str(JOB_PATH).split(os.sep)
        if len(data) >= 4:
            return {
                "show": data[3] if len(data) > 3 else "unknown",
                "asset": data[-2] if len(data) > 1 else "unknown",
                "shot": data[-2] if len(data) > 1 else "unknown", 
                "department": data[-1] if len(data) > 0 else "unknown",
                "path": JOB_PATH
            }
        else:
            return {
                "show": "unknown",
                "asset": "unknown",
                "shot": "unknown", 
                "department": "unknown",
                "path": JOB_PATH
            }
    except Exception:
        return {
            "show": "unknown",
            "asset": "unknown",
            "shot": "unknown",
            "department": "unknown", 
            "path": JOB_PATH
        }

job_info = get_job_info()
show = job_info["show"]
asset = job_info["asset"]
department = job_info["department"]


def _maya_main_window() -> QtWidgets.QWidget:
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)



def _find_maya_toolbar() -> QtWidgets.QToolBar:
    """Find Maya's main toolbar where we can add our badge."""
    main_window = _maya_main_window()
    if not main_window:
        return None
    
    # Look for Maya's main toolbar
    for child in main_window.findChildren(QtWidgets.QToolBar):
        if child.objectName() and ("main" in child.objectName().lower() or 
                                 "toolbar" in child.objectName().lower() or
                                 "shelf" in child.objectName().lower()):
            return child
    
    # Fallback: return the first toolbar found
    toolbars = main_window.findChildren(QtWidgets.QToolBar)
    if toolbars:
        return toolbars[0]
    
    return None

class BadgeWidget(QtWidgets.QWidget):
    """A custom widget that handles badge positioning and resizing."""
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setFixedHeight(30)
        self.setStyleSheet("background: transparent;")
        
        # Create the badge label
        self.badge_label = QtWidgets.QLabel(text, self)
        self.badge_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 11px;
                font-weight: normal;
                background-color: #444444;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                margin: 1px;
            }
        """)
        
        # Set Maya-style properties
        self.badge_label.setAlignment(QtCore.Qt.AlignCenter)
        self.badge_label.setMinimumWidth(180)
        self.badge_label.setMaximumWidth(350)
        self.badge_label.setFixedHeight(24)
        
        # Create layout
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
        layout.addWidget(self.badge_label)
        layout.addSpacing(300)  # Increased from 10 to 40 to move badge 30px left
        
        # Position at top of main window
        self.move(0, 0)
        self.resize(self.main_window.width(), 30)
        
        # Install event filter on main window to catch resize events
        self.main_window.installEventFilter(self)
        
        # Also use a timer as backup to check for size changes
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update_position)
        self.update_timer.start(100)  # Check every 100ms
    
    def eventFilter(self, obj, event):
        """Filter events to catch window resize events."""
        if obj == self.main_window and event.type() == QtCore.QEvent.Resize:
            self._update_position()
        return super().eventFilter(obj, event)
    
    def _update_position(self):
        """Update the badge position based on main window size."""
        if self.main_window and self.isVisible():
            new_width = self.main_window.width()
            if self.width() != new_width:
                self.resize(new_width, 30)
    
    def setText(self, text):
        """Update the badge text."""
        self.badge_label.setText(text)
    
    def text(self):
        """Get the badge text."""
        return self.badge_label.text()


def _add_badge_to_toolbar(text: str) -> BadgeWidget:
    """Add the badge as a widget positioned at the top-right of Maya's main window."""
    main_window = _maya_main_window()
    if not main_window:
        return None
    
    # Create the badge widget
    badge_widget = BadgeWidget(text, main_window)
    badge_widget.show()
    
    return badge_widget


# Public API
_badge_instance = None  # type: QtWidgets.QLabel

def show_badge(text: str | None = None) -> QtWidgets.QLabel:
    """
    Show (or recreate) the badge in Maya's toolbar.
    If `text` is None, uses asset information from job_info.
    """
    global _badge_instance
    
    # Remove existing badge if it exists
    if _badge_instance is not None:
        try:
            # Stop the timer if it exists
            if hasattr(_badge_instance, 'update_timer'):
                _badge_instance.update_timer.stop()
            _badge_instance.setParent(None)
            _badge_instance.deleteLater()
        except Exception:
            pass
        _badge_instance = None

    if text is None:
        # Use asset and department information in the format "Asset | Department"
        show_text = show.upper() if show and show != "unknown" else "—"
        asset_text = asset if asset and asset != "unknown" else "—"
        department_text = department if department and department != "unknown" else "—"
        text = f"{show_text} | {asset_text}"

    _badge_instance = _add_badge_to_toolbar(text)
    return _badge_instance

def set_badge_text(text: str):
    """Update the badge text if it exists; otherwise create one with that text."""
    global _badge_instance
    if _badge_instance is None:
        show_badge(text)
    else:
        _badge_instance.setText(text)


if __name__ == "__main__":
    # Show the badge in Maya's toolbar
    show_badge()
