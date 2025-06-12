import maya.cmds as cmds

def create_anim_set_from_controls(motion_group="MotionSystem", parent_set="Sets", new_set_name="AnimSet"):
    if not cmds.objExists(motion_group):
        cmds.warning(f"Group '{motion_group}' does not exist.")
        return

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
        return

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

# Run the function
# create_anim_set_from_controls()
