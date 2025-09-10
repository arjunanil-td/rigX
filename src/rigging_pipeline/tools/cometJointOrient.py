"""
CometJointOrient - Python implementation
Based on the original cometJointOrient.mel by Michael B. Comet

A comprehensive joint orientation utility for Maya with:
- Automatic joint orientation based on aim and up vectors
- Manual rotation tweaking capabilities
- World up direction control
- Auto-guess up direction functionality
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner


def maya_main_window():
    """Get Maya's main window"""
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class CometJointOrientUtils:
    """Utility functions for CometJointOrient functionality"""
    
    @staticmethod
    def get_cross_dir(obj_a, obj_b, obj_c):
        """
        Given three nodes, get the cross product of the directions from B->A and B->C
        """
        cross = [0.0, 0.0, 0.0]
        
        if not obj_a or not obj_b or not obj_c:
            return cross
        
        if not all(cmds.objExists(obj) for obj in [obj_a, obj_b, obj_c]):
            return cross
        
        try:
            pos_a = cmds.xform(obj_a, q=True, ws=True, rp=True)
            pos_b = cmds.xform(obj_b, q=True, ws=True, rp=True)
            pos_c = cmds.xform(obj_c, q=True, ws=True, rp=True)
            
            # Create vectors B->A and B->C
            v1 = om.MVector(pos_a[0] - pos_b[0], pos_a[1] - pos_b[1], pos_a[2] - pos_b[2])
            v2 = om.MVector(pos_c[0] - pos_b[0], pos_c[1] - pos_b[1], pos_c[2] - pos_b[2])
            
            # Cross product and normalize
            v_cross = v1 ^ v2
            v_cross.normalize()
            
            cross[0] = v_cross.x
            cross[1] = v_cross.y
            cross[2] = v_cross.z
            
        except Exception as e:
            print(f"Error calculating cross direction: {e}")
            
        return cross
    
    @staticmethod
    def orient_joints(joints, aim_axis, up_axis, up_dir, do_auto=False):
        """
        Orient joints based on aim and up vectors
        
        Args:
            joints: List of joint names to orient
            aim_axis: [x, y, z] values for aim axis
            up_axis: [x, y, z] values for up axis
            up_dir: [x, y, z] world up direction
            do_auto: Boolean for auto-guessing up direction
        """
        if not joints:
            cmds.warning("No joints selected for orientation")
            return
        
        prev_up = om.MVector(0, 0, 0)
        
        for i, joint in enumerate(joints):
            try:
                # Store children before unparenting
                children = cmds.listRelatives(joint, children=True, type=['transform', 'joint']) or []
                if children:
                    children = cmds.parent(children, world=True)
                
                # Find parent
                parents = cmds.listRelatives(joint, parent=True) or []
                parent = parents[0] if parents else ""
                
                # Find child joint for aiming
                aim_target = ""
                for child in children:
                    if cmds.nodeType(child) == "joint":
                        aim_target = child
                        break
                
                if aim_target:
                    up_vec = [0.0, 0.0, 0.0]
                    
                    # Auto-guess up direction if enabled
                    if do_auto:
                        pos_j = cmds.xform(joint, q=True, ws=True, rp=True)
                        pos_p = pos_j
                        if parent:
                            pos_p = cmds.xform(parent, q=True, ws=True, rp=True)
                        
                        tolerance = 0.0001
                        is_same_pos = all(abs(pos_j[k] - pos_p[k]) <= tolerance for k in range(3))
                        
                        if not parent or is_same_pos:
                            # Use next joint for cross calculation
                            aim_children = cmds.listRelatives(aim_target, children=True) or []
                            aim_child = ""
                            for child in aim_children:
                                if cmds.nodeType(child) == "joint":
                                    aim_child = child
                                    break
                            up_vec = CometJointOrientUtils.get_cross_dir(joint, aim_target, aim_child)
                        else:
                            up_vec = CometJointOrientUtils.get_cross_dir(parent, joint, aim_target)
                    
                    # Use default up direction if auto failed or disabled
                    if not do_auto or all(v == 0.0 for v in up_vec):
                        up_vec = up_dir
                    
                    # Create aim constraint
                    constraint = cmds.aimConstraint(
                        aim_target,
                        joint,
                        aim=aim_axis,
                        upVector=up_axis,
                        worldUpVector=up_vec,
                        worldUpType="vector",
                        weight=1.0
                    )
                    
                    cmds.delete(constraint)
                    
                    # Check for flipping and correct if needed
                    cur_up = om.MVector(up_vec[0], up_vec[1], up_vec[2])
                    cur_up.normalize()
                    dot = cur_up * prev_up
                    prev_up = om.MVector(up_vec[0], up_vec[1], up_vec[2])
                    
                    if i > 0 and dot <= 0.0:
                        # Flip 180 degrees on aim axis
                        cmds.xform(
                            joint,
                            relative=True,
                            objectSpace=True,
                            rotation=[
                                aim_axis[0] * 180.0,
                                aim_axis[1] * 180.0,
                                aim_axis[2] * 180.0
                            ]
                        )
                        prev_up *= -1.0
                    
                    # Clear joint orientation and apply
                    cmds.joint(joint, edit=True, zeroScaleOrient=True)
                    cmds.makeIdentity(joint, apply=True)
                
                elif parent:
                    # No target, copy parent orientation
                    constraint = cmds.orientConstraint(parent, joint, weight=1.0)
                    cmds.delete(constraint)
                    cmds.joint(joint, edit=True, zeroScaleOrient=True)
                    cmds.makeIdentity(joint, apply=True)
                
                # Reparent children
                if children:
                    cmds.parent(children, joint)
                    
            except Exception as e:
                cmds.warning(f"Failed to orient joint {joint}: {e}")
    
    @staticmethod
    def tweak_joints(joints, rotation):
        """
        Manually tweak joint orientations
        
        Args:
            joints: List of joint names
            rotation: [x, y, z] rotation values in degrees
        """
        for joint in joints:
            try:
                cmds.xform(
                    joint,
                    relative=True,
                    objectSpace=True,
                    rotation=rotation
                )
                cmds.joint(joint, edit=True, zeroScaleOrient=True)
                cmds.makeIdentity(joint, apply=True)
            except Exception as e:
                cmds.warning(f"Failed to tweak joint {joint}: {e}")


