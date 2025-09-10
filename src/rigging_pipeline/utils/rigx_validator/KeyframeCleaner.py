"""
KeyframeCleaner Validation Module
Cleans up unused keyframes and animation curves
"""

import maya.cmds as cmds

DESCRIPTION = "Clean unused keyframes and animation curves"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get all objects to check (either from selection or all in scene)
    if objList:
        to_check_list = objList
    else:
        to_check_list = cmds.ls(selection=False)
    
    if to_check_list:
        # Get animation node list
        anim_curves_list = cmds.ls(type="animCurve")
        if anim_curves_list:
            animated_list = []
            for anim_crv in anim_curves_list:
                connection_list = cmds.ls(cmds.listConnections(anim_crv), type=["transform", "blendShape", "nonLinear"])
                if connection_list and not connection_list[0] in animated_list:
                    animated_list.append(connection_list[0])
            
            if animated_list:
                for item in animated_list:
                    if item in to_check_list:
                        if cmds.objExists(item):
                            crv_list = cmds.listConnections(item, source=True, destination=False, type="animCurve")
                            if crv_list:
                                found_key = False
                                for crv in crv_list:
                                    # Check if it's a driven key (has multiple source connections)
                                    if len(cmds.listConnections(crv, source=True)) >= 2:
                                        pass  # driven key - don't delete
                                    else:  # normal key
                                        found_key = True
                                        break
                                
                                if found_key:
                                    if mode == "check":
                                        issues.append({
                                            'object': item,
                                            'message': f"Found keyframes on {item}",
                                            'fixed': False
                                        })
                                    elif mode == "fix":
                                        try:
                                            deleted_count = 0
                                            for crv in crv_list:
                                                if len(cmds.listConnections(crv, source=True)) < 2:
                                                    cmds.delete(crv)
                                                    deleted_count += 1
                                            
                                            if deleted_count > 0:
                                                issues.append({
                                                    'object': item,
                                                    'message': f"Cleaned {deleted_count} keyframes from {item}",
                                                    'fixed': True
                                                })
                                            else:
                                                issues.append({
                                                    'object': item,
                                                    'message': f"No keyframes to clean from {item}",
                                                    'fixed': True
                                                })
                                        except Exception as e:
                                            issues.append({
                                                'object': item,
                                                'message': f"Failed to clean keyframes: {str(e)}",
                                                'fixed': False
                                            })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "No animated objects found",
                        'fixed': True
                    })
        else:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': "No animation curves found",
                    'fixed': True
                })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No objects to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }
