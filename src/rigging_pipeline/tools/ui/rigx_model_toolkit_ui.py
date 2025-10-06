import os, sys
import maya.cmds as cmds
import maya.OpenMayaUI as omui

from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore, QtGui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET

from rigging_pipeline.tools.rigx_renameTool import launch_renameTool
from rigging_pipeline.utils.model.utils_model_tags import assign_tag_to_geo
from rigging_pipeline.utils.model.utils_model_validation import qc_validation_check
from rigging_pipeline.utils.model.utils_model_hierarchy import create_model_hierarchy
from rigging_pipeline.utils.rig.utils_name import search_replace

# Preset tags for tagging dropdown
PRESET_TAGS = ['bone', 'muscle', 'lodA', 'lodB', 'eye', 'nail', 'proxy', 'cloth']


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
    """ZFX Model Toolkit: Standardized Interface"""
    WINDOW_TITLE = "ZFX Model Toolkit"

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

        banner_label = QtWidgets.QLabel("ZebuFX Model Toolkit")
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

        # Separator
        sep2 = QtWidgets.QFrame()
        sep2.setFrameShape(QtWidgets.QFrame.HLine)
        sep2.setFrameShadow(QtWidgets.QFrame.Sunken)
        content_layout.addWidget(sep2)

        # Tagging Section
        tag_grp = QtWidgets.QGroupBox("Tag Geometry")
        tag_layout = QtWidgets.QVBoxLayout(tag_grp)

        # Mesh list
        self.t_list = QtWidgets.QListWidget()
        tag_layout.addWidget(self.t_list)

        # Tag combobox
        self.t_combo = QtWidgets.QComboBox()
        self.t_combo.setEditable(True)
        self.t_combo.addItems(PRESET_TAGS)
        tag_layout.addWidget(self.t_combo)

        # Assign button
        btn_tag = QtWidgets.QPushButton("Assign Tag")
        btn_tag.clicked.connect(self._on_tag)
        btn_tag.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        tag_layout.addWidget(btn_tag)

        self.t_status = QtWidgets.QLabel("")
        tag_layout.addWidget(self.t_status)
        content_layout.addWidget(tag_grp)

        # Separator
        sep3 = QtWidgets.QFrame()
        sep3.setFrameShape(QtWidgets.QFrame.HLine)
        sep3.setFrameShadow(QtWidgets.QFrame.Sunken)
        content_layout.addWidget(sep3)

        # QC Section
        qc_grp = QtWidgets.QGroupBox("Quality Control")
        qc_layout = QtWidgets.QVBoxLayout(qc_grp)

        self.qc_output = QtWidgets.QPlainTextEdit()
        self.qc_output.setReadOnly(True)
        qc_layout.addWidget(self.qc_output)

        btn_qc = QtWidgets.QPushButton("Run QC Checks")
        btn_qc.clicked.connect(self._on_qc)
        btn_qc.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        qc_layout.addWidget(btn_qc)
        content_layout.addWidget(qc_grp)

        # Close button
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.close)
        btn_close.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        content_layout.addWidget(btn_close)

        # Initial tag list refresh
        self._refresh_tag_list()

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

    def _refresh_tag_list(self):
        self.t_list.clear()
        style = QtWidgets.QApplication.instance().style()
        icon_ok = style.standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)
        icon_missing = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical)

        shapes = cmds.ls(type="mesh", noIntermediate=True, long=True) or []
        transforms = set()
        for shp in shapes:
            p = cmds.listRelatives(shp, parent=True, fullPath=True)
            if p:
                transforms.add(p[0])

        for tr in sorted(transforms):
            name = tr.split("|")[-1]
            if cmds.attributeQuery("zfxTag", node=tr, exists=True):
                tag_val = cmds.getAttr(f"{tr}.zfxTag")
                text = f"{name} — {tag_val}"
                icon = icon_ok
            else:
                text = f"{name} — missing"
                icon = icon_missing

            item = QtWidgets.QListWidgetItem(icon, text)
            item.setData(QtCore.Qt.UserRole, name)
            self.t_list.addItem(item)

    def _on_tag(self):
        # Refresh list to show updated icons
        self._refresh_tag_list()

        tag = self.t_combo.currentText().strip()
        if not tag:
            QtWidgets.QMessageBox.warning(self, "Missing Tag", "Please enter or select a tag.")
            return
        if tag not in [self.t_combo.itemText(i) for i in range(self.t_combo.count())]:
            self.t_combo.addItem(tag)

        geos = [item.data(QtCore.Qt.UserRole) for item in self.t_list.selectedItems()]
        if not geos:
            sel = cmds.ls(selection=True, transforms=True) or []
            geos = [g.split("|")[-1] for g in sel]
            if not geos:
                QtWidgets.QMessageBox.warning(self, "No Selection", "Select geometry in list or viewport.")
                return

        succ, fail = [], []
        for geo in geos:
            try:
                assign_tag_to_geo(geo, tag)
                succ.append(geo)
            except Exception as e:
                fail.append(f"{geo}: {e}")

        msgs = []
        if succ:
            msgs.append(f"✔ Tagged: {', '.join(succ)}")
        if fail:
            msgs.append(f"✖ Errors: {'; '.join(fail)}")
        self.t_status.setText("\n".join(msgs))

        # Refresh again to update status icons
        self._refresh_tag_list()

    def _on_qc(self):
        self.qc_output.clear()
        for line in qc_validation_check():
            self.qc_output.appendPlainText(line)


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
