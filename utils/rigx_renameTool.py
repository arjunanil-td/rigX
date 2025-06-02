import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from file.rigx_theme import THEME_STYLESHEET


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class RenameToolUI(QtWidgets.QDialog):
    """Modernized Rename Tool with Qt UI, enhanced functionality, and theming."""
    def __init__(self, parent=maya_main_window()):
        super(RenameToolUI, self).__init__(parent)
        
        self.setWindowTitle("RigX Rename Tool")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(400, 650)
        
        self.setStyleSheet(THEME_STYLESHEET)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # ───── Selection Options ─────
        sel_group = QtWidgets.QGroupBox("Selection Mode")
        sel_layout = QtWidgets.QHBoxLayout(sel_group)
        self.radio_selected = QtWidgets.QRadioButton("Selected")
        self.radio_hierarchy = QtWidgets.QRadioButton("Hierarchy")
        self.radio_all = QtWidgets.QRadioButton("All")
        self.radio_selected.setChecked(True)
        sel_layout.addWidget(self.radio_selected)
        sel_layout.addWidget(self.radio_hierarchy)
        sel_layout.addWidget(self.radio_all)
        layout.addWidget(sel_group)

        layout.addWidget(self._separator())

        # ───── Type Filter & Get ─────
        type_group = QtWidgets.QGroupBox("Object Type")
        type_layout = QtWidgets.QHBoxLayout(type_group)
        self.type_combo = QtWidgets.QComboBox()
        types = ["All", "joint", "ikHandle", "transform", "locator", "mesh", "nurbsCurve"]
        self.type_combo.addItems(types)
        type_layout.addWidget(self.type_combo)
        btn_info = QtWidgets.QPushButton("Get Objects")
        btn_info.clicked.connect(self.populate_object_list)
        type_layout.addWidget(btn_info)
        layout.addWidget(type_group)

        layout.addWidget(self._separator())

        # ───── Object List ─────
        self.obj_list = QtWidgets.QListWidget()
        self.obj_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.obj_list, 1)

        layout.addWidget(self._separator())

        # ───── Rename Parameters ─────
        form = QtWidgets.QFormLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.start_spin = QtWidgets.QSpinBox(); self.start_spin.setMinimum(0)
        self.pad_spin = QtWidgets.QSpinBox(); self.pad_spin.setMinimum(0)
        form.addRow("Base Name:", self.name_edit)
        form.addRow("Start #:", self.start_spin)
        form.addRow("Padding:", self.pad_spin)
        layout.addLayout(form)
        btn_rename = QtWidgets.QPushButton("Rename")
        btn_rename.clicked.connect(self.rename_objects)
        layout.addWidget(btn_rename)

        layout.addWidget(self._separator())

        # ───── Prefix / Suffix ─────
        pre_suf_layout = QtWidgets.QHBoxLayout()
        self.prefix_edit = QtWidgets.QLineEdit(); self.prefix_edit.setPlaceholderText("Prefix")
        self.suffix_edit = QtWidgets.QLineEdit(); self.suffix_edit.setPlaceholderText("Suffix")
        pre_suf_layout.addWidget(self.prefix_edit)
        pre_suf_layout.addWidget(self.suffix_edit)
        layout.addLayout(pre_suf_layout)
        affix_layout = QtWidgets.QHBoxLayout()
        btn_pref = QtWidgets.QPushButton("Add Prefix")
        btn_pref.clicked.connect(lambda: self.apply_affix(mode='prefix'))
        btn_suf = QtWidgets.QPushButton("Add Suffix")
        btn_suf.clicked.connect(lambda: self.apply_affix(mode='suffix'))
        affix_layout.addWidget(btn_pref); affix_layout.addWidget(btn_suf)
        layout.addLayout(affix_layout)

        layout.addWidget(self._separator())

        # ───── Search & Replace ─────
        sr_layout = QtWidgets.QHBoxLayout()
        self.search_edit = QtWidgets.QLineEdit(); self.search_edit.setPlaceholderText("Search")
        self.replace_edit = QtWidgets.QLineEdit(); self.replace_edit.setPlaceholderText("Replace")
        sr_layout.addWidget(self.search_edit); sr_layout.addWidget(self.replace_edit)
        layout.addLayout(sr_layout)
        btn_sr = QtWidgets.QPushButton("Search & Replace")
        btn_sr.clicked.connect(self.search_replace)
        layout.addWidget(btn_sr)

        layout.addWidget(self._separator())

        # ───── Case Conversion ─────
        case_layout = QtWidgets.QHBoxLayout()
        btn_lower = QtWidgets.QPushButton("toLower")
        btn_lower.clicked.connect(lambda: self.change_case('lower'))
        btn_upper = QtWidgets.QPushButton("toUpper")
        btn_upper.clicked.connect(lambda: self.change_case('upper'))
        btn_cap = QtWidgets.QPushButton("Capitalize")
        btn_cap.clicked.connect(lambda: self.change_case('capitalize'))
        case_layout.addWidget(btn_lower); case_layout.addWidget(btn_upper); case_layout.addWidget(btn_cap)
        layout.addLayout(case_layout)

        layout.addWidget(self._separator())

        # ───── Utilities ─────
        util_layout = QtWidgets.QHBoxLayout()
        btn_ns = QtWidgets.QPushButton("Clear Namespaces")
        btn_ns.clicked.connect(self.clear_namespaces)
        btn_dup = QtWidgets.QPushButton("Fix Duplicates")
        btn_dup.clicked.connect(self.fix_duplicates)
        btn_shape = QtWidgets.QPushButton("Fix Shape Names")
        btn_shape.clicked.connect(self.fix_shape_names)
        util_layout.addWidget(btn_ns); util_layout.addWidget(btn_dup); util_layout.addWidget(btn_shape)
        layout.addLayout(util_layout)

        layout.addWidget(self._separator())

        # ───── Close ─────
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def _separator(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        return line

    def get_selected_objects(self):
        mode = 'selected' if self.radio_selected.isChecked() else 'hierarchy' if self.radio_hierarchy.isChecked() else 'all'
        objtype = self.type_combo.currentText()
        if mode == 'selected':
            objs = cmds.ls(selection=True, long=True)
        elif mode == 'hierarchy':
            sel = cmds.ls(selection=True, long=True)
            objs = []
            for o in sel: objs += cmds.listRelatives(o, allDescendents=True, fullPath=True) or []
        else:
            objs = cmds.ls(long=True)
        filtered = []
        for o in objs:
            if objtype=='All' or cmds.nodeType(o).lower()==objtype.lower():
                filtered.append(o)
        return filtered

    def populate_object_list(self):
        self.obj_list.clear()
        for o in self.get_selected_objects():
            self.obj_list.addItem(o)

    def rename_objects(self):
        items = [i.text() for i in self.obj_list.selectedItems()]
        base = self.name_edit.text().strip()
        start = self.start_spin.value()
        pad = self.pad_spin.value()
        if not base:
            cmds.warning("Enter a base name.")
            return
        for idx, o in enumerate(items):
            num = str(start+idx).zfill(pad)
            new = f"{base}{num}"
            try: cmds.rename(o, new)
            except: cmds.warning(f"Failed to rename {o}")
        self.populate_object_list()

    def apply_affix(self, mode='prefix'):
        items = [i.text() for i in self.obj_list.selectedItems()]
        for o in items:
            name = o.split('|')[-1]
            new = (self.prefix_edit.text()+name) if mode=='prefix' else (name+self.suffix_edit.text())
            try: cmds.rename(o, new)
            except: cmds.warning(f"Could not rename {o}")
        self.populate_object_list()

    def search_replace(self):
        items = [i.text() for i in self.obj_list.selectedItems()]
        s, r = self.search_edit.text(), self.replace_edit.text()
        if not s: cmds.warning("Enter search text."); return
        for o in items:
            name = o.split('|')[-1]
            new = name.replace(s, r)
            try: cmds.rename(o, new)
            except: cmds.warning(f"Could not rename {o}")
        self.populate_object_list()

    def change_case(self, method):
        items = [i.text() for i in self.obj_list.selectedItems()]
        for o in items:
            name = o.split('|')[-1]
            if method=='lower': new = name.lower()
            elif method=='upper': new = name.upper()
            else: new = name.capitalize()
            try: cmds.rename(o, new)
            except: cmds.warning(f"Could not rename {o}")
        self.populate_object_list()

    def clear_namespaces(self):
        all_ns = cmds.namespaceInfo(listOnlyNamespaces=True,recurse=True) or []
        ignore = {'UI','shared'}
        refs = cmds.file(query=True,referenceNode=True) or []
        ref_ns = {cmds.referenceQuery(r, namespace=True) for r in refs if cmds.referenceQuery(r, namespace=True)}
        to_remove = [ns for ns in all_ns if ns.split(':')[0] not in ignore|ref_ns]
        to_remove.sort(key=lambda n: n.count(':'), reverse=True)
        for ns in to_remove:
            try: cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
            except: pass
        cmds.inViewMessage(statusMessage="Namespaces cleared",fade=True)

    def fix_duplicates(self):
        """Find duplicate short names and rename with incremental suffix."""
        objs = cmds.ls(long=True)
        names = {}
        for o in objs:
            short = o.split('|')[-1]
            names.setdefault(short, []).append(o)
        for short, paths in names.items():
            if len(paths) > 1:
                for i, path in enumerate(paths, start=1):
                    new_name = f"{short}_{i}"
                    try: cmds.rename(path, new_name)
                    except: cmds.warning(f"Dup fix failed: {path}")
        self.populate_object_list()
        cmds.inViewMessage(statusMessage="Duplicates fixed",fade=True)

    def fix_shape_names(self):
        """Ensure shape nodes follow transform name conventions."""
        transforms = cmds.ls(type='transform', long=True)
        for t in transforms:
            shapes = cmds.listRelatives(t, shapes=True, fullPath=True) or []
            for s in shapes:
                short_s = s.split('|')[-1]
                correct = t.split('|')[-1] + 'Shape'
                if short_s != correct:
                    new = f"{correct}"
                    try: cmds.rename(s, new)
                    except: cmds.warning(f"Shape rename failed: {s}")
        cmds.inViewMessage(statusMessage="Shape names fixed",fade=True)

_dialog = None

def launch_renameTool():
    global _dialog
    try: _dialog.close()
    except: pass
    _dialog = RenameToolUI()
    _dialog.show()
