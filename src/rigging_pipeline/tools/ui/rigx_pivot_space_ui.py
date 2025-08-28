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
from rigging_pipeline.utils.rig.utils_rig import select_object, rigx_create_pivot_space

def maya_main_window():
    if not MAYA_AVAILABLE:
        return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class PivotSpaceToolUI(QtWidgets.QDialog):
    """Pivot Space Tool"""
    def __init__(self, parent=None):
        super().__init__(parent or maya_main_window())
        QtWidgets.QApplication.instance().setStyleSheet(THEME_STYLESHEET)
        self.setWindowTitle("Pivot Space Tool")
        self.resize(400, 300)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Colorful Gradient Banner
        banner_frame = QtWidgets.QFrame()
        banner_frame.setFixedHeight(60)
        banner_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1b4332, stop:0.5 #2d6a4f, stop:1 #40916c);
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-size: 18pt;
                font-weight: bold;
            }
            QLabel#icon {
                padding-left: 35px;
                background: transparent;
                padding-top: 10px;
            }
            QLabel#title {
                padding-right: 35px;
            }
        """)
        banner_layout = QtWidgets.QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        banner_layout.setSpacing(10)

        # Add custom icon
        icon_path = os.path.join(os.path.expanduser("~"), "Documents", "maya", "2024", "prefs", "icons", "pivotTool.png")
        if os.path.exists(icon_path):
            icon_label = QtWidgets.QLabel()
            icon_label.setObjectName("icon")
            icon_pixmap = QtGui.QPixmap(icon_path)
            icon_pixmap = icon_pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            banner_layout.addWidget(icon_label)
        else:
            print(f"Warning: Icon not found at {icon_path}")

        banner_label = QtWidgets.QLabel("Pivot Space Tool")
        banner_label.setAlignment(QtCore.Qt.AlignCenter)
        banner_layout.addWidget(banner_label)

        # Update the banner label styling
        banner_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18pt;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)

        banner_layout.addStretch()
        layout.addWidget(banner_frame)

        # Main content
        content_group = QtWidgets.QGroupBox("Pivot Space Settings")
        content_layout = QtWidgets.QVBoxLayout()

        # Control selection
        control_layout = QtWidgets.QHBoxLayout()
        control_label = QtWidgets.QLabel("Control:")
        self.control_field = QtWidgets.QLineEdit()
        select_btn = QtWidgets.QPushButton("<<<")
        select_btn.clicked.connect(self._on_select_control)
        control_layout.addWidget(control_label)
        control_layout.addWidget(self.control_field)
        control_layout.addWidget(select_btn)
        content_layout.addLayout(control_layout)

        # Attribute name
        attr_layout = QtWidgets.QHBoxLayout()
        attr_label = QtWidgets.QLabel("Attribute Name:")
        self.attr_field = QtWidgets.QLineEdit("pivotSpace")
        attr_layout.addWidget(attr_label)
        attr_layout.addWidget(self.attr_field)
        content_layout.addLayout(attr_layout)

        # Enum string
        enum_layout = QtWidgets.QHBoxLayout()
        enum_label = QtWidgets.QLabel("Enum Values:")
        self.enum_field = QtWidgets.QLineEdit()
        self.enum_field.setText("pos1:pos2:pos3")
        enum_layout.addWidget(enum_label)
        enum_layout.addWidget(self.enum_field)
        content_layout.addLayout(enum_layout)

        # Transform fields
        self.transform_fields = []
        for i in range(3):
            transform_layout = QtWidgets.QHBoxLayout()
            transform_label = QtWidgets.QLabel(f"Transform {i+1}:")
            transform_field = QtWidgets.QLineEdit()
            select_btn = QtWidgets.QPushButton("<<<")
            select_btn.clicked.connect(lambda *args, idx=i: self._on_select_transform(idx))
            transform_layout.addWidget(transform_label)
            transform_layout.addWidget(transform_field)
            transform_layout.addWidget(select_btn)
            content_layout.addLayout(transform_layout)
            self.transform_fields.append(transform_field)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # Create button
        self.create_btn = QtWidgets.QPushButton("Create Pivot Space")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d6a4f;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #40916c;
            }
        """)
        self.create_btn.clicked.connect(self._on_create)
        layout.addWidget(self.create_btn)

        # Close button
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)

    def _on_select_control(self):
        sel = cmds.ls(selection=True)
        if sel:
            self.control_field.setText(sel[0])

    def _on_select_transform(self, index):
        sel = cmds.ls(selection=True)
        if sel:
            self.transform_fields[index].setText(sel[0])

    def _on_create(self):
        control = self.control_field.text()
        attr_name = self.attr_field.text()
        enum_string = self.enum_field.text()
        
        # Get non-empty transform fields
        passing_controls = [field.text() for field in self.transform_fields if field.text()]
        
        if rigx_create_pivot_space(control, attr_name, enum_string, passing_controls):
            cmds.inViewMessage(statusMessage="Pivot space created successfully.", fade=True)
        else:
            cmds.warning("Failed to create pivot space.")

def show_pivot_space_tool():
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, PivotSpaceToolUI):
            w.show()
            w.raise_()
            w.activateWindow()
            return w
    win = PivotSpaceToolUI()
    win.setParent(maya_main_window(), QtCore.Qt.Window)
    win.setWindowFlags(QtCore.Qt.Window)
    win.show()
    return win 