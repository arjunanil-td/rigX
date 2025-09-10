"""
FreezeTransform Validation Module
Checks for non-zero transforms and freezes them to zero/one values
"""

import maya.cmds as cmds

DESCRIPTION = "Check and fix non-zero transforms (freeze transforms)"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    all_object_list = []
    to_fix_list = []
    
    # Get transform objects (either from selection or all in scene)
    if cmds.ls(selection=True):
        all_object_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'transform']
    else:
        all_object_list = cmds.ls(type='transform', long=True)
    
    # Analysis transformations
    if all_object_list:
        anim_curves_list = cmds.ls(type='animCurve')
        zero_attr_list = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']
        one_attr_list = ['scaleX', 'scaleY', 'scaleZ']
        cameras_list = ['|persp', '|top', '|side', '|front', '|bottom', '|back', '|left']
        
        # Filter out cameras
        all_valid_objs = [obj for obj in all_object_list if obj not in cameras_list]
        
        for obj in all_valid_objs[:20]:  # Limit to 20 objects for performance
            if cmds.objExists(obj):
                # Check if transforms are frozen
                frozen_tr = _check_frozen_object(obj, zero_attr_list, 0)
                frozen_s = _check_frozen_object(obj, one_attr_list, 1)
                
                if not (frozen_tr and frozen_s):
                    if mode == "check":
                        issues.append({
                            'object': obj,
                            'message': f"Transform not frozen - T/R/S values need reset",
                            'fixed': False
                        })
                    elif mode == "fix":
                        try:
                            # Unlock attributes first
                            if _unlock_attributes(obj, zero_attr_list, anim_curves_list) and _unlock_attributes(obj, one_attr_list, anim_curves_list):
                                # Freeze transform
                                cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True)
                                
                                # Verify fix
                                if _check_frozen_object(obj, zero_attr_list, 0) and _check_frozen_object(obj, one_attr_list, 1):
                                    issues.append({
                                        'object': obj,
                                        'message': f"Transform frozen successfully",
                                        'fixed': True
                                    })
                                else:
                                    issues.append({
                                        'object': obj,
                                        'message': f"Freeze transform failed - manual check required",
                                        'fixed': False
                                    })
                            else:
                                issues.append({
                                    'object': obj,
                                    'message': f"Failed to unlock attributes - animation curves may exist",
                                    'fixed': False
                                })
                        except Exception as e:
                            issues.append({
                                'object': obj,
                                'message': f"Failed to freeze transform: {str(e)}",
                                'fixed': False
                            })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No transform objects found to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(all_object_list) if 'all_object_list' in locals() else 0,
        "total_issues": len(issues)
    }

def _check_frozen_object(obj, attr_list, comp_value):
    """Compare values. Return True if equal."""
    for attr in attr_list:
        try:
            if cmds.getAttr(f"{obj}.{attr}") != comp_value:
                return False
        except:
            return False
    return True

def _unlock_attributes(obj, attr_list, anim_curves_list):
    """Unlock attributes if they're not connected to animation curves."""
    for attr in attr_list:
        try:
            # Check if attribute is connected to animation curves
            connections = cmds.listConnections(f"{obj}.{attr}", source=True)
            if connections:
                for conn in connections:
                    if conn in anim_curves_list:
                        return False  # Can't unlock if connected to animation
            # Unlock the attribute
            cmds.setAttr(f"{obj}.{attr}", lock=False)
        except:
            cmds.setAttr(f"{obj}.{attr}", lock=False)
    return True
