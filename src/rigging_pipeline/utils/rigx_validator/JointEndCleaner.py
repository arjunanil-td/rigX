"""
JointEndCleaner Validation Module
Checks for unnecessary joints at the end of chains
"""

import maya.cmds as cmds

DESCRIPTION = "Check for unnecessary joints at the end of chains"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get joints to check
    if objList:
        to_check_list = cmds.ls(objList, type="joint")
    else:
        to_check_list = cmds.ls(selection=False, type="joint")
    
    if to_check_list:
        for item in to_check_list:
            if cmds.objExists(item):
                try:
                    # Check if joint is at the end of a chain (no children)
                    children = cmds.listRelatives(item, children=True, type="joint")
                    
                    if not children:
                        # Check if this joint is skinned
                        skin_clusters = cmds.listConnections(item, type="skinCluster")
                        
                        if not skin_clusters:
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"End joint {item} has no children and is not skinned - can be cleaned",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    cmds.delete(item)
                                    issues.append({
                                        'object': item,
                                        'message': f"Cleaned end joint: {item}",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': item,
                                        'message': f"Failed to clean end joint: {str(e)}",
                                        'fixed': False
                                    })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"End joint {item} is skinned - keep for skinning",
                                    'fixed': True
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': item,
                                'message': f"Joint {item} has children - not an end joint",
                                'fixed': True
                            })
                except Exception as e:
                    if mode == "check":
                        issues.append({
                            'object': item,
                            'message': f"Error checking joint: {str(e)}",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': item,
                        'message': f"Joint not found: {item}",
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
