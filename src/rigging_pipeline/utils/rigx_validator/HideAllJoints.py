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
        
        # Helper to determine if a joint is a jaw joint (by name)
        def _is_jaw_joint(joint_long_name):
            try:
                short_name = cmds.ls(joint_long_name, long=False)[0]
            except Exception:
                short_name = joint_long_name.split('|')[-1]
            return 'jaw' in short_name.lower()

        # Filter to jaw joints for reporting in check mode
        jaw_visible_joints = [j for j in visible_joints if _is_jaw_joint(j)]

        # Only process visible joints
        if mode == "check":
            # Report ONLY jaw joints as requested; ignore other visible joints
            if jaw_visible_joints:
                for item in jaw_visible_joints:
                    issues.append({
                        'object': item,
                        'message': f"Jaw joint is visible: {item}",
                        'fixed': False
                    })
            else:
                # Treat as pass even if other non-jaw joints are visible (per request)
                issues.append({
                    'object': "Scene",
                    'message': "All validations passed",
                    'fixed': True
                })
        elif mode == "fix":
            # Still hide ALL visible joints, but only report jaw joints to reduce noise
            for item in visible_joints:
                try:
                    cmds.setAttr(item + '.drawStyle', 2)
                    if _is_jaw_joint(item):
                        issues.append({
                            'object': item,
                            'message': f"Jaw joint hidden: {item}",
                            'fixed': True
                        })
                except Exception as e:
                    if _is_jaw_joint(item):
                        issues.append({
                            'object': item,
                            'message': f"Failed to hide jaw joint: {str(e)}",
                            'fixed': False
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
