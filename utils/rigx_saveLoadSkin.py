import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import json, os
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui
from file.rigx_theme import THEME_STYLESHEET

def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class SkinWeightsToolUI(QtWidgets.QDialog):
    """High-performance Skin Cluster Save/Load using OpenMaya API and JSON."""
    def __init__(self, parent=maya_main_window()):
        super(SkinWeightsToolUI, self).__init__(parent)
        self.setWindowTitle("Skin Cluster Save/Load Tool")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(THEME_STYLESHEET)
        self.resize(400, 200)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Save section
        save_grp = QtWidgets.QGroupBox("Save Skin Weights")
        h1 = QtWidgets.QHBoxLayout(save_grp)
        self.save_path = QtWidgets.QLineEdit()
        btn_sb = QtWidgets.QPushButton("Browse...")
        btn_sb.clicked.connect(self.browse_save)
        btn_save = QtWidgets.QPushButton("Save Weights")
        btn_save.clicked.connect(self.save_weights)
        h1.addWidget(self.save_path)
        h1.addWidget(btn_sb)
        h1.addWidget(btn_save)
        layout.addWidget(save_grp)
        layout.addWidget(self._separator())

        # Load section
        load_grp = QtWidgets.QGroupBox("Load Skin Weights")
        h2 = QtWidgets.QHBoxLayout(load_grp)
        self.load_path = QtWidgets.QLineEdit()
        btn_lb = QtWidgets.QPushButton("Browse...")
        btn_lb.clicked.connect(self.browse_load)
        btn_load = QtWidgets.QPushButton("Load Weights")
        btn_load.clicked.connect(self.load_weights)
        h2.addWidget(self.load_path)
        h2.addWidget(btn_lb)
        h2.addWidget(btn_load)
        layout.addWidget(load_grp)
        layout.addWidget(self._separator())

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        layout.addStretch()

    def _separator(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        return line

    def browse_save(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Weights", os.getenv('HOME'), "JSON Files (*.json)")
        if not path:
            return
        if not path.lower().endswith('.json'):
            path += '.json'
        self.save_path.setText(path)

    def browse_load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Weights", os.getenv('HOME'), "JSON Files (*.json)")
        if path:
            self.load_path.setText(path)

    def save_weights(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            cmds.warning("Select a skinned mesh.")
            return
        mesh = sel[0]
        # find skinCluster
        sc = next((h for h in cmds.listHistory(mesh) or [] if cmds.nodeType(h)=='skinCluster'), None)
        if not sc:
            cmds.warning("No skinCluster found.")
            return

        # API setup
        sel_list = om.MSelectionList(); sel_list.add(mesh)
        dag_path = sel_list.getDagPath(0)
        sc_sel = om.MSelectionList(); sc_sel.add(sc)
        sc_node = sc_sel.getDependNode(0)
        fn_skin = oma.MFnSkinCluster(sc_node)

        # ---- build a component covering all vertices ----
        iter_geo = om.MItGeometry(dag_path)
        num_verts = iter_geo.count()
        comp_fn = om.MFnSingleIndexedComponent()
        comp = comp_fn.create(om.MFn.kMeshVertComponent)
        for i in range(num_verts):
            comp_fn.addElement(i)

        # ---- bulk retrieve all weights ----
        weights_flat, inf_count = fn_skin.getWeights(dag_path, comp)
        flat_list = list(weights_flat)
        influences = [p.partialPathName() for p in fn_skin.influenceObjects()]
        nested = [flat_list[i*inf_count:(i+1)*inf_count] for i in range(num_verts)]

        data = {'influences': influences, 'weights': nested}
        try:
            with open(self.save_path.text(), 'w') as f:
                json.dump(data, f, separators=(',',':'))
            cmds.inViewMessage(statusMessage="Weights saved.", fade=True)
        except Exception as e:
            cmds.warning(f"Save failed: {e}")

    def load_weights(self):
        sel = cmds.ls(selection=True, type='transform')
        if not sel:
            cmds.warning("Select a mesh.")
            return
        mesh = sel[0]
        path = self.load_path.text()
        if not os.path.isfile(path):
            cmds.warning("Invalid JSON path.")
            return
        try:
            with open(path,'r') as f:
                data = json.load(f)
        except Exception as e:
            cmds.warning(f"Load failed: {e}")
            return

        influences = data.get('influences', [])
        nested = data.get('weights', [])
        num_verts = len(nested)
        if num_verts == 0:
            cmds.warning("No weights in JSON.")
            return

        # Bind new skinCluster
        sc = cmds.skinCluster(influences, mesh, toSelectedBones=True)[0]

        # API setup
        sel_list = om.MSelectionList(); sel_list.add(mesh)
        dag_path = sel_list.getDagPath(0)
        sc_sel = om.MSelectionList(); sc_sel.add(sc)
        sc_node = sc_sel.getDependNode(0)
        fn_skin = oma.MFnSkinCluster(sc_node)

        # ---- create component covering all verts ----
        comp_fn = om.MFnSingleIndexedComponent()
        comp_obj = comp_fn.create(om.MFn.kMeshVertComponent)
        for i in range(num_verts):
            comp_fn.addElement(i)

        # ---- build indices & weights arrays ----
        idx_array = om.MIntArray()
        for idx in range(len(influences)):
            idx_array.append(idx)
        flat_weights = [w for vert in nested for w in vert]
        weight_array = om.MDoubleArray(flat_weights)

        # ---- apply all weights in one call ----
        fn_skin.setWeights(dag_path, comp_obj, idx_array, weight_array, False)
        cmds.inViewMessage(statusMessage="Weights loaded.", fade=True)

# Singleton
_dialog = None

def show_skin_weights_tool():
    global _dialog
    try:
        _dialog.close()
    except:
        pass
    _dialog = SkinWeightsToolUI()
    _dialog.show()
