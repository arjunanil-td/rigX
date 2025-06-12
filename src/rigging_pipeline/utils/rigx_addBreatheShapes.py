import maya.cmds as cmds

def setup_breathe_shapes(mesh, blendshape_node, root_ctrl):
    """
    Sets up breathe shapes for a given mesh and blendshape node.
    
    Args:
        mesh (str): The mesh to set up
        blendshape_node (str): The blendshape node to use
        root_ctrl (str): The root control to connect to
    """
    if not cmds.objExists(mesh) or not cmds.objExists(blendshape_node):
        print(f"❌ Mesh {mesh} or blendshape node {blendshape_node} does not exist")
        return False
        
    # Get the deformation history of the mesh
    history = cmds.listHistory(mesh, interestLevel=2) or []
    targets = cmds.listAttr(f"{blendshape_node}.w", m=True) or []
    
    # Check if root control exists
    if not cmds.objExists(root_ctrl):
        print(f"❌ Root control {root_ctrl} does not exist")
        return False
        
    # Add and connect attributes for each target
    for target in targets:
        # Create attribute name (remove any 'In' or 'Out' suffix)
        attr_name = target.replace('In', '').replace('Out', '')
        
        # Add float attribute if it doesn't exist
        if not cmds.attributeQuery(attr_name, node=root_ctrl, exists=True):
            cmds.addAttr(root_ctrl, 
                        longName=attr_name,
                        attributeType='float',
                        min=-1,
                        max=1,
                        defaultValue=0,
                        keyable=True)
            print(f"✅ Added attribute {attr_name} to {root_ctrl}")
        
        # Set up driven keys for the target
        try:
            # For In targets (0 to -1)
            if target.endswith('In'):
                # Set key at 0
                cmds.setAttr(f"{root_ctrl}.{attr_name}", 0)
                cmds.setAttr(f"{blendshape_node}.{target}", 0)
                cmds.setDrivenKeyframe(f"{blendshape_node}.{target}", 
                                     currentDriver=f"{root_ctrl}.{attr_name}")
                
                # Set key at -1
                cmds.setAttr(f"{root_ctrl}.{attr_name}", -1)
                cmds.setAttr(f"{blendshape_node}.{target}", 1)
                cmds.setDrivenKeyframe(f"{blendshape_node}.{target}", 
                                     currentDriver=f"{root_ctrl}.{attr_name}")
                
                # Reset to 0
                cmds.setAttr(f"{root_ctrl}.{attr_name}", 0)
                print(f"✅ Set up In range for {target} (0 to -1)")
            
            # For Out targets (0 to 1)
            elif target.endswith('Out'):
                # Set key at 0
                cmds.setAttr(f"{root_ctrl}.{attr_name}", 0)
                cmds.setAttr(f"{blendshape_node}.{target}", 0)
                cmds.setDrivenKeyframe(f"{blendshape_node}.{target}", 
                                     currentDriver=f"{root_ctrl}.{attr_name}")
                
                # Set key at 1
                cmds.setAttr(f"{root_ctrl}.{attr_name}", 1)
                cmds.setAttr(f"{blendshape_node}.{target}", 1)
                cmds.setDrivenKeyframe(f"{blendshape_node}.{target}", 
                                     currentDriver=f"{root_ctrl}.{attr_name}")
                
                # Reset to 0
                cmds.setAttr(f"{root_ctrl}.{attr_name}", 0)
                print(f"✅ Set up Out range for {target} (0 to 1)")
            
        except Exception as e:
            print(f"❌ Failed to set up driven keys for {target}: {str(e)}")
    
    return True

def add_breathe_shapes():
    """
    Adds breathe shapes to the selected rig.
    """
    BREATHESHAPE_MESH = "breathShapes_GEO"
    BREATHESHAPE_LOW_MESH = "breathShapesLow_GEO"
    BREATHESHAPE_NODE = "breatheShape_BS"
    BREATHESHAPE_LOW_NODE = "shapesLow_BS"
    ROOT_CTRL = "RootX_M"
    
    # Set up high resolution mesh
    print("\nSetting up high resolution breathe shapes...")
    high_result = setup_breathe_shapes(BREATHESHAPE_MESH, BREATHESHAPE_NODE, ROOT_CTRL)
    
    # Set up low resolution mesh
    print("\nSetting up low resolution breathe shapes...")
    low_result = setup_breathe_shapes(BREATHESHAPE_LOW_MESH, BREATHESHAPE_LOW_NODE, ROOT_CTRL)
    
    return high_result and low_result

    
    
    
