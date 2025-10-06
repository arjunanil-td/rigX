"""
maya_path_rig_ui.py
Dockable (floating) PySide2 UI for the path rig builder for Maya 2024 (Python 3).

Drop this file into Maya's script editor or save as a .py and import it in Maya.
Run: PathRigUI.show()

Features:
 - Provide an existing curve or create a default curve
 - Number of controls, create joints, attach objects (comma-separated)
 - Control radii parameters
 - Build button that calls the path rig builder
 - After building, lists controls with sliders that drive each control's motionPath uValue (0..1)
 - Select control button for each control

Notes:
 - Uses PySide2 and maya.cmds; no external deps. Designed for Maya 2024.
 - This UI is floating; Maya docking via workspaceControl may be added later if you want it docked.

"""

from functools import partial
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore, QtGui
import shiboken2

# ---------- Path rig builder logic (reused / simplified from the module) ----------

def _ensure_curve(curve):
    if curve and cmds.objExists(curve):
        # find shape
        if cmds.objectType(curve) == 'nurbsCurve':
            transform = cmds.listRelatives(curve, parent=True, fullPath=True)[0]
            shape = curve
        else:
            transform = curve
            shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
            shape = shapes[0] if shapes else None
        if not shape or cmds.objectType(shape) != 'nurbsCurve':
            raise RuntimeError("Provided object is not a NURBS curve: {}".format(curve))
        return transform, shape
    pts = [(0,0,0), (5,0,2), (10,0,0), (15,0,-2), (20,0,0)]
    crv = cmds.curve(p=pts, d=3, name='path_default_crv')
    return crv, cmds.listRelatives(crv, shapes=True, fullPath=True)[0]


def _make_circle_ctrl(name, radius=0.5, normal=(0,1,0)):
    ctrl = cmds.circle(name=name, normal=normal, radius=radius, ch=False)[0]
    zero = cmds.group(ctrl, name=name + '_offset', em=True)
    cmds.parent(ctrl, zero)
    try:
        cmds.makeIdentity(ctrl, apply=True, t=0, r=0, s=0, n=0)
    except Exception:
        pass
    return zero, ctrl


