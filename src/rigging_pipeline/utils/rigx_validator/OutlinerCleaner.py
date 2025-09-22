"""
OutlinerCleaner Validation Module
Cleans up outliner by organizing and removing unnecessary nodes
Uses asset name from JOB_PATH (set by TopNodeChecker)
"""

import maya.cmds as cmds
import os
from pathlib import Path

DESCRIPTION = "Clean and organize outliner structure using queried asset name"

def get_job_info():
    """Get job information from JOB_PATH environment variable (mirrors TopNodeChecker logic)"""
    job_path_env = os.environ.get("JOB_PATH")
    JOB_PATH = Path(job_path_env) if job_path_env else None

    if JOB_PATH is None:
        return {
            "show": "unknown",
            "asset": "unknown",
            "shot": "unknown",
            "department": "unknown",
            "path": None
        }
    try:
        data = str(JOB_PATH).split(os.sep)
        if len(data) >= 4:
            return {
                "show": data[3] if len(data) > 3 else "unknown",
                "asset": data[-2] if len(data) > 1 else "unknown",
                "shot": data[-2] if len(data) > 1 else "unknown",
                "department": data[-1] if len(data) > 0 else "unknown",
                "path": JOB_PATH
            }
        else:
            return {
                "show": "unknown",
                "asset": "unknown",
                "shot": "unknown",
                "department": "unknown",
                "path": JOB_PATH
            }
    except Exception:
        return {
            "show": "unknown",
            "asset": "unknown",
            "shot": "unknown",
            "department": "unknown",
            "path": JOB_PATH
        }

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get the asset name that TopNodeChecker queried
    job_info = get_job_info()
    asset_name = (job_info.get("asset") or "unknown").strip()
    
    if not cmds.file(query=True, reference=True):
        # Get all transform nodes in the scene
        all_transforms = cmds.ls(type='transform', long=True)
        
        if all_transforms:
            # Filter out default Maya nodes
            default_nodes = ['persp', 'top', 'front', 'side', 'bottom', 'back', 'left']
            custom_nodes = [node for node in all_transforms if cmds.ls(node, long=False)[0] not in default_nodes]
            
            # If scene is empty (no custom transform nodes), pass validation
            if not custom_nodes:
                issues.append({
                    'object': "Scene",
                    'message': "All validations passed",
                    'fixed': True
                })
                return {
                    "status": "success",
                    "issues": issues,
                    "total_checked": 0,
                    "total_issues": len(issues)
                }
            
            # Find root level nodes (no parent or parent is world)
            root_nodes = []
            for node in custom_nodes:
                try:
                    parent = cmds.listRelatives(node, parent=True, fullPath=True)
                    if not parent or parent[0] == '|':
                        root_nodes.append(node)
                except:
                    continue
            
            # Find groups that match the queried asset name
            matching_groups = []
            other_root_nodes = []
            
            for node in root_nodes:
                node_name = cmds.ls(node, long=False)[0]
                # Check for exact match with asset name (case-insensitive)
                if node_name.lower() == asset_name.lower():
                    matching_groups.append(node)
                else:
                    other_root_nodes.append(node)
            
            if mode == "check":
                # Check for proper outliner structure using queried asset name
                if asset_name == "unknown":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot check outliner: asset name unknown (JOB_PATH not set)",
                        'fixed': False
                    })
                elif len(matching_groups) == 0:
                    # No group matching the asset name found
                    issues.append({
                        'object': "Scene",
                        'message': f"Top group '{asset_name}' (from JOB_PATH) not found in outliner. Please create or rename top group to match.",
                        'fixed': False
                    })
                elif len(matching_groups) > 1:
                    # Multiple groups with same name found
                    matching_names = [cmds.ls(node, long=False)[0] for node in matching_groups]
                    issues.append({
                        'object': "Scene",
                        'message': f"Multiple groups named '{asset_name}' found: {', '.join(matching_names)}. Should have only one.",
                        'fixed': False
                    })
                elif len(other_root_nodes) > 0:
                    # Other root nodes found (should be under asset group)
                    other_names = [cmds.ls(node, long=False)[0] for node in other_root_nodes[:10]]
                    if len(other_root_nodes) > 10:
                        other_names.append(f"... and {len(other_root_nodes) - 10} more")
                    issues.append({
                        'object': "Scene",
                        'message': f"Found {len(other_root_nodes)} root nodes that should be under '{asset_name}': {', '.join(other_names)}",
                        'fixed': False
                    })
                else:
                    # Perfect structure - one matching group, no other root nodes
                    matching_name = cmds.ls(matching_groups[0], long=False)[0]
                    issues.append({
                        'object': "Scene",
                        'message': f"Outliner is clean: only '{matching_name}' exists with default Maya elements",
                        'fixed': True
                    })
            
            elif mode == "fix":
                try:
                    if asset_name == "unknown":
                        issues.append({
                            'object': "Scene",
                            'message': "Cannot fix outliner: asset name unknown (JOB_PATH not set)",
                            'fixed': False
                        })
                        return {
                            "status": "success",
                            "issues": issues,
                            "total_checked": len(all_transforms) if 'all_transforms' in locals() else 0,
                            "total_issues": len(issues)
                        }
                    
                    if len(matching_groups) == 0:
                        # No group matching asset name - try to rename an existing group
                        if len(other_root_nodes) == 1:
                            # Only one root node - rename it to match asset name
                            source_node = other_root_nodes[0]
                            source_name = cmds.ls(source_node, long=False)[0]
                            
                            try:
                                # Check if target name already exists
                                if cmds.objExists(asset_name) and source_node != asset_name:
                                    issues.append({
                                        'object': "Scene",
                                        'message': f"Cannot rename '{source_name}' to '{asset_name}': target name already exists",
                                        'fixed': False
                                    })
                                else:
                                    new_name = cmds.rename(source_node, asset_name)
                                    issues.append({
                                        'object': new_name,
                                        'message': f"Renamed '{source_name}' to '{asset_name}' to match JOB_PATH",
                                        'fixed': True
                                    })
                            except Exception as e:
                                issues.append({
                                    'object': source_name,
                                    'message': f"Failed to rename '{source_name}' to '{asset_name}': {str(e)}",
                                    'fixed': False
                                })
                        elif len(other_root_nodes) > 1:
                            # Multiple root nodes - show dialog asking user to choose
                            other_names = [cmds.ls(node, long=False)[0] for node in other_root_nodes]
                            cmds.confirmDialog(
                                title="Outliner Structure Issue",
                                message=f"Multiple root nodes found: {', '.join(other_names)}. Please rename one to '{asset_name}' manually, then run fix again.",
                                button=["OK"],
                                defaultButton="OK"
                            )
                            issues.append({
                                'object': "Scene",
                                'message': f"Multiple root nodes found. Please rename one to '{asset_name}' manually.",
                                'fixed': False
                            })
                        else:
                            # No root nodes at all
                            cmds.confirmDialog(
                                title="Outliner Structure Issue",
                                message=f"No top group found. Please create a group named '{asset_name}' manually.",
                                button=["OK"],
                                defaultButton="OK"
                            )
                            issues.append({
                                'object': "Scene",
                                'message': f"No top group found. Please create a group named '{asset_name}' manually.",
                                'fixed': False
                            })
                        
                        return {
                            "status": "success",
                            "issues": issues,
                            "total_checked": len(all_transforms) if 'all_transforms' in locals() else 0,
                            "total_issues": len(issues)
                        }
                    
                    # Use the first matching group as the target
                    target_group = matching_groups[0]
                    target_name = cmds.ls(target_group, long=False)[0]
                    
                    # Delete extra matching groups if multiple exist
                    deleted_groups = 0
                    if len(matching_groups) > 1:
                        for matching_group in matching_groups[1:]:
                            if cmds.objExists(matching_group):
                                cmds.delete(matching_group)
                                deleted_groups += 1
                    
                    # Move all other root nodes under the target group
                    moved_nodes = 0
                    for node in other_root_nodes:
                        try:
                            cmds.parent(node, target_group)
                            moved_nodes += 1
                        except:
                            continue
                    
                    # Report results
                    if deleted_groups > 0 or moved_nodes > 0:
                        issues.append({
                            'object': target_name,
                            'message': f"Fixed: deleted {deleted_groups} extra groups named '{asset_name}', moved {moved_nodes} nodes under '{target_name}'",
                            'fixed': True
                        })
                    else:
                        issues.append({
                            'object': target_name,
                            'message': f"Outliner already clean: '{target_name}'",
                            'fixed': True
                        })
                        
                except Exception as e:
                    issues.append({
                        'object': "Scene",
                        'message': f"Failed to organize outliner: {str(e)}",
                        'fixed': False
                    })
        else:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': "No transform nodes found to organize",
                    'fixed': True
                })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "Cannot run in referenced scene",
                'fixed': False
            })
        elif mode == "fix":
            issues.append({
                'object': "Scene",
                'message': "Cannot fix in referenced scene",
                'fixed': False
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(all_transforms) if 'all_transforms' in locals() else 0,
        "total_issues": len(issues)
    }
