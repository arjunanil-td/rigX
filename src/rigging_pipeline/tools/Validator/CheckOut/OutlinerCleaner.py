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
            
            # Find char groups (nodes starting with "char")
            char_groups = []
            other_root_nodes = []
            
            for node in root_nodes:
                node_name = cmds.ls(node, long=False)[0]
                if node_name.startswith("char"):
                    char_groups.append(node)
                else:
                    other_root_nodes.append(node)
            
            if mode == "check":
                # Check for proper outliner structure
                if len(char_groups) == 0:
                    # No char group found
                    issues.append({
                        'object': "Scene",
                        'message': "No group starting with 'char' prefix found in outliner",
                        'fixed': False
                    })
                elif len(char_groups) > 1:
                    # Multiple char groups found
                    char_names = [cmds.ls(node, long=False)[0] for node in char_groups]
                    issues.append({
                        'object': "Scene",
                        'message': f"Multiple char groups found: {', '.join(char_names)}. Should have only one.",
                        'fixed': False
                    })
                elif len(other_root_nodes) > 0:
                    # Other root nodes found (should be under char group)
                    other_names = [cmds.ls(node, long=False)[0] for node in other_root_nodes[:10]]
                    if len(other_root_nodes) > 10:
                        other_names.append(f"... and {len(other_root_nodes) - 10} more")
                    issues.append({
                        'object': "Scene",
                        'message': f"Found {len(other_root_nodes)} root nodes that should be under char group: {', '.join(other_names)}",
                        'fixed': False
                    })
                else:
                    # Perfect structure - one char group, no other root nodes
                    char_name = cmds.ls(char_groups[0], long=False)[0]
                    issues.append({
                        'object': "Scene",
                        'message': f"Outliner is clean: only {char_name} exists with default Maya elements",
                        'fixed': True
                    })
            
            elif mode == "fix":
                try:
                    if len(char_groups) == 0:
                        # Create a default char group
                        char_group_name = "charDefault"
                        cmds.group(empty=True, name=char_group_name)
                        char_groups = [char_group_name]
                        issues.append({
                            'object': char_group_name,
                            'message': f"Created default char group: {char_group_name}",
                            'fixed': True
                        })
                    
                    # Use the first char group as the target
                    target_char_group = char_groups[0]
                    target_char_name = cmds.ls(target_char_group, long=False)[0]
                    
                    # Delete extra char groups if multiple exist
                    deleted_groups = 0
                    if len(char_groups) > 1:
                        for char_group in char_groups[1:]:
                            if cmds.objExists(char_group):
                                cmds.delete(char_group)
                                deleted_groups += 1
                    
                    # Move all other root nodes under the char group
                    moved_nodes = 0
                    for node in other_root_nodes:
                        try:
                            cmds.parent(node, target_char_group)
                            moved_nodes += 1
                        except:
                            continue
                    
                    # Report results
                    if deleted_groups > 0 or moved_nodes > 0:
                        issues.append({
                            'object': target_char_name,
                            'message': f"Fixed: deleted {deleted_groups} extra char groups, moved {moved_nodes} nodes under {target_char_name}",
                            'fixed': True
                        })
                    else:
                        issues.append({
                            'object': target_char_name,
                            'message': f"Outliner already clean: {target_char_name}",
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