def build_path_rig(curve=None, num_controls=5, prefix='path', create_joints=False, joint_prefix='bind', attach_objects=None, ctrl_radius=0.6, up_control_radius=1.2):
    if num_controls < 1:
        raise ValueError("num_controls must be >= 1")
    curve_transform, curve_shape = _ensure_curve(curve)
    top_grp = cmds.group(em=True, name=prefix + '_rig_grp')
    controls_grp = cmds.group(em=True, name=prefix + '_controls_grp', parent=top_grp)
    bind_grp = cmds.group(em=True, name=prefix + '_bind_grp', parent=top_grp)
    misc_grp = cmds.group(em=True, name=prefix + '_misc_grp', parent=top_grp)
    up_zero, up_ctrl = _make_circle_ctrl(prefix + '_upCtrl', radius=up_control_radius, normal=(0,0,1))
    cmds.parent(up_zero, controls_grp)
    bbox = cmds.exactWorldBoundingBox(curve_transform)
    center = [(bbox[0]+bbox[3])/2.0, (bbox[1]+bbox[4])/2.0, (bbox[2]+bbox[5])/2.0]
    cmds.xform(up_zero, ws=True, t=(center[0], center[1] + (bbox[4]-bbox[1]) * 0.8 + 1.0, center[2]))
    for s in ['sx','sy','sz']:
        try:
            cmds.setAttr(up_ctrl + '.' + s, lock=True)
        except Exception:
            pass

    controls = []
    motion_nodes = []
    joints = []

    for i in range(num_controls):
        u = 0.5 if num_controls == 1 else float(i) / float(num_controls - 1)
        ctl_zero, ctl = _make_circle_ctrl(f'{prefix}_ctl_{i+1:02d}', radius=ctrl_radius)
        cmds.parent(ctl_zero, controls_grp)
        mp = cmds.pathAnimation(ctl_zero, curve_transform, fractionMode=True, follow=True, name=f'{prefix}_mp_{i+1:02d}')
        motion_path_node = mp
        if not cmds.objExists(motion_path_node):
            created = cmds.ls(type='motionPath') or []
            motion_path_node = created[-1] if created else motion_path_node
        try:
            cmds.setAttr(motion_path_node + '.fractionMode', 1)
        except Exception:
            pass
        try:
            cmds.setAttr(motion_path_node + '.follow', 1)
        except Exception:
            pass
        try:
            cmds.setAttr(motion_path_node + '.frontAxis', 0)
            cmds.setAttr(motion_path_node + '.upAxis', 1)
        except Exception:
            pass
        try:
            for wut in (2,3,4):
                try:
                    cmds.setAttr(motion_path_node + '.worldUpType', wut)
                    break
                except Exception:
                    continue
            try:
                cmds.connectAttr(up_ctrl + '.worldMatrix[0]', motion_path_node + '.worldUpMatrix', force=True)
            except Exception:
                try:
                    cmds.connectAttr(up_ctrl + '.worldMatrix[0]', motion_path_node + '.worldUpObject', force=True)
                except Exception:
                    pos = cmds.xform(up_ctrl, q=True, ws=True, t=True)
                    try:
                        cmds.setAttr(motion_path_node + '.worldUpVector', pos[0], pos[1], pos[2])
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            cmds.setAttr(motion_path_node + '.uValue', u)
        except Exception:
            try:
                cmds.setAttr(motion_path_node + '.u', u)
            except Exception:
                pass
        try:
            connections = cmds.listConnections(motion_path_node + '.uValue', plugs=True) or []
            for con in connections:
                node = con.split('.')[0]
                if cmds.objectType(node).startswith('animCurve'):
                    try:
                        cmds.delete(node)
                    except Exception:
                        pass
        except Exception:
            pass
        for s in ['sx','sy','sz']:
            try:
                cmds.setAttr(ctl + '.' + s, lock=True)
            except Exception:
                pass
        controls.append({'zero': ctl_zero, 'ctrl': ctl, 'motionPath': motion_path_node, 'u': u})
        motion_nodes.append(motion_path_node)
        if create_joints:
            jname = '{}_jnt_{:02d}'.format(joint_prefix, i+1)
            j = cmds.joint(name=jname)
            pos = cmds.xform(ctl_zero, q=True, ws=True, t=True)
            cmds.xform(j, ws=True, t=pos)
            cmds.joint(j, e=True, oj='none')
            cmds.parent(j, bind_grp)
            joints.append(j)

    attached = []
    if attach_objects:
        for idx, obj in enumerate(attach_objects):
            if not cmds.objExists(obj):
                cmds.warning("attach_objects: object '{}' does not exist; skipping".format(obj))
                continue
            mp_name = f'{prefix}_attach_mp_{idx+1:02d}'
            try:
                mp = cmds.pathAnimation(obj, curve_transform, fractionMode=True, follow=True, name=mp_name)
            except Exception as e:
                cmds.warning("Failed to create motionPath for '{}': {}".format(obj, e))
                continue
            u_val = float(idx) / max(1, len(attach_objects)-1) if len(attach_objects) > 1 else 0.0
            try:
                cmds.setAttr(mp + '.uValue', u_val)
            except Exception:
                try:
                    cmds.setAttr(mp + '.u', u_val)
                except Exception:
                    pass
            attached.append({'object': obj, 'motionPath': mp, 'u': u_val})

    try:
        if curve is None or 'path_default_crv' in curve_transform:
            cmds.parent(curve_transform, misc_grp)
    except Exception:
        pass

    result = {
        'top_grp': top_grp,
        'controls_grp': controls_grp,
        'bind_grp': bind_grp,
        'misc_grp': misc_grp,
        'curve_transform': curve_transform,
        'curve_shape': curve_shape,
        'up_ctrl_zero': up_zero,
        'up_ctrl': up_ctrl,
        'controls': controls,
        'motion_nodes': motion_nodes,
        'joints': joints,
        'attached': attached
    }
    cmds.select(top_grp, r=True)
    return result


# ---------- Maya PySide2 UI ----------

# Global flag to prevent multiple UI instances
_ui_creation_in_progress = False

def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    if main_window_ptr is not None:
        return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    return None