class CometJointOrientUI(QtWidgets.QDialog):
    """CometJointOrient UI - Python/Qt version of the original MEL UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent or maya_main_window())
        
        self.setWindowTitle("CometJointOrient - Python")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(320, 400)
        self.setStyleSheet(THEME_STYLESHEET)
        
        self.build_ui()
    
    def build_ui(self):
        """Build the user interface"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add banner
        banner = Banner("CometJointOrient", "orient.png")
        layout.addWidget(banner)
        
        # Axis Display Section
        axis_group = QtWidgets.QGroupBox("Axis Display")
        axis_group.setStyleSheet(self._get_group_style())
        axis_layout = QtWidgets.QHBoxLayout(axis_group)
        
        show_btn = QtWidgets.QPushButton("Show Axis")
        show_btn.clicked.connect(lambda: cmds.toggle(state=True, localAxis=True))
        hide_btn = QtWidgets.QPushButton("Hide Axis")
        hide_btn.clicked.connect(lambda: cmds.toggle(state=False, localAxis=True))
        
        axis_layout.addWidget(show_btn)
        axis_layout.addWidget(hide_btn)
        layout.addWidget(axis_group)
        
        # Orientation Settings
        orient_group = QtWidgets.QGroupBox("Orientation Settings")
        orient_group.setStyleSheet(self._get_group_style())
        orient_layout = QtWidgets.QVBoxLayout(orient_group)
        
        # Aim Axis
        aim_row = QtWidgets.QHBoxLayout()
        aim_row.addWidget(QtWidgets.QLabel("Aim Axis:"))
        self.aim_group = QtWidgets.QButtonGroup()
        self.aim_x = QtWidgets.QRadioButton("X")
        self.aim_y = QtWidgets.QRadioButton("Y")
        self.aim_z = QtWidgets.QRadioButton("Z")
        self.aim_y.setChecked(True)  # Default to Y
        
        self.aim_group.addButton(self.aim_x, 0)
        self.aim_group.addButton(self.aim_y, 1)
        self.aim_group.addButton(self.aim_z, 2)
        
        aim_row.addWidget(self.aim_x)
        aim_row.addWidget(self.aim_y)
        aim_row.addWidget(self.aim_z)
        
        self.aim_reverse = QtWidgets.QCheckBox("Reverse")
        aim_row.addWidget(self.aim_reverse)
        aim_row.addStretch()
        orient_layout.addLayout(aim_row)
        
        # Up Axis
        up_row = QtWidgets.QHBoxLayout()
        up_row.addWidget(QtWidgets.QLabel("Up Axis:"))
        self.up_group = QtWidgets.QButtonGroup()
        self.up_x = QtWidgets.QRadioButton("X")
        self.up_y = QtWidgets.QRadioButton("Y")
        self.up_z = QtWidgets.QRadioButton("Z")
        self.up_x.setChecked(True)  # Default to X
        
        self.up_group.addButton(self.up_x, 0)
        self.up_group.addButton(self.up_y, 1)
        self.up_group.addButton(self.up_z, 2)
        
        up_row.addWidget(self.up_x)
        up_row.addWidget(self.up_y)
        up_row.addWidget(self.up_z)
        
        self.up_reverse = QtWidgets.QCheckBox("Reverse")
        up_row.addWidget(self.up_reverse)
        up_row.addStretch()
        orient_layout.addLayout(up_row)
        
        layout.addWidget(orient_group)
        
        # World Up Direction
        updir_group = QtWidgets.QGroupBox("World Up Direction")
        updir_group.setStyleSheet(self._get_group_style())
        updir_layout = QtWidgets.QVBoxLayout(updir_group)
        
        updir_row = QtWidgets.QHBoxLayout()
        updir_row.addWidget(QtWidgets.QLabel("World Up Dir:"))
        
        self.updir_x = QtWidgets.QDoubleSpinBox()
        self.updir_x.setRange(-10.0, 10.0)
        self.updir_x.setValue(1.0)
        self.updir_x.setDecimals(3)
        
        self.updir_y = QtWidgets.QDoubleSpinBox()
        self.updir_y.setRange(-10.0, 10.0)
        self.updir_y.setValue(0.0)
        self.updir_y.setDecimals(3)
        
        self.updir_z = QtWidgets.QDoubleSpinBox()
        self.updir_z.setRange(-10.0, 10.0)
        self.updir_z.setValue(0.0)
        self.updir_z.setDecimals(3)
        
        updir_row.addWidget(self.updir_x)
        updir_row.addWidget(self.updir_y)
        updir_row.addWidget(self.updir_z)
        updir_layout.addLayout(updir_row)
        
        # Quick set buttons
        quick_row = QtWidgets.QHBoxLayout()
        x_btn = QtWidgets.QPushButton("X")
        x_btn.clicked.connect(lambda: self.set_updir(1, 0, 0))
        y_btn = QtWidgets.QPushButton("Y")
        y_btn.clicked.connect(lambda: self.set_updir(0, 1, 0))
        z_btn = QtWidgets.QPushButton("Z")
        z_btn.clicked.connect(lambda: self.set_updir(0, 0, 1))
        
        quick_row.addWidget(x_btn)
        quick_row.addWidget(y_btn)
        quick_row.addWidget(z_btn)
        quick_row.addStretch()
        updir_layout.addLayout(quick_row)
        
        self.auto_dir = QtWidgets.QCheckBox("Auto-Guess Up Direction")
        updir_layout.addWidget(self.auto_dir)
        
        layout.addWidget(updir_group)
        
        # Orient button
        orient_btn = QtWidgets.QPushButton("Orient Joints")
        orient_btn.setMinimumHeight(35)
        orient_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #383838, stop:1 #48BB78);
                border: 1px solid #666666;
                border-radius: 4px;
                color: #2D2D2D;
                font-weight: bold;
                padding: 8px;
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
        orient_btn.clicked.connect(self.orient_joints)
        layout.addWidget(orient_btn)
        
        # Tweak Section
        tweak_group = QtWidgets.QGroupBox("Manual Tweak")
        tweak_group.setStyleSheet(self._get_group_style())
        tweak_layout = QtWidgets.QVBoxLayout(tweak_group)
        
        tweak_row = QtWidgets.QHBoxLayout()
        tweak_row.addWidget(QtWidgets.QLabel("Tweak:"))
        
        self.tweak_x = QtWidgets.QDoubleSpinBox()
        self.tweak_x.setRange(-180.0, 180.0)
        self.tweak_x.setValue(0.0)
        self.tweak_x.setDecimals(3)
        
        self.tweak_y = QtWidgets.QDoubleSpinBox()
        self.tweak_y.setRange(-180.0, 180.0)
        self.tweak_y.setValue(0.0)
        self.tweak_y.setDecimals(3)
        
        self.tweak_z = QtWidgets.QDoubleSpinBox()
        self.tweak_z.setRange(-180.0, 180.0)
        self.tweak_z.setValue(0.0)
        self.tweak_z.setDecimals(3)
        
        tweak_row.addWidget(self.tweak_x)
        tweak_row.addWidget(self.tweak_y)
        tweak_row.addWidget(self.tweak_z)
        
        zero_btn = QtWidgets.QPushButton("ZERO")
        zero_btn.clicked.connect(self.zero_tweak)
        tweak_row.addWidget(zero_btn)
        tweak_layout.addLayout(tweak_row)
        
        # Tweak buttons
        tweak_btn_row = QtWidgets.QHBoxLayout()
        pos_tweak_btn = QtWidgets.QPushButton("Manual + Rot Tweak")
        pos_tweak_btn.clicked.connect(lambda: self.tweak_joints(1.0))
        neg_tweak_btn = QtWidgets.QPushButton("Manual - Rot Tweak")
        neg_tweak_btn.clicked.connect(lambda: self.tweak_joints(-1.0))
        
        tweak_btn_row.addWidget(pos_tweak_btn)
        tweak_btn_row.addWidget(neg_tweak_btn)
        tweak_layout.addLayout(tweak_btn_row)
        
        layout.addWidget(tweak_group)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _get_group_style(self):
        """Get consistent group box styling"""
        return """
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
        """
    
    def set_updir(self, x, y, z):
        """Set up direction values"""
        self.updir_x.setValue(x)
        self.updir_y.setValue(y)
        self.updir_z.setValue(z)
    
    def zero_tweak(self):
        """Zero all tweak values"""
        self.tweak_x.setValue(0.0)
        self.tweak_y.setValue(0.0)
        self.tweak_z.setValue(0.0)
    
    def orient_joints(self):
        """Execute joint orientation"""
        try:
            joints = cmds.ls(type="joint", selection=True)
            if not joints:
                cmds.warning("No joints selected")
                return
            
            # Get aim axis
            aim_id = self.aim_group.checkedId()
            aim_axis = [0.0, 0.0, 0.0]
            aim_axis[aim_id] = -1.0 if self.aim_reverse.isChecked() else 1.0
            
            # Get up axis  
            up_id = self.up_group.checkedId()
            up_axis = [0.0, 0.0, 0.0]
            up_axis[up_id] = -1.0 if self.up_reverse.isChecked() else 1.0
            
            # Check for same axis
            if aim_id == up_id:
                cmds.warning("The AIM and UP axis are the same! Orientation probably won't work!")
                return
            
            # Get up direction
            up_dir = [
                self.updir_x.value(),
                self.updir_y.value(),
                self.updir_z.value()
            ]
            
            do_auto = self.auto_dir.isChecked()
            
            # Orient joints
            CometJointOrientUtils.orient_joints(joints, aim_axis, up_axis, up_dir, do_auto)
            
            # Reselect joints
            cmds.select(joints, replace=True)
            
            print("// cometJointOrient")
            print(f"Oriented {len(joints)} joints")
            
        except Exception as e:
            cmds.error(f"Error orienting joints: {str(e)}")
    
    def tweak_joints(self, multiplier):
        """Apply tweak to selected joints"""
        try:
            joints = cmds.ls(type="joint", selection=True)
            if not joints:
                cmds.warning("No joints selected")
                return
            
            rotation = [
                self.tweak_x.value() * multiplier,
                self.tweak_y.value() * multiplier,
                self.tweak_z.value() * multiplier
            ]
            
            CometJointOrientUtils.tweak_joints(joints, rotation)
            
            # Reselect joints
            cmds.select(joints, replace=True)
            
            print(f"Tweaked {len(joints)} joints by {rotation}")
            
        except Exception as e:
            cmds.error(f"Error tweaking joints: {str(e)}")


