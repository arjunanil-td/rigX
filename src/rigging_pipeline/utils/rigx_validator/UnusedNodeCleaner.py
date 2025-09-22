"""
UnusedNodeCleaner Validation Module
Cleans up unused materials, nodes, and unused animation curves
"""

import maya.cmds as cmds

DESCRIPTION = "Clean unused materials, nodes, and unused animation curves"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get all materials in scene
    to_check_list = cmds.ls(selection=False, materials=True)
    
    if to_check_list:
        if len(to_check_list) > 3:  # Discarding default materials
            # Getting data to analyse
            default_mat_list = ['lambert1', 'standardSurface1', 'particleCloud1']
            all_mat_list = list(set(to_check_list) - set(default_mat_list))
            
            # Get used materials by checking shadingEngine connections to geometry
            used_mat_list = []
            for material in all_mat_list:
                # Get the shadingEngine connected to this material
                shading_engines = cmds.listConnections(material, type='shadingEngine') or []
                for sg in shading_engines:
                    # Check if the shadingEngine has any geometry members
                    members = cmds.sets(sg, query=True) or []
                    if members:
                        # Check if any members are actual geometry (mesh, nurbsSurface, etc.)
                        for member in members:
                            if cmds.objectType(member) in ['mesh', 'nurbsSurface', 'nurbsCurve']:
                                used_mat_list.append(material)
                                break
                        if material in used_mat_list:
                            break
            
            # Get truly unused materials
            unused_mat_list = list(set(all_mat_list) - set(used_mat_list))
            
            if mode == "check":
                if len(unused_mat_list) > 0:
                    # Report each truly unused material individually
                    for material in unused_mat_list:
                        issues.append({
                            'object': material,
                            'message': f"Unused material: {material}",
                            'fixed': False
                        })
                else:
                    issues.append({
                        'object': "Scene",
                        'message': "No unused materials found",
                        'fixed': True
                    })
            elif mode == "fix":
                try:
                    # Use Maya's built-in command to delete unused materials
                    import maya.mel as mel
                    fix_result = mel.eval("MLdeleteUnused;")
                    issues.append({
                        'object': "Scene",
                        'message': f"Fixed: {fix_result} nodes = {len(unused_mat_list)} materials",
                        'fixed': True
                    })
                except Exception as e:
                    issues.append({
                        'object': "Scene",
                        'message': f"Failed to fix: materials",
                        'fixed': False
                    })
        else:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': "Not enough materials to check",
                    'fixed': True
                })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No materials found to check",
                'fixed': True
            })
    
    # Also handle unused animation curves here
    try:
        all_anim_curves = cmds.ls(type='animCurve') or []
        unused_anim_curves = []
        for anim_curve in all_anim_curves:
            # Skip referenced nodes
            if cmds.objExists(anim_curve) and cmds.referenceQuery(anim_curve, isNodeReferenced=True):
                continue
            # If the anim curve has no destination connections, it doesn't drive anything
            dest_conns = cmds.listConnections(anim_curve, source=False, destination=True, plugs=True) or []
            if not dest_conns:
                # Accept as unused if it also has no source driving outputs, or only time input
                src_conns = cmds.listConnections(anim_curve, source=True, destination=False, plugs=True) or []
                if not src_conns:
                    unused_anim_curves.append(anim_curve)
                else:
                    drives_anything = False
                    for plug in src_conns:
                        if '.output' in plug or '.outputX' in plug or '.outputY' in plug or '.outputZ' in plug:
                            drives_anything = True
                            break
                    if not drives_anything:
                        unused_anim_curves.append(anim_curve)

        if unused_anim_curves:
            if mode == "check":
                for curve in unused_anim_curves:
                    issues.append({
                        'object': curve,
                        'message': f"Unused animation curve: {curve}",
                        'fixed': False
                    })
            elif mode == "fix":
                for curve in unused_anim_curves:
                    try:
                        cmds.delete(curve)
                        issues.append({
                            'object': curve,
                            'message': f"Removed unused animation curve: {curve}",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': curve,
                            'message': f"Failed to remove animation curve {curve}: {str(e)}",
                            'fixed': False
                        })
        else:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': "No unused animation curves found",
                    'fixed': True
                })
    except Exception as e:
        issues.append({
            'object': "Scene",
            'message': f"Error checking unused animation curves: {str(e)}",
            'fixed': False
        })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }
