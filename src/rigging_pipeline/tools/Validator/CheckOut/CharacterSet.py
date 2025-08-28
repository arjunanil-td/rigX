"""
CharacterSet Validation Module
Validates and manages character sets in Maya scenes
"""

import maya.cmds as cmds

DESCRIPTION = "Validate and manage character sets for proper rigging workflow"

def create_anim_set_from_controls(motion_group="MotionSystem", parent_set="Sets", new_set_name="AnimSet"):
    """Create AnimSet from NURBS curve controls under MotionSystem group"""
    if not cmds.objExists(motion_group):
        cmds.warning(f"Group '{motion_group}' does not exist.")
        return None

    # Find all child transforms under MotionSystem
    all_children = cmds.listRelatives(motion_group, allDescendents=True, type="transform") or []
    
    # Filter for those with nurbsCurve shapes
    control_transforms = []
    for node in all_children:
        shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
        for shape in shapes:
            if cmds.nodeType(shape) == "nurbsCurve":
                control_transforms.append(node)
                break  # Stop after first valid shape

    if not control_transforms:
        cmds.warning("No NURBS curve controls found under MotionSystem.")
        return None

    # Create new set if it doesn't exist
    if not cmds.objExists(new_set_name):
        anim_set = cmds.sets(control_transforms, name=new_set_name)
    else:
        anim_set = new_set_name
        cmds.sets(control_transforms, edit=True, forceElement=anim_set)

    # Parent new set under the main 'Sets' set
    if cmds.objExists(parent_set):
        cmds.sets(anim_set, include=parent_set)
    else:
        cmds.warning(f"Parent set '{parent_set}' does not exist. 'AnimSet' created standalone.")

    print(f"Created '{new_set_name}' with {len(control_transforms)} controls.")
    return anim_set

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    try:
        if mode == "check":
            # First check: Look for 'Sets' set
            try:
                sets_node = cmds.ls("Sets", type='objectSet')
                print(f"DEBUG: sets_node result: {sets_node} (type: {type(sets_node)})")
            except Exception as e:
                print(f"DEBUG: Error in cmds.ls for Sets: {e}")
                sets_node = []
            
            if not sets_node:
                # 'Sets' set not found - this is an error
                issues.append({
                    'object': "Scene",
                    'message': "Missing 'Sets' set - required for character set validation",
                    'fixed': False
                })
            else:
                # 'Sets' set found, now check for 'AnimSet', 'DeformSet', and optionally 'FaceControlSet' parented to it
                required_sets = ["AnimSet", "DeformSet"]  # FaceControlSet is optional
                optional_sets = ["FaceControlSet"]
                missing_sets = []
                properly_parented_sets = []
                
                # Check required sets first
                for set_name in required_sets:
                    try:
                        current_set = cmds.ls(set_name, type='objectSet')
                        print(f"DEBUG: {set_name} result: {current_set} (type: {type(current_set)})")
                        
                        if not current_set:
                            # Set not found - this is an error for required sets
                            missing_sets.append(set_name)
                        else:
                            # Set exists, check if it's parented to 'Sets'
                            try:
                                print(f"DEBUG: Checking membership of {set_name} in Sets")
                                # Get all members of the Sets set
                                sets_members = cmds.sets("Sets", query=True) or []
                                print(f"DEBUG: Sets members: {sets_members}")
                                
                                # Check if current set is in the members list
                                is_member = set_name in sets_members
                                print(f"DEBUG: {set_name} is_member result: {is_member}")
                                
                                if not is_member:
                                    # Set is not parented to 'Sets' - this is an error
                                    issues.append({
                                        'object': set_name,
                                        'message': f"'{set_name}' is not parented to 'Sets' set",
                                        'fixed': False
                                    })
                                else:
                                    properly_parented_sets.append(set_name)
                            except Exception as e:
                                print(f"DEBUG: Error checking membership for {set_name}: {e}")
                                # If there's an error checking membership, assume it's not parented
                                issues.append({
                                    'object': set_name,
                                    'message': f"'{set_name}' is not properly parented to 'Sets' set: {str(e)}",
                                    'fixed': False
                                })
                    except Exception as e:
                        print(f"DEBUG: Error in cmds.ls for {set_name}: {e}")
                        missing_sets.append(set_name)
                
                # Check optional sets (only if they exist)
                for set_name in optional_sets:
                    try:
                        current_set = cmds.ls(set_name, type='objectSet')
                        print(f"DEBUG: Optional {set_name} result: {current_set} (type: {type(current_set)})")
                        
                        if current_set:
                            # Optional set exists, check if it's parented to 'Sets'
                            try:
                                print(f"DEBUG: Checking membership of optional {set_name} in Sets")
                                # Get all members of the Sets set
                                sets_members = cmds.sets("Sets", query=True) or []
                                print(f"DEBUG: Sets members: {sets_members}")
                                
                                # Check if current set is in the members list
                                is_member = set_name in sets_members
                                print(f"DEBUG: Optional {set_name} is_member result: {is_member}")
                                
                                if not is_member:
                                    # Optional set is not parented to 'Sets' - this is an error
                                    issues.append({
                                        'object': set_name,
                                        'message': f"'{set_name}' is not parented to 'Sets' set",
                                        'fixed': False
                                    })
                                else:
                                    properly_parented_sets.append(set_name)
                            except Exception as e:
                                print(f"DEBUG: Error checking membership for optional {set_name}: {e}")
                                # If there's an error checking membership, assume it's not parented
                                issues.append({
                                    'object': set_name,
                                    'message': f"'{set_name}' is not properly parented to 'Sets' set: {str(e)}",
                                    'fixed': False
                                })
                        else:
                            # Optional set is missing - show warning in check mode
                            issues.append({
                                'object': set_name,
                                'message': f"'{set_name}' is missing (optional set)",
                                'fixed': False
                            })
                    except Exception as e:
                        print(f"DEBUG: Error in cmds.ls for optional {set_name}: {e}")
                        # Don't add optional sets to missing_sets if there's an error
                
                # Report missing required sets only
                for missing_set in missing_sets:
                    issues.append({
                        'object': "Scene",
                        'message': f"Missing '{missing_set}' - required for character set validation",
                        'fixed': False
                    })
                
                # If all required sets exist and are properly parented, report success
                if len(properly_parented_sets) >= len(required_sets):
                    # Only show success if there are no issues at all
                    if len(issues) == 0:
                        success_message = f"Character set structure is valid: 'Sets' set exists and all required sets ({', '.join(required_sets)}) are properly parented"
                        if len(properly_parented_sets) > len(required_sets):
                            # Include info about optional sets that are also properly parented
                            optional_parented = [s for s in properly_parented_sets if s in optional_sets]
                            if optional_parented:
                                success_message += f" (optional sets {', '.join(optional_parented)} are also properly parented)"
                        
                        issues.append({
                            'object': "Scene",
                            'message': success_message,
                            'fixed': True
                        })
                    # If there are issues (like missing optional sets), don't show success message
        
        elif mode == "fix":
            # Try to fix the issues
            try:
                sets_node = cmds.ls("Sets", type='objectSet')
                print(f"DEBUG: Fix mode - sets_node: {sets_node}")
            except Exception as e:
                print(f"DEBUG: Error in fix mode cmds.ls for Sets: {e}")
                sets_node = []
            
            if not sets_node:
                # Create 'Sets' set if it doesn't exist
                try:
                    cmds.sets(name="Sets", empty=True)
                    issues.append({
                        'object': "Sets",
                        'message': "Created missing 'Sets' set",
                        'fixed': True
                    })
                except Exception as e:
                    issues.append({
                        'object': "Scene",
                        'message': f"Failed to create 'Sets' set: {str(e)}",
                        'fixed': False
                    })
                    return {"status": "success", "issues": issues, "total_checked": 1, "total_issues": len(issues)}
            
            # Check if all required sets exist
            required_sets = ["AnimSet", "DeformSet"]
            optional_sets = ["FaceControlSet"]
            
            # Create required sets if they don't exist
            for set_name in required_sets:
                try:
                    current_set = cmds.ls(set_name, type='objectSet')
                    print(f"DEBUG: Fix mode - {set_name}: {current_set}")
                    
                    if not current_set:
                        # Create the missing required set
                        try:
                            if set_name == "AnimSet":
                                # Use the special function to create AnimSet from controls
                                anim_set = create_anim_set_from_controls()
                                if anim_set:
                                    issues.append({
                                        'object': set_name,
                                        'message': f"Created missing '{set_name}' from MotionSystem controls",
                                        'fixed': True
                                    })
                                else:
                                    # Fallback to empty set if no controls found
                                    cmds.sets(name=set_name, empty=True)
                                    issues.append({
                                        'object': set_name,
                                        'message': f"Created missing '{set_name}' as empty set (no controls found)",
                                        'fixed': True
                                    })
                            else:
                                # Create other required sets as empty sets
                                cmds.sets(name=set_name, empty=True)
                                issues.append({
                                    'object': set_name,
                                    'message': f"Created missing '{set_name}'",
                                    'fixed': True
                                })
                        except Exception as e:
                            issues.append({
                                'object': "Scene",
                                'message': f"Failed to create '{set_name}': {str(e)}",
                                'fixed': False
                            })
                            return {"status": "success", "issues": issues, "total_checked": 1, "total_issues": len(issues)}
                except Exception as e:
                    print(f"DEBUG: Error in fix mode cmds.ls for {set_name}: {e}")
                    # Try to create the set anyway
                    try:
                        if set_name == "AnimSet":
                            # Use the special function to create AnimSet from controls
                            anim_set = create_anim_set_from_controls()
                            if anim_set:
                                issues.append({
                                    'object': set_name,
                                    'message': f"Created missing '{set_name}' from MotionSystem controls",
                                    'fixed': True
                                })
                            else:
                                # Fallback to empty set if no controls found
                                cmds.sets(name=set_name, empty=True)
                                issues.append({
                                    'object': set_name,
                                    'message': f"Created missing '{set_name}' as empty set (no controls found)",
                                    'fixed': True
                                })
                        else:
                            # Create other required sets as empty sets
                            cmds.sets(name=set_name, empty=True)
                            issues.append({
                                'object': set_name,
                                'message': f"Created missing '{set_name}'",
                                'fixed': True
                            })
                    except Exception as create_error:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to create '{set_name}': {str(create_error)}",
                            'fixed': False
                        })
                        return {"status": "success", "issues": issues, "total_checked": 1, "total_issues": len(issues)}
            
            # Handle optional sets (only create if they don't exist, don't fail if creation fails)
            for set_name in optional_sets:
                try:
                    current_set = cmds.ls(set_name, type='objectSet')
                    print(f"DEBUG: Fix mode - optional {set_name}: {current_set}")
                    
                    if not current_set:
                        # Optional set is missing, ask user if they want to continue
                        result = cmds.confirmDialog(
                            title="Optional Set Missing",
                            message=f"'{set_name}' is missing. Would you like to continue without it?",
                            button=["Yes", "No"],
                            defaultButton="Yes",
                            cancelButton="No",
                            dismissString="No"
                        )
                        
                        if result == "No":
                            # User chose not to continue
                            issues.append({
                                'object': set_name,
                                'message': f"User chose not to continue without '{set_name}'",
                                'fixed': False
                            })
                            # Return early since user doesn't want to continue
                            return {"status": "success", "issues": issues, "total_checked": 1, "total_issues": len(issues)}
                        else:
                            # User chose to continue, but don't create optional sets automatically
                            issues.append({
                                'object': set_name,
                                'message': f"'{set_name}' is missing but user chose to continue without it",
                                'fixed': True
                            })
                except Exception as e:
                    print(f"DEBUG: Error in fix mode cmds.ls for optional {set_name}: {e}")
                    # Don't fail for optional sets
            
            # Check if all existing sets (required + optional) are parented to 'Sets' and fix if needed
            all_sets_to_check = required_sets + optional_sets
            
            for set_name in all_sets_to_check:
                try:
                    current_set = cmds.ls(set_name, type='objectSet')
                    if current_set:  # Only check sets that actually exist
                        print(f"DEBUG: Fix mode - checking membership for {set_name}")
                        # Get all members of the Sets set
                        sets_members = cmds.sets("Sets", query=True) or []
                        print(f"DEBUG: Fix mode - Sets members: {sets_members}")
                        
                        # Check if current set is in the members list
                        is_member = set_name in sets_members
                        print(f"DEBUG: Fix mode - {set_name} is_member: {is_member}")
                        
                        if not is_member:
                            # Parent current set to 'Sets'
                            try:
                                cmds.sets(set_name, add="Sets")
                                issues.append({
                                    'object': set_name,
                                    'message': f"Parented '{set_name}' to 'Sets' set",
                                    'fixed': True
                                })
                            except Exception as e:
                                issues.append({
                                    'object': set_name,
                                    'message': f"Failed to parent '{set_name}' to 'Sets': {str(e)}",
                                    'fixed': False
                                })
                except Exception as e:
                    print(f"DEBUG: Error in fix mode membership check for {set_name}: {e}")
                    # If there's an error checking membership, try to add it anyway
                    try:
                        cmds.sets(set_name, add="Sets")
                        issues.append({
                            'object': set_name,
                            'message': f"Parented '{set_name}' to 'Sets' set",
                            'fixed': True
                        })
                    except Exception as add_error:
                        issues.append({
                            'object': set_name,
                            'message': f"Failed to parent '{set_name}' to 'Sets': {str(add_error)}",
                            'fixed': False
                        })
            
            # If all fixes were successful, report final success
            if all(issue['fixed'] for issue in issues):
                issues.append({
                    'object': "Scene",
                    'message': "Character set structure has been fixed and is now valid",
                    'fixed': True
                })
    
    except Exception as e:
        print(f"DEBUG: Main exception in CharacterSet: {e}")
        issues.append({
            'object': "Scene",
            'message': f"Error during character set validation: {str(e)}",
            'fixed': False
        })
    
    # Return the correct format expected by the validation system
    return {"status": "success", "issues": issues, "total_checked": 1, "total_issues": len(issues)}
