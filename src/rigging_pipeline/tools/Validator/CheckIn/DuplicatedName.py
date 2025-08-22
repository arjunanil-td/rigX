"""
DuplicatedName Validation Module
Checks for duplicated names
"""

import maya.cmds as cmds

DESCRIPTION = "Check for duplicated names"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
    # Get objects to check (either from selection or all in scene)
    if cmds.ls(selection=True):
        to_check_list = cmds.ls(selection=True, long=False)
    else:
        to_check_list = cmds.ls(long=False)
    
    if to_check_list:
        found_duplicated = False
        for node in to_check_list:
            if "|" in node:
                found_duplicated = True
                break
        
        if found_duplicated:
            # Analysis the elements in order to put it with ordenation from children to grandfather (inverted hierarchy)
            size_list = []
            ordered_obj_list = []
            for i, element in enumerate(to_check_list):
                # Find the number of occurrences of "|" in the string (element)
                number = element.count("|")
                # Add to a list another list with number and element
                size_list.append([number, element])
            
            # Sort (put in alphabetic order to A-Z) and reverse (invert the order to Z-A)
            size_list.sort()
            size_list.reverse()
            
            # Add the elements to the final orderedObjList
            for n, value in enumerate(size_list):
                ordered_obj_list.append(size_list[n][1])
            
            # Prepare a list with nodeNames to iteration
            short_name_list = []
            for long_name in ordered_obj_list:
                # Verify if there are children in order to get the shortNames
                if "|" in long_name:
                    short_name_list.append(long_name[long_name.rfind("|")+1:])
                else:
                    short_name_list.append(long_name)
            
            # Compare each obj in the list with the others
            n = 0
            for i, obj in enumerate(short_name_list):
                # Use another list without the first element to compare if the item repeats
                another_list = short_name_list[i+1:]
                for item in another_list:
                    if cmds.objExists(ordered_obj_list[i]):
                        if obj == item:
                            # Found issue here
                            if mode == "check":
                                issues.append({
                                    'object': ordered_obj_list[i],
                                    'message': f"Duplicate name found: {obj}",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    new_name = f"{obj}{n}"
                                    cmds.rename(ordered_obj_list[i], new_name)
                                    n += 1
                                    issues.append({
                                        'object': ordered_obj_list[i],
                                        'message': f"Renamed to: {new_name}",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': ordered_obj_list[i],
                                        'message': f"Failed to rename: {str(e)}",
                                        'fixed': False
                                    })
        else:
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': "No duplicate names found",
                    'fixed': True
                })
    else:
        if mode == "check":
            issues.append({
                'object': "Scene",
                'message': "No objects to check",
                'fixed': True
            })
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(to_check_list) if 'to_check_list' in locals() else 0,
        "total_issues": len(issues)
    }
