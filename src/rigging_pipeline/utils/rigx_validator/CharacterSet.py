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

# Global variable to track intentionally skipped sets across function calls
_intentionally_skipped_sets = []

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    global _intentionally_skipped_sets
    issues = []
    
    try:
        # Check if scene is empty (no transform nodes except default Maya nodes)
        all_transforms = cmds.ls(type='transform', long=True) or []
        default_nodes = ['persp', 'top', 'front', 'side', 'bottom', 'back', 'left']
        custom_nodes = [node for node in all_transforms if cmds.ls(node, long=False)[0] not in default_nodes]
        
        # If scene is empty (no custom transform nodes), pass validation
        if not custom_nodes:
            issues.append({
                'object': "Scene",
                'message': "All validations passed",
                'fixed': True
            })
            return {"status": "success", "issues": issues, "total_checked": 1, "total_issues": len(issues)}
        
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
                # 'Sets' set found, now check for 'AnimSet', 'DeformSet', and 'FaceControlSet' parented to it
                required_sets = ["AnimSet", "DeformSet", "FaceControlSet"]  # FaceControlSet is now required
                optional_sets = []  # No optional sets anymore
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
                
                # All sets are now required, so they will be checked in the required sets loop above
                
                # Report missing required sets only (excluding intentionally skipped ones)
                for missing_set in missing_sets:
                    if missing_set not in _intentionally_skipped_sets:
                        issues.append({
                            'object': "Scene",
                            'message': f"Missing '{missing_set}' - required for character set validation",
                            'fixed': False
                        })
                    else:
                        # This set was intentionally skipped, mark as fixed
                        issues.append({
                            'object': "Scene",
                            'message': f"'{missing_set}' was intentionally skipped by user",
                            'fixed': True
                        })
                
                # ───── Integrated Control Values check (AnimSet + optional FaceControlSet) ─────
                try:
                    sets_members_for_ctrl = cmds.sets("Sets", query=True) or []
                except Exception:
                    sets_members_for_ctrl = []
                include_face = "FaceControlSet" in sets_members_for_ctrl

                if "AnimSet" in sets_members_for_ctrl:
                    controls = []
                    try:
                        controls.extend(cmds.sets("AnimSet", q=True) or [])
                    except Exception:
                        controls = controls
                    if include_face:
                        try:
                            controls.extend(cmds.sets("FaceControlSet", q=True) or [])
                        except Exception:
                            controls = controls
                    
                    def _attr_exists_and_unlocked(attribute_name):
                        if not cmds.objExists(attribute_name):
                            return False
                        try:
                            return not cmds.getAttr(attribute_name, lock=True)
                        except Exception:
                            return True
                    
                    for ctrl in controls:
                        if not cmds.objExists(ctrl):
                            issues.append({
                                'object': ctrl,
                                'message': f"{ctrl} (missing in scene)",
                                'fixed': False
                            })
                            continue
                        bad_attrs = []
                        # Translate
                        for axis in ["X", "Y", "Z"]:
                            attr = f"{ctrl}.translate{axis}"
                            if _attr_exists_and_unlocked(attr):
                                try:
                                    if cmds.getAttr(attr) != 0:
                                        bad_attrs.append(attr)
                                except Exception:
                                    pass
                        # Rotate
                        for axis in ["X", "Y", "Z"]:
                            attr = f"{ctrl}.rotate{axis}"
                            if _attr_exists_and_unlocked(attr):
                                try:
                                    if cmds.getAttr(attr) != 0:
                                        bad_attrs.append(attr)
                                except Exception:
                                    pass
                        # Scale
                        for axis in ["X", "Y", "Z"]:
                            attr = f"{ctrl}.scale{axis}"
                            if _attr_exists_and_unlocked(attr):
                                try:
                                    if cmds.getAttr(attr) != 1:
                                        bad_attrs.append(attr)
                                except Exception:
                                    pass
                        if bad_attrs:
                            issues.append({
                                'object': ctrl,
                                'message': f"Offending attrs: {', '.join(bad_attrs)}",
                                'fixed': False
                            })
                else:
                    # If AnimSet itself is not under Sets, control values cannot be validated here
                    pass
                
                # If all required sets exist and are properly parented (or were intentionally skipped), report success
                total_valid_sets = len(properly_parented_sets) + len(_intentionally_skipped_sets)
                if total_valid_sets >= len(required_sets):
                    # Only show success if there are no unfixed issues
                    unfixed_issues = [issue for issue in issues if not issue['fixed']]
                    if len(unfixed_issues) == 0:
                        # Clear all detailed issues and just show simple success message
                        issues = []
                        issues.append({
                            'object': "Scene",
                            'message': "All validations passed",
                            'fixed': True
                        })
                        # Clear the intentionally skipped list since we're showing success
                        _intentionally_skipped_sets.clear()
                    # If there are unfixed issues, don't show success message
        
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
            required_sets = ["AnimSet", "DeformSet", "FaceControlSet"]  # FaceControlSet is now required
            optional_sets = []  # No optional sets anymore
            
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
                            elif set_name == "FaceControlSet":
                                # For FaceControlSet, ask user what to do
                                result = cmds.confirmDialog(
                                    title="FaceControlSet Missing",
                                    message="FaceControlSet is missing. Would you like me to create it?",
                                    button=["Create FaceControlSet", "Skip for now"],
                                    defaultButton="Create FaceControlSet",
                                    cancelButton="Skip for now",
                                    dismissString="Skip for now"
                                )
                                
                                if result == "Create FaceControlSet":
                                    # Create FaceControlSet as empty set
                                    cmds.sets(name=set_name, empty=True)
                                    issues.append({
                                        'object': set_name,
                                        'message': f"Created missing '{set_name}'",
                                        'fixed': True
                                    })
                                else:
                                    # User chose to skip - mark as fixed since they made a conscious choice
                                    _intentionally_skipped_sets.append(set_name)
                                    issues.append({
                                        'object': set_name,
                                        'message': f"User chose to skip creating '{set_name}' (intentionally omitted)",
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
                        elif set_name == "FaceControlSet":
                            # For FaceControlSet, ask user what to do in fallback mode
                            result = cmds.confirmDialog(
                                title="FaceControlSet Missing",
                                message="FaceControlSet is missing. Would you like me to create it?",
                                button=["Create FaceControlSet", "Skip for now"],
                                defaultButton="Create FaceControlSet",
                                cancelButton="Skip for now",
                                dismissString="Skip for now"
                            )
                            
                            if result == "Create FaceControlSet":
                                # Create FaceControlSet as empty set
                                cmds.sets(name=set_name, empty=True)
                                issues.append({
                                    'object': set_name,
                                    'message': f"Created missing '{set_name}'",
                                    'fixed': True
                                })
                            else:
                                # User chose to skip - mark as fixed since they made a conscious choice
                                _intentionally_skipped_sets.append(set_name)
                                issues.append({
                                    'object': set_name,
                                    'message': f"User chose to skip creating '{set_name}' (intentionally omitted)",
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
            
            # FaceControlSet is now required, so it will be handled in the required sets loop above
            
            # Check if all existing sets are parented to 'Sets' and fix if needed
            all_sets_to_check = required_sets
            
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
            all_fixed = all(issue['fixed'] for issue in issues) if issues else True

            # ───── Integrated Control Values fix (AnimSet + optional FaceControlSet) ─────
            try:
                sets_members_for_ctrl = cmds.sets("Sets", query=True) or []
            except Exception:
                sets_members_for_ctrl = []
            include_face = "FaceControlSet" in sets_members_for_ctrl
            if "AnimSet" in sets_members_for_ctrl:
                controls = []
                try:
                    controls.extend(cmds.sets("AnimSet", q=True) or [])
                except Exception:
                    controls = controls
                if include_face:
                    try:
                        controls.extend(cmds.sets("FaceControlSet", q=True) or [])
                    except Exception:
                        controls = controls
                
                def _attr_exists_and_unlocked(attribute_name):
                    if not cmds.objExists(attribute_name):
                        return False
                    try:
                        return not cmds.getAttr(attribute_name, lock=True)
                    except Exception:
                        return True
                
                for ctrl in controls:
                    bad_attrs = []
                    for axis in ["X", "Y", "Z"]:
                        t_attr = f"{ctrl}.translate{axis}"
                        r_attr = f"{ctrl}.rotate{axis}"
                        s_attr = f"{ctrl}.scale{axis}"
                        if _attr_exists_and_unlocked(t_attr):
                            try:
                                if cmds.getAttr(t_attr) != 0:
                                    bad_attrs.append(t_attr)
                                    cmds.setAttr(t_attr, 0)
                            except Exception:
                                pass
                        if _attr_exists_and_unlocked(r_attr):
                            try:
                                if cmds.getAttr(r_attr) != 0:
                                    bad_attrs.append(r_attr)
                                    cmds.setAttr(r_attr, 0)
                            except Exception:
                                pass
                        if _attr_exists_and_unlocked(s_attr):
                            try:
                                if cmds.getAttr(s_attr) != 1:
                                    bad_attrs.append(s_attr)
                                    cmds.setAttr(s_attr, 1)
                            except Exception:
                                pass
                    if bad_attrs:
                        issues.append({
                            'object': ctrl,
                            'message': f"Reset: {', '.join(bad_attrs)}",
                            'fixed': True
                        })
            
            # Recompute all_fixed after resets
            all_fixed = all(issue['fixed'] for issue in issues) if issues else True

            if all_fixed:
                # Clear all detailed issues and just show simple success message
                issues = []
                issues.append({
                    'object': "Scene",
                    'message': "All validations passed",
                    'fixed': True
                })
                # Clear the intentionally skipped list since we're showing success
                _intentionally_skipped_sets.clear()
    
    except Exception as e:
        print(f"DEBUG: Main exception in CharacterSet: {e}")
        issues.append({
            'object': "Scene",
            'message': f"Error during character set validation: {str(e)}",
            'fixed': False
        })
    
    # Return the correct format expected by the validation system
    return {"status": "success", "issues": issues, "total_checked": 1, "total_issues": len(issues)}
