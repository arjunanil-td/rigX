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

def _add_badge_to_toolbar(text: str) -> QtWidgets.QLabel:
    """Add the badge as a label positioned at the top-right of Maya's main window."""
    main_window = _maya_main_window()
    if not main_window:
        return None
    
    # Create the badge label as a child of Maya's main window
    badge_label = QtWidgets.QLabel(text, main_window)
    badge_label.setStyleSheet("""
        QLabel {
            color: #00ffff;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #2d3748, stop:0.5 #4a5568, stop:1 #718096);
            border: 2px solid #4299e1;
            border-radius: 8px;
            padding: 4px 8px;
            margin: 2px;
        }
    """)
    badge_label.setAlignment(QtCore.Qt.AlignCenter)
    badge_label.setMinimumWidth(200)
    badge_label.setMaximumWidth(400)
    
    # Position the badge at the top-right corner of Maya's main window
    main_rect = main_window.geometry()
    badge_size = badge_label.sizeHint()
    
    # Calculate position: top-right corner with some margin
    x = main_rect.width() - badge_size.width() - 300  # 20px margin from right
    y = 0  # 10px margin from top
    
    badge_label.move(x, y)
    badge_label.show()
    
    return badge_label


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
