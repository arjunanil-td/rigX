import maya.cmds as mc

def setup_model_visibility(low_res, hi_res):
    """
    Adds a modelVis enum attribute to the main control and connects it to switch visibility
    between low-res and hi-res meshes.
    """
    main_control = "Main"
    if not all([main_control, low_res, hi_res]):
        mc.warning("Main control, low_res, and hi_res must all be provided.")
        return

    # Sanity check — exit if attribute already exists
    if mc.attributeQuery("modelVis", node=main_control, exists=True):
        mc.warning(f"'modelVis' attribute already exists on {main_control}. Skipping setup.")
        return

    # Add enum attribute
    mc.addAttr(main_control, longName="modelVis", attributeType="enum",
               enumName="lowRes:hiRes", keyable=True)
    print(f"Added 'modelVis' enum to {main_control}")

    # Create condition nodes
    cond_low = mc.createNode("condition", name=f"{main_control}_lowVisCond")
    cond_hi = mc.createNode("condition", name=f"{main_control}_hiVisCond")

    # Configure them
    mc.setAttr(f"{cond_low}.secondTerm", 0)
    mc.setAttr(f"{cond_hi}.secondTerm", 1)
    mc.setAttr(f"{cond_low}.colorIfTrueR", 1)
    mc.setAttr(f"{cond_low}.colorIfFalseR", 0)
    mc.setAttr(f"{cond_hi}.colorIfTrueR", 1)
    mc.setAttr(f"{cond_hi}.colorIfFalseR", 0)

    # Connect main control to condition nodes
    mc.connectAttr(f"{main_control}.modelVis", f"{cond_low}.firstTerm", force=True)
    mc.connectAttr(f"{main_control}.modelVis", f"{cond_hi}.firstTerm", force=True)

    # Connect condition nodes to visibility
    mc.connectAttr(f"{cond_low}.outColorR", f"{low_res}.visibility", force=True)
    mc.connectAttr(f"{cond_hi}.outColorR", f"{hi_res}.visibility", force=True)

    print(f"✅ Model visibility setup complete for {main_control}")
