"""
ReferencedFileChecker Validation Module
Checks for referenced files and their status
"""

import maya.cmds as cmds

DESCRIPTION = "Check and validate referenced files"

def run_validation(mode="check", objList=None, action=None):
    """Run the validation module
    
    Args:
        mode (str): "check" or "fix"
        objList (list): List of objects to check (optional)
        action (str): When in fix mode, specify the action to take: "import", "remove", or "keep"
    """
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
                    file_exists = os.path.exists(ref_file)
                    
                    if file_exists:
                        if mode == "check":
                            issues.append({
                                'object': ref_node,
                                'message': f"Reference found: {ref_namespace} -> {os.path.basename(ref_file)} (consider removing or importing)",
                                'fixed': False
                            })
                        elif mode == "fix":
                            # Use the action parameter if provided, otherwise show dialog
                            if action:
                                result = action
                            else:
                                # Ask user what to do with this valid reference
                                result = cmds.confirmDialog(
                                    title="Reference Found",
                                    message=f"Reference found: {ref_namespace} -> {os.path.basename(ref_file)}",
                                    button=["Remove Reference", "Import Reference", "Keep Reference"],
                                    defaultButton="Keep Reference",
                                    cancelButton="Keep Reference",
                                    dismissString="Keep Reference"
                                )
                            
                            if result == "Remove Reference" or result == "remove":
                                try:
                                    # Remove the reference
                                    cmds.file(removeReference=True, referenceNode=ref_node)
                                    issues.append({
                                        'object': ref_node,
                                        'message': f"Reference removed: {ref_namespace}",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': ref_node,
                                        'message': f"Failed to remove reference: {str(e)}",
                                        'fixed': False
                                    })
                            elif result == "Import Reference" or result == "import":
                                try:
                                    # Import the reference (this will make it part of the scene)
                                    cmds.file(importReference=True, referenceNode=ref_node)
                                    issues.append({
                                        'object': ref_node,
                                        'message': f"Reference imported into scene: {ref_namespace}",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': ref_node,
                                        'message': f"Failed to import reference: {str(e)}",
                                        'fixed': False
                                    })
                            else:
                                # User chose to keep the reference
                                issues.append({
                                    'object': ref_node,
                                    'message': f"Reference kept: {ref_namespace}",
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
                            # Use the action parameter if provided, otherwise show dialog
                            if action:
                                result = action
                            else:
                                # Ask user what they want to do with the broken reference
                                result = cmds.confirmDialog(
                                    title="Broken Reference Found",
                                    message=f"Broken reference found: {ref_namespace} -> {os.path.basename(ref_file)}\n\nWhat would you like me to do?",
                                    button=["Remove Reference", "Import Reference", "Skip"],
                                    defaultButton="Remove Reference",
                                    cancelButton="Skip",
                                    dismissString="Skip"
                                )
                            
                            if result == "Remove Reference" or result == "remove":
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
                            elif result == "Import Reference" or result == "import":
                                try:
                                    # Import the reference (this will make it part of the scene)
                                    cmds.file(importReference=True, referenceNode=ref_node)
                                    issues.append({
                                        'object': ref_node,
                                        'message': f"Reference imported into scene: {ref_namespace}",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': ref_node,
                                        'message': f"Failed to import reference: {str(e)}",
                                        'fixed': False
                                    })
                            else:
                                # User chose to skip
                                issues.append({
                                    'object': ref_node,
                                    'message': f"Broken reference skipped: {ref_namespace}",
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
