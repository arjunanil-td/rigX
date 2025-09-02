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
from rigging_pipeline.tools.ui.rigx_utilityTools_ui import RigXUtilityToolsUI


def maya_main_window():
    if not MAYA_AVAILABLE:
        return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class RigXUtilityTools:
    """Main class for RigX Utility Tools functionality"""
    
    def __init__(self):
        self.ui = None
        
    def show_ui(self):
        """Show the RigX Utility Tools UI"""
        if not self.ui:
            self.ui = RigXUtilityToolsUI()
        self.ui.show()
        self.ui.raise_()
        self.ui.activateWindow()
    
    def run_offset_group_tool(self):
        """Create offset groups for selected objects"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to create offset groups for")
                return
            
            # Create custom dialog for smaller integer input
            from PySide2 import QtWidgets, QtCore
            from maya import OpenMayaUI as omui
            from shiboken2 import wrapInstance
            
            # Get Maya main window
            ptr = omui.MQtUtil.mainWindow()
            maya_window = wrapInstance(int(ptr), QtWidgets.QWidget)
            
            # Create custom dialog
            dialog = QtWidgets.QDialog(maya_window)
            dialog.setWindowTitle("Offset Groups")
            dialog.setFixedSize(250, 120)
            dialog.setModal(True)
            
            # Layout
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Label
            label = QtWidgets.QLabel("Enter number of offset groups to create:")
            layout.addWidget(label)
            
            # Integer input field (small size)
            input_field = QtWidgets.QSpinBox()
            input_field.setMinimum(1)
            input_field.setMaximum(10)
            input_field.setValue(1)
            input_field.setFixedWidth(80)  # Make it small
            input_field.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(input_field, alignment=QtCore.Qt.AlignCenter)
            
            # Buttons
            button_layout = QtWidgets.QHBoxLayout()
            create_btn = QtWidgets.QPushButton("Create")
            cancel_btn = QtWidgets.QPushButton("Cancel")
            button_layout.addWidget(create_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            # Connect buttons
            create_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            # Set focus to input field
            input_field.setFocus()
            input_field.selectAll()
            
            # Show dialog
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                num_groups = input_field.value()
                
                created_groups = []
                for obj in selected:
                    # Get parent of the object before creating groups
                    parent = cmds.listRelatives(obj, parent=True)
                    
                    # Create multiple offset groups for each object
                    for i in range(num_groups):
                        if num_groups == 1:
                            base_name = f"{obj}_offset01_GRP"
                        else:
                            base_name = f"{obj}_offset{i+1:02d}_GRP"
                        
                        # Check if name exists and add suffix if needed
                        group_name = base_name
                        counter = 1
                        while cmds.objExists(group_name):
                            group_name = f"{base_name}{counter}"
                            counter += 1
                        
                        # Create offset group
                        offset_grp = cmds.group(empty=True, name=group_name)
                        
                        # Use matchTransform for more accurate positioning
                        cmds.matchTransform(offset_grp, obj, position=True, rotation=True)
                        
                        # For the first group, parent the object under it
                        if i == 0:
                            cmds.parent(obj, offset_grp)
                        else:
                            # For additional groups, parent the previous group under the new one
                            cmds.parent(created_groups[-1], offset_grp)
                        
                        created_groups.append(offset_grp)
                    
                    # If object had a parent, parent the topmost offset group to it
                    if parent and num_groups > 0:
                        cmds.parent(created_groups[-1], parent[0])
                
                # Select all created groups
                cmds.select(created_groups)
            else:
                return
            
        except Exception as e:
            cmds.error(f"Error creating offset groups: {str(e)}")
    
    def run_joint_at_center_tool(self):
        """Create joint at center of selected objects"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to create joint at center")
                return
            
            for obj in selected:
                # Get bounding box center
                bbox = cmds.exactWorldBoundingBox(obj)
                center_x = (bbox[0] + bbox[3]) / 2
                center_y = (bbox[1] + bbox[4]) / 2
                center_z = (bbox[2] + bbox[5]) / 2
                
                # Create joint at center
                joint_name = f"{obj}_Jnt"
                cmds.select(clear=True)
                cmds.joint(position=(center_x, center_y, center_z), name=joint_name)
            
            cmds.confirmDialog(title="Joint Created", 
                             message=f"Created joints at center of {len(selected)} objects")
            
        except Exception as e:
            cmds.error(f"Error creating joint at center: {str(e)}")
    
    def run_curve_to_joint_tool(self):
        """Create joints along selected curves"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select one or more curves")
                return
            
            curves = cmds.filterExpand(selected, selectionMask=9)  # Filter for curves only
            if not curves:
                cmds.warning("Please select valid NURBS curves")
                return
            
            # Ask user for number of joints
            result = cmds.promptDialog(
                title="Curve to Joint",
                message="Enter number of joints to create:",
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel',
                text='5'
            )
            
            if result != 'OK':
                return
            
            try:
                num_joints = int(cmds.promptDialog(query=True, text=True))
                if num_joints < 1:
                    cmds.warning("Number of joints must be at least 1")
                    return
            except ValueError:
                cmds.warning("Please enter a valid number")
                return
            
            created_joints = []
            for curve in curves:
                # Create joints along curve
                cmds.select(clear=True)
                joint_list = []
                
                for i in range(num_joints):
                    # Calculate parameter value starting from vertex 0 (0 to 1)
                    param = i / float(num_joints - 1) if num_joints > 1 else 0
                    
                    # Get position on curve
                    pos = cmds.pointOnCurve(curve, parameter=param, position=True)
                    
                    # Create joint
                    joint_name = f"{curve}_jnt_{i+1:02d}"
                    joint = cmds.joint(position=pos, name=joint_name)
                    joint_list.append(joint)
                    created_joints.append(joint)
                
                # Connect joints in chain
                if len(joint_list) > 1:
                    for i in range(1, len(joint_list)):
                        cmds.parent(joint_list[i], joint_list[i-1])
                
                # Orient joints
                if len(joint_list) > 1:
                    cmds.select(joint_list[0])
                    cmds.joint(edit=True, orientJoint='xyz', secondaryAxisOrient='yup', children=True)
            
            # Select created joints
            if created_joints:
                cmds.select(created_joints)
                cmds.confirmDialog(title="Joints Created", 
                                 message=f"Created {len(created_joints)} joints from {len(curves)} curves")
            
        except Exception as e:
            cmds.error(f"Error creating joints from curve: {str(e)}")
    
    def run_inbetween_joints_tool(self):
        """Create joints between two selected joints"""
        try:
            selected = cmds.ls(selection=True)
            if not selected or len(selected) != 2:
                cmds.warning("Please select exactly two joints")
                return
            
            # Check if both selections are joints
            joint1, joint2 = selected[0], selected[1]
            if not cmds.objectType(joint1, isType="joint") or not cmds.objectType(joint2, isType="joint"):
                cmds.warning("Please select two joints")
                return
            
            # Ask user for number of joints
            result = cmds.promptDialog(
                title="Inbetween Joints",
                message="Enter number of joints to create:",
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel',
                text='3'
            )
            
            if result != 'OK':
                return
            
            try:
                num_joints = int(cmds.promptDialog(query=True, text=True))
                if num_joints < 1:
                    cmds.warning("Number of joints must be at least 1")
                    return
            except ValueError:
                cmds.warning("Please enter a valid number")
                return
            
            # Get positions of the two joints
            pos1 = cmds.xform(joint1, query=True, worldSpace=True, translation=True)
            pos2 = cmds.xform(joint2, query=True, worldSpace=True, translation=True)
            
            # Check if the joints are already parented
            parent1 = cmds.listRelatives(joint1, parent=True)
            parent2 = cmds.listRelatives(joint2, parent=True)
            
            # Check if joints are in a chain (joint2 is parented to joint1) or share the same parent
            joints_are_parented = False
            if parent2 and parent2[0] == joint1:
                # Joint2 is parented to joint1 (chain relationship)
                joints_are_parented = True
            elif parent1 and parent1[0] == joint2:
                # Joint1 is parented to joint2 (reverse chain relationship)
                joints_are_parented = True
            elif parent1 and parent2 and parent1[0] == parent2[0]:
                # Both joints share the same parent
                joints_are_parented = True
            
            # Calculate positions for inbetween joints
            created_joints = []
            for i in range(1, num_joints + 1):
                # Calculate interpolation factor (0 to 1)
                factor = i / (num_joints + 1)
                
                # Interpolate position
                x = pos1[0] + (pos2[0] - pos1[0]) * factor
                y = pos1[1] + (pos2[1] - pos1[1]) * factor
                z = pos1[2] + (pos2[2] - pos1[2]) * factor
                
                # Clear selection before creating joint
                cmds.select(clear=True)
                
                # Create joint
                joint_name = f"inbetween_jnt_{i:02d}"
                new_joint = cmds.joint(position=(x, y, z), name=joint_name)
                created_joints.append(new_joint)
            
            # Handle parenting based on whether the selected joints are parented
            if joints_are_parented and created_joints:
                # If joints are parented, create a chain
                # Parent the first inbetween joint to the first selected joint
                cmds.parent(created_joints[0], joint1)
                
                # Parent subsequent inbetween joints to the previous one
                for i in range(1, len(created_joints)):
                    cmds.parent(created_joints[i], created_joints[i-1])
                
                # Parent the last selected joint to the last inbetween joint
                cmds.parent(joint2, created_joints[-1])
                
                # Orient the created joints
                cmds.select(created_joints[0], replace=True)
                cmds.joint(created_joints[0], edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
            else:
                # If joints are not parented, keep inbetween joints unparented
                # Just orient each joint individually
                for joint in created_joints:
                    cmds.select(joint, replace=True)
                    cmds.joint(joint, edit=True, orientJoint="xyz", secondaryAxisOrient="yup", zeroScaleOrient=True)
            
            # Select all created joints and show confirmation
            if created_joints:
                cmds.select(created_joints)
            
        except Exception as e:
            cmds.error(f"Error creating inbetween joints: {str(e)}")
    
    def run_zero_out_tool(self):
        """Create zero-out group for selected objects"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to create zero-out groups for")
                return
            
            for obj in selected:
                # Get object's world position and rotation
                world_pos = cmds.xform(obj, query=True, worldSpace=True, translation=True)
                world_rot = cmds.xform(obj, query=True, worldSpace=True, rotation=True)
                
                # Create zero-out group
                group_name = f"{obj}_grp"
                zero_group = cmds.group(empty=True, name=group_name)
                
                # Set group to object's world position and rotation
                cmds.xform(zero_group, worldSpace=True, translation=world_pos)
                cmds.xform(zero_group, worldSpace=True, rotation=world_rot)
                
                # Get object's parent
                parent = cmds.listRelatives(obj, parent=True)
                
                if parent:
                    # Parent zero group to object's parent
                    cmds.parent(zero_group, parent[0])
                    # Parent object to zero group
                    cmds.parent(obj, zero_group)
                else:
                    # Parent object to zero group
                    cmds.parent(obj, zero_group)
            
            cmds.confirmDialog(title="Zero Out", 
                             message=f"Created zero-out groups for {len(selected)} objects")
            
        except Exception as e:
            cmds.error(f"Error creating zero-out groups: {str(e)}")

    def run_copy_weights_tool(self, copy_type):
        """Copy skin weights between objects"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to copy weights")
                return
            
            if copy_type == "one_to_many":
                if len(selected) < 2:
                    cmds.warning("Please select one source object and at least one target object")
                    return
                
                source = selected[0]
                targets = selected[1:]
                
                # Copy weights from source to all targets
                for target in targets:
                    try:
                        cmds.copySkinWeights(sourceSkin=source, destinationSkin=target, noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint")
                    except Exception as e:
                        cmds.warning(f"Could not copy weights to {target}: {str(e)}")
                
                cmds.confirmDialog(title="Copy Weights", 
                                 message=f"Copied weights from {source} to {len(targets)} objects")
                
            elif copy_type == "many_to_one":
                if len(selected) < 2:
                    cmds.warning("Please select multiple source objects and one target object")
                    return
                
                sources = selected[:-1]
                target = selected[-1]
                
                # Copy weights from all sources to target
                for source in sources:
                    try:
                        cmds.copySkinWeights(sourceSkin=source, destinationSkin=target, noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint")
                    except Exception as e:
                        cmds.warning(f"Could not copy weights from {source}: {str(e)}")
                
                cmds.confirmDialog(title="Copy Weights", 
                                 message=f"Copied weights from {len(sources)} objects to {target}")
            
        except Exception as e:
            cmds.error(f"Error copying weights: {str(e)}")


def main():
    """Main function to run the tool"""
    tool = RigXUtilityTools()
    tool.show_ui()


if __name__ == "__main__":
    main()
