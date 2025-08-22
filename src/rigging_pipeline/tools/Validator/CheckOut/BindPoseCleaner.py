"""
BindPoseCleaner Validation Module
Checks for bind pose issues and cleans up problematic ones
"""

import maya.cmds as cmds

DESCRIPTION = "Check and fix bind pose issues"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get bind pose nodes (either from selection or all in scene)
    if objList:
        to_check_list = cmds.ls(objList, type="dagPose")
    else:
        to_check_list = cmds.ls(selection=False, type="dagPose")  # bindPose nodes
    
    if to_check_list:
        # Check if there are multiple bind pose nodes (this can cause issues)
        if len(to_check_list) > 1:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': f"Found {len(to_check_list)} bind pose nodes - multiple bind poses can cause issues",
                    'fixed': False
                })
            elif mode == "fix":
                try:
                    # Only delete bind poses that are not the main one
                    # Keep the first one and delete the rest
                    main_bind_pose = to_check_list[0]
                    bind_poses_to_delete = to_check_list[1:]
                    
                    for item in bind_poses_to_delete:
                        try:
                            cmds.lockNode(item, lock=False)
                            cmds.delete(item)
                        except Exception as e:
                            issues.append({
                                'object': item,
                                'message': f"Failed to delete bind pose {item}: {str(e)}",
                                'fixed': False
                            })
                    
                    if len(bind_poses_to_delete) > 0:
                        issues.append({
                            'object': "Scene",
                            'message': f"Cleaned up {len(bind_poses_to_delete)} duplicate bind pose nodes, kept {main_bind_pose}",
                            'fixed': True
                        })
                    else:
                        issues.append({
                            'object': "Scene",
                            'message': "No duplicate bind poses to clean",
                            'fixed': True
                        })
                except Exception as e:
                    issues.append({
                        'object': "Scene",
                        'message': f"Failed to clean bind poses: {str(e)}",
                        'fixed': False
                    })
        else:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': f"Found 1 bind pose node: {to_check_list[0]} - no action needed",
                    'fixed': True
                })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No bind pose nodes found - this is normal for scenes without skinning",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }
