import os, sys
import maya.cmds as cmds
import maya.OpenMayaUI as omui

from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore, QtGui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET

from rigging_pipeline.tools.rigx_renameTool import launch_renameTool
from rigging_pipeline.utils.model.utils_model_hierarchy import create_model_hierarchy
from rigging_pipeline.utils.rig.utils_name import search_replace


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class GradientBanner(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(GradientBanner, self).__init__(parent)
        self.setFixedHeight(40)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        gradient = QtGui.QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QtGui.QColor(45, 45, 45))
        gradient.setColorAt(1, QtGui.QColor(65, 65, 65))
        painter.fillRect(self.rect(), gradient)


class ModelToolkitWindow(QtWidgets.QDialog):
    """ZFX Model Utility: Standardized Interface"""
    WINDOW_TITLE = "QubeX Model Utility"

    def __init__(self, parent=None):
        super(ModelToolkitWindow, self).__init__(parent or maya_main_window())
        self.setStyleSheet(THEME_STYLESHEET)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(400, 600)
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
                    stop:0 #2b2d42, stop:0.5 #3d405b, stop:1 #4a4e69);
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
        banner_layout.setSpacing(0)

        # Add custom icon
        icon_path = os.path.join(os.path.expanduser("~"), "Documents", "maya", "2024", "prefs", "icons", "modelToolkit.png")
        if os.path.exists(icon_path):
            icon_label = QtWidgets.QLabel()
            icon_label.setObjectName("icon")
            icon_pixmap = QtGui.QPixmap(icon_path)
            # Scale the icon to 40x40 while maintaining aspect ratio
            icon_pixmap = icon_pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            banner_layout.addWidget(icon_label)

        banner_label = QtWidgets.QLabel("QubeX Utility")
        banner_label.setObjectName("title")
        banner_label.setAlignment(QtCore.Qt.AlignCenter)
        banner_layout.addWidget(banner_label)

        banner_layout.addStretch()

        layout.addWidget(banner_frame)

        # Main content container
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        layout.addWidget(content)

        # Hierarchy Section
        hierarchy_grp = QtWidgets.QGroupBox("Create Hierarchy")
        hierarchy_layout = QtWidgets.QVBoxLayout(hierarchy_grp)
        
        form = QtWidgets.QFormLayout()
        self.h_root = QtWidgets.QLineEdit("charZebuHuman")
        self.h_asset = QtWidgets.QLineEdit("zebuHumanA")
        form.addRow("Asset Name:", self.h_root)
        form.addRow("Variant:", self.h_asset)
        hierarchy_layout.addLayout(form)

        btn_hierarchy = QtWidgets.QPushButton("Create Hierarchy")
        btn_hierarchy.clicked.connect(self._on_hierarchy)
        btn_hierarchy.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        hierarchy_layout.addWidget(btn_hierarchy)

        self.h_status = QtWidgets.QLabel("")
        hierarchy_layout.addWidget(self.h_status)
        content_layout.addWidget(hierarchy_grp)

        # Separator
        sep1 = QtWidgets.QFrame()
        sep1.setFrameShape(QtWidgets.QFrame.HLine)
        sep1.setFrameShadow(QtWidgets.QFrame.Sunken)
        content_layout.addWidget(sep1)

        # Rename Section
        rename_grp = QtWidgets.QGroupBox("Rename Objects")
        rename_layout = QtWidgets.QVBoxLayout(rename_grp)

        form = QtWidgets.QFormLayout()
        self.r_search = QtWidgets.QLineEdit()
        self.r_replace = QtWidgets.QLineEdit()
        form.addRow("Search Pattern:", self.r_search)
        form.addRow("Replace With:", self.r_replace)
        rename_layout.addLayout(form)

        btn_rename = QtWidgets.QPushButton("Rename Selected")
        btn_rename.clicked.connect(self._on_rename)
        btn_rename.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        rename_layout.addWidget(btn_rename)

        btn_rename_tool = QtWidgets.QPushButton("Open Rename Tool")
        btn_rename_tool.clicked.connect(launch_renameTool)
        btn_rename_tool.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        rename_layout.addWidget(btn_rename_tool)

        self.r_status = QtWidgets.QLabel("")
        rename_layout.addWidget(self.r_status)
        content_layout.addWidget(rename_grp)


        # Close button
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_close.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        content_layout.addWidget(btn_close)

    def _on_hierarchy(self):
        root = self.h_root.text().strip()
        asset = self.h_asset.text().strip()
        if not asset:
            QtWidgets.QMessageBox.warning(self, "Missing Asset", "Please enter an asset name.")
            return
        try:
            create_model_hierarchy(asset, root=root, verbose=True)
            self.h_status.setText(f"✔ Hierarchy created for model '{root}'.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            self.h_status.setText(f"✖ {e}")

    def _on_rename(self):
        pat = self.r_search.text()
        rep = self.r_replace.text()
        if not pat:
            QtWidgets.QMessageBox.warning(self, "Missing Pattern", "Please enter a search pattern.")
            return
        try:
            selected_objects = cmds.ls(selection=True, long=True) or []
            if not selected_objects:
                QtWidgets.QMessageBox.warning(self, "No Selection", "Please select objects to rename.")
                return
            search_replace(selected_objects, pat, rep)
            self.r_status.setText(f"✔ Renamed using '{pat}'→'{rep}'")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            self.r_status.setText(f"✖ {e}")



def show_model_toolkit_window():
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, ModelToolkitWindow):
            w.show()
            w.raise_()
            w.activateWindow()
            return w
    win = ModelToolkitWindow()
    win.setParent(maya_main_window(), QtCore.Qt.Window)
    win.setWindowFlags(QtCore.Qt.Window)
    win.show()
    return win
