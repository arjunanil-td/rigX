"""
TweakNodeCleaner Validation Module
Cleans up tweak nodes
"""

import maya.cmds as cmds

DESCRIPTION = "Clean tweak nodes"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get tweak nodes to check (either from selection or all in scene)
    if objList:
        to_check_list = cmds.ls(objList, type='tweak')
    else:
        to_check_list = cmds.ls(selection=False, type='tweak')
    
    if to_check_list:
        for item in to_check_list:
            if cmds.objExists(item):
                # Check if there are edited control points in the tweak node
                has_edits = check_edited_control_points(item)
                
                if not has_edits:
                    if mode == "check":
                        issues.append({
                            'object': item,
                            'message': f"Found tweak node with no edits: {item}",
                            'fixed': False
                        })
                    elif mode == "fix":
                        try:
                            # Unlock and delete the tweak node
                            cmds.lockNode(item, lock=False)
                            cmds.delete(item)
                            
                            issues.append({
                                'object': item,
                                'message': f"Tweak node cleaned: {item}",
                                'fixed': True
                            })
                        except Exception as e:
                            issues.append({
                                'object': item,
                                'message': f"Failed to clean tweak node: {str(e)}",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': item,
                            'message': f"Tweak node has edits - manual review needed: {item}",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': item,
                        'message': f"Tweak node not found: {item}",
                        'fixed': False
                    })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No tweak nodes found to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }

def check_edited_control_points(item):
    """Check if there are edited control points in the given tweak node"""
    if cmds.objExists(item):
        try:
            p_list = cmds.getAttr(f"{item}.plist", multiIndices=True)
            if p_list:
                for idx in p_list:
                    cp_list = cmds.getAttr(f"{item}.plist[{idx}].controlPoints", multiIndices=True)
                    if cp_list:
                        for cp in cp_list:
                            value = cmds.getAttr(f"{item}.plist[{idx}].controlPoints[{cp}]")
                            if value != [0.0, 0.0, 0.0]:
                                return True
        except:
            pass
    return False