class PathRigUI(QtWidgets.QDialog):
    WINDOW_TITLE = 'Path Rig Builder'
    _instance = None  # Class variable to track instance
    
    def __init__(self, parent=None):
        global _ui_creation_in_progress
        
        # Prevent recursive UI creation
        if _ui_creation_in_progress:
            raise RuntimeError("UI creation already in progress - preventing recursion")
        
        _ui_creation_in_progress = True
        
        try:
            # Get Maya main window if no parent provided
            if parent is None:
                parent = get_maya_main_window()
            
            super(PathRigUI, self).__init__(parent)
            self.setWindowTitle(self.WINDOW_TITLE)
            self.setMinimumWidth(420)
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
            self._result = None
            self._rig_data = None
            self._build_ui()
            
            # Set class instance
            PathRigUI._instance = self
        finally:
            _ui_creation_in_progress = False

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self.curve_edit = QtWidgets.QLineEdit()
        self.curve_edit.setPlaceholderText('leave blank to create default curve')
        form.addRow('Curve:', self.curve_edit)

        self.num_spin = QtWidgets.QSpinBox()
        self.num_spin.setRange(1, 64)
        self.num_spin.setValue(5)
        form.addRow('Num controls:', self.num_spin)

        self.create_jnts_cb = QtWidgets.QCheckBox('Create joints')
        form.addRow('', self.create_jnts_cb)

        self.attach_edit = QtWidgets.QLineEdit()
        self.attach_edit.setPlaceholderText('comma separated object names (optional)')
        form.addRow('Attach objects:', self.attach_edit)

        self.ctrl_radius_spin = QtWidgets.QDoubleSpinBox()
        self.ctrl_radius_spin.setRange(0.01, 10.0)
        self.ctrl_radius_spin.setSingleStep(0.1)
        self.ctrl_radius_spin.setValue(0.6)
        form.addRow('Control radius:', self.ctrl_radius_spin)

        self.up_radius_spin = QtWidgets.QDoubleSpinBox()
        self.up_radius_spin.setRange(0.01, 20.0)
        self.up_radius_spin.setSingleStep(0.1)
        self.up_radius_spin.setValue(1.2)
        form.addRow('Up control radius:', self.up_radius_spin)

        layout.addLayout(form)

        btn_layout = QtWidgets.QHBoxLayout()
        self.build_btn = QtWidgets.QPushButton('Build Path Rig')
        self.build_btn.clicked.connect(self.on_build)
        btn_layout.addWidget(self.build_btn)

        self.refresh_btn = QtWidgets.QPushButton('Refresh Controls')
        self.refresh_btn.clicked.connect(self.refresh_controls_list)
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)

        layout.addWidget(self._make_separator())

        self.controls_scroll = QtWidgets.QScrollArea()
        self.controls_scroll.setWidgetResizable(True)
        self.controls_container = QtWidgets.QWidget()
        self.controls_layout = QtWidgets.QVBoxLayout(self.controls_container)
        self.controls_layout.setAlignment(QtCore.Qt.AlignTop)
        self.controls_scroll.setWidget(self.controls_container)
        layout.addWidget(QtWidgets.QLabel('Controls (post-build):'))
        layout.addWidget(self.controls_scroll, 1)

        footer = QtWidgets.QHBoxLayout()
        self.close_btn = QtWidgets.QPushButton('Close')
        self.close_btn.clicked.connect(self.close)
        footer.addStretch()
        footer.addWidget(self.close_btn)
        layout.addLayout(footer)

    def _make_separator(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        return line

    def on_build(self):
        curve = self.curve_edit.text().strip() or None
        num_controls = int(self.num_spin.value())
        create_joints = bool(self.create_jnts_cb.isChecked())
        attach_text = self.attach_edit.text().strip()
        attach_objects = [s.strip() for s in attach_text.split(',') if s.strip()] if attach_text else None
        ctrl_radius = float(self.ctrl_radius_spin.value())
        up_radius = float(self.up_radius_spin.value())

        # Disable build button to prevent multiple clicks
        self.build_btn.setEnabled(False)
        self.build_btn.setText('Building...')
        
        try:
            # Use Maya's idle queue to prevent UI blocking
            cmds.evalDeferred(lambda: self._build_rig_deferred(curve, num_controls, create_joints, attach_objects, ctrl_radius, up_radius))
        except Exception as e:
            cmds.warning('Failed to build path rig: {}'.format(e))
            self.build_btn.setEnabled(True)
            self.build_btn.setText('Build Path Rig')

    def _build_rig_deferred(self, curve, num_controls, create_joints, attach_objects, ctrl_radius, up_radius):
        """Build rig in Maya's idle queue to prevent UI blocking"""
        try:
            res = build_path_rig(curve=curve, num_controls=num_controls, prefix='uiPath', create_joints=create_joints, attach_objects=attach_objects, ctrl_radius=ctrl_radius, up_control_radius=up_radius)
            self._rig_data = res
            cmds.inViewMessage(amg='Path rig created: <hl>{}</hl>'.format(res['top_grp']), pos='midCenter', fade=True)
            # Refresh controls list in next idle cycle
            cmds.evalDeferred(self.refresh_controls_list)
        except Exception as e:
            cmds.warning('Failed to build path rig: {}'.format(e))
        finally:
            # Re-enable build button
            self.build_btn.setEnabled(True)
            self.build_btn.setText('Build Path Rig')

    def refresh_controls_list(self):
        # clear layout
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()
        clear_layout(self.controls_layout)

        if not self._rig_data:
            self.controls_layout.addWidget(QtWidgets.QLabel('No rig built yet.'))
            return

        controls = self._rig_data.get('controls', [])
        for idx, c in enumerate(controls):
            row = QtWidgets.QWidget()
            hl = QtWidgets.QHBoxLayout(row)
            # label
            lab = QtWidgets.QLabel('{}:'.format(c['ctrl']))
            lab.setMinimumWidth(140)
            hl.addWidget(lab)
            # slider
            s = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            s.setRange(0, 1000)
            s.setValue(int(c.get('u', 0.0) * 1000.0))
            s.setSingleStep(1)
            s.valueChanged.connect(partial(self.on_u_slider_changed, idx))
            hl.addWidget(s, 1)
            # select button
            sel_btn = QtWidgets.QPushButton('Select')
            sel_btn.clicked.connect(partial(self.on_select_control, c['zero']))
            hl.addWidget(sel_btn)
            self.controls_layout.addWidget(row)

    def on_u_slider_changed(self, idx, value):
        if not self._rig_data:
            return
        try:
            control = self._rig_data['controls'][idx]
            mp = control.get('motionPath')
            u = float(value) / 1000.0
            
            # Use evalDeferred to prevent UI blocking during slider changes
            def set_u_value():
                try:
                    if cmds.objExists(mp):
                        try:
                            cmds.setAttr(mp + '.uValue', u)
                        except Exception:
                            try:
                                cmds.setAttr(mp + '.u', u)
                            except Exception:
                                pass
                        control['u'] = u
                except Exception as e:
                    cmds.warning('Failed to set uValue: {}'.format(e))
            
            cmds.evalDeferred(set_u_value)
        except Exception as e:
            cmds.warning('Failed to set uValue: {}'.format(e))

    def on_select_control(self, zero_name):
        # Use evalDeferred to prevent UI blocking during selection
        def select_control():
            try:
                if cmds.objExists(zero_name):
                    cmds.select(zero_name, r=True)
            except Exception as e:
                cmds.warning('Failed to select control: {}'.format(e))
        
        cmds.evalDeferred(select_control)

    # convenience show method
    @classmethod
    def show(cls):
        # Check if we already have an instance
        if cls._instance is not None and cls._instance.isVisible():
            # Bring existing window to front
            cls._instance.raise_()
            cls._instance.activateWindow()
            return cls._instance
        
        # Check if window already exists and is visible
        existing_window = None
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, PathRigUI):
                if w.isVisible():
                    # Bring existing window to front
                    w.raise_()
                    w.activateWindow()
                    cls._instance = w
                    return w
                else:
                    existing_window = w
        
        # Close any existing hidden windows
        if existing_window:
            try:
                existing_window.close()
            except Exception:
                pass
        
        # Create new window
        try:
            win = cls()
            win.show()
            return win
        except Exception as e:
            import maya.cmds as cmds
            cmds.warning('Failed to create Path Rig UI: {}'.format(e))
            return None


# Safe way to show the UI - call this function instead of running the script directly
def show_path_rig_ui():
    """Show the Path Rig UI. Call this function instead of running the script directly."""
    global _ui_creation_in_progress
    
    # Prevent multiple simultaneous UI creation attempts
    if _ui_creation_in_progress:
        import maya.cmds as cmds
        cmds.warning('UI creation already in progress - please wait')
        return None
    
    try:
        return PathRigUI.show()
    except Exception as e:
        import maya.cmds as cmds
        cmds.warning('Failed to show Path Rig UI: {}'.format(e))
        return None

# Remove the automatic execution to prevent recursion
# Instead, call show_path_rig_ui() manually in Maya script editor
