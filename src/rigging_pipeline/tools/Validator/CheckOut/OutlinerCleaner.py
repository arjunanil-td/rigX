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
            
            # Check for nodes that can be organized
            nodes_to_organize = []
            
            for node in custom_nodes:
                try:
                    # Check if node is at root level (no parent or parent is world)
                    parent = cmds.listRelatives(node, parent=True, fullPath=True)
                    if not parent or parent[0] == '|':
                        # Check if node has children
                        children = cmds.listRelatives(node, children=True, fullPath=True)
                        if children:
                            # This is a root node with children - could be organized
                            nodes_to_organize.append(node)
                except:
                    continue
            
            if nodes_to_organize:
                if mode == "check":
                    # Show specific nodes that can be organized
                    node_names = [cmds.ls(node, long=False)[0] for node in nodes_to_organize[:10]]  # Show first 10
                    if len(nodes_to_organize) > 10:
                        node_names.append(f"... and {len(nodes_to_organize) - 10} more")
                    
                    issues.append({
                        'object': "Scene",
                        'message': f"Found {len(nodes_to_organize)} root nodes that could be organized: {', '.join(node_names)}",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Create organization groups if they don't exist
                        org_groups = {
                            'Geometry_Grp': [],
                            'Rig_Grp': [],
                            'Controls_Grp': [],
                            'Joints_Grp': [],
                            'Utility_Grp': []
                        }
                        
                        for node in nodes_to_organize:
                            node_name = cmds.ls(node, long=False)[0]
                            node_type = cmds.objectType(node)
                            
                            # Determine which group this node belongs to
                            target_group = None
                            if node_type == 'mesh' or 'geo' in node_name.lower():
                                target_group = 'Geometry_Grp'
                            elif 'ctrl' in node_name.lower() or 'control' in node_name.lower():
                                target_group = 'Controls_Grp'
                            elif node_type == 'joint':
                                target_group = 'Joints_Grp'
                            elif 'rig' in node_name.lower():
                                target_group = 'Rig_Grp'
                            else:
                                target_group = 'Utility_Grp'
                            
                            # Create group if it doesn't exist
                            if not cmds.objExists(target_group):
                                cmds.group(empty=True, name=target_group)
                                # Set group attributes
                                cmds.setAttr(f"{target_group}.visibility", 1)
                                cmds.setAttr(f"{target_group}.overrideEnabled", 0)
                            
                            # Parent node to appropriate group
                            try:
                                cmds.parent(node, target_group)
                                org_groups[target_group].append(node_name)
                            except:
                                continue
                        
                        # Report organization results
                        organized_count = sum(len(nodes) for nodes in org_groups.values())
                        issues.append({
                            'object': "Scene",
                            'message': f"Outliner organized: {organized_count} nodes moved to appropriate groups",
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
                        'message': "Outliner is already well organized",
                        'fixed': True
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
