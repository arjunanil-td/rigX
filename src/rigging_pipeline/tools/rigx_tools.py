import maya.cmds as cmds
import maya.api.OpenMaya as om

from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.tools.ui.rigx_tools_ui import RigXToolsUI


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class RigXTools:
    """Main class for RigX Utility Tools functionality"""
    
    def __init__(self):
        self.ui = None
        
    def show_ui(self):
        """Show the RigX Utility Tools UI"""
        if not self.ui:
            self.ui = RigXToolsUI()
        self.ui.show()
        self.ui.raise_()
        self.ui.activateWindow()
    
    def run_tool_1(self):
        """Execute tool 1 functionality"""
        try:
            # Example tool functionality
            selected = cmds.ls(selection=True)
            if selected:
                cmds.confirmDialog(title="Tool 1", message=f"Processing {len(selected)} selected objects")
            else:
                cmds.warning("Please select objects first")
        except Exception as e:
            cmds.error(f"Error in tool 1: {str(e)}")
    
    def run_tool_2(self):
        """Execute tool 2 functionality"""
        try:
            # Example tool functionality
            cmds.confirmDialog(title="Tool 2", message="Tool 2 executed successfully")
        except Exception as e:
            cmds.error(f"Error in tool 2: {str(e)}")
    
    def run_tool_3(self):
        """Execute tool 3 functionality"""
        try:
            # Example tool functionality
            cmds.confirmDialog(title="Tool 3", message="Tool 3 executed successfully")
        except Exception as e:
            cmds.error(f"Error in tool 3: {str(e)}")
    
    def run_offset_group_tool(self):
        """Create offset groups for selected objects"""
        try:
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.warning("Please select objects to create offset groups for")
                return
            
            # Ask for number of offset groups to create
            result = cmds.promptDialog(
                title="Offset Groups",
                message="Enter number of offset groups to create:",
                button=['Create', 'Cancel'],
                defaultButton='Create',
                cancelButton='Cancel',
                dismissString='Cancel'
            )
            
            if result == 'Create':
                num_groups_str = cmds.promptDialog(query=True, text=True)
                try:
                    num_groups = int(num_groups_str)
                    if num_groups <= 0:
                        cmds.warning("Number of groups must be greater than 0")
                        return
                except ValueError:
                    cmds.warning("Please enter a valid number")
                    return
                
                created_groups = []
                for obj in selected:
                    # Create multiple offset groups for each object
                    for i in range(num_groups):
                        if num_groups == 1:
                            group_name = f"{obj}_offset"
                        else:
                            group_name = f"{obj}_offset_{i+1:02d}"
                        
                        # Create offset group
                        offset_grp = cmds.group(empty=True, name=group_name)
                        
                        # Get object's world matrix
                        obj_matrix = cmds.xform(obj, query=True, matrix=True, worldSpace=True)
                        
                        # Set offset group's transform to match object
                        cmds.xform(offset_grp, matrix=obj_matrix, worldSpace=True)
                        
                        # Parent object under offset group (only for the first group)
                        if i == 0:
                            cmds.parent(obj, offset_grp)
                        else:
                            # For additional groups, parent them under the previous group
                            cmds.parent(offset_grp, created_groups[-1])
                        
                        created_groups.append(offset_grp)
                
                # Select all created groups
                cmds.select(created_groups)
                cmds.confirmDialog(title="Offset Groups", 
                                 message=f"Created {len(created_groups)} offset groups for {len(selected)} objects")
            
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


def main():
    """Main function to run the tool"""
    tool = RigXTools()
    tool.show_ui()


if __name__ == "__main__":
    main()
