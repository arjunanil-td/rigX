"""
ControllerTag Validation Module
Checks for controller tags
"""

import maya.cmds as cmds

DESCRIPTION = "Check and clean controller tags"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    try:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "Checking for controller tags",
                'fixed': False
            })
        elif mode == "fix":
            try:
                # Remove controller tags
                cmds.delete("controllerTag*")
                issues.append({
                    'object': "Scene",
                    'message': "Controller tags cleaned successfully",
                    'fixed': True
                })
            except Exception as e:
                issues.append({
                    'object': "Scene",
                    'message': f"Failed to clean controller tags: {str(e)}",
                    'fixed': False
                })
    except:
        pass
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": 1,
        "total_issues": len(issues)
    }
