"""
ColorSetCleaner Validation Module
Cleans up unused color sets from meshes
"""

import maya.cmds as cmds

DESCRIPTION = "Clean unused color sets from meshes"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Check for color sets
    meshes = cmds.ls(type='mesh', long=True)
    for mesh in meshes:
        if cmds.objExists(mesh):
            try:
                color_sets = cmds.polyColorSet(mesh, query=True, allColorSets=True)
                if color_sets:
                    if mode == "check":
                        issues.append({
                            'object': mesh,
                            'message': f"Color sets found: {len(color_sets)}",
                            'fixed': False
                        })
                    elif mode == "fix":
                        try:
                            for color_set in color_sets:
                                cmds.polyColorSet(mesh, delete=True, colorSet=color_set)
                            issues.append({
                                'object': mesh,
                                'message': f"Color sets cleaned successfully",
                                'fixed': True
                            })
                        except Exception as e:
                            issues.append({
                                'object': mesh,
                                'message': f"Failed to clean color sets: {str(e)}",
                                'fixed': False
                            })
            except:
                pass
    
    if not issues and mode == "check":
        issues.append({
            'object': "Scene",
            'message': "No color sets found",
            'fixed': True
        })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(meshes) if meshes else 0,
        "total_issues": len(issues)
    }
