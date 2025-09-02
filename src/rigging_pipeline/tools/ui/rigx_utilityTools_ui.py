import os
import sys

# Maya imports
try:
    import maya.cmds as cmds
    import maya.OpenMayaUI as omui
    from shiboken2 import wrapInstance
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    print("Warning: Maya modules not available. This tool must be run within Maya.")

# Qt imports
from PySide2 import QtWidgets, QtCore, QtGui

# Pipeline imports
from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET

# Mapping of actions to QStyle icons - Simplified
ICON_MAP = {
    'offset': QtWidgets.QStyle.SP_ArrowUp,
    'sets': QtWidgets.QStyle.SP_FileDialogListView,
    'create': QtWidgets.QStyle.SP_FileDialogNewFolder,
    'add': QtWidgets.QStyle.SP_ArrowRight,
    'remove': QtWidgets.QStyle.SP_MessageBoxCritical,
    'close': QtWidgets.QStyle.SP_DialogCloseButton,
    'controller': QtWidgets.QStyle.SP_ComputerIcon,
    'joint': QtWidgets.QStyle.SP_MessageBoxInformation,
    'attribute': QtWidgets.QStyle.SP_FileDialogDetailedView,
    'lock': QtWidgets.QStyle.SP_DialogApplyButton,
    'unlock': QtWidgets.QStyle.SP_DialogResetButton,
    'hide': QtWidgets.QStyle.SP_DialogApplyButton,
    'unhide': QtWidgets.QStyle.SP_DialogResetButton
}


