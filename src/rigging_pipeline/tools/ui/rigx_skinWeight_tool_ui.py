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
from rigging_pipeline.utils.utils_skinWeights import (
    save_weights, save_weights_multiple, save_weights_group,
    load_weights, load_weights_multiple, load_weights_group,
    load_weights_from_file,
    copy_weights_one_to_many, copy_weights_many_to_one,
    add_influence, remove_influence, bind_skin, unbind_skin,
    remove_unused_influences, curve_to_skin, lattice_to_skin,
    cluster_to_skin
)
from rigging_pipeline.utils.utils_cleanup import create_clean_mesh_duplicate

# Mapping of actions to QStyle icons
ICON_MAP = {
    'save': QtWidgets.QStyle.SP_DialogSaveButton,
    'open': QtWidgets.QStyle.SP_DialogOpenButton,
    'copy_o2m': QtWidgets.QStyle.SP_ArrowRight,
    'copy_m2o': QtWidgets.QStyle.SP_ArrowLeft,
    'close': QtWidgets.QStyle.SP_DialogCloseButton
}


def maya_main_window():
    if not MAYA_AVAILABLE:
        return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class SkinWeightsToolUI(QtWidgets.QDialog):
    """ZFX Skin Weights Utility"""
    def __init__(self, parent=None):
        super(SkinWeightsToolUI, self).__init__(parent or maya_main_window())
        QtWidgets.QApplication.instance().setStyleSheet(THEME_STYLESHEET)
        self.setWindowTitle("Skin Weights Utility")
        self.resize(400, 600)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        style = QtWidgets.QApplication.instance().style()

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
        icon_path = os.path.join(os.path.expanduser("~"), "Documents", "maya", "2024", "prefs", "icons", "skinTool.png")
        if os.path.exists(icon_path):
            icon_label = QtWidgets.QLabel()
            icon_label.setObjectName("icon")
            icon_pixmap = QtGui.QPixmap(icon_path)
            # Scale the icon to 32x32 while maintaining aspect ratio
            icon_pixmap = icon_pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            banner_layout.addWidget(icon_label)
        else:
            print(f"Warning: Icon not found at {icon_path}")

        banner_label = QtWidgets.QLabel("ZebuFX Skin Toolkit")
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
            QLabel::first-letter {
                font-family: 'Impact', 'Arial Black', sans-serif;
                font-size: 24pt;
                color: #ffd700;
            }
        """)

        banner_layout.addStretch()

        layout.addWidget(banner_frame)
        

        # Load/Save Weights group
        group_ws = QtWidgets.QGroupBox("Load/Save Weights")
        ws_layout = QtWidgets.QGridLayout()
        save_icon = style.standardIcon(ICON_MAP['save'])
        load_icon = style.standardIcon(ICON_MAP['open'])
        # Save buttons
        self.btn_save_single = QtWidgets.QPushButton(save_icon, "Save Single")
        self.btn_save_multi  = QtWidgets.QPushButton(save_icon, "Save Multiple")
        self.btn_save_group  = QtWidgets.QPushButton(save_icon, "Save Group")
        for i, btn in enumerate((self.btn_save_single, self.btn_save_multi, self.btn_save_group)):
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            ws_layout.addWidget(btn, 0, i)
        # Load buttons
        self.btn_load_single = QtWidgets.QPushButton(load_icon, "Load Single")
        self.btn_load_multi  = QtWidgets.QPushButton(load_icon, "Load Multiple")
        self.btn_load_group  = QtWidgets.QPushButton(load_icon, "Load Group")
        for i, btn in enumerate((self.btn_load_single, self.btn_load_multi, self.btn_load_group)):
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            ws_layout.addWidget(btn, 1, i)
        group_ws.setLayout(ws_layout)
        layout.addWidget(group_ws)

        # Copy Weights group
        group_copy = QtWidgets.QGroupBox("Copy Weights")
        c_layout = QtWidgets.QHBoxLayout()
        self.btn_copy_o2m = QtWidgets.QPushButton(style.standardIcon(ICON_MAP['copy_o2m']), "One → Many")
        self.btn_copy_m2o = QtWidgets.QPushButton(style.standardIcon(ICON_MAP['copy_m2o']), "Many → One")
        for btn in (self.btn_copy_o2m, self.btn_copy_m2o):
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            c_layout.addWidget(btn)
        group_copy.setLayout(c_layout)
        layout.addWidget(group_copy)

        # Skin Utils group
        group_utils = QtWidgets.QGroupBox("Skin Utils")
        u_layout = QtWidgets.QVBoxLayout()
        
        # Create box layout for influence buttons
        inf_box = QtWidgets.QHBoxLayout()
        self.btn_add_inf = QtWidgets.QPushButton("Add Influence")
        self.btn_rem_inf = QtWidgets.QPushButton("Remove Influence")
        for btn in (self.btn_add_inf, self.btn_rem_inf):
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            inf_box.addWidget(btn)
        u_layout.addLayout(inf_box)
        
        # Create box layout for bind/unbind buttons
        bind_box = QtWidgets.QHBoxLayout()
        self.btn_bind = QtWidgets.QPushButton("Bind Skin")
        self.btn_unbind = QtWidgets.QPushButton("Unbind Skin")
        for btn in (self.btn_bind, self.btn_unbind):
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            bind_box.addWidget(btn)
        u_layout.addLayout(bind_box)
        
        # Add remaining buttons
        self.btn_rm_unused = QtWidgets.QPushButton("Remove Unused Influences")
        self.btn_clean_dup = QtWidgets.QPushButton("Clean Duplicate")
        for btn in (self.btn_rm_unused, self.btn_clean_dup):
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            u_layout.addWidget(btn)
            
        group_utils.setLayout(u_layout)
        layout.addWidget(group_utils)

        # Convert Skin group
        group_conv = QtWidgets.QGroupBox("Convert Skin")
        cv_layout = QtWidgets.QVBoxLayout()
        self.btn_curve2s   = QtWidgets.QPushButton("Curve to Skin")
        self.btn_lattice2s = QtWidgets.QPushButton("Lattice to Skin")
        self.btn_cluster2s = QtWidgets.QPushButton("Cluster to Skin")
        for btn in (self.btn_curve2s, self.btn_lattice2s, self.btn_cluster2s):
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            cv_layout.addWidget(btn)
        group_conv.setLayout(cv_layout)
        layout.addWidget(group_conv)

        # Separator and close
        sep = QtWidgets.QFrame(); sep.setFrameShape(QtWidgets.QFrame.HLine); sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(sep)
        self.btn_close = QtWidgets.QPushButton("Close")
        self.btn_close.setIcon(style.standardIcon(ICON_MAP['close']))
        self.btn_close.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.btn_close.clicked.connect(self.close)
        layout.addWidget(self.btn_close)

        # Connect signals
        self.btn_save_single.clicked.connect(self._on_save_single)
        self.btn_save_multi.clicked.connect(self._on_save_multi)
        self.btn_save_group.clicked.connect(self._on_save_group)
        self.btn_load_single.clicked.connect(self._on_load_single)
        self.btn_load_multi.clicked.connect(self._on_load_multi)
        self.btn_load_group.clicked.connect(self._on_load_group)
        self.btn_copy_o2m.clicked.connect(self._on_copy_o2m)
        self.btn_copy_m2o.clicked.connect(self._on_copy_m2o)
        self.btn_add_inf.clicked.connect(lambda: add_influence(cmds.ls(selection=True)[0], cmds.ls(selection=True)[1]))
        self.btn_rem_inf.clicked.connect(lambda: remove_influence(cmds.ls(selection=True)[0], cmds.ls(selection=True)[1]))
        self.btn_bind.clicked.connect(lambda: bind_skin(cmds.ls(selection=True)))
        self.btn_unbind.clicked.connect(lambda: unbind_skin(cmds.ls(selection=True)[0]))
        self.btn_rm_unused.clicked.connect(lambda: remove_unused_influences(cmds.ls(selection=True)[0]))
        self.btn_clean_dup.clicked.connect(lambda: create_clean_mesh_duplicate())
        self.btn_curve2s.clicked.connect(lambda: curve_to_skin(cmds.ls(selection=True)[0], cmds.ls(selection=True)[1]))
        self.btn_lattice2s.clicked.connect(lambda: lattice_to_skin(cmds.ls(selection=True)[0], cmds.ls(selection=True)[1]))
        self.btn_cluster2s.clicked.connect(lambda: cluster_to_skin(cmds.ls(selection=True)[0], cmds.ls(selection=True)[1]))

    # Save Handlers
    def _on_save_single(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Weights - Single", "", "JSON Files (*.json)")
        if path:
            meshes = cmds.ls(selection=True, transforms=True)
            if meshes:
                save_weights(meshes[0], path)
            else:
                cmds.warning("Select one mesh to save.")

    def _on_save_multi(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Weights - Multiple", "", "JSON Files (*.json)")
        if path:
            meshes = cmds.ls(selection=True, transforms=True)
            if meshes:
                save_weights_multiple(meshes, path)
            else:
                cmds.warning("Select meshes to save.")

    def _on_save_group(self):
        group, ok = QtWidgets.QInputDialog.getText(self, "Save Weights - Group", "Group name:")
        if ok and group:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Weights - Group", "", "JSON Files (*.json)")
            if path:
                save_weights_group(group, path)

    # Load Handlers
    def _on_load_single(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Weights - Single", "", "JSON Files (*.json)")
        if path:
            meshes = cmds.ls(selection=True, transforms=True)
            if meshes:
                if load_weights_from_file(meshes[0], path):
                    cmds.inViewMessage(statusMessage="Weights loaded successfully.", fade=True)
                else:
                    cmds.warning("Failed to load weights.")
            else:
                cmds.warning("Select one mesh to load.")

    def _on_load_multi(self):
        # Use folder selection dialog instead of file dialog
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Load Weights - Multiple", "", QtWidgets.QFileDialog.ShowDirsOnly)
        if folder:
            meshes = cmds.ls(selection=True, transforms=True)
            if meshes:
                # Get all JSON files in the folder
                json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
                if not json_files:
                    cmds.warning(f"No weight files found in {folder}")
                    return
                
                # Create a mapping of mesh names to their weight files
                mesh_to_file = {}
                for mesh in meshes:
                    safe_name = mesh.replace('|', '_').replace('/', '_').replace('\\', '_')
                    weight_file = f"{safe_name}.json"
                    if weight_file in json_files:
                        mesh_to_file[mesh] = os.path.join(folder, weight_file)
                
                if not mesh_to_file:
                    cmds.warning("No matching weight files found for selected meshes.")
                    return
                
                # Load weights for each mesh that has a matching file
                loaded_count = 0
                for mesh, weight_file in mesh_to_file.items():
                    if load_weights_from_file(mesh, weight_file):
                        loaded_count += 1
                
                if loaded_count:
                    cmds.inViewMessage(statusMessage=f"Loaded weights for {loaded_count} meshes.", fade=True)
                else:
                    cmds.warning("Failed to load weights for any meshes.")
            else:
                cmds.warning("Select meshes to load.")

    def _on_load_group(self):
        group, ok = QtWidgets.QInputDialog.getText(self, "Load Weights - Group", "Group name:")
        if ok and group:
            # Use folder selection dialog for group loading as well
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Load Weights - Group", "", QtWidgets.QFileDialog.ShowDirsOnly)
            if folder:
                load_weights_group(group, folder)

    # Copy Handlers
    def _on_copy_o2m(self):
        sels = cmds.ls(selection=True, transforms=True)
        if len(sels) < 2:
            cmds.warning("Select source then targets.")
        else:
            copy_weights_one_to_many(sels[0], sels[1:])

    def _on_copy_m2o(self):
        sels = cmds.ls(selection=True, transforms=True)
        if len(sels) < 2:
            cmds.warning("Select sources then target.")
        else:
            copy_weights_many_to_one(sels[:-1], sels[-1])


def show_skin_weights_tool():
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, SkinWeightsToolUI):
            w.show(); w.raise_(); w.activateWindow(); return w
    win = SkinWeightsToolUI(); win.setParent(maya_main_window(), QtCore.Qt.Window);
    win.setWindowFlags(QtCore.Qt.Window); win.show(); return win
