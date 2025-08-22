"""
NgSkinToolsCleaner Validation Module
Cleans up NgSkinTools nodes
"""

import maya.cmds as cmds

DESCRIPTION = "Clean NgSkinTools nodes"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get NgSkinTools nodes to check
    ngst_nodes = cmds.ls(type='ngst2SkinLayerData')
    
    if ngst_nodes:
        for node in ngst_nodes:
            if cmds.objExists(node):
                if mode == "check":
                    issues.append({
                        'object': node,
                        'message': f"NgSkinTools node found: {node}",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Delete the NgSkinTools node
                        cmds.delete(node)
                        issues.append({
                            'object': node,
                            'message': f"NgSkinTools node cleaned: {node}",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': node,
                            'message': f"Failed to clean NgSkinTools node: {str(e)}",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': node,
                        'message': f"NgSkinTools node not found: {node}",
                        'fixed': False
                    })
        
        # Clear selection after cleanup
        cmds.select(clear=True)
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No NgSkinTools nodes found",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(ngst_nodes) if 'ngst_nodes' in locals() else 0,
        "total_issues": len(issues)
    }
