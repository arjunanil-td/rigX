"""
UnusedSkinCleaner Validation Module
Cleans up unused skin clusters and unused influence joints
"""

import maya.cmds as cmds

DESCRIPTION = "Clean unused skin clusters and unused influence joints"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get skin clusters to check (either from selection or all in scene)
    if objList:
        to_check_list = cmds.ls(objList, type="skinCluster")
    else:
        to_check_list = cmds.ls(selection=False, type="skinCluster")
    
    if to_check_list:
        for item in to_check_list:
            if cmds.objExists(item):
                try:
                    # Get the mesh connected to this skin cluster
                    mesh_list = cmds.skinCluster(item, query=True, geometry=True)
                    if mesh_list:
                        # Get the influence joints and weighted influences
                        influence_list = cmds.skinCluster(item, query=True, influence=True)
                        weighted_influence_list = cmds.skinCluster(item, query=True, weightedInfluence=True)
                        
                        # Check if there are unused influence joints (joints with no weights)
                        if influence_list and weighted_influence_list:
                            unused_joints = []
                            for joint in influence_list:
                                if joint not in weighted_influence_list:
                                    unused_joints.append(joint)
                            
                            if unused_joints:
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Found {len(unused_joints)} unused influence joints: {', '.join(unused_joints)}",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        # Remove unused influence joints
                                        cmds.skinCluster(item, edit=True, removeInfluence=unused_joints, toSelectedBones=True)
                                        issues.append({
                                            'object': item,
                                            'message': f"Removed {len(unused_joints)} unused influence joints from {item}",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': item,
                                            'message': f"Failed to remove unused joints: {str(e)}",
                                            'fixed': False
                                        })
                            else:
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Skin cluster {item} has no unused influence joints",
                                        'fixed': True
                                    })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"Skin cluster {item} has no influence joints",
                                    'fixed': False
                                })
                    else:
                        # Skin cluster with no geometry - this can be safely deleted
                        if mode == "check":
                            issues.append({
                                'object': item,
                                'message': f"Skin cluster {item} has no geometry connected - can be cleaned",
                                'fixed': False
                            })
                        elif mode == "fix":
                            try:
                                # Unlock and delete the orphaned skin cluster
                                cmds.lockNode(item, lock=False)
                                cmds.delete(item)
                                issues.append({
                                    'object': item,
                                    'message': f"Orphaned skin cluster cleaned: {item}",
                                    'fixed': True
                                })
                            except Exception as e:
                                issues.append({
                                    'object': item,
                                    'message': f"Failed to clean orphaned skin cluster: {str(e)}",
                                    'fixed': False
                                })
                except Exception as e:
                    if mode == "check":
                        issues.append({
                            'object': item,
                            'message': f"Error checking skin cluster: {str(e)}",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': item,
                        'message': f"Skin cluster not found: {item}",
                        'fixed': False
                    })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No skin clusters found to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }
