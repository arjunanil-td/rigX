import maya.cmds as cmds

# Use this to fix the puppet fps issue after facial build
def replace_pointOnCurveInfo_with_motionPath(attach_group=None):

    attach_group = cmds.listRelatives("SkinAttachCtrls", children=True, type="transform")
    if not attach_group:
        cmds.warning("No SkinAttachCtrls found. Please create them first.")
        return

    for node in attach_group:
        # Get translate compound connection
        conn = cmds.listConnections(f"{node}.translate", plugs=True, source=True, destination=False, connections=True)

        if not conn:
            continue

        # Look for pointOnCurveInfo.position → translate connection
        for i in range(0, len(conn), 2):
            dest_attr = conn[i]
            src_attr = conn[i + 1]

            if ".position" not in src_attr:
                continue

            poc_node = src_attr.split(".")[0]
            if cmds.nodeType(poc_node) != "pointOnCurveInfo":
                continue

            print(f"Processing: {node}")

            # Get curve and parameter
            input_curve = cmds.listConnections(f"{poc_node}.inputCurve", source=True, destination=False)
            if not input_curve:
                cmds.warning(f"Could not find curve connected to {poc_node}")
                continue

            parameter = cmds.getAttr(f"{poc_node}.parameter")
            curve = input_curve[0]

            # Create motionPath node
            mp_node = cmds.createNode("motionPath", name=f"{node}_mpSampler")
            cmds.connectAttr(f"{curve}.worldSpace[0]", f"{mp_node}.geometryPath", force=True)

            # Set motionPath attributes
            cmds.setAttr(f"{mp_node}.fractionMode", 0)  # raw parameter mode
            cmds.setAttr(f"{mp_node}.uValue", parameter)
            cmds.setAttr(f"{mp_node}.follow", 0)
            cmds.setAttr(f"{mp_node}.worldUpType", 0)

            # Disconnect old pointOnCurveInfo.position → translate
            try:
                cmds.disconnectAttr(f"{poc_node}.position", f"{node}.translate")
            except:
                pass

            # Connect motionPath to translate
            for axis, attr in zip("XYZ", ["xCoordinate", "yCoordinate", "zCoordinate"]):
                cmds.connectAttr(f"{mp_node}.{attr}", f"{node}.translate{axis}", force=True)

            # Clean up
            if not cmds.listConnections(poc_node, source=False, destination=False):
                cmds.delete(poc_node)

            cmds.inViewMessage(amg=f"<hl>Replaced pointOnCurveInfo on {node}</hl>", pos="topCenter", fade=True)