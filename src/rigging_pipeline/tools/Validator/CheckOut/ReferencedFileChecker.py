"""
ReferencedFileChecker Validation Module
Checks for referenced files and their status
"""

import maya.cmds as cmds

DESCRIPTION = "Check and validate referenced files"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    print(f"DEBUG: ReferencedFileChecker - Starting validation in mode: {mode}")
    
    # Get all reference nodes in the scene
    reference_nodes = cmds.ls(type='reference')
    print(f"DEBUG: ReferencedFileChecker - Found reference nodes: {reference_nodes}")
    
    if reference_nodes:
        # Filter out default Maya references
        default_refs = ['sharedReferenceNode']
        custom_refs = [ref for ref in reference_nodes if ref not in default_refs]
        print(f"DEBUG: ReferencedFileChecker - Custom references after filtering: {custom_refs}")
        
        if custom_refs:
            for ref_node in custom_refs:
                try:
                    # Get reference file path
                    ref_file = cmds.referenceQuery(ref_node, filename=True)
                    ref_namespace = cmds.referenceQuery(ref_node, namespace=True)
                    print(f"DEBUG: ReferencedFileChecker - Processing reference: {ref_node} -> {ref_file} (namespace: {ref_namespace})")
                    
                    # Check if reference file exists
                    import os
                    file_exists = os.path.exists(ref_file)
                    print(f"DEBUG: ReferencedFileChecker - File exists: {file_exists}")
                    
                    if file_exists:
                        if mode == "check":
                            issues.append({
                                'object': ref_node,
                                'message': f"Reference found: {ref_namespace} -> {os.path.basename(ref_file)} (consider removing or importing)",
                                'fixed': False
                            })
                        elif mode == "fix":
                            # Ask user what to do with this valid reference
                            print(f"DEBUG: ReferencedFileChecker - Found valid reference: {ref_namespace} -> {ref_file}")
                            
                            try:
                                result = cmds.confirmDialog(
                                    title="Reference Found",
                                    message=f"Reference found: {ref_namespace} -> {os.path.basename(ref_file)}",
                                    button=["Remove Reference", "Import Reference", "Keep Reference"],
                                    defaultButton="Keep Reference",
                                    cancelButton="Keep Reference",
                                    dismissString="Keep Reference"
                                )
                                print(f"DEBUG: ReferencedFileChecker - User chose: {result}")
                            except Exception as dialog_error:
                                print(f"DEBUG: ReferencedFileChecker - Dialog error: {dialog_error}")
                                result = "Keep Reference"  # Default to keep if dialog fails
                            
                            if result == "Remove Reference":
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
                            elif result == "Import Reference":
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
                            print(f"DEBUG: ReferencedFileChecker - Found broken reference: {ref_namespace} -> {ref_file}")
                            
                            # Ask user what they want to do with the broken reference
                            try:
                                result = cmds.confirmDialog(
                                    title="Broken Reference Found",
                                    message=f"Broken reference found: {ref_namespace} -> {os.path.basename(ref_file)}\n\nWhat would you like me to do?",
                                    button=["Remove Reference", "Import Reference", "Skip"],
                                    defaultButton="Remove Reference",
                                    cancelButton="Skip",
                                    dismissString="Skip"
                                )
                                print(f"DEBUG: ReferencedFileChecker - User chose: {result}")
                            except Exception as dialog_error:
                                print(f"DEBUG: ReferencedFileChecker - Dialog error: {dialog_error}")
                                result = "Skip"  # Default to skip if dialog fails
                            
                            if result == "Remove Reference":
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
                            elif result == "Import Reference":
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
