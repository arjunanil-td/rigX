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
    """Main class for RigX Utility Tools functionality - Enhanced with RG Tools"""
    
    def __init__(self):
         self.ui = None
         
    def show_ui(self):
         """Show the RigX Utility Tools UI"""
         if not self.ui:
             self.ui = RigXUtilityToolsUI()
         self.ui.show()
         self.ui.raise_()
         self.ui.activateWindow()
    
    # ==================== EXISTING TOOLS ====================
    
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
                             # This creates the hierarchy: Group3 -> Group2 -> Group1 -> Object
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
    
    def run_sets_add_tool(self):
         """Add selected objects to a set"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to add to a set")
                 return
             
             # Get existing sets
             existing_sets = cmds.ls(type='objectSet')
             if not existing_sets:
                 cmds.warning("No sets found. Create a set first.")
                 return
             
             # Show dialog to select set
             result = cmds.promptDialog(
                 title="Add to Set",
                 message="Enter set name:",
                 button=['Add', 'Cancel'],
                 defaultButton='Add',
                 cancelButton='Cancel',
                 dismissString='Cancel'
             )
             
             if result == 'Add':
                 set_name = cmds.promptDialog(query=True, text=True)
                 if set_name and cmds.objExists(set_name):
                     # Add objects to set
                     cmds.sets(selected, add=set_name)
                     cmds.confirmDialog(title="Add to Set", 
                                      message=f"Added {len(selected)} objects to set '{set_name}'")
                 else:
                     cmds.warning(f"Set '{set_name}' does not exist")
             
         except Exception as e:
             cmds.error(f"Error adding objects to set: {str(e)}")
    
    def run_sets_create_tool(self):
         """Create a new set with selected objects"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to create a set with")
                 return
             
             # Show dialog to enter set name
             result = cmds.promptDialog(
                 title="Create Set",
                 message="Enter set name:",
                 button=['Create', 'Cancel'],
                 defaultButton='Create',
                 cancelButton='Cancel',
                 dismissString='Cancel'
             )
             
             if result == 'Create':
                 set_name = cmds.promptDialog(query=True, text=True)
                 if set_name:
                     # Create new set with selected objects
                     new_set = cmds.sets(selected, name=set_name)
                     cmds.confirmDialog(title="Create Set", 
                                      message=f"Created set '{set_name}' with {len(selected)} objects")
                 else:
                     cmds.warning("Please enter a valid set name")
             
         except Exception as e:
             cmds.error(f"Error creating set: {str(e)}")
    
    def run_sets_remove_tool(self):
         """Remove selected objects from sets"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to remove from sets")
                 return
             
             # Get all sets
             all_sets = cmds.ls(type='objectSet')
             removed_count = 0
             
             for obj in selected:
                 for set_name in all_sets:
                     if cmds.sets(obj, isMember=set_name):
                         cmds.sets(obj, remove=set_name)
                         removed_count += 1
             
             if removed_count > 0:
                 cmds.confirmDialog(title="Remove from Sets", 
                                  message=f"Removed {removed_count} object-set relationships")
             else:
                 cmds.warning("Selected objects are not members of any sets")
             
         except Exception as e:
             cmds.error(f"Error removing objects from sets: {str(e)}")

    # ==================== RG TOOLS CONVERSION ====================
    
    def run_override_color_tool(self, color_index):
         """Set override color for selected objects"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to set color")
                 return
             
             for obj in selected:
                 cmds.setAttr(f"{obj}.overrideEnabled", 1)
                 cmds.setAttr(f"{obj}.overrideColor", color_index)
             
             cmds.confirmDialog(title="Color Set", 
                              message=f"Set color {color_index} for {len(selected)} objects")
             
         except Exception as e:
             cmds.error(f"Error setting color: {str(e)}")
    
    def run_create_controller_tool(self, controller_type):
         """Create a controller of specified type"""
         try:
             selected = cmds.ls(selection=True)
             
             if selected:
                 # Create controller and replace shape of selected objects
                 controller_curve = self._create_controller_curve(controller_type)
                 if controller_curve:
                     cmds.select(selected)
                     cmds.select(controller_curve, add=True)
                     self._replace_shapes()
                     cmds.delete(controller_curve)
                     cmds.select(selected)
             else:
                 # Create standalone controller
                 controller_curve = self._create_controller_curve(controller_type)
                 if controller_curve:
                     cmds.select(controller_curve)
             
         except Exception as e:
             cmds.error(f"Error creating controller: {str(e)}")
    
    def _create_controller_curve(self, controller_type):
         """Create a controller curve based on type"""
         try:
             if controller_type == "Triangle":
                 return cmds.curve(degree=1, 
                     point=[(-1.03923, 0, 0.6), (1.03923, 0, 0.6), (0, 0, -1.2), (-1.03923, 0, 0.6)],
                     knot=[0, 1, 2, 3], name="Triangle")
             
             elif controller_type == "Circle":
                 return cmds.circle(center=(0, 0, 0), normal=(0, 1, 0), sweep=360, radius=1, 
                     degree=3, sections=8, constructionHistory=False, name="Circle")[0]
             
             elif controller_type == "Square":
                 return cmds.curve(degree=1,
                     point=[(1, 0, -1), (-1, 0, -1), (-1, 0, 1), (1, 0, 1), (1, 0, -1)],
                     knot=[0, 1, 2, 3, 4], name="Square")
             
             elif controller_type == "FatCross":
                 return cmds.curve(degree=1,
                     point=[(2, 0, 1), (2, 0, -1), (1, 0, -1), (1, 0, -2), (-1, 0, -2), 
                            (-1, 0, -1), (-2, 0, -1), (-2, 0, 1), (-1, 0, 1), (-1, 0, 2), 
                            (1, 0, 2), (1, 0, 1), (2, 0, 1)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], name="FatCross")
             
             elif controller_type == "Pyramid":
                 return cmds.curve(degree=1,
                     point=[(0, 2, 0), (1, 0, -1), (-1, 0, -1), (0, 2, 0), (-1, 0, 1), 
                            (1, 0, 1), (0, 2, 0), (1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -1)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], name="Pyramid")
             
             elif controller_type == "Cube":
                 return cmds.curve(degree=1,
                     point=[(0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5),
                            (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5),
                            (0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5),
                            (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], name="Cube")
             
             elif controller_type == "Sphere":
                 # Simplified sphere curve
                 return cmds.circle(center=(0, 0, 0), normal=(0, 1, 0), sweep=360, radius=1, 
                     degree=3, sections=12, constructionHistory=False, name="Sphere")[0]
             
             elif controller_type == "Cone":
                 return cmds.curve(degree=1,
                     point=[(0.5, -1, 0.866025), (-0.5, -1, 0.866025), (0, 1, 0), (0.5, -1, 0.866025),
                            (1, -1, 0), (0, 1, 0), (0.5, -1, -0.866025), (1, -1, 0), (0, 1, 0),
                            (-0.5, -1, -0.866026), (0.5, -1, -0.866025), (0, 1, 0), (-1, -1, -1.5885e-007),
                            (-0.5, -1, -0.866026), (0, 1, 0), (-0.5, -1, 0.866025), (-1, -1, -1.5885e-007)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], name="Cone")
             
             elif controller_type == "Rombus":
                 return cmds.curve(degree=1,
                     point=[(0, 1, 0), (1, 0, 0), (0, 0, 1), (-1, 0, 0), (0, 0, -1), (0, 1, 0),
                            (0, 0, 1), (0, -1, 0), (0, 0, -1), (1, 0, 0), (0, 1, 0), (-1, 0, 0),
                            (0, -1, 0), (1, 0, 0)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], name="Rombus")
             
             elif controller_type == "SingleNormal":
                 return cmds.curve(degree=1,
                     point=[(0, 0, -1.32), (-0.99, 0, 0), (-0.33, 0, 0), (-0.33, 0, 0.99),
                            (0.33, 0, 0.99), (0.33, 0, 0), (0.99, 0, 0), (0, 0, -1.32)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7], name="SingleNormal")
             
             elif controller_type == "FourNormal":
                 return cmds.curve(degree=1,
                     point=[(0, 0, -1.98), (-0.495, 0, -1.32), (-0.165, 0, -1.32), (-0.165, 0, -0.165),
                            (-1.32, 0, -0.165), (-1.32, 0, -0.495), (-1.98, 0, 0), (-1.32, 0, 0.495),
                            (-1.32, 0, 0.165), (-0.165, 0, 0.165), (-0.165, 0, 1.32), (-0.495, 0, 1.32),
                            (0, 0, 1.98), (0.495, 0, 1.32), (0.165, 0, 1.32), (0.165, 0, 0.165),
                            (1.32, 0, 0.165), (1.32, 0, 0.495), (1.98, 0, 0), (1.32, 0, -0.495),
                            (1.32, 0, -0.165), (0.165, 0, -0.165), (0.165, 0, -1.32), (0.495, 0, -1.32),
                            (0, 0, -1.98)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24], name="FourNormal")
             
             elif controller_type == "Dumbell":
                 return cmds.curve(degree=1,
                     point=[(-1.207536, 0, 0.0254483), (-1.123549, -0.202763, 0.0254483), (-0.920786, -0.28675, 0.0254483),
                            (-0.718023, -0.202763, 0.0254483), (-0.63504, -0.00242492, 0.0254483), (0.634091, 0, 0.0254483),
                            (0.718023, -0.202763, 0.0254483), (0.920786, -0.28675, 0.0254483), (1.123549, -0.202763, 0.0254483),
                            (1.207536, 0, 0.0254483), (1.123549, 0.202763, 0.0254483), (0.920786, 0.28675, 0.0254483),
                            (0.718023, 0.202763, 0.0254483), (0.634091, 0, 0.0254483), (-0.63504, -0.00242492, 0.0254483),
                            (-0.718023, 0.202763, 0.0254483), (-0.920786, 0.28675, 0.0254483), (-1.123549, 0.202763, 0.0254483),
                            (-1.207536, 0, 0.0254483)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18], name="Dumbell")
             
             elif controller_type == "ArrowOnBall":
                 return cmds.curve(degree=1,
                     point=[(0, 0.35, -1.001567), (-0.336638, 0.677886, -0.751175), (-0.0959835, 0.677886, -0.751175),
                            (-0.0959835, 0.850458, -0.500783), (-0.0959835, 0.954001, -0.0987656), (-0.500783, 0.850458, -0.0987656),
                            (-0.751175, 0.677886, -0.0987656), (-0.751175, 0.677886, -0.336638), (-1.001567, 0.35, 0),
                            (-0.751175, 0.677886, 0.336638), (-0.751175, 0.677886, 0.0987656), (-0.500783, 0.850458, 0.0987656),
                            (-0.0959835, 0.954001, 0.0987656), (-0.0959835, 0.850458, 0.500783), (-0.0959835, 0.677886, 0.751175),
                            (-0.336638, 0.677886, 0.751175), (0, 0.35, 1.001567), (0.336638, 0.677886, 0.751175),
                            (0.0959835, 0.677886, 0.751175), (0.0959835, 0.850458, 0.500783), (0.0959835, 0.954001, 0.0987656),
                            (0.500783, 0.850458, 0.0987656), (0.751175, 0.677886, 0.0987656), (0.751175, 0.677886, 0.336638),
                            (1.001567, 0.35, 0), (0.751175, 0.677886, -0.336638), (0.751175, 0.677886, -0.0987656),
                            (0.500783, 0.850458, -0.0987656), (0.0959835, 0.954001, -0.0987656), (0.0959835, 0.850458, -0.500783),
                            (0.0959835, 0.677886, -0.751175), (0.336638, 0.677886, -0.751175), (0, 0.35, -1.001567)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32], name="ArrowOnBall")
             
             elif controller_type == "Pin":
                 return cmds.curve(degree=1,
                     point=[(0, 0, 0), (0, 1.503334, 0), (-0.079367, 1.511676, 0), (-0.155265, 1.536337, 0),
                            (-0.224378, 1.576239, 0), (-0.283684, 1.629638, 0), (-0.330592, 1.694201, 0),
                            (-0.363051, 1.767106, 0), (-0.379643, 1.845166, 0), (-0.379643, 1.924971, 0),
                            (-0.363051, 2.003031, 0), (-0.330592, 2.075936, 0), (-0.283684, 2.140499, 0),
                            (-0.224378, 2.193898, 0), (-0.155265, 2.2338, 0), (-0.079367, 2.258461, 0),
                            (0, 2.266803, 0), (0.079367, 2.258461, 0), (0.155265, 2.2338, 0),
                            (0.224378, 2.193898, 0), (0.283684, 2.140499, 0), (0.330592, 2.075936, 0),
                            (0.363051, 2.003031, 0), (0.379643, 1.924971, 0), (0.379643, 1.845166, 0),
                            (0.363051, 1.767106, 0), (0.330592, 1.694201, 0), (0.283684, 1.629638, 0),
                            (0.224378, 1.576239, 0), (0.155265, 1.536337, 0), (0.079367, 1.511676, 0),
                            (0, 1.503334, 0)],
                     knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31], name="Pin")
             
             else:
                 cmds.warning(f"Unknown controller type: {controller_type}")
                 return None
                 
         except Exception as e:
             cmds.error(f"Error creating controller curve: {str(e)}")
             return None
    
    def _replace_shapes(self):
         """Replace shapes of selected objects with source object shape"""
         try:
             selected = cmds.ls(selection=True)
             if len(selected) < 2:
                 cmds.warning("Select target objects first, then source object")
                 return
             
             # Last selected object is the source
             source_obj = selected[-1]
             target_objs = selected[:-1]
             
             # Create temporary group with source shape
             temp_group = cmds.group(empty=True, name=f"TempGrp_{source_obj}")
             source_shapes = cmds.listRelatives(source_obj, shapes=True, fullPath=True)
             if source_shapes:
                 cmds.parent(source_shapes[0], temp_group, shape=True, add=True)
             
             # Replace each target object's shape
             for target_obj in target_objs:
                 # Duplicate the temp group
                 duplicated = cmds.duplicate(temp_group, renameChildren=True)
                 new_shape = cmds.listRelatives(duplicated[0], shapes=True, fullPath=True)
                 
                 if new_shape:
                     # Parent new shape to target object
                     cmds.parent(new_shape[0], target_obj, shape=True, add=True)
                     
                     # Delete old shapes
                     old_shapes = cmds.listRelatives(target_obj, shapes=True, fullPath=True)
                     for old_shape in old_shapes[:-1]:  # Keep the new shape
                         if cmds.objExists(old_shape):
                             cmds.delete(old_shape)
                     
                     # Rename the new shape
                     cmds.rename(new_shape[0], f"{target_obj}Shape")
                 
                 # Clean up duplicate
                 cmds.delete(duplicated)
             
             # Clean up temp group
             cmds.delete(temp_group)
             
         except Exception as e:
             cmds.error(f"Error replacing shapes: {str(e)}")
    
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
         """Create joints along selected curves using Maya API 2.0 for accurate length-based positioning"""
         try:
             # Import Maya API 2.0
             import maya.api.OpenMaya as om
             
             selected = cmds.ls(selection=True, long=True)
             if not selected:
                 cmds.warning("Please select one or more NURBS curves")
                 return
             
             # Create custom dialog for number of joints
             from PySide2 import QtWidgets, QtCore
             from maya import OpenMayaUI as omui
             from shiboken2 import wrapInstance
             
             # Get Maya main window
             ptr = omui.MQtUtil.mainWindow()
             maya_window = wrapInstance(int(ptr), QtWidgets.QWidget)
             
             # Create custom dialog
             dialog = QtWidgets.QDialog(maya_window)
             dialog.setWindowTitle("Joints on Curve (by length)")
             dialog.setFixedSize(300, 120)
             dialog.setModal(True)
             
             # Layout
             layout = QtWidgets.QVBoxLayout(dialog)
             
             # Number of joints input
             row = QtWidgets.QHBoxLayout()
             row.addWidget(QtWidgets.QLabel("Number of joints:"))
             spin = QtWidgets.QSpinBox()
             spin.setRange(2, 200)
             spin.setValue(6)
             row.addWidget(spin)
             layout.addLayout(row)
             
             # Buttons
             btn_row = QtWidgets.QHBoxLayout()
             create_btn = QtWidgets.QPushButton("Create Joints")
             cancel_btn = QtWidgets.QPushButton("Cancel")
             btn_row.addWidget(create_btn)
             btn_row.addWidget(cancel_btn)
             layout.addLayout(btn_row)
             
             # Connect buttons
             create_btn.clicked.connect(dialog.accept)
             cancel_btn.clicked.connect(dialog.reject)
             
             # Set focus to spin box
             spin.setFocus()
             spin.selectAll()
             
             # Show dialog
             if dialog.exec_() == QtWidgets.QDialog.Accepted:
                 num_joints = spin.value()
             else:
                 return
             
             created_joints = []
             
             for node in selected:
                 # Get the shape node
                 shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
                 if shapes:
                     shape = shapes[0]
                 else:
                     if cmds.nodeType(node) == "nurbsCurve":
                         shape = node
                     else:
                         cmds.warning(f"Selection '{node}' is not a NURBS curve.")
                         continue
                 
                 if cmds.nodeType(shape) != "nurbsCurve":
                     cmds.warning(f"Selection '{node}' is not a NURBS curve.")
                     continue
                 
                 try:
                     # Use Maya API 2.0 for accurate curve operations
                     selList = om.MSelectionList()
                     selList.add(shape)
                     dagPath = selList.getDagPath(0)
                     fnCurve = om.MFnNurbsCurve(dagPath)
                     
                     curve_length = fnCurve.length()
                     
                     # Check if curve is closed
                     form = fnCurve.form
                     is_closed = (form == om.MFnNurbsCurve.kClosed or
                                  form == om.MFnNurbsCurve.kPeriodic)
                     denom = float(num_joints) if is_closed else float(num_joints - 1)
                     
                     # Calculate positions along curve
                     positions = []
                     for i in range(num_joints):
                         dist = (curve_length / denom) * i
                         param = fnCurve.findParamFromLength(dist)
                         pt = fnCurve.getPointAtParam(param, om.MSpace.kWorld)
                         positions.append([pt.x, pt.y, pt.z])
                     
                 except Exception as e:
                     cmds.warning(f"Failed to read curve '{node}' with OpenMaya: {str(e)}")
                     continue
                 
                 if not positions:
                     cmds.warning(f"No sample positions computed for curve '{node}'.")
                     continue
                 
                 # Create joints in a chain
                 created = []
                 cmds.select(clear=True)
                 
                 # Create first joint
                 joint_name = f"{node}_jnt_01"
                 j0 = cmds.joint(position=positions[0], name=joint_name)
                 created.append(j0)
                 created_joints.append(j0)
                 
                 # Create remaining joints in chain
                 for idx, pos in enumerate(positions[1:], start=2):
                     cmds.select(created[-1])
                     joint_name = f"{node}_jnt_{idx:02d}"
                     j = cmds.joint(position=pos, name=joint_name)
                     created.append(j)
                     created_joints.append(j)
                 
                 # Orient the joint chain properly
                 try:
                     # Select the root joint of the chain
                     cmds.select(created[0], replace=True)
                     
                     # Use joint command to orient the entire chain
                     cmds.joint(created[0], edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
                         
                 except Exception as e:
                     cmds.warning(f"Joint orient failed for curve '{node}': {str(e)}")
             
             # Select all created joints and show confirmation
             if created_joints:
                 cmds.select(created_joints)
                 cmds.inViewMessage(amg=f"<hl>{len(created_joints)}</hl> joints created",
                                    pos="midCenter", fade=True)
             else:
                 cmds.warning("No joints were created.")
             
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
              
              # Create custom dialog for number of joints
              from PySide2 import QtWidgets, QtCore
              from maya import OpenMayaUI as omui
              from shiboken2 import wrapInstance
              
              # Get Maya main window
              ptr = omui.MQtUtil.mainWindow()
              maya_window = wrapInstance(int(ptr), QtWidgets.QWidget)
              
              # Create custom dialog
              dialog = QtWidgets.QDialog(maya_window)
              dialog.setWindowTitle("Inbetween Joints")
              dialog.setFixedSize(300, 120)
              dialog.setModal(True)
              
              # Layout
              layout = QtWidgets.QVBoxLayout(dialog)
              
              # Number of joints input
              row = QtWidgets.QHBoxLayout()
              row.addWidget(QtWidgets.QLabel("Number of joints:"))
              spin = QtWidgets.QSpinBox()
              spin.setRange(1, 50)
              spin.setValue(3)
              row.addWidget(spin)
              layout.addLayout(row)
              
              # Buttons
              btn_row = QtWidgets.QHBoxLayout()
              create_btn = QtWidgets.QPushButton("Create Joints")
              cancel_btn = QtWidgets.QPushButton("Cancel")
              btn_row.addWidget(create_btn)
              btn_row.addWidget(cancel_btn)
              layout.addLayout(btn_row)
              
              # Connect buttons
              create_btn.clicked.connect(dialog.accept)
              cancel_btn.clicked.connect(dialog.reject)
              
              # Set focus to spin box
              spin.setFocus()
              spin.selectAll()
              
              # Show dialog
              if dialog.exec_() == QtWidgets.QDialog.Accepted:
                  num_joints = spin.value()
              else:
                  return
              
              # Get positions of the two joints
              pos1 = cmds.xform(joint1, query=True, worldSpace=True, translation=True)
              pos2 = cmds.xform(joint2, query=True, worldSpace=True, translation=True)
              
              # Calculate positions for inbetween joints
              created_joints = []
              for i in range(1, num_joints + 1):
                  # Calculate interpolation factor (0 to 1)
                  factor = i / (num_joints + 1)
                  
                  # Interpolate position
                  x = pos1[0] + (pos2[0] - pos1[0]) * factor
                  y = pos1[1] + (pos2[1] - pos1[1]) * factor
                  z = pos1[2] + (pos2[2] - pos1[2]) * factor
                  
                  # Create joint
                  joint_name = f"inbetween_jnt_{i:02d}"
                  new_joint = cmds.joint(position=(x, y, z), name=joint_name)
                  created_joints.append(new_joint)
              
              # Orient the created joints
              if created_joints:
                  # Select the first inbetween joint and orient the chain
                  cmds.select(created_joints[0], replace=True)
                  cmds.joint(created_joints[0], edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
              
              # Select all created joints and show confirmation
              if created_joints:
                  cmds.select(created_joints)
                  cmds.inViewMessage(amg=f"<hl>{len(created_joints)}</hl> inbetween joints created",
                                     pos="midCenter", fade=True)
              else:
                  cmds.warning("No joints were created.")
              
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
    
    def run_reskin_tool(self):
         """Reskin selected objects"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select skinned objects to reskin")
                 return
             
             for obj in selected:
                 # Find skin cluster
                 skin_cluster = cmds.findRelatedSkinCluster(obj)
                 
                 if skin_cluster:
                     # Get skin cluster info
                     shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
                     influences = cmds.skinCluster(skin_cluster, query=True, influence=True)
                     
                     if shapes and influences:
                         # Unbind skin
                         cmds.skinCluster(skin_cluster, edit=True, unbind=True)
                         
                         # Delete bind pose
                         cmds.delete("*bindPose*")
                         
                         # Rebind skin
                         cmds.skinCluster(influences, shapes[0], name=skin_cluster)
                 else:
                     cmds.warning(f"No skin cluster found for {obj}")
             
             cmds.confirmDialog(title="Reskin", 
                              message=f"Reskinned {len(selected)} objects")
             
         except Exception as e:
             cmds.error(f"Error reskinning objects: {str(e)}")
    
    def run_orient_joint_tool(self, orientation_type):
         """Orient joints based on specified type"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select joints to orient")
                 return
             
             for joint in selected:
                 if cmds.objectType(joint, isType="joint"):
                     children = cmds.listRelatives(joint, children=True)
                     
                     if children:
                         # Orient with children
                         if orientation_type == "YUP":
                             cmds.joint(joint, edit=True, orientJoint="xyz", secondaryAxisOrient="yup")
                         elif orientation_type == "YDN":
                             cmds.joint(joint, edit=True, orientJoint="xyz", secondaryAxisOrient="ydown")
                         elif orientation_type == "ZUP":
                             cmds.joint(joint, edit=True, orientJoint="xzy", secondaryAxisOrient="yup")
                         elif orientation_type == "ZDN":
                             cmds.joint(joint, edit=True, orientJoint="xzy", secondaryAxisOrient="ydown")
                         elif orientation_type == "NONE":
                             cmds.joint(joint, edit=True, orientJoint="none")
                     else:
                         # Orient without children
                         if orientation_type == "NONE":
                             cmds.joint(joint, edit=True, orientJoint="none")
             
             cmds.confirmDialog(title="Joint Orientation", 
                              message=f"Oriented {len(selected)} joints")
             
         except Exception as e:
             cmds.error(f"Error orienting joints: {str(e)}")
    
    def run_add_attribute_tool(self, attr_type):
         """Add custom attributes to selected objects"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to add attributes to")
                 return
             
             for obj in selected:
                 if attr_type == "enum":
                     cmds.addAttr(obj, longName="TYPE_ATTRIBUTES_NAME", attributeType="enum", 
                                 enumName="Off:On:", keyable=False, channelBox=True)
                 elif attr_type == "floatA":
                     cmds.addAttr(obj, longName="TYPE_ATTRIBUTES_NAME", attributeType="double", 
                                 minValue=0, maxValue=1, defaultValue=0, keyable=True)
                 elif attr_type == "floatB":
                     cmds.addAttr(obj, longName="TYPE_ATTRIBUTES_NAME", attributeType="double", 
                                 minValue=0, maxValue=10, defaultValue=0, keyable=True)
                 elif attr_type == "floatC":
                     cmds.addAttr(obj, longName="TYPE_ATTRIBUTES_NAME", attributeType="double", 
                                 minValue=-10, maxValue=10, defaultValue=0, keyable=True)
                 elif attr_type == "floatD":
                     cmds.addAttr(obj, longName="TYPE_ATTRIBUTES_NAME", attributeType="double", 
                                 keyable=True)
             
             cmds.confirmDialog(title="Add Attribute", 
                              message=f"Added {attr_type} attribute to {len(selected)} objects")
             
         except Exception as e:
             cmds.error(f"Error adding attributes: {str(e)}")
    
    def run_lock_hide_attributes_tool(self, action_type):
         """Lock or hide attributes"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to modify attributes")
                 return
             
             for obj in selected:
                 if action_type == "lock":
                     # Lock all transform attributes
                     cmds.setAttr(f"{obj}.tx", lock=True)
                     cmds.setAttr(f"{obj}.ty", lock=True)
                     cmds.setAttr(f"{obj}.tz", lock=True)
                     cmds.setAttr(f"{obj}.rx", lock=True)
                     cmds.setAttr(f"{obj}.ry", lock=True)
                     cmds.setAttr(f"{obj}.rz", lock=True)
                     cmds.setAttr(f"{obj}.sx", lock=True)
                     cmds.setAttr(f"{obj}.sy", lock=True)
                     cmds.setAttr(f"{obj}.sz", lock=True)
                     cmds.setAttr(f"{obj}.v", lock=True)
                 
                 elif action_type == "unlock":
                     # Unlock all transform attributes
                     cmds.setAttr(f"{obj}.tx", lock=False)
                     cmds.setAttr(f"{obj}.ty", lock=False)
                     cmds.setAttr(f"{obj}.tz", lock=False)
                     cmds.setAttr(f"{obj}.rx", lock=False)
                     cmds.setAttr(f"{obj}.ry", lock=False)
                     cmds.setAttr(f"{obj}.rz", lock=False)
                     cmds.setAttr(f"{obj}.sx", lock=False)
                     cmds.setAttr(f"{obj}.sy", lock=False)
                     cmds.setAttr(f"{obj}.sz", lock=False)
                     cmds.setAttr(f"{obj}.v", lock=False)
                 
                 elif action_type == "hide":
                     # Hide all transform attributes
                     cmds.setAttr(f"{obj}.tx", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.ty", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.tz", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.rx", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.ry", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.rz", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.sx", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.sy", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.sz", keyable=False, channelBox=False)
                     cmds.setAttr(f"{obj}.v", keyable=False, channelBox=False)
                 
                 elif action_type == "unhide":
                     # Show all transform attributes
                     cmds.setAttr(f"{obj}.tx", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.ty", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.tz", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.rx", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.ry", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.rz", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.sx", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.sy", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.sz", keyable=True, channelBox=True)
                     cmds.setAttr(f"{obj}.v", keyable=True, channelBox=True)
             
             cmds.confirmDialog(title="Attribute Modification", 
                              message=f"Modified attributes for {len(selected)} objects")
             
         except Exception as e:
             cmds.error(f"Error modifying attributes: {str(e)}")
    
    def run_create_sets_tool(self, set_type):
         """Create different types of sets"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to add to set")
                 return
             
             if set_type == "anim":
                 set_name = "AnimSet"
                 cmds.sets(selected, name=set_name)
             elif set_type == "render":
                 set_name = "RenderSet"
                 cmds.sets(selected, name=set_name)
             elif set_type == "cache":
                 set_name = "CacheSet"
                 cmds.sets(selected, name=set_name)
             
             cmds.confirmDialog(title="Create Set", 
                              message=f"Created {set_name} with {len(selected)} objects")
             
         except Exception as e:
             cmds.error(f"Error creating set: {str(e)}")
    
    def run_add_to_sets_tool(self, set_type):
         """Add selected objects to existing sets"""
         try:
             selected = cmds.ls(selection=True)
             if not selected:
                 cmds.warning("Please select objects to add to set")
                 return
             
             if set_type == "anim":
                 set_name = "AnimSet"
             elif set_type == "render":
                 set_name = "RenderSet"
             elif set_type == "cache":
                 set_name = "CacheSet"
             
             if cmds.objExists(set_name):
                 cmds.sets(selected, add=set_name)
                 cmds.confirmDialog(title="Add to Set", 
                                  message=f"Added {len(selected)} objects to {set_name}")
             else:
                 cmds.warning(f"Set '{set_name}' does not exist. Create it first.")
             
         except Exception as e:
             cmds.error(f"Error adding to set: {str(e)}")


def main():
    """Main function to run the tool"""
    tool = RigXUtilityTools()
    tool.show_ui()


if __name__ == "__main__":
    main()