def maya_main_window():
    if not MAYA_AVAILABLE:
        return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class RigXUtilityToolsUI(QtWidgets.QMainWindow):
    """RigX Utility Tools - Optimized for Performance"""
    
    def __init__(self, parent=None):
        super().__init__(parent or maya_main_window())
        self.setStyleSheet(THEME_STYLESHEET)
        self.setWindowTitle("RigX Utility Tools")
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(450, 700)  # Slightly smaller for better performance
        self.tool_instance = None
        
        # Create central widget for QMainWindow
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        self._build_ui(central_widget)

    def _build_ui(self, parent_widget):
        layout = QtWidgets.QVBoxLayout(parent_widget)
        layout.setSpacing(8)  # Reduced spacing
        layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        
        # Set darker background for the main widget
        parent_widget.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                color: #e2e8f0;
            }
        """)

        style = QtWidgets.QApplication.instance().style()

        # Simplified Banner
        banner_frame = QtWidgets.QFrame()
        banner_frame.setFixedHeight(50)  # Smaller banner
        banner_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1b4332, stop:0.5 #2d6a4f, stop:1 #40916c);
                border-radius: 6px;
            }
            QLabel {
                color: white;
                font-size: 16pt;
                font-weight: bold;
            }
        """)
        banner_layout = QtWidgets.QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(10, 0, 10, 0)
        
        # Add custom icon - Following Skin Toolkit pattern
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        icon_path = os.path.join(script_dir, "config", "icons", "rigX_utils.png")
        
        if os.path.exists(icon_path):
            icon_label = QtWidgets.QLabel()
            icon_label.setObjectName("icon")
            icon_pixmap = QtGui.QPixmap(icon_path)
            # Scale the icon to 40x40 while maintaining aspect ratio
            icon_pixmap = icon_pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            icon_label.setStyleSheet("""
                QLabel {
                    background: transparent;
                    padding: 0px;
                    margin: 0px;
                }
            """)
            banner_layout.addWidget(icon_label)
        else:
            print(f"Warning: RigX Utility Tools icon not found at {icon_path}")
            # Fallback to a text-based icon if the image isn't found
            icon_label = QtWidgets.QLabel("⚙️")
            icon_label.setObjectName("icon")
            icon_label.setStyleSheet("font-size: 24pt; color: white; background: transparent;")
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            banner_layout.addWidget(icon_label)
        
        banner_label = QtWidgets.QLabel("RigX Utility Tools")
        banner_label.setAlignment(QtCore.Qt.AlignCenter)
        banner_layout.addWidget(banner_label)
        banner_layout.addStretch()
        layout.addWidget(banner_frame)

        # Create tab widget
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #666666;
                background-color: #2D2D2D;
            }
            QTabBar::tab {
                border: 1px solid #666666;
                background-color: #2D2D2D;
                color: #e2e8f0;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
                border-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #48bb78;
                color: #2D2D2D;
                border-color: #666666;
            }
            QTabBar::tab:hover {
                background: #2D2D2D;
                border-color: #666666;
            }
        """)
        
        # ==================== JOINT TAB ====================
        joint_tab = QtWidgets.QWidget()
        joint_layout = QtWidgets.QVBoxLayout(joint_tab)
        joint_layout.setSpacing(8)
        joint_layout.setContentsMargins(8, 8, 8, 8)
        
        # Quick Tools Section
        group_quick = QtWidgets.QGroupBox("Quick Tools")
        group_quick.setStyleSheet("""
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:0.5 #f0f0f0, stop:1 #e0e0e0);
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        quick_layout = QtWidgets.QGridLayout()
        
        quick_tools = [
            ("Joint @ Center", "joint"),
            ("Curve to Joint", "create"),
            ("Inbetween Joints", "create")
        ]
        
        for i, (tool_name, icon_key) in enumerate(quick_tools):
            btn = QtWidgets.QPushButton(tool_name)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            from functools import partial
            btn.clicked.connect(partial(self.run_quick_tool, tool_name))
            quick_layout.addWidget(btn, i // 2, i % 2)
        
        group_quick.setLayout(quick_layout)
        joint_layout.addWidget(group_quick)
        
        # Joint Tools Section
        group_joints = QtWidgets.QGroupBox("Joint Tools")
        group_joints.setStyleSheet("""
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:0.5 #f0f0f0, stop:1 #e0e0e0);
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        joints_layout = QtWidgets.QGridLayout()
        
        orientation_types = ["YUP", "YDN", "ZUP", "ZDN", "NONE"]
        for i, orient_type in enumerate(orientation_types):
            btn = QtWidgets.QPushButton(f"Orient {orient_type}")
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            btn.clicked.connect(partial(self.run_orient_joint_tool, orient_type))
            joints_layout.addWidget(btn, 0, i)
        
        group_joints.setLayout(joints_layout)
        joint_layout.addWidget(group_joints)
        
        joint_layout.addStretch()
        tab_widget.addTab(joint_tab, "Joints")
        
        # ==================== CONTROL TAB ====================
        control_tab = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_tab)
        control_layout.setSpacing(8)
        control_layout.setContentsMargins(8, 8, 8, 8)
        
        # Quick Tools Section
        group_quick_controls = QtWidgets.QGroupBox("Quick Tools")
        group_quick_controls.setStyleSheet("""
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:0.5 #f0f0f0, stop:1 #e0e0e0);
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        quick_controls_layout = QtWidgets.QGridLayout()
        
        quick_control_tools = [
            ("Offset Groups", "offset"),
            ("Zero Out", "create")
        ]
        
        for i, (tool_name, icon_key) in enumerate(quick_control_tools):
            btn = QtWidgets.QPushButton(style.standardIcon(ICON_MAP[icon_key]), tool_name)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            from functools import partial
            btn.clicked.connect(partial(self.run_quick_tool, tool_name))
            quick_controls_layout.addWidget(btn, 0, i)
        
        group_quick_controls.setLayout(quick_controls_layout)
        control_layout.addWidget(group_quick_controls)
        
        # Controller Tools Section
        group_controllers = QtWidgets.QGroupBox("Controllers")
        group_controllers.setStyleSheet("""
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:0.5 #f0f0f0, stop:1 #e0e0e0);
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        controllers_layout = QtWidgets.QGridLayout()
        
        controller_types = ["Circle", "Square", "Triangle", "Cube", "Sphere", "Pyramid"]
        
        for i, ctrl_type in enumerate(controller_types):
            btn = QtWidgets.QPushButton(ctrl_type)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            btn.clicked.connect(partial(self.run_create_controller_tool, ctrl_type))
            controllers_layout.addWidget(btn, i // 3, i % 3)
        
        # Add "More..." button for additional controllers
        more_btn = QtWidgets.QPushButton("More...")
        more_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        more_btn.clicked.connect(self.show_controller_dialog)
        controllers_layout.addWidget(more_btn, 2, 0, 1, 3)
        
        group_controllers.setLayout(controllers_layout)
        control_layout.addWidget(group_controllers)
        
        # Color Tools Section
        group_colors = QtWidgets.QGroupBox("Colors")
        group_colors.setStyleSheet("""
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffffff;
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        colors_layout = QtWidgets.QGridLayout()
        
        color_options = [
            ("Red", 13), ("Blue", 6), ("Green", 14), ("Yellow", 17), ("Purple", 9), ("Orange", 12)
        ]
        
        for i, (color_name, color_index) in enumerate(color_options):
            btn = QtWidgets.QPushButton(color_name)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            btn.clicked.connect(partial(self.run_override_color_tool, color_index))
            
            # Simple color styling with hover effects
            if color_name == "Red":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff4444;
                        border: 1px solid #cc0000;
                        border-radius: 4px;
                        color: white;
                        padding: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ff6666;
                        border-color: #ff0000;
                    }
                    QPushButton:pressed {
                        background-color: #cc0000;
                        border-color: #990000;
                    }
                """)
            elif color_name == "Blue":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4444ff;
                        border: 1px solid #0000cc;
                        border-radius: 4px;
                        color: white;
                        padding: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #6666ff;
                        border-color: #0000ff;
                    }
                    QPushButton:pressed {
                        background-color: #0000cc;
                        border-color: #000099;
                    }
                """)
            elif color_name == "Green":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #44ff44;
                        border: 1px solid #00cc00;
                        border-radius: 4px;
                        color: black;
                        padding: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #66ff66;
                        border-color: #00ff00;
                    }
                    QPushButton:pressed {
                        background-color: #00cc00;
                        border-color: #009900;
                    }
                """)
            elif color_name == "Yellow":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffff44;
                        border: 1px solid #cccc00;
                        border-radius: 4px;
                        color: black;
                        padding: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ffff66;
                        border-color: #ffff00;
                    }
                    QPushButton:pressed {
                        background-color: #cccc00;
                        border-color: #999900;
                    }
                """)
            elif color_name == "Purple":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff44ff;
                        border: 1px solid #cc00cc;
                        border-radius: 4px;
                        color: white;
                        padding: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ff66ff;
                        border-color: #ff00ff;
                    }
                    QPushButton:pressed {
                        background-color: #cc00cc;
                        border-color: #990099;
                    }
                """)
            elif color_name == "Orange":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff8844;
                        border: 1px solid #cc6600;
                        border-radius: 4px;
                        color: white;
                        padding: 8px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ffaa66;
                        border-color: #ff8800;
                    }
                    QPushButton:pressed {
                        background-color: #cc6600;
                        border-color: #994400;
                    }
                """)
            
            colors_layout.addWidget(btn, i // 3, i % 3)
        
        group_colors.setLayout(colors_layout)
        control_layout.addWidget(group_colors)
        
        control_layout.addStretch()
        tab_widget.addTab(control_tab, "Controls")
        
        # ==================== ATTRIBUTE TAB ====================
        attribute_tab = QtWidgets.QWidget()
        attribute_layout = QtWidgets.QVBoxLayout(attribute_tab)
        attribute_layout.setSpacing(8)
        attribute_layout.setContentsMargins(8, 8, 8, 8)
        
        # Attribute Tools Section
        group_attributes = QtWidgets.QGroupBox("Attributes")
        group_attributes.setStyleSheet("""
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffffff;
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        attributes_layout = QtWidgets.QGridLayout()
        
        attr_actions = [
            ("Add On/Off", "enum"),
            ("Add 0-1", "floatA"),
            ("Lock All", "lock"),
            ("Unlock All", "unlock")
        ]
        
        for i, (action_name, action_type) in enumerate(attr_actions):
            btn = QtWidgets.QPushButton(action_name)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            if action_type in ["lock", "unlock"]:
                btn.clicked.connect(partial(self.run_lock_hide_attributes_tool, action_type))
            else:
                btn.clicked.connect(partial(self.run_add_attribute_tool, action_type))
            attributes_layout.addWidget(btn, i // 2, i % 2)
        
        group_attributes.setLayout(attributes_layout)
        attribute_layout.addWidget(group_attributes)
        
        attribute_layout.addStretch()
        tab_widget.addTab(attribute_tab, "Attributes")
        
        # ==================== SET TAB ====================
        set_tab = QtWidgets.QWidget()
        set_layout = QtWidgets.QVBoxLayout(set_tab)
        set_layout.setSpacing(8)
        set_layout.setContentsMargins(8, 8, 8, 8)
        
        # Sets Management Section
        group_sets = QtWidgets.QGroupBox("Sets")
        group_sets.setStyleSheet("""
            QGroupBox {
                border: 1px solid #666666;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
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
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffffff;
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        sets_layout = QtWidgets.QGridLayout()
        
        set_operations = [
            ("Create AnimSet", "anim"),
            ("Create RenderSet", "render"),
            ("Add to AnimSet", "anim"),
            ("Add to RenderSet", "render")
        ]
        
        for i, (op_name, set_type) in enumerate(set_operations):
            btn = QtWidgets.QPushButton(op_name)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            if op_name.startswith("Create"):
                btn.clicked.connect(partial(self.run_create_sets_tool, set_type))
            else:
                btn.clicked.connect(partial(self.run_add_to_sets_tool, set_type))
            sets_layout.addWidget(btn, i // 2, i % 2)
        
        group_sets.setLayout(sets_layout)
        set_layout.addWidget(group_sets)
        
        set_layout.addStretch()
        tab_widget.addTab(set_tab, "Sets")
        
        # Add tab widget to main layout
        layout.addWidget(tab_widget)
        
        # Separator and close
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(sep)

        # Action Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        # Close Button
        self.btn_close = QtWidgets.QPushButton("Close")
        self.btn_close.setIcon(style.standardIcon(ICON_MAP['close']))
        self.btn_close.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffffff;
                border-color: #ffffff;
                color: #2D2D2D;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                border-color: #ffffff;
            }
        """)
        self.btn_close.clicked.connect(self.close)
        
        button_layout.addWidget(self.btn_close)
        layout.addLayout(button_layout)

    # ==================== OPTIMIZED TOOL METHODS ====================
    
    def run_quick_tool(self, tool_name):
        """Run quick tools based on name"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        
        if tool_name == "Offset Groups":
            self.tool_instance.run_offset_group_tool()
        elif tool_name == "Joint @ Center":
            self.tool_instance.run_joint_at_center_tool()
        elif tool_name == "Curve to Joint":
            self.tool_instance.run_curve_to_joint_tool()
        elif tool_name == "Inbetween Joints":
            self.tool_instance.run_inbetween_joints_tool()
        elif tool_name == "Zero Out":
            self.tool_instance.run_zero_out_tool()
        elif tool_name == "Re-Skin":
            self.tool_instance.run_reskin_tool()

    def show_controller_dialog(self):
         """Show dialog for additional controller types"""
         if not self.tool_instance:
             from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
             self.tool_instance = RigXUtilityTools()
         
         # Create dialog matching main UI style
         dialog = QtWidgets.QDialog(self)
         dialog.setWindowTitle("Additional Controllers")
         dialog.setFixedSize(400, 300)
         dialog.setModal(True)
         
         # Set transparent grey background only
         dialog.setStyleSheet("""
             QDialog {
                 background-color: rgba(128, 128, 128, 0.8);
             }
         """)
         
         layout = QtWidgets.QVBoxLayout(dialog)
         layout.setSpacing(8)
         layout.setContentsMargins(8, 8, 8, 8)
         
         # Banner matching main UI
         banner_frame = QtWidgets.QFrame()
         banner_frame.setFixedHeight(40)
         banner_frame.setStyleSheet("""
             QFrame {
                 background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                     stop:0 #1b4332, stop:0.5 #2d6a4f, stop:1 #40916c);
                 border-radius: 6px;
             }
             QLabel {
                 color: white;
                 font-size: 14pt;
                 font-weight: bold;
             }
         """)
         banner_layout = QtWidgets.QHBoxLayout(banner_frame)
         banner_layout.setContentsMargins(10, 0, 10, 0)
         
         banner_label = QtWidgets.QLabel("Additional Controllers")
         banner_label.setAlignment(QtCore.Qt.AlignCenter)
         banner_layout.addWidget(banner_label)
         layout.addWidget(banner_frame)
         
         # Create scroll area like main UI
         scroll_area = QtWidgets.QScrollArea()
         scroll_area.setWidgetResizable(True)
         scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
         scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
         
         scroll_widget = QtWidgets.QWidget()
         scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
         scroll_layout.setSpacing(8)
         
         # Controller group box
         group_controllers = QtWidgets.QGroupBox("Controller Types")
         controllers_layout = QtWidgets.QGridLayout()
         controllers_layout.setSpacing(6)
         
         # Additional controller types
         additional_types = ["FatCross", "Cone", "Rombus", "SingleNormal", "FourNormal", "Dumbell", "ArrowOnBall", "Pin"]
         
         for i, ctrl_type in enumerate(additional_types):
             btn = QtWidgets.QPushButton(ctrl_type)
             btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
             btn.setMinimumHeight(30)
             # Use Maya default font and white color with hover effects
             btn.setStyleSheet("""
                 QPushButton {
                     background-color: rgba(74, 85, 104, 0.8);
                     border: 1px solid #666666;
                     border-radius: 4px;
                     padding: 6px;
                     color: white;
                     font-weight: bold;
                 }
                 QPushButton:hover {
                     background-color: rgba(255, 255, 255, 0.9);
                     border-color: #ffffff;
                     color: #2D2D2D;
                 }
                 QPushButton:pressed {
                     background-color: rgba(224, 224, 224, 0.9);
                     border-color: #ffffff;
                 }
             """)
             from functools import partial
             btn.clicked.connect(partial(self.run_create_controller_tool, ctrl_type))
             controllers_layout.addWidget(btn, i // 3, i % 3)
         
         group_controllers.setLayout(controllers_layout)
         scroll_layout.addWidget(group_controllers)
         
         # Add stretch
         scroll_layout.addStretch()
         
         # Set the scroll widget
         scroll_area.setWidget(scroll_widget)
         layout.addWidget(scroll_area)
         
         # Separator and close buttons like main UI
         sep = QtWidgets.QFrame()
         sep.setFrameShape(QtWidgets.QFrame.HLine)
         sep.setFrameShadow(QtWidgets.QFrame.Sunken)
         layout.addWidget(sep)
         
         # Action Buttons
         button_layout = QtWidgets.QHBoxLayout()
         
         # Close Button
         close_btn = QtWidgets.QPushButton("Close")
         close_btn.setIcon(QtWidgets.QApplication.instance().style().standardIcon(QtWidgets.QStyle.SP_DialogCloseButton))
         close_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
         close_btn.setStyleSheet("""
             QPushButton {
                 background-color: #4A4A4A;
                 border: 1px solid #666666;
                 border-radius: 4px;
                 color: #e2e8f0;
                 padding: 8px;
                 font-weight: bold;
             }
             QPushButton:hover {
                 background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                     stop:0 #ffffff, stop:0.5 #f0f0f0, stop:1 #e0e0e0);
                 border-color: #ffffff;
                 color: #2D2D2D;
             }
             QPushButton:pressed {
                 background-color: #e0e0e0;
                 border-color: #ffffff;
             }
         """)
         close_btn.clicked.connect(dialog.close)
         
         button_layout.addWidget(close_btn)
         layout.addLayout(button_layout)
         
         dialog.exec_()

    def run_create_controller_tool(self, controller_type):
        """Run controller creation tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_create_controller_tool(controller_type)

    def run_override_color_tool(self, color_index):
        """Run color override tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_override_color_tool(color_index)

    def run_orient_joint_tool(self, orientation_type):
        """Run joint orientation tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_orient_joint_tool(orientation_type)

    def run_add_attribute_tool(self, attr_type):
        """Run add attribute tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_add_attribute_tool(attr_type)

    def run_lock_hide_attributes_tool(self, action_type):
        """Run lock/hide attributes tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_lock_hide_attributes_tool(action_type)

    def run_copy_weights_tool(self, copy_type):
        """Run copy weights tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_copy_weights_tool(copy_type)

    def run_create_sets_tool(self, set_type):
        """Run create sets tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_create_sets_tool(set_type)

    def run_add_to_sets_tool(self, set_type):
        """Run add to sets tool"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_add_to_sets_tool(set_type)
