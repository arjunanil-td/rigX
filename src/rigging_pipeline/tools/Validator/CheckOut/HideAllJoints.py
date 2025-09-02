"""
HideAllJoints Validation Module
Hides all joints in the scene
"""

import maya.cmds as cmds

DESCRIPTION = "Hide all joints in the scene"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get joints to check (either from selection or all in scene)
    if cmds.ls(selection=True):
        to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'joint']
    else:
        to_check_list = cmds.ls(type='joint', long=True)
    
    if to_check_list:
        visible_joints = []
        hidden_joints = []
        
        for item in to_check_list:
            if cmds.objExists(item):
                # Check if joint is already hidden
                if not cmds.getAttr(item + '.drawStyle') == 2:
                    visible_joints.append(item)
                else:
                    hidden_joints.append(item)
            else:
                if mode == "check":
                    issues.append({
                        'object': item,
                        'message': f"Joint not found: {item}",
                        'fixed': False
                    })
        
        # Only process visible joints
        for item in visible_joints:
            if mode == "check":
                issues.append({
                    'object': item,
                    'message': f"Joint is visible: {item}",
                    'fixed': False
                })
            elif mode == "fix":
                try:
                    # Hide the joint
                    cmds.setAttr(item + '.drawStyle', 2)
                    issues.append({
                        'object': item,
                        'message': f"Joint hidden: {item}",
                        'fixed': True
                    })
                except Exception as e:
                    issues.append({
                        'object': item,
                        'message': f"Failed to hide joint: {str(e)}",
                        'fixed': False
                    })
        
        # If all joints are already hidden, report success
        if not visible_joints and hidden_joints:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': "All validations passed",
                    'fixed': True
                })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No joints found to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }
