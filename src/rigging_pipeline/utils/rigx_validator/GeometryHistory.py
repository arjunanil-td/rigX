"""
GeometryHistory Validation Module
Checks for geometry history and deletes it
"""

import maya.cmds as cmds

DESCRIPTION = "Check and delete geometry history"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get geometry to check (either from selection or all in scene)
    if cmds.ls(selection=True):
        geo_to_clean_list = cmds.ls(selection=True, long=True)
    else:
        geo_to_clean_list = cmds.ls(type=['mesh', 'nurbsSurface', 'nurbsCurve'], long=True)
    
    if geo_to_clean_list:
        for geo in geo_to_clean_list:
            if cmds.objExists(geo):
                # Check if geometry has construction history
                history = cmds.listHistory(geo, interestLevel=2)
                if history and len(history) > 1:  # More than just the shape node
                    if mode == "check":
                        issues.append({
                            'object': geo,
                            'message': f"Geometry has construction history: {geo}",
                            'fixed': False
                        })
                    elif mode == "fix":
                        try:
                            # Delete construction history
                            cmds.delete(geo, constructionHistory=True)
                            issues.append({
                                'object': geo,
                                'message': f"Construction history deleted: {geo}",
                                'fixed': True
                            })
                        except Exception as e:
                            issues.append({
                                'object': geo,
                                'message': f"Failed to delete history: {str(e)}",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': geo,
                            'message': f"Geometry has no construction history: {geo}",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': geo,
                        'message': f"Geometry not found: {geo}",
                        'fixed': False
                    })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No geometry found to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(geo_to_clean_list) if 'geo_to_clean_list' in locals() else 0,
        "total_issues": len(issues)
    }
