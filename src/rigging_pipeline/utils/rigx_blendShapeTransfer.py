'''
# Run the UI
open_blendshape_transfer_ui()

'''



import maya.cmds as cmds

def transfer_blendshapes_from_high_to_low(high_mesh, low_mesh, new_blendshape_name='low_bs'):
    history = cmds.listHistory(high_mesh)
    bs_node = next((node for node in history if cmds.nodeType(node) == 'blendShape'), None)
    
    if not bs_node:
        cmds.error("❌ No blendShape node found on high-poly mesh.")
    
    target_names = cmds.listAttr(bs_node + '.w', m=True)
    if not target_names:
        cmds.error("❌ No blendshape targets found on high-poly mesh.")
    
    print(f"🔍 Found {len(target_names)} blendshape targets on {bs_node}.")

    if cmds.objExists(new_blendshape_name):
        cmds.delete(new_blendshape_name)
    new_bs_node = cmds.blendShape(low_mesh, name=new_blendshape_name)[0]

    for i, target in enumerate(target_names):
        print(f"➡️ Transferring: {target}")
        cmds.setAttr(f"{bs_node}.{target}", 1)
        
        high_dup = cmds.duplicate(high_mesh, name=f"{target}_highDup")[0]
        low_dup = cmds.duplicate(low_mesh, name=f"{target}_lowDup")[0]
        
        cmds.transferAttributes(high_dup, low_dup,
                                transferPositions=1,
                                transferNormals=0,
                                transferUVs=0,
                                sampleSpace=0,
                                searchMethod=3)
        cmds.delete(low_dup, ch=True)
        transferred_shape = cmds.rename(low_dup, f"{target}")
        
        cmds.blendShape(new_bs_node, edit=True, t=(low_mesh, i, transferred_shape, 1.0))
        cmds.setAttr(f"{bs_node}.{target}", 0)
        
        cmds.delete(high_dup, transferred_shape)
        print(f"✅ Transferred {target} to {new_bs_node}")

    print(f"\n🎉 All blendshapes transferred to new blendShape node: {new_bs_node}")
    return new_bs_node


# -------------------------
# UI Function
# -------------------------
def open_blendshape_transfer_ui():
    if cmds.window("blendshapeTransferUI", exists=True):
        cmds.deleteUI("blendshapeTransferUI")
    
    window = cmds.window("blendshapeTransferUI", title="Blendshape Transfer Tool", sizeable=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnAlign="center")

    cmds.text(label="Select your meshes")
    
    high_field = cmds.textFieldButtonGrp(label="High-Poly Mesh", buttonLabel="<<", cw3=[100, 200, 40])
    low_field = cmds.textFieldButtonGrp(label="Low-Poly Mesh", buttonLabel="<<", cw3=[100, 200, 40])
    
    def set_high(*_):
        sel = cmds.ls(selection=True)
        if sel:
            cmds.textFieldButtonGrp(high_field, edit=True, text=sel[0])
    
    def set_low(*_):
        sel = cmds.ls(selection=True)
        if sel:
            cmds.textFieldButtonGrp(low_field, edit=True, text=sel[0])
    
    def run_transfer(*_):
        high = cmds.textFieldButtonGrp(high_field, query=True, text=True)
        low = cmds.textFieldButtonGrp(low_field, query=True, text=True)
        if not high or not low:
            cmds.warning("Please specify both meshes.")
            return
        transfer_blendshapes_from_high_to_low(high, low)
    
    cmds.textFieldButtonGrp(high_field, edit=True, buttonCommand=set_high)
    cmds.textFieldButtonGrp(low_field, edit=True, buttonCommand=set_low)
    
    cmds.button(label="Transfer Blendshapes", command=run_transfer, height=40, bgc=(0.4, 0.8, 0.4))
    
    cmds.setParent("..")
    cmds.showWindow(window)