# Global dialog reference
_comet_joint_orient_dialog = None


def launch_comet_joint_orient():
    """Launch the CometJointOrient dialog"""
    global _comet_joint_orient_dialog
    
    try:
        if _comet_joint_orient_dialog is not None:
            _comet_joint_orient_dialog.close()
            _comet_joint_orient_dialog.deleteLater()
    except:
        pass
    
    _comet_joint_orient_dialog = CometJointOrientUI()
    _comet_joint_orient_dialog.show()
    return _comet_joint_orient_dialog


# Quick access functions
def quick_orient_joints(aim_axis="Y", up_axis="X", up_dir=(1, 0, 0), auto_guess=False):
    """Quick orient function for integration"""
    joints = cmds.ls(type="joint", selection=True)
    if not joints:
        cmds.warning("No joints selected")
        return
    
    # Convert axis strings to vectors
    axis_map = {"X": [1, 0, 0], "Y": [0, 1, 0], "Z": [0, 0, 1]}
    aim_vec = axis_map.get(aim_axis, [0, 1, 0])
    up_vec = axis_map.get(up_axis, [1, 0, 0])
    
    CometJointOrientUtils.orient_joints(joints, aim_vec, up_vec, up_dir, auto_guess)
    print(f"Quick oriented {len(joints)} joints")


def quick_show_axis():
    """Quick function to show joint axis"""
    cmds.toggle(state=True, localAxis=True)


def quick_hide_axis():
    """Quick function to hide joint axis"""
    cmds.toggle(state=False, localAxis=True)
