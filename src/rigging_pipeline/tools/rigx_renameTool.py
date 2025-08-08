import maya.cmds as cmds
import rigging_pipeline.utils.utils_cleanup as cleanup
import rigging_pipeline.utils.rig.utils_name as name_cleanup

from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner



def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class RenameToolUI(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(RenameToolUI, self).__init__(parent)
        
        self.setWindowTitle("RigX Rename Tool")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(400, 650)
        
        self.setStyleSheet(THEME_STYLESHEET)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Add the centralized banner
        banner = Banner("RigX Rename Tool", "rename.png")
        layout.addWidget(banner)

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
        btn_pref.clicked.connect(lambda: self.run_apply_affix(mode='prefix'))
        btn_suf = QtWidgets.QPushButton("Add Suffix")
        btn_suf.clicked.connect(lambda: self.run_apply_affix(mode='suffix'))
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
        btn_sr.clicked.connect(self.run_search_replace)
        layout.addWidget(btn_sr)

        layout.addWidget(self._separator())

        # ───── Case Conversion ─────
        case_layout = QtWidgets.QHBoxLayout()
        btn_lower = QtWidgets.QPushButton("toLower")
        btn_lower.clicked.connect(lambda: self.run_change_case('lower'))
        btn_upper = QtWidgets.QPushButton("toUpper")
        btn_upper.clicked.connect(lambda: self.run_change_case('upper'))
        btn_cap = QtWidgets.QPushButton("Capitalize")
        btn_cap.clicked.connect(lambda: self.run_change_case('capitalize'))
        case_layout.addWidget(btn_lower); case_layout.addWidget(btn_upper); case_layout.addWidget(btn_cap)
        layout.addLayout(case_layout)

        layout.addWidget(self._separator())

        # ───── Utilities ─────
        util_layout = QtWidgets.QHBoxLayout()
        btn_ns = QtWidgets.QPushButton("Clear Namespaces")
        btn_ns.clicked.connect(cleanup.cleanup_namespaces)
        btn_dup = QtWidgets.QPushButton("Fix Duplicates")
        btn_dup.clicked.connect(self.run_fix_duplicates)
        btn_shape = QtWidgets.QPushButton("Fix Shape Names")
        btn_shape.clicked.connect(self.run_fix_shape_names)
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
            for o in sel:
                descendants = cmds.listRelatives(o, allDescendents=True, fullPath=True) or []
                # Only include transform nodes (geometry), not shapes
                objs += [d for d in descendants if cmds.nodeType(d) == 'transform']
        else:
            objs = cmds.ls(type='transform', long=True)
        filtered = []
        for o in objs:
            if objtype=='All' or cmds.nodeType(o).lower()==objtype.lower():
                filtered.append(o)
        return filtered

    def populate_object_list(self):
        self.obj_list.clear()
        for o in self.get_selected_objects():
            short_name = o.split('|')[-1]
            item = QtWidgets.QListWidgetItem(short_name)
            item.setData(QtCore.Qt.UserRole, o)  # Store full path for later use
            self.obj_list.addItem(item)

    def rename_objects(self):
        items = self.get_selected_objects()
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

    def run_apply_affix(self, mode):
        items = self.get_selected_objects()
        affix = self.prefix_edit.text() if mode == 'prefix' else self.suffix_edit.text()
        name_cleanup.apply_affix(items, affix, mode)
        self.populate_object_list()

    def run_search_replace(self):
        items = self.get_selected_objects()
        search_text = self.search_edit.text()
        replace_text = self.replace_edit.text()
        name_cleanup.search_replace(items, search_text, replace_text)
        self.populate_object_list()
    
    def run_change_case(self, method):
        items = self.get_selected_objects()
        name_cleanup.change_case(items, method)
        self.populate_object_list()

    def run_fix_duplicates(self):
        name_cleanup.fix_duplicates()
        self.populate_object_list()

    def run_fix_shape_names(self):
        name_cleanup.fix_shape_names()
        self.populate_object_list()

_dialog = None

def launch_renameTool():
    global _dialog
    try: _dialog.close()
    except: pass
    _dialog = RenameToolUI()
    _dialog.show()
