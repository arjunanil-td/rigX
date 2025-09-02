# -*- coding: utf-8 -*-
"""
RigX Context Badge — a tiny text widget for Houdini (Qt).
Usage (from Houdini Python Shell or shelf):
    import rigx_job_badge_houdini as rcb
    rcb.show_badge("Kantara | charTiger | SH010")

You can update the text later with:
    rcb.set_badge_text("Kantara | SH020 | v012")

If RIGX_SHOW is defined, show_badge() with no arg will use it by default.
"""
from __future__ import annotations
import os
from pathlib import Path

# Houdini uses Qt directly
from PySide2 import QtCore, QtGui, QtWidgets
import hou

def get_job_info():
    """Get job information from environment or current scene."""
    try:
        # Try to get from environment variable first
        job_path = os.environ.get("JOB_PATH")
        if job_path:
            data = str(job_path).split(os.sep)
            job_info = {
                "show": data[3] if len(data) > 3 else "unknown",
                "asset": data[-2] if len(data) > 1 else "unknown",
                "shot": data[-2] if len(data) > 1 else "unknown",
                "department": data[-1] if len(data) > 0 else "unknown",
                "path": job_path
            }
        else:
            # Fallback: try to get from current scene path
            scene_path = hou.hipFile.path()
            if scene_path and scene_path != "untitled":
                data = str(scene_path).split(os.sep)
                job_info = {
                    "show": data[-4] if len(data) > 3 else "unknown",
                    "asset": data[-2] if len(data) > 1 else "unknown",
                    "shot": data[-2] if len(data) > 1 else "unknown",
                    "department": data[-1] if len(data) > 0 else "unknown",
                    "path": scene_path
                }
            else:
                job_info = {
                    "show": "unknown",
                    "asset": "unknown",
                    "shot": "unknown",
                    "department": "unknown",
                    "path": "unknown"
                }
    except Exception:
        job_info = {
            "show": "unknown",
            "asset": "unknown",
            "shot": "unknown",
            "department": "unknown",
            "path": "unknown"
        }
    
    return job_info

def _houdini_main_window() -> QtWidgets.QWidget:
    """Get Houdini's main window."""
    try:
        # Houdini provides direct access to the main window
        return hou.qt.mainWindow()
    except Exception:
        # Fallback: try to find the main window
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if widget.isWindow() and widget.windowTitle() and "houdini" in widget.windowTitle().lower():
                return widget
        return None

def _add_badge_to_houdini(text: str) -> QtWidgets.QLabel:
    """Add the badge as a label positioned at the top-right of Houdini's main window."""
    main_window = _houdini_main_window()
    if not main_window:
        return None
    
    # Create the badge label as a child of Houdini's main window
    badge_label = QtWidgets.QLabel(text, main_window)
    badge_label.setObjectName("rigx_job_badge")  # Give it a specific object name
    badge_label.setStyleSheet("""
        QLabel#rigx_job_badge {
            color: #00ffff;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 #2d3748, stop:0.5 #4a5568, stop:1 #718096);
            border: 2px solid #4299e1;
            border-radius: 2px;
            padding: 4px 8px;
            margin: 2px;
        }
    """)
    badge_label.setAlignment(QtCore.Qt.AlignCenter)
    badge_label.setMinimumWidth(200)
    badge_label.setMaximumWidth(400)
    
    # Position the badge at the top-right corner of Houdini's main window
    main_rect = main_window.geometry()
    badge_size = badge_label.sizeHint()
    
    # Calculate position: top-right corner with some margin
    x = main_rect.width() - badge_size.width() - 20  # 20px margin from right
    y = 10  # 10px margin from top
    
    badge_label.move(x, y)
    badge_label.show()
    
    return badge_label

# Public API
_badge_instance = None  # type: QtWidgets.QLabel

def show_badge(text: str | None = None) -> QtWidgets.QLabel:
    """
    Show (or recreate) the badge in Houdini's main window.
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
        job_info = get_job_info()
        show_text = job_info["show"].upper() if job_info["show"] and job_info["show"] != "unknown" else "—"
        asset_text = job_info["asset"] if job_info["asset"] and job_info["asset"] != "unknown" else "—"
        text = f"{show_text} | {asset_text}"

    _badge_instance = _add_badge_to_houdini(text)
    return _badge_instance

def set_badge_text(text: str):
    """Update the badge text if it exists; otherwise create one with that text."""
    global _badge_instance
    if _badge_instance is None:
        show_badge(text)
    else:
        _badge_instance.setText(text)

def hide_badge():
    """Hide the badge if it exists."""
    global _badge_instance
    if _badge_instance is not None:
        try:
            _badge_instance.setParent(None)
            _badge_instance.deleteLater()
        except Exception:
            pass
        _badge_instance = None

if __name__ == "__main__":
    # Show the badge in Houdini's main window
    show_badge()
