"""
UnknownNodesCleaner Validation Module
Cleans up unknown nodes
"""

import maya.cmds as cmds

DESCRIPTION = "Clean unknown nodes"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get unknown nodes to check (either from selection or all in scene)
    if objList:
        to_check_list = cmds.ls(objList, type='unknown')
    else:
        to_check_list = cmds.ls(selection=False, type='unknown')
    
    if to_check_list:
        for item in to_check_list:
            if cmds.objExists(item):
                if mode == "check":
                    issues.append({
                        'object': item,
                        'message': f"Unknown node found: {item}",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Unlock and delete the unknown node
                        cmds.lockNode(item, lock=False)
                        cmds.delete(item)
                        
                        issues.append({
                            'object': item,
                            'message': f"Unknown node cleaned: {item}",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': item,
                            'message': f"Failed to clean unknown node: {str(e)}",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': item,
                        'message': f"Unknown node not found: {item}",
                        'fixed': False
                    })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No unknown nodes found to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }
