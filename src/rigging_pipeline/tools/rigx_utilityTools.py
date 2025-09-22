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


# Global UI manager to track open windows
class UIManager:
    """Global UI manager to prevent multiple instances of the same tool"""
    
    _open_windows = {}
    
    @classmethod
    def close_existing_window(cls, window_name):
        """Close existing window if it exists"""
        try:
            if window_name in cls._open_windows:
                window = cls._open_windows[window_name]
                if window and hasattr(window, 'isVisible') and window.isVisible():
                    window.close()
                    window.deleteLater()
                del cls._open_windows[window_name]
        except Exception as e:
            # If there's any error, just remove the key and continue
            if window_name in cls._open_windows:
                del cls._open_windows[window_name]
            print(f"Warning: Error closing window {window_name}: {e}")
    
    @classmethod
    def register_window(cls, window_name, window_instance):
        """Register a new window instance"""
        try:
            cls._open_windows[window_name] = window_instance
        except Exception as e:
            print(f"Warning: Error registering window {window_name}: {e}")
    
    @classmethod
    def is_window_open(cls, window_name):
        """Check if a window is currently open"""
        try:
            if window_name in cls._open_windows:
                window = cls._open_windows[window_name]
                return window and hasattr(window, 'isVisible') and window.isVisible()
            return False
        except Exception as e:
            # If there's any error, assume window is not open
            if window_name in cls._open_windows:
                del cls._open_windows[window_name]
            return False


