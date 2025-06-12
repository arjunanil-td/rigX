import maya.cmds as cmds

def assign_tag_to_geo(geo, tag):
    """
    Assign (or reassign) a string attribute 'zTag' on the given geometry.
    If the attribute exists and is locked, unlock it, update its value, then relock.
    If it doesn't exist, create it, set it, and lock it.
    """
    full = cmds.ls(geo, long=True)
    if not full:
        raise RuntimeError(f"Geometry '{geo}' not found in scene.")
    node = full[0]

    attr = "zTag"
    attr_full = f"{node}.{attr}"

    # 1) If attribute doesn't exist, add it
    if not cmds.attributeQuery(attr, node=node, exists=True):
        cmds.addAttr(node, longName=attr, dataType="string")
    else:
        # 2) If it exists and is locked, unlock it
        if cmds.getAttr(attr_full, lock=True):
            cmds.setAttr(attr_full, lock=False)

    # 3) Set new value
    cmds.setAttr(attr_full, tag, type="string")

    # 4) Lock it down
    cmds.setAttr(attr_full, lock=True)
