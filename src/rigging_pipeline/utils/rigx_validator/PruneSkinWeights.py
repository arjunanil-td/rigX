"""
PruneSkinWeights Validation Module
Prunes skin weights below threshold
"""

import maya.cmds as cmds
import maya.mel as mel

DESCRIPTION = "Prune skin weights below threshold"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    prune_min_value = 0.0005
    
    # Get skin clusters to check (either from selection or all in scene)
    if objList:
        to_check_list = objList
    else:
        to_check_list = cmds.ls(selection=False, type='skinCluster')
    
    if to_check_list:
        for skin_cluster_node in to_check_list:
            if cmds.objExists(skin_cluster_node):
                try:
                    # Get geometry connected to this skin cluster
                    mesh_list = cmds.skinCluster(skin_cluster_node, query=True, geometry=True)
                    if mesh_list:
                        # Get skin weights for the first mesh
                        mesh = mesh_list[0]
                        if cmds.objExists(mesh):
                            # Get influence joints
                            influence_list = cmds.skinCluster(skin_cluster_node, query=True, influence=True)
                            
                            if influence_list:
                                # Check for low weights
                                to_prune_list = []
                                try:
                                    # Get skin weights using Maya's built-in method
                                    weights = cmds.skinPercent(skin_cluster_node, mesh, query=True, value=True)
                                    if weights:
                                        for v, weight_list in enumerate(weights):
                                            for w in weight_list:
                                                if w < prune_min_value:
                                                    to_prune_list.append(v)
                                                    break
                                except:
                                    # Fallback method if skinPercent fails
                                    pass
                                
                                if to_prune_list:
                                    if mode == "check":
                                        issues.append({
                                            'object': skin_cluster_node,
                                            'message': f"Found {len(to_prune_list)} vertices with low weights (< {prune_min_value})",
                                            'fixed': False
                                        })
                                    elif mode == "fix":
                                        try:
                                            # Unlock influence joints
                                            for jnt in influence_list:
                                                if cmds.objExists(jnt):
                                                    cmds.setAttr(f"{jnt}.liw", 0)  # unlock
                                            
                                            # Select mesh and prune weights
                                            cmds.select(mesh)
                                            mel.eval(f'doPruneSkinClusterWeightsArgList 2 {{ "{prune_min_value}", "1" }};')
                                            
                                            issues.append({
                                                'object': skin_cluster_node,
                                                'message': f"Pruned {len(to_prune_list)} vertices with low weights",
                                                'fixed': True
                                            })
                                        except Exception as e:
                                            issues.append({
                                                'object': skin_cluster_node,
                                                'message': f"Failed to prune weights: {str(e)}",
                                                'fixed': False
                                            })
                                        finally:
                                            cmds.select(clear=True)
                                else:
                                    if mode == "check":
                                        issues.append({
                                            'object': skin_cluster_node,
                                            'message': f"No low weights found - all weights above {prune_min_value}",
                                            'fixed': True
                                        })
                            else:
                                if mode == "check":
                                    issues.append({
                                        'object': skin_cluster_node,
                                        'message': "No influence joints found",
                                        'fixed': False
                                    })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': skin_cluster_node,
                                    'message': "Connected geometry not found",
                                    'fixed': False
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': skin_cluster_node,
                                'message': "No geometry connected to skin cluster",
                                'fixed': False
                            })
                except Exception as e:
                    if mode == "check":
                        issues.append({
                            'object': skin_cluster_node,
                            'message': f"Error checking skin weights: {str(e)}",
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