class RigXUtilityTools:
    """Main class for RigX Utility Tools functionality - Enhanced with RG Tools"""
    
    def __init__(self):
         self.ui = None
         
    def show_ui(self):
         """Show the RigX Utility Tools UI - closes existing instance first"""
         # Close existing window if it exists
         UIManager.close_existing_window("RigXUtilityTools")
         
         # Create new UI instance
         self.ui = RigXUtilityToolsUI()
         
         # Register the window
         UIManager.register_window("RigXUtilityTools", self.ui)
         
         # Show the window
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
        """Create joints at the center of selected objects or components"""
        try:
            sel = cmds.ls(selection=True, flatten=True)
            
            if not sel:
                cmds.warning("Nothing selected.")
                return
            
            pos = None
            
            # If it's a component (vertex/edge/face)
            if "." in sel[0]:
                pos = cmds.xform(sel, q=True, ws=True, t=True)
                x = sum(pos[0::3]) / (len(pos) // 3)
                y = sum(pos[1::3]) / (len(pos) // 3)
                z = sum(pos[2::3]) / (len(pos) // 3)
                pos = [x, y, z]
            
            else:
                # Object pivot
                pos = cmds.xform(sel[0], q=True, ws=True, rp=True)
            
            # Create joint
            jnt = cmds.joint(position=pos)
            
            # Unparent so it stays at world level
            cmds.parent(jnt, world=True)
            
            cmds.select(jnt)
            print("Joint created at:", pos)
            
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
    
    def run_joint_to_curve_tool(self, joints=None, degree=None, curve_type='CV'):
        """Create a curve through the selected joint chain or from a single selected joint's chain.

        Args:
            joints (list[str] | None): Joint names to use. If None, uses current Maya joint selection.
            degree (int | None): Curve degree (1, 2 or 3). If None, auto-choose based on points.
            curve_type (str): 'CV' (default) or 'EP' to create CV or EP curve.
        """
        try:
            if not MAYA_AVAILABLE:
                cmds.warning("Maya is not available.")
                return
            
            selection = joints if joints else (cmds.ls(selection=True, type='joint') or [])
            if not selection:
                cmds.warning("Please select one or more joints")
                return
            
            def _ordered_chain_from_single_root(root_joint):
                ordered = [root_joint]
                current = root_joint
                while True:
                    children = cmds.listRelatives(current, children=True, type='joint') or []
                    if not children:
                        break
                    if len(children) > 1:
                        cmds.warning(f"Joint '{current}' has multiple child joints; select the desired chain joints explicitly to control ordering.")
                        break
                    ordered.append(children[0])
                    current = children[0]
                return ordered
            
            def _ordered_chain_from_selection(sel_joints):
                sel_set = set(sel_joints)
                root_candidates = []
                for j in sel_joints:
                    parent = cmds.listRelatives(j, parent=True, type='joint') or []
                    if not parent or parent[0] not in sel_set:
                        root_candidates.append(j)
                start = root_candidates[0] if root_candidates else sel_joints[0]
                ordered = [start]
                used = {start}
                current = start
                while True:
                    children = cmds.listRelatives(current, children=True, type='joint') or []
                    next_in_chain = None
                    for c in children:
                        if c in sel_set and c not in used:
                            next_in_chain = c
                            break
                    if not next_in_chain:
                        break
                    ordered.append(next_in_chain)
                    used.add(next_in_chain)
                    current = next_in_chain
                if len(used) != len(sel_set):
                    remaining = [j for j in sel_joints if j not in used]
                    def _pos(j):
                        p = cmds.xform(j, q=True, ws=True, t=True)
                        return p[0], p[1], p[2]
                    from math import sqrt
                    def _dist(a, b):
                        return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)
                    while remaining:
                        last_pos = _pos(ordered[-1])
                        remaining.sort(key=lambda j: _dist(_pos(j), last_pos))
                        ordered.append(remaining.pop(0))
                return ordered
            
            if len(selection) == 1:
                joints = _ordered_chain_from_single_root(selection[0])
            else:
                joints = _ordered_chain_from_selection(selection)
            
            if not joints or len(joints) < 2:
                cmds.warning("Need at least two joints to create a curve")
                return
            
            positions = []
            for j in joints:
                pos = cmds.xform(j, q=True, ws=True, t=True)
                if not pos or len(pos) < 3:
                    cmds.warning(f"Failed to query position for joint '{j}'")
                    continue
                positions.append((pos[0], pos[1], pos[2]))
            
            if len(positions) < 2:
                cmds.warning("Not enough valid joint positions to create a curve")
                return
            
            # Use provided degree if valid, else infer from points
            if degree not in (1, 2, 3):
                degree = 3 if len(positions) >= 4 else (2 if len(positions) >= 3 else 1)
            # Clamp degree to allowed by number of points
            max_allowed = max(1, len(positions) - 1)
            degree = min(degree, max_allowed)
            # Compute next available name 'curve_01', 'curve_02', ...
            def _next_curve_name(prefix="curve_", padding=2):
                index = 1
                while True:
                    candidate = f"{prefix}{index:0{padding}d}"
                    if not cmds.objExists(candidate):
                        return candidate
                    index += 1
            curve_name = _next_curve_name()
            try:
                if str(curve_type).upper() == 'EP':
                    curve = cmds.curve(ep=positions, d=degree, name=curve_name)
                else:
                    curve = cmds.curve(p=positions, d=degree, name=curve_name)
            except Exception as exc:
                cmds.error(f"Failed to create curve: {exc}")
                return
            
            cmds.select(curve, r=True)
            try:
                # Visually distinguish CV vs EP by toggling CV display
                shape = (cmds.listRelatives(curve, shapes=True, fullPath=True) or [None])[0]
                if shape and cmds.objExists(shape + ".dispCV"):
                    cmds.setAttr(shape + ".dispCV", 1 if str(curve_type).upper() == 'CV' else 0)
            except Exception:
                pass
            try:
                cmds.inViewMessage(amg=f"<hl>Curve</hl> created from {len(positions)} joint(s)", pos="midCenter", fade=True)
            except Exception:
                pass
        except Exception as e:
            cmds.error(f"Error creating curve from joints: {str(e)}")
    
    def run_inbetween_joints_tool(self):
        """Create in-between joints between two selected joints"""
        try:
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
            
            # Use the improved inbetween joints function
            self.create_inbetween_joints(num_joints)
            
        except Exception as e:
            cmds.error(f"Error in inbetween joints tool: {str(e)}")
    
    def create_inbetween_joints(self, num_joints=1):
        """
        Create in-between joints between two selected joints.
        - If joint2 is a child of joint1 -> insert in-betweens in the chain.
        - Otherwise -> create floating in-betweens.
        - In-betweens inherit orientation from their parent (if parented).
        """
        sel = cmds.ls(sl=True, type="joint")
        if len(sel) != 2:
            cmds.warning("Please select exactly two joints.")
            return

        jnt1, jnt2 = sel
        pos1 = cmds.xform(jnt1, q=True, ws=True, t=True)
        pos2 = cmds.xform(jnt2, q=True, ws=True, t=True)

        # Calculate step vector
        step = [(p2 - p1) / (num_joints + 1) for p1, p2 in zip(pos1, pos2)]

        inbetween_joints = []
        for i in range(num_joints):
            # Position for new joint
            new_pos = [p1 + step_val * (i + 1) for p1, step_val in zip(pos1, step)]

            # Clear selection before creation
            cmds.select(clear=True)

            # Create joint
            new_jnt = cmds.joint(name=f"{jnt1}_inbetween_{i+1}_jnt")

            # Snap to position
            cmds.xform(new_jnt, ws=True, t=new_pos)

            # Copy orientation from jnt1 (or latest parent)
            if i == 0:
                parent = jnt1
            else:
                parent = inbetween_joints[i - 1]

            orient = cmds.getAttr(parent + ".jointOrient")[0]
            cmds.setAttr(new_jnt + ".jointOrientX", orient[0])
            cmds.setAttr(new_jnt + ".jointOrientY", orient[1])
            cmds.setAttr(new_jnt + ".jointOrientZ", orient[2])

            inbetween_joints.append(new_jnt)

        # -------------------------------
        # Parenting logic
        # -------------------------------
        parented = cmds.listRelatives(jnt2, parent=True) == [jnt1]

        if parented:
            # Chain mode
            cmds.parent(inbetween_joints[0], jnt1)
            for i in range(1, len(inbetween_joints)):
                cmds.parent(inbetween_joints[i], inbetween_joints[i - 1])
            cmds.parent(jnt2, inbetween_joints[-1])
        else:
            cmds.warning("Joints are not in the same chain. Created independent in-between joints.")

        cmds.select(inbetween_joints)
        print(f"Created joints: {inbetween_joints}")
        return inbetween_joints
    
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
    
    # ===== Attribute Manager backend =====
    def list_user_attributes(self, obj):
        try:
            # Exclude standard transform attrs
            std = set(["tx","ty","tz","rx","ry","rz","sx","sy","sz","v","visibility","rotateX","rotateY","rotateZ","translateX","translateY","translateZ","scaleX","scaleY","scaleZ"])            
            all_attrs = cmds.listAttr(obj, userDefined=True) or []
            # Include keyable and channelBox custom attrs too
            cb = cmds.listAttr(obj, keyable=True) or []
            cb += cmds.listAttr(obj, channelBox=True) or []
            cb = [a for a in cb if a not in std]
            # Merge and unique
            merged = sorted(list(set(all_attrs + cb)))
            return merged
        except Exception:
            return []

    def list_hidden_attributes(self, obj):
        """List hidden attributes (not keyable and not shown in channel box), including TRS and user-defined."""
        try:
            # Visible attributes (either keyable or explicitly in channel box)
            visible = set((cmds.listAttr(obj, keyable=True) or []) + (cmds.listAttr(obj, channelBox=True) or []))
            # Standard TRS + visibility (long names)
            standard = [
                "translateX", "translateY", "translateZ",
                "rotateX", "rotateY", "rotateZ",
                "scaleX", "scaleY", "scaleZ",
                "visibility"
            ]
            # User-defined attributes
            user_defined = cmds.listAttr(obj, userDefined=True) or []
            candidates = list(dict.fromkeys(standard + user_defined))
            hidden = [a for a in candidates if a not in visible]
            return hidden
        except Exception:
            return []

    def attribute_manager(self, action, attr_names=None, options=None):
        """Perform attribute actions on selection.
        action: add/remove/lock/unlock/hide/unhide/transfer
        options for add: {type: double|long|bool|enum, enum: 'a:b:c'}
        options for transfer: {source: objA, target: objB}
        """
        try:
            sel = cmds.ls(selection=True) or []
            if action == "transfer":
                if not options or "source" not in options or "target" not in options:
                    cmds.warning("Provide source and target for transfer")
                    return
                if not attr_names:
                    cmds.warning("Provide attribute name to transfer")
                    return
                attr = attr_names[0]
                self._transfer_attribute_with_connections(options["source"], options["target"], attr)
                cmds.inViewMessage(amg=f"<hl>Transferred</hl> {attr}", pos="midCenter", fade=True)
                return

            if not sel:
                cmds.warning("Select object(s)")
                return
            for obj in sel:
                if action == "add":
                    if not options or "type" not in options:
                        continue
                    atype = options["type"]
                    name = (attr_names or ["newAttr"])[0]
                    full = f"{obj}.{name}"
                    if cmds.objExists(full):
                        continue
                    if atype == "enum":
                        enum_def = options.get("enum", "A:B")
                        cmds.addAttr(obj, longName=name, attributeType="enum", enumName=enum_def)
                        cmds.setAttr(full, keyable=False, channelBox=True)
                    elif atype == "bool":
                        cmds.addAttr(obj, longName=name, attributeType="bool")
                        cmds.setAttr(full, keyable=True)
                    elif atype == "long":
                        # Use min/max if provided
                        if "min" in options or "max" in options:
                            minv = options.get("min", -2**31)
                            maxv = options.get("max", 2**31-1)
                            cmds.addAttr(obj, longName=name, attributeType="long", minValue=minv, maxValue=maxv, defaultValue=minv)
                        else:
                            cmds.addAttr(obj, longName=name, attributeType="long")
                        cmds.setAttr(full, keyable=True)
                    else:
                        # double
                        if "min" in options or "max" in options:
                            minv = options.get("min", 0.0)
                            maxv = options.get("max", 1.0)
                            cmds.addAttr(obj, longName=name, attributeType="double", minValue=minv, maxValue=maxv, defaultValue=minv)
                        else:
                            cmds.addAttr(obj, longName=name, attributeType="double")
                        cmds.setAttr(full, keyable=True)
                elif action == "remove":
                    for name in (attr_names or []):
                        full = f"{obj}.{name}"
                        if cmds.objExists(full):
                            # Break connections before delete
                            self._disconnect_all(full)
                            try:
                                cmds.deleteAttr(full)
                            except Exception:
                                pass
                elif action in ["lock","unlock"]:
                    state = (action == "lock")
                    for name in (attr_names or []):
                        full = f"{obj}.{name}"
                        if cmds.objExists(full):
                            try:
                                cmds.setAttr(full, lock=state)
                            except Exception:
                                pass
                elif action in ["hide","unhide"]:
                    for name in (attr_names or []):
                        full = f"{obj}.{name}"
                        if cmds.objExists(full):
                            try:
                                if action == "unhide":
                                    # Ensure attribute is unlocked and keyable (for non-enum). Enums are channelBox-only.
                                    cmds.setAttr(full, lock=False)
                                    atype = cmds.getAttr(full, type=True)
                                    if atype == "enum":
                                        cmds.setAttr(full, keyable=False)
                                        cmds.setAttr(full, channelBox=True)
                                    else:
                                        cmds.setAttr(full, keyable=True)
                                else:
                                    # Hide
                                    cmds.setAttr(full, keyable=False)
                                    cmds.setAttr(full, channelBox=False)
                            except Exception:
                                pass
        except Exception as e:
            cmds.error(f"Attribute manager error: {str(e)}")

    def _disconnect_all(self, plug):
        try:
            src = cmds.listConnections(plug, s=True, d=False, plugs=True) or []
            for s in src:
                try:
                    cmds.disconnectAttr(s, plug)
                except Exception:
                    pass
            dst = cmds.listConnections(plug, s=False, d=True, plugs=True) or []
            for d in dst:
                try:
                    cmds.disconnectAttr(plug, d)
                except Exception:
                    pass
        except Exception:
            pass

    def _transfer_attribute_with_connections(self, source_obj, target_obj, attr):
        """Create the same attribute on target, copy value, and replicate connections."""
        src_plug = f"{source_obj}.{attr}"
        if not cmds.objExists(src_plug):
            cmds.warning(f"Attribute {src_plug} does not exist")
            return
        # Query attribute type and properties
        atype = cmds.getAttr(src_plug, type=True)
        # Create on target if missing
        tgt_plug = f"{target_obj}.{attr}"
        if not cmds.objExists(tgt_plug):
            if atype == "enum":
                enum_names = cmds.addAttr(src_plug, q=True, enumName=True) or "A:B"
                cmds.addAttr(target_obj, longName=attr, attributeType="enum", enumName=enum_names)
                cmds.setAttr(tgt_plug, keyable=False, channelBox=True)
            elif atype in ["double", "doubleLinear", "doubleAngle", "float"]:
                cmds.addAttr(target_obj, longName=attr, attributeType="double")
                cmds.setAttr(tgt_plug, keyable=True)
            elif atype in ["long", "short", "byte"]:
                cmds.addAttr(target_obj, longName=attr, attributeType="long")
                cmds.setAttr(tgt_plug, keyable=True)
            elif atype == "bool":
                cmds.addAttr(target_obj, longName=attr, attributeType="bool")
                cmds.setAttr(tgt_plug, keyable=True)
            else:
                # Fallback to double
                cmds.addAttr(target_obj, longName=attr, attributeType="double")
                cmds.setAttr(tgt_plug, keyable=True)
        # Copy value if settable
        try:
            if not cmds.getAttr(tgt_plug, lock=True):
                val = cmds.getAttr(src_plug)
                # getAttr returns tuple for some types
                if isinstance(val, (list, tuple)):
                    try:
                        cmds.setAttr(tgt_plug, *val[0])
                    except Exception:
                        cmds.setAttr(tgt_plug, val)
                else:
                    cmds.setAttr(tgt_plug, val)
        except Exception:
            pass
        # Replicate incoming connections (source driving -> connect same driver to target)
        drivers = cmds.listConnections(src_plug, s=True, d=False, plugs=True) or []
        for drv in drivers:
            try:
                cmds.connectAttr(drv, tgt_plug, force=True)
            except Exception:
                pass
        # Replicate outgoing connections (source output -> connect target output to same dests)
        dests = cmds.listConnections(src_plug, s=False, d=True, plugs=True) or []
        for dst in dests:
            try:
                cmds.connectAttr(tgt_plug, dst, force=True)
            except Exception:
                pass
        # Finally, remove attribute from source (move semantics)
        try:
            self._disconnect_all(src_plug)
            cmds.deleteAttr(src_plug)
        except Exception:
            pass

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
                    # Show all transform attributes and ensure they are unlocked and keyable
                    for attr in ["tx","ty","tz","rx","ry","rz","sx","sy","sz","v"]:
                        try:
                            cmds.setAttr(f"{obj}.{attr}", lock=False)
                            cmds.setAttr(f"{obj}.{attr}", keyable=True, channelBox=True)
                        except Exception:
                            pass
             
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

    # ==================== RENAME TOOLS ====================
    
    def run_rename_tool(self, action, ui_data=None):
        """Run rename tools based on action"""
        try:
            if action == "sequential":
                self._run_sequential_rename()
            elif action == "prefix":
                self._run_prefix_suffix("prefix")
            elif action == "suffix":
                self._run_prefix_suffix("suffix")
            elif action == "search_replace":
                self._run_search_replace()
            elif action == "sequential_ui":
                self._run_sequential_rename_ui(ui_data)
            elif action == "prefix_ui":
                self._run_prefix_suffix_ui("prefix", ui_data)
            elif action == "suffix_ui":
                self._run_prefix_suffix_ui("suffix", ui_data)
            elif action == "search_replace_ui":
                self._run_search_replace_ui(ui_data)
            elif action == "upper":
                self._run_change_case("upper")
            elif action == "lower":
                self._run_change_case("lower")
            elif action == "title":
                self._run_change_case("title")
            elif action == "camel":
                self._run_change_case("camel")
            elif action == "fix_duplicates":
                self._run_fix_duplicates()
            elif action == "fix_shapes":
                self._run_fix_shape_names()
            elif action == "clear_fields":
                self._clear_rename_fields()
            elif action == "open_tool":
                self._run_open_rename_tool()
            else:
                cmds.warning(f"Unknown rename action: {action}")
        except Exception as e:
            cmds.error(f"Error in rename tool: {str(e)}")
    
    def _run_sequential_rename(self):
        """Run sequential rename with dialog using CometRename logic"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to rename")
                return
            
            # Create dialog for sequential naming
            from PySide2 import QtWidgets, QtCore
            dialog = QtWidgets.QDialog()
            dialog.setWindowTitle("Sequential Rename - CometRename Style")
            dialog.setModal(True)
            dialog.resize(300, 150)
            
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Base name
            layout.addWidget(QtWidgets.QLabel("Base Name:"))
            name_edit = QtWidgets.QLineEdit("object")
            layout.addWidget(name_edit)
            
            # Number settings
            num_layout = QtWidgets.QHBoxLayout()
            num_layout.addWidget(QtWidgets.QLabel("Start #:"))
            start_spin = QtWidgets.QSpinBox()
            start_spin.setRange(0, 9999)
            start_spin.setValue(1)
            num_layout.addWidget(start_spin)
            
            num_layout.addWidget(QtWidgets.QLabel("Padding:"))
            pad_spin = QtWidgets.QSpinBox()
            pad_spin.setRange(0, 10)
            pad_spin.setValue(0)
            num_layout.addWidget(pad_spin)
            layout.addLayout(num_layout)
            
            # Buttons
            btn_layout = QtWidgets.QHBoxLayout()
            ok_btn = QtWidgets.QPushButton("Rename")
            cancel_btn = QtWidgets.QPushButton("Cancel")
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            ok_btn.clicked.connect(dialog.accept)
            cancel_btn.clicked.connect(dialog.reject)
            
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                base_name = name_edit.text().strip()
                start_num = start_spin.value()
                padding = pad_spin.value()
                
                if not base_name:
                    cmds.warning("Please enter a base name")
                    return
                
                # Use CometRename functionality
                from rigging_pipeline.tools.cometRename import comet_rename_number
                comet_rename_number(base_name, start_num, padding)
                print(f"Renamed {len(selected)} objects using CometRename logic")
                
        except Exception as e:
            cmds.error(f"Error in sequential rename: {str(e)}")
    
    def _run_prefix_suffix(self, mode):
        """Add prefix or suffix to selected objects using CometRename logic"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to rename")
                return
            
            result = cmds.promptDialog(
                title=f"Add {mode.title()} - CometRename Style",
                message=f"Enter {mode} to add:",
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel'
            )
            
            if result == 'OK':
                affix = cmds.promptDialog(query=True, text=True)
                if affix:
                    # Use CometRename functionality
                    from rigging_pipeline.tools.cometRename import comet_add_prefix, comet_add_suffix
                    if mode == "prefix":
                        comet_add_prefix(affix)
                    else:
                        comet_add_suffix(affix)
                    print(f"Applied {mode} '{affix}' to {len(selected)} objects using CometRename logic")
                else:
                    cmds.warning(f"Please enter a {mode}")
                    
        except Exception as e:
            cmds.error(f"Error adding {mode}: {str(e)}")
    
    def _run_search_replace(self):
        """Search and replace in object names using CometRename logic"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to rename")
                return
            
            # Get search text
            result = cmds.promptDialog(
                title="Search & Replace - CometRename Style",
                message="Enter search text:",
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel'
            )
            
            if result == 'OK':
                search_text = cmds.promptDialog(query=True, text=True)
                if not search_text:
                    cmds.warning("Please enter search text")
                    return
                
                # Get replace text
                result = cmds.promptDialog(
                    title="Search & Replace - CometRename Style",
                    message="Enter replace text:",
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel'
                )
                
                if result == 'OK':
                    replace_text = cmds.promptDialog(query=True, text=True)
                    
                    # Use CometRename functionality
                    from rigging_pipeline.tools.cometRename import comet_search_replace
                    comet_search_replace(search_text, replace_text)
                    print(f"Replaced '{search_text}' with '{replace_text}' in {len(selected)} objects using CometRename logic")
                    
        except Exception as e:
            cmds.error(f"Error in search and replace: {str(e)}")
    
    def _run_change_case(self, case_type):
        """Change case of object names using CometRename logic"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to rename")
                return
            
            # Use CometRename functionality for consistency
            from rigging_pipeline.tools.cometRename import comet_change_case
            comet_change_case(case_type)
            
        except Exception as e:
            cmds.error(f"Error changing case: {str(e)}")
    
    def _run_fix_duplicates(self):
        """Fix duplicate names in scene"""
        try:
            from rigging_pipeline.utils.rig import utils_name
            utils_name.fix_duplicates()
            print("Fixed duplicate names in scene")
            
        except Exception as e:
            cmds.error(f"Error fixing duplicates: {str(e)}")
    
    def _run_fix_shape_names(self):
        """Fix shape names to match transform names"""
        try:
            from rigging_pipeline.utils.rig import utils_name
            utils_name.fix_shape_names()
            print("Fixed shape names in scene")
            
        except Exception as e:
            cmds.error(f"Error fixing shape names: {str(e)}")
    
    def _run_open_rename_tool(self):
        """Open the full CometRename tool"""
        try:
            from rigging_pipeline.tools.cometRename import launch_comet_rename
            launch_comet_rename()
            
        except Exception as e:
            cmds.error(f"Error opening CometRename tool: {str(e)}")

    # ==================== UI-BASED RENAME METHODS ====================
    
    def _run_sequential_rename_ui(self, ui_data):
        """Run sequential rename using UI field data"""
        try:
            if not ui_data or not ui_data.get('rename_text'):
                cmds.warning("Please enter a base name")
                return
            
            base_name = ui_data['rename_text'].strip()
            start_num = ui_data.get('start_num', 1)
            padding = ui_data.get('padding', 2)
            selection_mode = ui_data.get('selection_mode', 'selected')
            
            # Use CometRename functionality
            from rigging_pipeline.tools.cometRename import comet_rename_number
            comet_rename_number(base_name, start_num, padding, selection_mode)
            print(f"Renamed objects to '{base_name}' using {selection_mode} mode with CometRename logic")
            
        except Exception as e:
            cmds.error(f"Error in UI sequential rename: {str(e)}")
    
    def _run_prefix_suffix_ui(self, mode, ui_data):
        """Run prefix/suffix using UI field data"""
        try:
            if not ui_data:
                cmds.warning(f"No UI data provided for {mode}")
                return
            
            text_key = f"{mode}_text"
            affix = ui_data.get(text_key, '').strip()
            selection_mode = ui_data.get('selection_mode', 'selected')
            
            if not affix:
                cmds.warning(f"Please enter {mode} text")
                return
            
            # Use CometRename functionality
            from rigging_pipeline.tools.cometRename import comet_add_prefix, comet_add_suffix
            if mode == "prefix":
                comet_add_prefix(affix, selection_mode)
            else:
                comet_add_suffix(affix, selection_mode)
            print(f"Applied {mode} '{affix}' using {selection_mode} mode with CometRename logic")
            
        except Exception as e:
            cmds.error(f"Error in UI {mode}: {str(e)}")
    
    def _run_search_replace_ui(self, ui_data):
        """Run search and replace using UI field data"""
        try:
            if not ui_data:
                cmds.warning("No UI data provided for search and replace")
                return
            
            search_text = ui_data.get('search_text', '').strip()
            replace_text = ui_data.get('replace_text', '')  # Can be empty
            selection_mode = ui_data.get('selection_mode', 'selected')
            
            if not search_text:
                cmds.warning("Please enter search text")
                return
            
            # Use CometRename functionality
            from rigging_pipeline.tools.cometRename import comet_search_replace
            comet_search_replace(search_text, replace_text, selection_mode)
            print(f"Replaced '{search_text}' with '{replace_text}' using {selection_mode} mode with CometRename logic")
            
        except Exception as e:
            cmds.error(f"Error in UI search and replace: {str(e)}")
    
    def _clear_rename_fields(self):
        """Clear all rename fields - this will be handled by the UI"""
        try:
            print("Clearing rename fields...")
            # The UI will handle clearing its own fields
            
        except Exception as e:
            cmds.error(f"Error clearing fields: {str(e)}")

    # ==================== ROTATION/ORIENT TOOLS ====================
    
    def run_rotation_to_orient_tool(self):
        """Convert rotation values to joint orient values with tallying"""
        try:
            selection = cmds.ls(selection=True, type="joint")
            if not selection:
                cmds.warning("Please select joints to convert rotation to orient.")
                return
            
            for joint in selection:
                # Get current rotation values
                rotation = cmds.getAttr(f"{joint}.rotate")[0]
                
                # Get current joint orient values
                current_orient = cmds.getAttr(f"{joint}.jointOrient")[0]
                
                # Add rotation to current orient (tally)
                new_orient = [
                    current_orient[0] + rotation[0],
                    current_orient[1] + rotation[1], 
                    current_orient[2] + rotation[2]
                ]
                
                # Set new joint orient values
                cmds.setAttr(f"{joint}.jointOrientX", new_orient[0])
                cmds.setAttr(f"{joint}.jointOrientY", new_orient[1])
                cmds.setAttr(f"{joint}.jointOrientZ", new_orient[2])
                
                # Zero out rotation values
                cmds.setAttr(f"{joint}.rotateX", 0)
                cmds.setAttr(f"{joint}.rotateY", 0)
                cmds.setAttr(f"{joint}.rotateZ", 0)
            
            cmds.inViewMessage(
                amg=f"<hl>Rotation to Orient</hl> applied to {len(selection)} joint(s)",
                pos="midCenter", 
                fade=True
            )
            print(f"✅ Converted rotation to orient for {len(selection)} joint(s)")
            
        except Exception as e:
            cmds.error(f"Error in rotation to orient conversion: {str(e)}")
    
    def run_orient_to_rotation_tool(self):
        """Convert joint orient values to rotation values with tallying"""
        try:
            selection = cmds.ls(selection=True, type="joint")
            if not selection:
                cmds.warning("Please select joints to convert orient to rotation.")
                return
            
            for joint in selection:
                # Get current joint orient values
                orient = cmds.getAttr(f"{joint}.jointOrient")[0]
                
                # Get current rotation values
                current_rotation = cmds.getAttr(f"{joint}.rotate")[0]
                
                # Add orient to current rotation (tally)
                new_rotation = [
                    current_rotation[0] + orient[0],
                    current_rotation[1] + orient[1],
                    current_rotation[2] + orient[2]
                ]
                
                # Set new rotation values
                cmds.setAttr(f"{joint}.rotateX", new_rotation[0])
                cmds.setAttr(f"{joint}.rotateY", new_rotation[1])
                cmds.setAttr(f"{joint}.rotateZ", new_rotation[2])
                
                # Zero out joint orient values
                cmds.setAttr(f"{joint}.jointOrientX", 0)
                cmds.setAttr(f"{joint}.jointOrientY", 0)
                cmds.setAttr(f"{joint}.jointOrientZ", 0)
            
            cmds.inViewMessage(
                amg=f"<hl>Orient to Rotation</hl> applied to {len(selection)} joint(s)",
                pos="midCenter", 
                fade=True
            )
            print(f"✅ Converted orient to rotation for {len(selection)} joint(s)")
            
        except Exception as e:
            cmds.error(f"Error in orient to rotation conversion: {str(e)}")

    # ==================== JOINT TOOLS ====================
    
    def run_joint_tool(self, action):
        """Run joint tools based on action"""
        try:
            if action == "comet_orient":
                self._run_comet_orient()
            elif action == "unhide_joints":
                self.run_unhide_joints_tool()
            else:
                cmds.warning(f"Unknown joint tool action: {action}")
        except Exception as e:
            cmds.error(f"Error in joint tool: {str(e)}")
    
    def run_unhide_joints_tool(self):
        """Set joint draw style to bone (skip visibility modifications)"""
        try:
            # Get all joints in the scene
            all_joints = cmds.ls(type='joint')
            
            if not all_joints:
                cmds.warning("No joints found in the scene")
                return
            
            draw_style_count = 0
            failed_count = 0
            
            for joint in all_joints:
                # Only set draw style to bone (skip visibility modifications)
                try:
                    cmds.setAttr(f"{joint}.drawStyle", 0)  # 0 = bone style
                    draw_style_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"⚠️ Cannot modify draw style of joint '{joint}': {str(e)}")
            
            # Provide feedback
            if failed_count == 0:
                cmds.inViewMessage(
                    amg=f"<hl>Set draw style</hl> to bone for {draw_style_count} joint(s)",
                    pos="midCenter", 
                    fade=True
                )
                print(f"✅ Set draw style to bone for {draw_style_count} joint(s)")
            else:
                cmds.inViewMessage(
                    amg=f"<hl>Set draw style</hl> to bone for {draw_style_count} joint(s), {failed_count} failed",
                    pos="midCenter", 
                    fade=True
                )
                print(f"✅ Set draw style to bone for {draw_style_count} joint(s), {failed_count} joints failed")
            
        except Exception as e:
            cmds.error(f"Error setting joint draw style: {str(e)}")
    
    def _run_comet_orient(self):
        """Open the full CometJointOrient tool"""
        try:
            from rigging_pipeline.tools.cometJointOrient import launch_comet_joint_orient
            launch_comet_joint_orient()
        except Exception as e:
            cmds.error(f"Error opening CometJointOrient tool: {str(e)}")

    # ==================== TOOLS SECTION ====================
    
    def run_rivet_tool(self, create_joint=False):
        """Create a rivet constraint on selected faces, edges, or vertices"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select faces, edges, vertices, or objects to create rivet on")
                return
            
            # Check if we have component selection (faces, edges, vertices)
            component_selection = cmds.filterExpand(selected, sm=31)  # faces
            if not component_selection:
                component_selection = cmds.filterExpand(selected, sm=32)  # edges
            if not component_selection:
                component_selection = cmds.filterExpand(selected, sm=31)  # vertices
            
            rivets_created = []
            
            if component_selection:
                # Handle component selection (faces, edges, vertices)
                for component in component_selection:
                    rivet_name = self._create_rivet_on_component(component, create_joint)
                    if rivet_name:
                        rivets_created.append(rivet_name)
            else:
                # Handle object selection
                for obj in selected:
                    if cmds.objExists(obj):
                        rivet_name = self._create_rivet_on_object(obj, create_joint)
                        if rivet_name:
                            rivets_created.append(rivet_name)
            
            if rivets_created:
                cmds.confirmDialog(title="Rivet Tool", 
                                 message=f"Created {len(rivets_created)} rivet(s) successfully:\n" + "\n".join(rivets_created))
            else:
                cmds.warning("No rivets were created. Please check your selection.")
            
        except Exception as e:
            cmds.error(f"Error creating rivet: {str(e)}")
    
    def _create_rivet_on_component(self, component, create_joint=False):
        """Create rivet on a specific component (face, edge, or vertex)"""
        try:
            # Extract object name from component
            obj_name = component.split('.')[0]
            
            # Create rivet locator
            rivet_name = f"{obj_name}_rivet1"
            if cmds.objExists(rivet_name):
                counter = 1
                while cmds.objExists(f"{obj_name}_rivet{counter}"):
                    counter += 1
                rivet_name = f"{obj_name}_rivet{counter}"
            
            # Create rivet locator
            rivet_locator = cmds.spaceLocator(name=rivet_name)[0]
            
            # Position rivet at component location
            if '.f[' in component:  # Face
                face_center = cmds.xform(component, query=True, worldSpace=True, boundingBox=True)
                center_x = (face_center[0] + face_center[3]) / 2
                center_y = (face_center[1] + face_center[4]) / 2
                center_z = (face_center[2] + face_center[5]) / 2
                cmds.xform(rivet_locator, worldSpace=True, translation=[center_x, center_y, center_z])
            elif '.e[' in component:  # Edge
                edge_center = cmds.xform(component, query=True, worldSpace=True, boundingBox=True)
                center_x = (edge_center[0] + edge_center[3]) / 2
                center_y = (edge_center[1] + edge_center[4]) / 2
                center_z = (edge_center[2] + edge_center[5]) / 2
                cmds.xform(rivet_locator, worldSpace=True, translation=[center_x, center_y, center_z])
            elif '.vtx[' in component:  # Vertex
                vertex_pos = cmds.xform(component, query=True, worldSpace=True, translation=True)
                cmds.xform(rivet_locator, worldSpace=True, translation=vertex_pos)
            
            # Create rivet constraint
            rivet_constraint = cmds.rivet(obj_name, rivet_locator, name=f"{rivet_name}_rivetConstraint")
            
            # Create joint under rivet if requested
            if create_joint:
                joint_name = f"{rivet_name}_joint"
                joint = cmds.joint(name=joint_name, position=[0, 0, 0])
                cmds.parent(joint, rivet_locator)
                cmds.joint(joint, edit=True, orientJoint='none', zeroScaleOrient=True)
            
            return rivet_name
            
        except Exception as e:
            cmds.error(f"Error creating rivet on component {component}: {str(e)}")
            return None
    
    def _create_rivet_on_object(self, obj, create_joint=False):
        """Create rivet on an object"""
        try:
            # Create rivet locator
            rivet_name = f"{obj}_rivet1"
            if cmds.objExists(rivet_name):
                counter = 1
                while cmds.objExists(f"{obj}_rivet{counter}"):
                    counter += 1
                rivet_name = f"{obj}_rivet{counter}"
            
            # Create rivet locator at object center
            rivet_locator = cmds.spaceLocator(name=rivet_name)[0]
            obj_center = cmds.xform(obj, query=True, worldSpace=True, boundingBox=True)
            center_x = (obj_center[0] + obj_center[3]) / 2
            center_y = (obj_center[1] + obj_center[4]) / 2
            center_z = (obj_center[2] + obj_center[5]) / 2
            cmds.xform(rivet_locator, worldSpace=True, translation=[center_x, center_y, center_z])
            
            # Create rivet constraint
            rivet_constraint = cmds.rivet(obj, rivet_locator, name=f"{rivet_name}_rivetConstraint")
            
            # Create joint under rivet if requested
            if create_joint:
                joint_name = f"{rivet_name}_joint"
                joint = cmds.joint(name=joint_name, position=[0, 0, 0])
                cmds.parent(joint, rivet_locator)
                cmds.joint(joint, edit=True, orientJoint='none', zeroScaleOrient=True)
            
            return rivet_name
            
        except Exception as e:
            cmds.error(f"Error creating rivet on object {obj}: {str(e)}")
            return None
    
    def run_follicle_tool(self):
        """Create a follicle on selected surface"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select a surface to create follicle on")
                return
            
            surface = selected[0]
            
            # Create follicle
            follicle_name = "follicle1"
            if cmds.objExists(follicle_name):
                follicle_name = cmds.rename(follicle_name, f"{follicle_name}#")
            
            # Create follicle using Maya's follicle functionality
            follicle_shape = cmds.createNode("follicle", name=f"{follicle_name}Shape")
            follicle_transform = cmds.listRelatives(follicle_shape, parent=True)[0]
            follicle_transform = cmds.rename(follicle_transform, follicle_name)
            
            # Connect to surface if it's a nurbs surface
            if cmds.objectType(surface) == "nurbsSurface":
                surface_shape = cmds.listRelatives(surface, shapes=True)[0]
                cmds.connectAttr(f"{surface_shape}.worldSpace[0]", f"{follicle_shape}.inputSurface")
                cmds.connectAttr(f"{follicle_shape}.outRotate", f"{follicle_transform}.rotate")
                cmds.connectAttr(f"{follicle_shape}.outTranslate", f"{follicle_transform}.translate")
            
            cmds.confirmDialog(title="Follicle Tool", 
                             message=f"Created follicle '{follicle_name}' successfully")
            
        except Exception as e:
            cmds.error(f"Error creating follicle: {str(e)}")


def launch_utilityTools():
    """Launch the RigX Utility Tools"""
    try:
        tools = RigXUtilityTools()
        tools.show_ui()
        print("✅ RigX Utility Tools launched successfully!")
        return tools
    except Exception as e:
        print(f"❌ Error launching RigX Utility Tools: {str(e)}")
        return None


def main():
    """Main function to run the RigX Utility Tools"""
    return launch_utilityTools()


if __name__ == "__main__":
    main()
