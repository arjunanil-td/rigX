"""
ReferencedFileChecker Validation Module
Checks for referenced files and their status
"""

import maya.cmds as cmds

DESCRIPTION = "Check and validate referenced files"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get all reference nodes in the scene
    reference_nodes = cmds.ls(type='reference')
    
    if reference_nodes:
        # Filter out default Maya references
        default_refs = ['sharedReferenceNode']
        custom_refs = [ref for ref in reference_nodes if ref not in default_refs]
        
        if custom_refs:
            for ref_node in custom_refs:
                try:
                    # Get reference file path
                    ref_file = cmds.referenceQuery(ref_node, filename=True)
                    ref_namespace = cmds.referenceQuery(ref_node, namespace=True)
                    
                    # Check if reference file exists
                    import os
                    if os.path.exists(ref_file):
                        if mode == "check":
                            issues.append({
                                'object': ref_node,
                                'message': f"Reference is valid: {ref_namespace} -> {os.path.basename(ref_file)}",
                                'fixed': True
                            })
                        elif mode == "fix":
                            # Reference is valid, no fix needed
                            issues.append({
                                'object': ref_node,
                                'message': f"Reference is valid: {ref_namespace}",
                                'fixed': True
                            })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': ref_node,
                                'message': f"Broken reference: {ref_namespace} -> {os.path.basename(ref_file)} (file not found)",
                                'fixed': False
                            })
                        elif mode == "fix":
                            try:
                                # Remove broken reference
                                cmds.file(removeReference=True, referenceNode=ref_node)
                                issues.append({
                                    'object': ref_node,
                                    'message': f"Broken reference removed: {ref_namespace}",
                                    'fixed': True
                                })
                            except Exception as e:
                                issues.append({
                                    'object': ref_node,
                                    'message': f"Failed to remove broken reference: {str(e)}",
                                    'fixed': False
                                })
                except Exception as e:
                    if mode == "check":
                        issues.append({
                            'object': ref_node,
                            'message': f"Error checking reference: {str(e)}",
                            'fixed': False
                        })
        else:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': "No custom references found - only default Maya references present",
                    'fixed': True
                })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No references found in scene - this is a clean scene file",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(reference_nodes) if reference_nodes else 0,
        "total_issues": len(issues)
    }
