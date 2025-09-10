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
        
        # Joint Radius Control Section
        group_radius = QtWidgets.QGroupBox("Joint Radius Control")
        group_radius.setStyleSheet("""
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
            QSlider::groove:horizontal {
                border: 1px solid #666666;
                height: 8px;
                background: #4A4A4A;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #48BB78, stop:0.5 #3AA356, stop:1 #2F855A);
                border: 1px solid #666666;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ECC7F, stop:0.5 #5CBB6D, stop:1 #48BB78);
                border-color: #888888;
            }
            QLabel {
                color: #e2e8f0;
                font-weight: bold;
            }
            QDoubleSpinBox {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px;
                font-weight: bold;
            }
            QDoubleSpinBox:focus {
                border-color: #ffffff;
            }
        """)
        
        radius_layout = QtWidgets.QHBoxLayout()
        radius_layout.setSpacing(10)
        
        # Radius label
        radius_label = QtWidgets.QLabel("Radius:")
        radius_label.setMinimumWidth(50)
        
        # Radius slider
        self.radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radius_slider.setMinimum(0)
        self.radius_slider.setMaximum(100)  # 0-100 for 0.0-10.0 range
        self.radius_slider.setValue(10)  # Default to 1.0
        self.radius_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.radius_slider.setTickInterval(10)
        
        # Radius spinbox (double for float values)
        self.radius_spinbox = QtWidgets.QDoubleSpinBox()
        self.radius_spinbox.setMinimum(0.0)
        self.radius_spinbox.setMaximum(10.0)
        self.radius_spinbox.setValue(1.0)
        self.radius_spinbox.setSingleStep(0.1)
        self.radius_spinbox.setDecimals(1)
        self.radius_spinbox.setSuffix("")
        
        # Connect signals for real-time updates
        self.radius_slider.valueChanged.connect(self._on_slider_changed)
        self.radius_spinbox.valueChanged.connect(self._on_spinbox_changed)
        
        # Add widgets to layout
        radius_layout.addWidget(radius_label)
        radius_layout.addWidget(self.radius_slider)
        radius_layout.addWidget(self.radius_spinbox)
        
        group_radius.setLayout(radius_layout)
        joint_layout.addWidget(group_radius)
        
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
        quick_layout = QtWidgets.QVBoxLayout()
        
        quick_tools = [
            ("Joint @ Center", "joint"),
            ("Curve to Joint", "create"),
            ("Inbetween Joints", "create"),
            ("Rotation to Orient", "orient"),
            ("Orient to Rotation", "orient")
        ]
        
        for i, (tool_name, icon_key) in enumerate(quick_tools):
            # Create custom icon for Joint @ Center
            if tool_name == "Joint @ Center":
                btn = self._create_joint_center_button(tool_name)
            else:
                btn = QtWidgets.QPushButton(tool_name)
            
            # Add tooltip descriptions
            self._add_tooltip(btn, tool_name)
            
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            from functools import partial
            btn.clicked.connect(partial(self.run_quick_tool, tool_name))
            quick_layout.addWidget(btn)
        
        group_quick.setLayout(quick_layout)
        joint_layout.addWidget(group_quick)
        
        # Joint Tools Section (Merged with Orient Tools)
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
        
        # Main layout for the merged section
        joints_main_layout = QtWidgets.QVBoxLayout()
        joints_main_layout.setSpacing(8)
        
        # Orientation buttons layout
        joints_layout = QtWidgets.QGridLayout()
        orientation_types = ["YUP", "YDN", "ZUP", "ZDN", "NONE"]
        for i, orient_type in enumerate(orientation_types):
            btn = QtWidgets.QPushButton(f"Orient {orient_type}")
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            btn.clicked.connect(partial(self.run_orient_joint_tool, orient_type))
            joints_layout.addWidget(btn, 0, i)
        
        joints_main_layout.addLayout(joints_layout)
        
        # CometJointOrient Tool Button
        comet_orient_btn = QtWidgets.QPushButton("CometJointOrient Tool")
        comet_orient_btn.setMinimumHeight(32)
        # Add tooltip description
        self._add_tooltip(comet_orient_btn, "CometJointOrient Tool")
        comet_orient_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #383838, stop:1 #48BB78);
                border: 1px solid #666666;
                border-radius: 4px;
                color: #2D2D2D;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #6ECC7F, stop:1 #5CBB6D);
                border-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #48BB78, stop:1 #3AA356);
                color: #2D2D2D;
            }
        """)
        comet_orient_btn.clicked.connect(partial(self.run_joint_tool, "comet_orient"))
        joints_main_layout.addWidget(comet_orient_btn)
        
        group_joints.setLayout(joints_main_layout)
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
            # Add tooltip descriptions
            self._add_tooltip(btn, tool_name)
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

        # Attribute Manager Section (only)
        group_attr_manager = QtWidgets.QGroupBox("Attribute Manager")
        group_attr_manager.setStyleSheet("""
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
            QListWidget {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #e2e8f0;
            }
            QPushButton {
                background-color: #4A4A4A;
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 6px;
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
        attr_manager_layout = QtWidgets.QVBoxLayout()

        body_row = QtWidgets.QHBoxLayout()

        btn_col = QtWidgets.QVBoxLayout()
        add_btn = QtWidgets.QPushButton("Add Attribute")
        add_btn.clicked.connect(self.add_attribute_dialog)
        remove_btn = QtWidgets.QPushButton("Remove Attribute")
        remove_btn.clicked.connect(self.remove_selected_attributes)
        lock_btn = QtWidgets.QPushButton("Lock")
        lock_btn.clicked.connect(lambda: self.apply_attr_action_to_selection("lock"))
        unlock_btn = QtWidgets.QPushButton("Unlock")
        unlock_btn.clicked.connect(lambda: self.apply_attr_action_to_selection("unlock"))
        hide_btn = QtWidgets.QPushButton("Hide")
        hide_btn.clicked.connect(lambda: self.apply_attr_action_to_selection("hide"))
        unhide_btn = QtWidgets.QPushButton("Unhide")
        unhide_btn.clicked.connect(self.show_unhide_dialog)
        transfer_btn = QtWidgets.QPushButton("Transfer →")
        transfer_btn.clicked.connect(self.transfer_selected_attribute)

        for w in [add_btn, remove_btn, lock_btn, unlock_btn, hide_btn, unhide_btn, transfer_btn]:
            btn_col.addWidget(w)
        btn_col.addStretch()
        body_row.addLayout(btn_col, 1)

        attr_manager_layout.addLayout(body_row)
        group_attr_manager.setLayout(attr_manager_layout)
        attribute_layout.addWidget(group_attr_manager)

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
        
        # ==================== RENAME TAB ====================
        rename_tab = QtWidgets.QWidget()
        rename_layout = QtWidgets.QVBoxLayout(rename_tab)
        rename_layout.setSpacing(8)
        rename_layout.setContentsMargins(8, 8, 8, 8)
        
        # Selection Mode Section
        selection_group = QtWidgets.QGroupBox("Selection Mode")
        selection_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #cccccc;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #2D2D2D;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px 0 5px;
            }
        """)
        
        selection_layout = QtWidgets.QHBoxLayout(selection_group)
        selection_layout.setSpacing(15)
        
        self.radio_selected = QtWidgets.QRadioButton("Selected")
        self.radio_hierarchy = QtWidgets.QRadioButton("Hierarchy")
        self.radio_all = QtWidgets.QRadioButton("All")
        
        # Set default to Selected
        self.radio_selected.setChecked(True)
        
        # Style the radio buttons
        radio_style = """
            QRadioButton {
                color: #e2e8f0;
                font-weight: bold;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #666666;
                border-radius: 8px;
                background-color: #2D2D2D;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #cccccc;
                border-radius: 8px;
                background-color: #48BB78;
            }
        """
        
        self.radio_selected.setStyleSheet(radio_style)
        self.radio_hierarchy.setStyleSheet(radio_style)
        self.radio_all.setStyleSheet(radio_style)
        
        selection_layout.addWidget(self.radio_selected)
        selection_layout.addWidget(self.radio_hierarchy)
        selection_layout.addWidget(self.radio_all)
        selection_layout.addStretch()
        
        rename_layout.addWidget(selection_group)
        
        # Search & Replace Section
        group_search_replace = QtWidgets.QGroupBox("Search & Replace")
        group_search_replace.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #cccccc;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #2D2D2D;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px 0 5px;
            }
        """)
        
        search_replace_layout = QtWidgets.QVBoxLayout()
        search_replace_layout.setSpacing(5)
        
        # Search field
        search_row = QtWidgets.QHBoxLayout()
        search_row.addWidget(QtWidgets.QLabel("Search:"))
        self.search_field = QtWidgets.QLineEdit()
        self.search_field.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #cccccc;
                background-color: #404040;
            }
        """)
        search_row.addWidget(self.search_field)
        search_replace_layout.addLayout(search_row)
        
        # Replace field
        replace_row = QtWidgets.QHBoxLayout()
        replace_row.addWidget(QtWidgets.QLabel("Replace:"))
        self.replace_field = QtWidgets.QLineEdit()
        self.replace_field.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #cccccc;
                background-color: #404040;
            }
        """)
        replace_row.addWidget(self.replace_field)
        search_replace_layout.addLayout(replace_row)
        
        # Search & Replace button
        search_btn = QtWidgets.QPushButton("Search And Replace")
        search_btn.setMinimumHeight(32)
        # Add tooltip description
        self._add_tooltip(search_btn, "Search And Replace")
        search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #383838, stop:1 #48BB78);
                border: 1px solid #666666;
                border-radius: 4px;
                color: #2D2D2D;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #6ECC7F, stop:1 #5CBB6D);
                border-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #48BB78, stop:1 #3AA356);
                color: #2D2D2D;
            }
        """)
        search_btn.clicked.connect(partial(self.run_rename_tool, "search_replace_ui"))
        search_replace_layout.addWidget(search_btn)
        
        group_search_replace.setLayout(search_replace_layout)
        rename_layout.addWidget(group_search_replace)
        
        # Prefix/Suffix Section
        group_prefix_suffix = QtWidgets.QGroupBox("Add Prefix / Suffix")
        group_prefix_suffix.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #cccccc;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #2D2D2D;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px 0 5px;
            }
        """)
        
        prefix_suffix_layout = QtWidgets.QVBoxLayout()
        prefix_suffix_layout.setSpacing(5)
        
        # Prefix field
        prefix_row = QtWidgets.QHBoxLayout()
        prefix_row.addWidget(QtWidgets.QLabel("Prefix:"))
        self.prefix_field = QtWidgets.QLineEdit()
        self.prefix_field.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #cccccc;
                background-color: #404040;
            }
        """)
        prefix_row.addWidget(self.prefix_field)
        prefix_btn = QtWidgets.QPushButton("Add")
        prefix_btn.setMinimumWidth(60)
        # Add tooltip description
        self._add_tooltip(prefix_btn, "Add Prefix")
        prefix_btn.setStyleSheet(self._get_button_style())
        prefix_btn.clicked.connect(partial(self.run_rename_tool, "prefix_ui"))
        prefix_row.addWidget(prefix_btn)
        prefix_suffix_layout.addLayout(prefix_row)
        
        # Suffix field
        suffix_row = QtWidgets.QHBoxLayout()
        suffix_row.addWidget(QtWidgets.QLabel("Suffix:"))
        self.suffix_field = QtWidgets.QLineEdit()
        self.suffix_field.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #cccccc;
                background-color: #404040;
            }
        """)
        suffix_row.addWidget(self.suffix_field)
        suffix_btn = QtWidgets.QPushButton("Add")
        suffix_btn.setMinimumWidth(60)
        # Add tooltip description
        self._add_tooltip(suffix_btn, "Add Suffix")
        suffix_btn.setStyleSheet(self._get_button_style())
        suffix_btn.clicked.connect(partial(self.run_rename_tool, "suffix_ui"))
        suffix_row.addWidget(suffix_btn)
        prefix_suffix_layout.addLayout(suffix_row)
        
        group_prefix_suffix.setLayout(prefix_suffix_layout)
        rename_layout.addWidget(group_prefix_suffix)
        
        # Rename & Number Section
        group_rename_number = QtWidgets.QGroupBox("Rename & Number")
        group_rename_number.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #cccccc;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #2D2D2D;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px 0 5px;
            }
        """)
        
        rename_number_layout = QtWidgets.QVBoxLayout()
        rename_number_layout.setSpacing(5)
        
        # Rename field
        rename_row = QtWidgets.QHBoxLayout()
        rename_row.addWidget(QtWidgets.QLabel("Rename:"))
        self.rename_field = QtWidgets.QLineEdit()
        self.rename_field.setStyleSheet("""
            QLineEdit {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #cccccc;
                background-color: #404040;
            }
        """)
        rename_row.addWidget(self.rename_field)
        rename_number_layout.addLayout(rename_row)
        
        # Number controls
        number_row = QtWidgets.QHBoxLayout()
        number_row.addWidget(QtWidgets.QLabel("Start #:"))
        self.start_spin = QtWidgets.QSpinBox()
        self.start_spin.setRange(0, 9999)
        self.start_spin.setValue(1)
        self.start_spin.setMinimumWidth(60)
        number_row.addWidget(self.start_spin)
        
        number_row.addWidget(QtWidgets.QLabel("Padding:"))
        self.padding_spin = QtWidgets.QSpinBox()
        self.padding_spin.setRange(0, 10)
        self.padding_spin.setValue(2)
        self.padding_spin.setMinimumWidth(60)
        number_row.addWidget(self.padding_spin)
        rename_number_layout.addLayout(number_row)
        
        rename_btn = QtWidgets.QPushButton("Rename")
        rename_btn.setMinimumHeight(32)
        # Add tooltip description
        self._add_tooltip(rename_btn, "Rename")
        rename_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #383838, stop:1 #48BB78);
                border: 1px solid #666666;
                border-radius: 4px;
                color: #2D2D2D;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #6ECC7F, stop:1 #5CBB6D);
                border-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #48BB78, stop:1 #3AA356);
                color: #2D2D2D;
            }
        """)
        rename_btn.clicked.connect(partial(self.run_rename_tool, "sequential_ui"))
        rename_number_layout.addWidget(rename_btn)
        
        group_rename_number.setLayout(rename_number_layout)
        rename_layout.addWidget(group_rename_number)
        
        # Utility Tools Section
        group_utilities = QtWidgets.QGroupBox("Utility Tools")
        group_utilities.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #cccccc;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #2D2D2D;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px 0 5px;
            }
        """)
        
        utilities_layout = QtWidgets.QGridLayout()
        utilities_layout.setSpacing(5)
        
        utility_tools = [
            ("Upper Case", "upper"),
            ("Lower Case", "lower"),
            ("Title Case", "title"),
            ("Camel Case", "camel"),
            ("Fix Duplicates", "fix_duplicates"),
            ("Fix Shape Names", "fix_shapes")
        ]
        
        for i, (text, action) in enumerate(utility_tools):
            btn = QtWidgets.QPushButton(text)
            btn.setMinimumHeight(28)
            btn.setStyleSheet(self._get_button_style())
            btn.clicked.connect(partial(self.run_rename_tool, action))
            utilities_layout.addWidget(btn, i // 2, i % 2)
        
        group_utilities.setLayout(utilities_layout)
        rename_layout.addWidget(group_utilities)
        
        # Clear All Fields - Full width button
        clear_btn = QtWidgets.QPushButton("Clear All Fields")
        clear_btn.setMinimumHeight(35)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                stop:0 #383838, stop:1 #48BB78);
                border: 1px solid #666666;
                border-radius: 4px;
                color: #e2e8f0;
                font-weight: bold;
                padding: 8px;
                margin-top: 5px;
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
        clear_btn.clicked.connect(partial(self.run_rename_tool, "clear_fields"))
        rename_layout.addWidget(clear_btn)
        
        rename_layout.addStretch()
        tab_widget.addTab(rename_tab, "Rename")
        
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
    
    def _create_joint_center_button(self, tool_name):
        """Create Joint @ Center button with custom icon"""
        # Load custom jointAtCenter icon
        icon_path = r"C:\Users\mohanraj.s\Documents\maya\scripts\rigX\config\icons\rigX_jointAtCenter.png"
        
        if os.path.exists(icon_path):
            joint_icon = QtGui.QIcon(icon_path)
            btn = QtWidgets.QPushButton(joint_icon, tool_name)
            # Set proper alignment for icon and text
            btn.setStyleSheet("""
                QPushButton {
                    text-align: center;
                    padding-left: 4px;
                    padding-right: 8px;
                    padding-top: 4px;
                    padding-bottom: 4px;
                }
                QPushButton QIcon {
                    margin-right: 4px;
                }
            """)
        else:
            # Fallback to standard button if icon not found
            btn = QtWidgets.QPushButton(tool_name)
            print(f"Warning: Joint @ Center icon not found at {icon_path}")
        
        return btn

    def _add_tooltip(self, button, tool_name):
        """Add tooltip descriptions for buttons"""
        tooltips = {
            "Joint @ Center": "Create a joint at the center of selected objects, vert, edges or faces",
            "Curve to Joint": "Create joints along a selected curve based on curve length",
            "Inbetween Joints": "Create joints between two selected joints",
            "Rotation to Orient": "Convert rotation values to joint orient values",
            "Orient to Rotation": "Convert joint orient values to rotation values",
            "Offset Groups": "Create offset groups for selected objects",
            "Zero Out": "Reset transforms to zero for selected objects",
            "Re-Skin": "Re-skin selected objects",
            "CometJointOrient Tool": "Open the full CometJointOrient tool for advanced joint orientation",
            "Search And Replace": "Search for text in object names and replace with new text",
            "Add Prefix": "Add a prefix to the beginning of selected object names",
            "Add Suffix": "Add a suffix to the end of selected object names",
            "Rename": "Rename selected objects with sequential numbering"
        }
        
        if tool_name in tooltips:
            button.setToolTip(tooltips[tool_name])

    def _on_slider_changed(self, value):
        """Handle slider value change - convert to float and update spinbox"""
        float_value = value / 10.0  # Convert 0-100 to 0.0-10.0
        self.radius_spinbox.blockSignals(True)
        self.radius_spinbox.setValue(float_value)
        self.radius_spinbox.blockSignals(False)
        self.apply_joint_radius()

    def _on_spinbox_changed(self, value):
        """Handle spinbox value change - convert to int and update slider"""
        int_value = int(value * 10)  # Convert 0.0-10.0 to 0-100
        self.radius_slider.blockSignals(True)
        self.radius_slider.setValue(int_value)
        self.radius_slider.blockSignals(False)
        self.apply_joint_radius()

    def apply_joint_radius(self):
        """Apply radius to selected joints or all joints if none selected"""
        try:
            import maya.cmds as cmds
            
            radius_value = self.radius_spinbox.value()
            
            # Get selected objects
            selection = cmds.ls(selection=True)
            
            # Filter for joints only
            joints = []
            if selection:
                # Check if any selected objects are joints
                for obj in selection:
                    if cmds.nodeType(obj) == "joint":
                        joints.append(obj)
                    else:
                        # Check if it's a transform with joint shape
                        shapes = cmds.listRelatives(obj, shapes=True, type="joint")
                        if shapes:
                            joints.append(obj)
            
            # If no joints selected, get all joints in scene
            if not joints:
                joints = cmds.ls(type="joint")
                if not joints:
                    return  # No joints found, silently return
            
            # Apply radius to joints
            for joint in joints:
                try:
                    cmds.setAttr(f"{joint}.radius", radius_value)
                except Exception as e:
                    print(f"Warning: Could not set radius for {joint}: {e}")
                    continue
            
        except Exception as e:
            cmds.warning(f"Error applying joint radius: {str(e)}")

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
        elif tool_name == "Rotation to Orient":
            self.tool_instance.run_rotation_to_orient_tool()
        elif tool_name == "Orient to Rotation":
            self.tool_instance.run_orient_to_rotation_tool()
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

    # ===== Attribute Manager handlers =====
    def refresh_attribute_list(self):
        # List UI removed; nothing to refresh
        pass

    def _selected_attr_names(self):
        try:
            import maya.cmds as cmds
            # Query selected main attributes from Maya's Channel Box
            attrs = cmds.channelBox('mainChannelBox', query=True, selectedMainAttributes=True) or []
            # Ensure list of unique strings
            return list(dict.fromkeys([a for a in attrs if isinstance(a, str) and a]))
        except Exception:
            return []

    def add_attribute_dialog(self):
        try:
            from PySide2 import QtWidgets
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Add Attribute")
            dialog.setModal(True)
            layout = QtWidgets.QFormLayout(dialog)
            name_edit = QtWidgets.QLineEdit()
            type_combo = QtWidgets.QComboBox()
            type_combo.addItems(["double", "long", "bool", "enum"])
            enum_edit = QtWidgets.QLineEdit()
            enum_edit.setPlaceholderText("enum1:enum2:enum3")
            min_spin = QtWidgets.QDoubleSpinBox()
            min_spin.setRange(-1e9, 1e9)
            min_spin.setDecimals(4)
            min_spin.setValue(0.0)
            max_spin = QtWidgets.QDoubleSpinBox()
            max_spin.setRange(-1e9, 1e9)
            max_spin.setDecimals(4)
            max_spin.setValue(1.0)
            def _toggle_minmax(idx):
                t = type_combo.currentText()
                enabled = t in ["double", "long"]
                min_spin.setEnabled(enabled)
                max_spin.setEnabled(enabled)
                enum_edit.setEnabled(t == "enum")
            type_combo.currentIndexChanged.connect(_toggle_minmax)
            _toggle_minmax(0)
            layout.addRow("Name", name_edit)
            layout.addRow("Type", type_combo)
            layout.addRow("Enum", enum_edit)
            layout.addRow("Min", min_spin)
            layout.addRow("Max", max_spin)
            btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            layout.addRow(btns)
            btns.accepted.connect(dialog.accept)
            btns.rejected.connect(dialog.reject)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                name = name_edit.text().strip()
                attr_type = type_combo.currentText()
                enum_def = enum_edit.text().strip()
                min_val = min_spin.value()
                max_val = max_spin.value()
                if not name:
                    QtWidgets.QMessageBox.warning(self, "Add Attribute", "Please enter an attribute name")
                    return
                if not self.tool_instance:
                    from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
                    self.tool_instance = RigXUtilityTools()
                self.tool_instance.attribute_manager("add", [name], {"type": attr_type, "enum": enum_def, "min": min_val, "max": max_val})
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Add Attribute", f"Error: {e}")

    def remove_selected_attributes(self):
        try:
            names = self._selected_attr_names()
            if not names:
                QtWidgets.QMessageBox.information(self, "Remove Attribute", "Select attribute(s) in the Channel Box")
                return
            if not self.tool_instance:
                from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
                self.tool_instance = RigXUtilityTools()
            self.tool_instance.attribute_manager("remove", names)
            self.refresh_attribute_list()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Remove Attribute", f"Error: {e}")

    def apply_attr_action_to_selection(self, action):
        try:
            names = self._selected_attr_names()
            if not names and action in ["lock", "unlock", "hide", "unhide"]:
                QtWidgets.QMessageBox.information(self, action.title(), "Select attribute(s) in the Channel Box")
                return
            if not self.tool_instance:
                from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
                self.tool_instance = RigXUtilityTools()
            self.tool_instance.attribute_manager(action, names)
            self.refresh_attribute_list()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, action.title(), f"Error: {e}")

    def show_unhide_dialog(self):
        try:
            import maya.cmds as cmds
            from PySide2 import QtWidgets
            sel = cmds.ls(selection=True) or []
            if not sel:
                QtWidgets.QMessageBox.information(self, "Unhide Attributes", "Select one or more objects in the Outliner")
                return
            if not self.tool_instance:
                from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
                self.tool_instance = RigXUtilityTools()
            # Gather hidden attributes across all selected; use intersection to show only common ones
            hidden_sets = []
            for obj in sel:
                hidden_sets.append(set(self.tool_instance.list_hidden_attributes(obj)))
            hidden_common = sorted(list(set.intersection(*hidden_sets))) if hidden_sets else []
            if not hidden_common:
                QtWidgets.QMessageBox.information(self, "Unhide Attributes", "No hidden user-defined attributes found on all selected objects")
                return
            # Multi-select dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Unhide Attributes")
            layout = QtWidgets.QVBoxLayout(dialog)
            list_widget = QtWidgets.QListWidget()
            list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
            for a in hidden_common:
                list_widget.addItem(a)
            layout.addWidget(list_widget)
            btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            layout.addWidget(btns)
            btns.accepted.connect(dialog.accept)
            btns.rejected.connect(dialog.reject)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                names = [i.text() for i in list_widget.selectedItems()]
                if not names:
                    return
                # Apply unhide across all selected objects
                self.tool_instance.attribute_manager("unhide", names)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Unhide Attributes", f"Error: {e}")

    def transfer_selected_attribute(self):
        try:
            import maya.cmds as cmds
            names = self._selected_attr_names()
            if len(names) != 1:
                QtWidgets.QMessageBox.information(self, "Transfer Attribute", "Select exactly one attribute in the Channel Box")
                return
            sel = cmds.ls(selection=True) or []
            if len(sel) != 2:
                QtWidgets.QMessageBox.information(self, "Transfer Attribute", "Select exactly two objects (TARGET first, then SOURCE)")
                return
            if not self.tool_instance:
                from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
                self.tool_instance = RigXUtilityTools()
            # User flow: target first, then source
            target_obj = sel[0]
            source_obj = sel[1]
            self.tool_instance.attribute_manager("transfer", names, {"source": source_obj, "target": target_obj})
            self.refresh_attribute_list()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Transfer Attribute", f"Error: {e}")


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

    def run_rename_tool(self, action):
        """Run rename tool based on action"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        
        # Pass UI field values for the UI-based actions
        ui_data = {}
        if hasattr(self, 'search_field'):
            ui_data['search_text'] = self.search_field.text()
        if hasattr(self, 'replace_field'):
            ui_data['replace_text'] = self.replace_field.text()
        if hasattr(self, 'prefix_field'):
            ui_data['prefix_text'] = self.prefix_field.text()
        if hasattr(self, 'suffix_field'):
            ui_data['suffix_text'] = self.suffix_field.text()
        if hasattr(self, 'rename_field'):
            ui_data['rename_text'] = self.rename_field.text()
        if hasattr(self, 'start_spin'):
            ui_data['start_num'] = self.start_spin.value()
        if hasattr(self, 'padding_spin'):
            ui_data['padding'] = self.padding_spin.value()
        
        # Add selection mode
        if hasattr(self, 'radio_selected') and hasattr(self, 'radio_hierarchy') and hasattr(self, 'radio_all'):
            if self.radio_selected.isChecked():
                ui_data['selection_mode'] = 'selected'
            elif self.radio_hierarchy.isChecked():
                ui_data['selection_mode'] = 'hierarchy'
            elif self.radio_all.isChecked():
                ui_data['selection_mode'] = 'all'
            else:
                ui_data['selection_mode'] = 'selected'  # Default fallback
        
        # Handle special UI actions
        if action == "clear_fields":
            self._clear_rename_fields()
        else:
            self.tool_instance.run_rename_tool(action, ui_data)

    def run_joint_tool(self, action):
        """Run joint tool based on action"""
        if not self.tool_instance:
            from rigging_pipeline.tools.rigx_utilityTools import RigXUtilityTools
            self.tool_instance = RigXUtilityTools()
        self.tool_instance.run_joint_tool(action)

    def _clear_rename_fields(self):
        """Clear all rename input fields"""
        try:
            if hasattr(self, 'search_field'):
                self.search_field.clear()
            if hasattr(self, 'replace_field'):
                self.replace_field.clear()
            if hasattr(self, 'prefix_field'):
                self.prefix_field.clear()
            if hasattr(self, 'suffix_field'):
                self.suffix_field.clear()
            if hasattr(self, 'rename_field'):
                self.rename_field.clear()
            if hasattr(self, 'start_spin'):
                self.start_spin.setValue(1)
            if hasattr(self, 'padding_spin'):
                self.padding_spin.setValue(2)
            print("Cleared all rename fields")
        except Exception as e:
            print(f"Error clearing fields: {str(e)}")

    def _get_button_style(self):
        """Get consistent button styling for rename tools"""
        return """
            QPushButton {
                background-color: #2D2D2D;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                color: #e2e8f0;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,0.1), stop:1 rgba(255,255,255,0.05));
                border-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
                color: #2D2D2D;
            }
        """

    def closeEvent(self, event):
        """Handle window close event - clean up resources"""
        # Clean up any resources if needed
        try:
            # Remove from UIManager if it exists
            from rigging_pipeline.tools.rigx_utilityTools import UIManager
            if "RigXUtilityTools" in UIManager._open_windows:
                del UIManager._open_windows["RigXUtilityTools"]
        except Exception as e:
            # If there's any error, just continue
            pass
        
        # Accept the close event
        event.accept()
