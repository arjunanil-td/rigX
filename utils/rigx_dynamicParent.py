import maya.cmds as mc

def setup_dynamic_parent(control, targets, enum_names=None):
    """
    Sets up a dynamic parent switch system using a parent constraint and enum switch.

    Args:
        control (str): The control to which the enum and switch will be added.
        targets (list): List of parent objects (e.g., world, pelvis, chest).
        enum_names (list, optional): List of enum display names. Defaults to cleaned versions of targets.
    """
    if not control or not targets:
        mc.warning("Control and targets must be provided.")
        return

    if not enum_names:
        enum_names = [t.replace("Ctrl_", "") if "Ctrl_" in t else t for t in targets]

    # Get the parent of the control (usually a group/null)
    parent_group = mc.listRelatives(control, parent=True, fullPath=True)
    if not parent_group:
        mc.warning(f"Control {control} has no parent group. Dynamic parent requires a transform parent.")
        return
    parent_group = parent_group[0]

    # Apply parent constraint to the group (maintain offset)
    pcon = mc.parentConstraint(targets, parent_group, maintainOffset=True)[0]

    # Add identifying string attr (optional, but helpful)
    if not mc.attributeQuery("mNodeId", node=control, exists=True):
        mc.addAttr(control, ln="mNodeId", dt="string")
    mc.setAttr(f"{control}.mNodeId", control, type="string")

    # Add enum attribute for parent switching
    if not mc.attributeQuery("parentTo", node=control, exists=True):
        mc.addAttr(control, ln="parentTo", at="enum", en=":".join(enum_names) + ":", keyable=True)

    # Create condition nodes to drive weights
    weight_attrs = mc.parentConstraint(pcon, query=True, wal=True)  # weight aliases
    target_nodes = mc.parentConstraint(pcon, query=True, tl=True)   # target objects

    if not weight_attrs or not target_nodes:
        mc.error(f"Failed to retrieve constraint weights or targets from: {pcon}")
        return

    if len(weight_attrs) != len(target_nodes):
        mc.error("Mismatch between constraint weight aliases and target objects. Cannot continue.")
        return

    for i in range(len(weight_attrs)):
        enum_label = enum_names[i] if i < len(enum_names) else f"Option{i}"
        con_node = mc.createNode("condition", name=f"{control}_Par_{enum_label}")
        mc.setAttr(f"{con_node}.secondTerm", i)
        mc.setAttr(f"{con_node}.colorIfTrueR", 1)
        mc.setAttr(f"{con_node}.colorIfFalseR", 0)
        mc.connectAttr(f"{control}.parentTo", f"{con_node}.firstTerm", force=True)
        mc.connectAttr(f"{con_node}.outColorR", f"{pcon}.{weight_attrs[i]}", force=True)


