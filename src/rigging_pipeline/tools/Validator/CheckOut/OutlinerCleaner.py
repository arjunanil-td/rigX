"""
OutlinerCleaner Validation Module
Cleans up outliner by organizing and removing unnecessary nodes
"""

import maya.cmds as cmds

DESCRIPTION = "Clean and organize outliner structure"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    if not cmds.file(query=True, reference=True):
        # Get all transform nodes in the scene
        all_transforms = cmds.ls(type='transform', long=True)
        
        if all_transforms:
            # Filter out default Maya nodes
            default_nodes = ['persp', 'top', 'front', 'side', 'bottom', 'back', 'left']
            custom_nodes = [node for node in all_transforms if cmds.ls(node, long=False)[0] not in default_nodes]
            
            # Find root level nodes (no parent or parent is world)
            root_nodes = []
            for node in custom_nodes:
                try:
                    parent = cmds.listRelatives(node, parent=True, fullPath=True)
                    if not parent or parent[0] == '|':
                        root_nodes.append(node)
                except:
                    continue
            
            # Find valid groups (nodes starting with "char", "prop", or "vhcl")
            valid_groups = []
            other_root_nodes = []
            
            for node in root_nodes:
                node_name = cmds.ls(node, long=False)[0]
                if node_name.startswith(("char", "prop", "vhcl")):
                    valid_groups.append(node)
                else:
                    other_root_nodes.append(node)
            
            if mode == "check":
                # Check for proper outliner structure
                if len(valid_groups) == 0:
                    # No valid group found
                    issues.append({
                        'object': "Scene",
                        'message': "Top group is not starting with 'char', 'prop', or 'vhcl'. Please add prefix accordingly.",
                        'fixed': False
                    })
                elif len(valid_groups) > 1:
                    # Multiple valid groups found
                    valid_names = [cmds.ls(node, long=False)[0] for node in valid_groups]
                    issues.append({
                        'object': "Scene",
                        'message': f"Multiple top groups found: {', '.join(valid_names)}. Should have only one.",
                        'fixed': False
                    })
                elif len(other_root_nodes) > 0:
                    # Other root nodes found (should be under valid group)
                    other_names = [cmds.ls(node, long=False)[0] for node in other_root_nodes[:10]]
                    if len(other_root_nodes) > 10:
                        other_names.append(f"... and {len(other_root_nodes) - 10} more")
                    issues.append({
                        'object': "Scene",
                        'message': f"Found {len(other_root_nodes)} root nodes that should be under top group: {', '.join(other_names)}",
                        'fixed': False
                    })
                else:
                    # Perfect structure - one valid group, no other root nodes
                    valid_name = cmds.ls(valid_groups[0], long=False)[0]
                    issues.append({
                        'object': "Scene",
                        'message': f"Outliner is clean: only {valid_name} exists with default Maya elements",
                        'fixed': True
                    })
            
            elif mode == "fix":
                try:
                    if len(valid_groups) == 0:
                        # Show dialog with message only
                        cmds.confirmDialog(
                            title="Outliner Structure Issue",
                            message="Top group prefix is not matching with 'char', 'prop', or 'vhcl'. Please update it manually according to the asset.",
                            button=["OK"],
                            defaultButton="OK"
                        )
                        
                        # Cannot automatically fix - user needs to add prefix manually
                        issues.append({
                            'object': "Scene",
                            'message': "Cannot automatically fix: Top group is not starting with 'char', 'prop', or 'vhcl'. Please rename your top group manually.",
                            'fixed': False
                        })
                        return {
                            "status": "success",
                            "issues": issues,
                            "total_checked": len(all_transforms) if 'all_transforms' in locals() else 0,
                            "total_issues": len(issues)
                        }
                    
                    # Use the first valid group as the target
                    target_valid_group = valid_groups[0]
                    target_valid_name = cmds.ls(target_valid_group, long=False)[0]
                    
                    # Delete extra valid groups if multiple exist
                    deleted_groups = 0
                    if len(valid_groups) > 1:
                        for valid_group in valid_groups[1:]:
                            if cmds.objExists(valid_group):
                                cmds.delete(valid_group)
                                deleted_groups += 1
                    
                    # Move all other root nodes under the valid group
                    moved_nodes = 0
                    for node in other_root_nodes:
                        try:
                            cmds.parent(node, target_valid_group)
                            moved_nodes += 1
                        except:
                            continue
                    
                    # Report results
                    if deleted_groups > 0 or moved_nodes > 0:
                        issues.append({
                            'object': target_valid_name,
                            'message': f"Fixed: deleted {deleted_groups} extra top groups, moved {moved_nodes} nodes under {target_valid_name}",
                            'fixed': True
                        })
                    else:
                        issues.append({
                            'object': target_valid_name,
                            'message': f"Outliner already clean: {target_valid_name}",
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
