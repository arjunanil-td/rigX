"""
DisplayLayers Validation Module
Checks that no display layers exist (except defaultLayer)
"""

import maya.cmds as cmds

DESCRIPTION = "Check and remove unnecessary display layers"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    try:
        # Check if we're in a referenced scene (not if the scene itself is a reference)
        # We can still work with display layers even if the scene has references
        all_layers = cmds.ls(type="displayLayer")
        extra_layers = []
        for layer in all_layers:
            if layer != "defaultLayer":
                extra_layers.append(layer)
        
        if mode == "check":
            if extra_layers:
                for layer in extra_layers:
                    issues.append({
                        'object': layer,
                        'message': f"Display layer found: {layer}",
                        'fixed': False
                    })
            else:
                issues.append({
                    'object': "Scene",
                    'message': "No display layers found - scene is clean",
                    'fixed': True
                })
        elif mode == "fix":
            try:
                deleted_count = 0
                for layer in extra_layers:
                    if cmds.objExists(layer):
                        cmds.delete(layer)
                        deleted_count += 1
                
                if deleted_count > 0:
                    issues.append({
                        'object': "Scene",
                        'message': f"Display layers cleared: {deleted_count} layers removed",
                        'fixed': True
                    })
                else:
                    issues.append({
                        'object': "Scene",
                        'message': "No display layers to clear",
                        'fixed': True
                    })
            except Exception as e:
                issues.append({
                    'object': "Scene",
                    'message': f"Failed to clear display layers: {str(e)}",
                    'fixed': False
                })
    except Exception as e:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': f"Display layer validation failed: {str(e)}",
                'fixed': False
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(all_layers) if 'all_layers' in locals() else 0,
        "total_issues": len(issues)
    }
