#!/usr/bin/env python3
"""
rigX Animation Rigging Tools UI

This module provides the UI components for animation rigging workflows.
"""

import maya.cmds as cmds
import os
import sys

# Maya imports
try:
    import maya.OpenMayaUI as omui
    from shiboken2 import wrapInstance
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

# Qt imports
from PySide2 import QtWidgets, QtCore, QtGui

# Add the rigX path to sys.path if not already there
rigx_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if rigx_path not in sys.path:
    sys.path.append(rigx_path)

# Pipeline imports
from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner


def maya_main_window():
    """Get Maya's main window as a QWidget."""
    if not MAYA_AVAILABLE:
        return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class RigXAnimRigUI(QtWidgets.QMainWindow):
    """Animation Rigging Tools UI for rigX pipeline."""
    
    def __init__(self, tool_instance=None, parent=None):
        super().__init__(parent or maya_main_window())
        self.tool_instance = tool_instance
        self.window_title = "rigX AnimRig"
        self.window_width = 350
        self.window_height = 350
        
        self.setStyleSheet(THEME_STYLESHEET)
        self.setWindowTitle(self.window_title)
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(self.window_width, self.window_height)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Set darker background for the main widget
        central_widget.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                color: #e2e8f0;
            }
        """)
        
        self._build_ui(central_widget)
        
    def _build_ui(self, parent_widget):
        """Build the UI components."""
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(parent_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Add banner
        banner = Banner("AnimRig", "rigX_icon_animRig.png")
        main_layout.addWidget(banner)
        
        # Simple Transform Puppet Section
        puppet_group = QtWidgets.QGroupBox("Puppet Setup")
        puppet_group.setStyleSheet(self._get_group_style())
        
        puppet_layout = QtWidgets.QVBoxLayout(puppet_group)
        puppet_layout.setSpacing(8)
        
        # Model Group Input
        model_input_layout = QtWidgets.QHBoxLayout()
        model_input_layout.setSpacing(8)
        
        model_label = QtWidgets.QLabel("Model Group:")
        model_label.setStyleSheet("color: #e2e8f0; font-weight: normal;")
        model_input_layout.addWidget(model_label)
        
        self.model_group_field = QtWidgets.QLineEdit()
        self.model_group_field.setPlaceholderText("")
        self.model_group_field.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px;
            }
            QLineEdit:focus {
                border-color: #48bb78;
            }
        """)
        model_input_layout.addWidget(self.model_group_field)
        
        # Push button to get selected object name
        push_btn = QtWidgets.QPushButton("<<<")
        push_btn.setMaximumWidth(60)
        push_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #48bb78;
                border-color: #48bb78;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #2d6a4f;
                border-color: #48bb78;
            }
        """)
        push_btn.clicked.connect(self._on_push_model_group)
        model_input_layout.addWidget(push_btn)
        
        puppet_layout.addLayout(model_input_layout)
        
        # Custom Joint: Collapsible field toggled by (+) button
        custom_joint_header = QtWidgets.QHBoxLayout()
        custom_joint_header.setSpacing(8)
        custom_joint_label = QtWidgets.QLabel("Custom Joint:")
        custom_joint_label.setStyleSheet("color: #e2e8f0; font-weight: normal;")
        custom_joint_header.addWidget(custom_joint_label)
        self.custom_joint_toggle_btn = QtWidgets.QPushButton("+")
        self.custom_joint_toggle_btn.setMaximumWidth(28)
        self.custom_joint_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 2px 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #48bb78;
                border-color: #48bb78;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #2d6a4f;
                border-color: #48bb78;
            }
        """)
        self.custom_joint_toggle_btn.clicked.connect(self._toggle_custom_joint_field)
        custom_joint_header.addWidget(self.custom_joint_toggle_btn)
        custom_joint_header.addStretch(1)
        puppet_layout.addLayout(custom_joint_header)

        # Expandable area containing the editable field and push-from-selection
        self.custom_joint_expand_widget = QtWidgets.QWidget()
        expand_layout = QtWidgets.QHBoxLayout(self.custom_joint_expand_widget)
        expand_layout.setSpacing(8)
        expand_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_joint_field = QtWidgets.QLineEdit()
        self.custom_joint_field.setPlaceholderText("")
        self.custom_joint_field.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px;
            }
            QLineEdit:focus {
                border-color: #48bb78;
            }
        """)
        expand_layout.addWidget(self.custom_joint_field)
        custom_joint_push_btn = QtWidgets.QPushButton("<<<")
        custom_joint_push_btn.setMaximumWidth(60)
        custom_joint_push_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #48bb78;
                border-color: #48bb78;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #2d6a4f;
                border-color: #48bb78;
            }
        """)
        custom_joint_push_btn.clicked.connect(self._on_push_custom_joint)
        expand_layout.addWidget(custom_joint_push_btn)
        self.custom_joint_expand_widget.setVisible(False)
        puppet_layout.addWidget(self.custom_joint_expand_widget)
        
        # Ignore End Joint options
        self.ignore_end_joint_chk = QtWidgets.QCheckBox("Ignore End Joint")
        self.ignore_end_joint_chk.setChecked(False)  # Default to include all joints
        self.ignore_end_joint_chk.setStyleSheet("""
            QCheckBox {
                color: #e2e8f0;
                font-weight: normal;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #666666;
                background-color: #2D2D2D;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #48bb78;
                background-color: #48bb78;
                border-radius: 3px;
            }
        """)
        # Place Ignore End Joint and Matrix Connection on the same line
        options_inline_layout = QtWidgets.QHBoxLayout()
        options_inline_layout.setSpacing(12)
        options_inline_layout.addWidget(self.ignore_end_joint_chk)
        self.matrix_connection_chk = QtWidgets.QCheckBox("Matrix Connection")
        self.matrix_connection_chk.setChecked(False)
        options_inline_layout.addSpacing(20)
        options_inline_layout.addWidget(self.matrix_connection_chk)
        options_inline_layout.addStretch(1)
        puppet_layout.addLayout(options_inline_layout)

        # Extra Global Controls option
        extra_global_layout = QtWidgets.QHBoxLayout()
        extra_global_layout.setSpacing(8)
        extra_global_label = QtWidgets.QLabel("Extra Global Controls:")
        extra_global_label.setStyleSheet("color: #e2e8f0; font-weight: normal;")
        extra_global_layout.addWidget(extra_global_label)
        self.extra_global_spin = QtWidgets.QSpinBox()
        self.extra_global_spin.setMinimum(0)
        self.extra_global_spin.setMaximum(10)
        self.extra_global_spin.setValue(0)
        self.extra_global_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 2px 6px;
            }
        """)
        extra_global_layout.addWidget(self.extra_global_spin)
        puppet_layout.addLayout(extra_global_layout)
        
        # Simple Transform Puppet button
        self.puppet_btn = QtWidgets.QPushButton("Simple Transform Puppet")
        self.puppet_btn.clicked.connect(self._on_create_simple_puppet)
        self.puppet_btn.setEnabled(False)  # Initially disabled
        self.puppet_btn.setStyleSheet(self._get_puppet_button_style())
        puppet_layout.addWidget(self.puppet_btn)
        
        # Connect text change signal to enable/disable button
        self.model_group_field.textChanged.connect(self._on_model_group_changed)
        
        main_layout.addWidget(puppet_group)
        
        # FK Controls Section
        fk_group = QtWidgets.QGroupBox("FK Controls")
        fk_group.setStyleSheet(self._get_group_style())
        
        fk_layout = QtWidgets.QVBoxLayout(fk_group)
        fk_layout.setSpacing(8)

        # Joints input above parent controls in hierarchy
        fk_joints_layout = QtWidgets.QHBoxLayout()
        fk_joints_layout.setSpacing(8)
        fk_joints_label = QtWidgets.QLabel("Joints:")
        fk_joints_label.setStyleSheet("color: #e2e8f0; font-weight: normal;")
        fk_joints_layout.addWidget(fk_joints_label)
        self.fk_joints_field = QtWidgets.QLineEdit()
        self.fk_joints_field.setPlaceholderText("")
        self.fk_joints_field.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px;
            }
            QLineEdit:focus {
                border-color: #48bb78;
            }
        """)
        fk_joints_layout.addWidget(self.fk_joints_field)
        fk_joints_push_btn = QtWidgets.QPushButton("<<<")
        fk_joints_push_btn.setMaximumWidth(60)
        fk_joints_push_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #48bb78;
                border-color: #48bb78;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #2d6a4f;
                border-color: #48bb78;
            }
        """)
        fk_joints_push_btn.clicked.connect(self._on_push_fk_joints)
        fk_joints_layout.addWidget(fk_joints_push_btn)
        fk_layout.addLayout(fk_joints_layout)
        
        # Checkboxes
        self.fk_parent_chk = QtWidgets.QCheckBox("Parent controls in hierarchy")
        self.fk_parent_chk.setChecked(True)
        fk_layout.addWidget(self.fk_parent_chk)
        
        self.fk_matrix_chk = QtWidgets.QCheckBox("Use OffsetParentMatrix")
        self.fk_matrix_chk.setChecked(True)
        fk_layout.addWidget(self.fk_matrix_chk)
        
        # Create FK Controls button
        create_btn = QtWidgets.QPushButton("Create FK Controls")
        create_btn.clicked.connect(self._on_create_fk_controls)
        fk_layout.addWidget(create_btn)
        
        main_layout.addWidget(fk_group)
        
        # Push/Publish Section removed per request
        
    def _get_group_style(self):
        """Get the styling for group boxes."""
        return """
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
                padding-bottom: 6px;
                background-color: #2D2D2D;
                color: #e2e8f0;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #cccccc;
            }
            QCheckBox {
                color: #e2e8f0;
                font-weight: normal;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #666666;
                background-color: #2D2D2D;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #48bb78;
                background-color: #48bb78;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #48bb78;
                border-color: #48bb78;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #2d6a4f;
                border-color: #48bb78;
            }
        """
    
    def _get_puppet_button_style(self):
        """Get styling for the puppet button with green theme."""
        return """
            QPushButton {
                background-color: #38A169;
                color: white;
                border: 2px solid #2F855A;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #48BB78;
                border-color: #38A169;
            }
            QPushButton:pressed {
                background-color: #2F855A;
                border-color: #276749;
            }
            QPushButton:disabled {
                background-color: #2D5A3D;
                color: #68A078;
                border-color: #1A3D26;
            }
        """
    
    def _on_push_custom_joint(self):
        """Handle Push button click to get selected object name."""
        try:
            import maya.cmds as cmds
            selection = cmds.ls(selection=True)
            if selection:
                # Get the first selected object's name
                selected_name = cmds.ls(selection[0], shortNames=True)[0]
                self.custom_joint_field.setText(selected_name)
            else:
                cmds.warning("Please select an object first.")
        except Exception as e:
            cmds.warning(f"Error getting selection: {str(e)}")
    
    def _on_create_simple_puppet(self):
        """Handle Simple Transform Puppet button click."""
        if self.tool_instance:
            model_group = self.model_group_field.text().strip()
            # Get custom joint from text field (single joint)
            custom_joint_text = self.custom_joint_field.text().strip() if self.custom_joint_expand_widget.isVisible() else ""
            custom_joints = [custom_joint_text] if custom_joint_text else []
            use_matrix = self.matrix_connection_chk.isChecked()
            ignore_end_joint = self.ignore_end_joint_chk.isChecked()
            extra_global_controls = int(self.extra_global_spin.value())
            self.tool_instance.create_simple_puppet(model_group, custom_joints, use_matrix, ignore_end_joint, extra_global_controls)
    
    def _on_create_fk_controls(self):
        """Handle Create FK Controls button click."""
        if self.tool_instance:
            import maya.cmds as cmds
            import re
            parent_in_hierarchy = self.fk_parent_chk.isChecked()
            use_matrix = self.fk_matrix_chk.isChecked()
            joints_text = self.fk_joints_field.text().strip() if hasattr(self, 'fk_joints_field') else ''
            if joints_text:
                names = [n for n in re.split(r'[\s,;]+', joints_text) if n]
                existing = [n for n in names if cmds.objExists(n)]
                if existing:
                    cmds.select(existing, r=True)
                else:
                    cmds.warning("No valid joints found from the provided text; using current selection.")
            self.tool_instance.create_fk_controls(parent_in_hierarchy, use_matrix)
    
    def _on_model_group_changed(self):
        """Handle model group field text change to enable/disable puppet button."""
        text = self.model_group_field.text().strip()
        self.puppet_btn.setEnabled(bool(text))
    
    def _on_push_model_group(self):
        """Handle Push button click to get selected object name."""
        try:
            import maya.cmds as cmds
            selection = cmds.ls(selection=True)
            if selection:
                # Get the first selected object's name
                selected_name = cmds.ls(selection[0], shortNames=True)[0]
                self.model_group_field.setText(selected_name)
            else:
                cmds.warning("Please select an object first.")
        except Exception as e:
            cmds.warning(f"Error getting selection: {str(e)}")

    def _on_push_fk_joints(self):
        """Populate the FK joints field from current selection."""
        try:
            import maya.cmds as cmds
            sel = cmds.ls(selection=True) or []
            if sel:
                # Prefer short names
                shorts = [cmds.ls(s, shortNames=True)[0] for s in sel]
                self.fk_joints_field.setText(" ".join(shorts))
            else:
                cmds.warning("Please select joint(s) first.")
        except Exception as e:
            cmds.warning(f"Error reading selection: {str(e)}")

    def _toggle_custom_joint_field(self):
        """Toggle the expandable custom joint field visibility."""
        is_visible = self.custom_joint_expand_widget.isVisible()
        self.custom_joint_expand_widget.setVisible(not is_visible)
        self.custom_joint_toggle_btn.setText("-" if not is_visible else "+")
    
    # Push rig functionality removed with UI section
    
    def show_ui(self):
        """Show the UI window."""
        self.show()
