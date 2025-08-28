import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class RigXToolsUI(QtWidgets.QMainWindow):
    """UI for the RigX Utility Tools"""
    
    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)
        
        self.setWindowTitle("RigX Utility Tools")
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(500, 700)
        
        self.setStyleSheet(THEME_STYLESHEET)
        self.build_ui()
    
    def build_ui(self):
        # Create central widget for QMainWindow
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add the centralized banner
        banner = Banner("RigX Utility Tools", "../icons/rigX_utils.png")
        layout.addWidget(banner)
        
        # ───── Tool Selection ─────
        tools_group = QtWidgets.QGroupBox("Available Tools")
        tools_layout = QtWidgets.QVBoxLayout(tools_group)
        
        # Offset Group Tool
        offset_layout = QtWidgets.QHBoxLayout()
        self.btn_offset_group = QtWidgets.QPushButton("Offset Group")
        self.btn_offset_group.clicked.connect(self.run_offset_group_tool)
        self.btn_offset_group.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover { 
                background-color: #45a049; 
            }
            QPushButton:pressed { 
                background-color: #3d8b40; 
            }
        """)
        offset_desc = QtWidgets.QLabel("Create offset groups for selected objects")
        offset_desc.setStyleSheet("color: #cccccc; font-size: 11px;")
        offset_layout.addWidget(self.btn_offset_group)
        offset_layout.addWidget(offset_desc)
        offset_layout.addStretch()
        tools_layout.addLayout(offset_layout)
        
        # Sets Create Tool
        sets_create_layout = QtWidgets.QHBoxLayout()
        self.btn_sets_create = QtWidgets.QPushButton("Create Set")
        self.btn_sets_create.clicked.connect(self.run_sets_create_tool)
        self.btn_sets_create.setStyleSheet("""
            QPushButton { 
                background-color: #2196F3; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover { 
                background-color: #1976D2; 
            }
            QPushButton:pressed { 
                background-color: #1565C0; 
            }
        """)
        sets_create_desc = QtWidgets.QLabel("Create a new set with selected objects")
        sets_create_desc.setStyleSheet("color: #cccccc; font-size: 11px;")
        sets_create_layout.addWidget(self.btn_sets_create)
        sets_create_layout.addWidget(sets_create_desc)
        sets_create_layout.addStretch()
        tools_layout.addLayout(sets_create_layout)
        
        # Sets Add Tool
        sets_add_layout = QtWidgets.QHBoxLayout()
        self.btn_sets_add = QtWidgets.QPushButton("Add to Set")
        self.btn_sets_add.clicked.connect(self.run_sets_add_tool)
        self.btn_sets_add.setStyleSheet("""
            QPushButton { 
                background-color: #FF9800; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover { 
                background-color: #F57C00; 
            }
            QPushButton:pressed { 
                background-color: #EF6C00; 
            }
        """)
        sets_add_desc = QtWidgets.QLabel("Add selected objects to an existing set")
        sets_add_desc.setStyleSheet("color: #cccccc; font-size: 11px;")
        sets_add_layout.addWidget(self.btn_sets_add)
        sets_add_layout.addWidget(sets_add_desc)
        sets_add_layout.addStretch()
        tools_layout.addLayout(sets_add_layout)
        
        # Sets Remove Tool
        sets_remove_layout = QtWidgets.QHBoxLayout()
        self.btn_sets_remove = QtWidgets.QPushButton("Remove from Sets")
        self.btn_sets_remove.clicked.connect(self.run_sets_remove_tool)
        self.btn_sets_remove.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover { 
                background-color: #d32f2f; 
            }
            QPushButton:pressed { 
                background-color: #c62828; 
            }
        """)
        sets_remove_desc = QtWidgets.QLabel("Remove selected objects from all sets")
        sets_remove_desc.setStyleSheet("color: #cccccc; font-size: 11px;")
        sets_remove_layout.addWidget(self.btn_sets_remove)
        sets_remove_layout.addWidget(sets_remove_desc)
        sets_remove_layout.addStretch()
        tools_layout.addLayout(sets_remove_layout)
        
        layout.addWidget(tools_group)
        
        # ───── Options Panel ─────
        options_group = QtWidgets.QGroupBox("Tool Options")
        options_layout = QtWidgets.QVBoxLayout(options_group)
        
        # Selection mode
        sel_layout = QtWidgets.QHBoxLayout()
        sel_label = QtWidgets.QLabel("Selection Mode:")
        sel_label.setStyleSheet("color: white; font-weight: bold;")
        self.radio_selected = QtWidgets.QRadioButton("Selected")
        self.radio_hierarchy = QtWidgets.QRadioButton("Hierarchy")
        self.radio_all = QtWidgets.QRadioButton("All")
        self.radio_selected.setChecked(True)
        
        sel_layout.addWidget(sel_label)
        sel_layout.addWidget(self.radio_selected)
        sel_layout.addWidget(self.radio_hierarchy)
        sel_layout.addWidget(self.radio_all)
        sel_layout.addStretch()
        options_layout.addLayout(sel_layout)
        
        # Object type filter
        type_layout = QtWidgets.QHBoxLayout()
        type_label = QtWidgets.QLabel("Object Type:")
        type_label.setStyleSheet("color: white; font-weight: bold;")
        self.type_combo = QtWidgets.QComboBox()
        types = ["All", "joint", "ikHandle", "transform", "locator", "mesh", "nurbsCurve"]
        self.type_combo.addItems(types)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        options_layout.addLayout(type_layout)
        
        layout.addWidget(options_group)
        
        # ───── Status Panel ─────
        status_group = QtWidgets.QGroupBox("Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)
        
        self.status_label = QtWidgets.QLabel("Ready to use tools")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 10px;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # ───── Action Buttons ─────
        button_layout = QtWidgets.QHBoxLayout()
        
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_status)
        self.btn_refresh.setStyleSheet("""
            QPushButton { 
                background-color: #666666; 
                color: white; 
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: #777777; 
            }
        """)
        
        self.btn_close = QtWidgets.QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white; 
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: #d32f2f; 
            }
        """)
        
        button_layout.addWidget(self.btn_refresh)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_close)
        
        layout.addLayout(button_layout)
    
    def run_offset_group_tool(self):
        """Execute offset group tool"""
        try:
            selected = cmds.ls(selection=True)
            if selected:
                self.status_label.setText(f"Offset Group: Processing {len(selected)} objects")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 10px;")
                
                # Import and call the tool function
                from rigging_pipeline.tools.rigx_tools import RigXTools
                tool = RigXTools()
                tool.run_offset_group_tool()
                
                self.status_label.setText("Offset Group: Completed successfully")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 10px;")
            else:
                self.status_label.setText("Offset Group: Please select objects first")
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 10px;")
                cmds.warning("Please select objects first")
        except Exception as e:
            self.status_label.setText("Offset Group: Error occurred")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold; padding: 10px;")
            cmds.error(f"Error in offset group tool: {str(e)}")
    
    def run_sets_create_tool(self):
        """Execute sets create tool"""
        try:
            selected = cmds.ls(selection=True)
            if selected:
                self.status_label.setText(f"Create Set: Processing {len(selected)} objects")
                self.status_label.setStyleSheet("color: #2196F3; font-weight: bold; padding: 10px;")
                
                # Import and call the tool function
                from rigging_pipeline.tools.rigx_tools import RigXTools
                tool = RigXTools()
                tool.run_sets_create_tool()
                
                self.status_label.setText("Create Set: Completed successfully")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 10px;")
            else:
                self.status_label.setText("Create Set: Please select objects first")
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 10px;")
                cmds.warning("Please select objects first")
        except Exception as e:
            self.status_label.setText("Create Set: Error occurred")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold; padding: 10px;")
            cmds.error(f"Error in create set tool: {str(e)}")
    
    def run_sets_add_tool(self):
        """Execute sets add tool"""
        try:
            selected = cmds.ls(selection=True)
            if selected:
                self.status_label.setText(f"Add to Set: Processing {len(selected)} objects")
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 10px;")
                
                # Import and call the tool function
                from rigging_pipeline.tools.rigx_tools import RigXTools
                tool = RigXTools()
                tool.run_sets_add_tool()
                
                self.status_label.setText("Add to Set: Completed successfully")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 10px;")
            else:
                self.status_label.setText("Add to Set: Please select objects first")
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 10px;")
                cmds.warning("Please select objects first")
        except Exception as e:
            self.status_label.setText("Add to Set: Error occurred")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold; padding: 10px;")
            cmds.error(f"Error in add to set tool: {str(e)}")
    
    def run_sets_remove_tool(self):
        """Execute sets remove tool"""
        try:
            selected = cmds.ls(selection=True)
            if selected:
                self.status_label.setText(f"Remove from Sets: Processing {len(selected)} objects")
                self.status_label.setStyleSheet("color: #f44336; font-weight: bold; padding: 10px;")
                
                # Import and call the tool function
                from rigging_pipeline.tools.rigx_tools import RigXTools
                tool = RigXTools()
                tool.run_sets_remove_tool()
                
                self.status_label.setText("Remove from Sets: Completed successfully")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 10px;")
            else:
                self.status_label.setText("Remove from Sets: Please select objects first")
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 10px;")
                cmds.warning("Please select objects first")
        except Exception as e:
            self.status_label.setText("Remove from Sets: Error occurred")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold; padding: 10px;")
            cmds.error(f"Error in remove from sets tool: {str(e)}")
    
    def refresh_status(self):
        """Refresh the status display"""
        selected = cmds.ls(selection=True)
        if selected:
            self.status_label.setText(f"Ready: {len(selected)} objects selected")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 10px;")
        else:
            self.status_label.setText("Ready: No objects selected")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 10px;")
