import maya.cmds as cmds

def create_pivot_space_window():
    # Check if window exists and delete it
    if cmds.window("enumAttrWindow", exists=True):
        cmds.deleteUI("enumAttrWindow")
    
    # Create window
    window = cmds.window("enumAttrWindow", title="pivot_space", widthHeight=(400, 300))
    
    # Create main layout
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=["both", 5])
    
    # Control selection
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
    cmds.text(label="Control:", width=100)
    cmds.textField("controlField", width=200)
    cmds.button(label="Select", command=lambda x: select_object("controlField"))
    cmds.setParent("..")
    
    # Attribute name
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text(label="Attribute Name:", width=100)
    cmds.textField("attrField", width=200)
    cmds.setParent("..")
    
    # Enum string
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text(label="Enum Values:", width=100)
    cmds.textField("enumField", width=200, text="pos1:pos2:pos3")
    cmds.setParent("..")
    
    # Passing control 1
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
    cmds.text(label="Transform 1:", width=100)
    cmds.textField("passingField1", width=200)
    cmds.button(label="Select", command=lambda x: select_object("passingField1"))
    cmds.setParent("..")
    
    # Passing control 2
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
    cmds.text(label="Transform 2:", width=100)
    cmds.textField("passingField2", width=200)
    cmds.button(label="Select", command=lambda x: select_object("passingField2"))
    cmds.setParent("..")
    
    # Passing control 3
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
    cmds.text(label="Transform 3:", width=100)
    cmds.textField("passingField3", width=200)
    cmds.button(label="Select", command=lambda x: select_object("passingField3"))
    cmds.setParent("..")
    
    cmds.separator(height=10, style='in')
    
    # Single button to do everything (green colored)
    cmds.button(label="create pivot space", command=create_all, width=200, backgroundColor=(0.2, 0.8, 0.2))
    
    # Show window
    cmds.showWindow(window)

def select_object(field_name):
    """Generic function to handle object selection"""
    sel = cmds.ls(selection=True)
    if sel:
        cmds.textField(field_name, edit=True, text=sel[0])

def create_all(*args):
    """Create enum attribute, locator and set SDK in one go"""
    # First create enum attribute
    control = cmds.textField("controlField", query=True, text=True)
    attr_name = cmds.textField("attrField", query=True, text=True)
    enum_string = cmds.textField("enumField", query=True, text=True)
    
    if not control or not attr_name:
        cmds.warning("Please specify both control and attribute name")
        return
        
    if not cmds.objExists(control):
        cmds.warning("Control object does not exist")
        return
        
    # Create the enum attribute
    cmds.addAttr(control, longName=attr_name, attributeType='enum', enumName=enum_string, keyable=True)
    
    # Create locator setup with names relative to control
    loc_name = f"{control}_pivot_ctrl"
    offset_name = f"{control}_pivot_offset"
    
    # Create locator at origin
    loc = cmds.spaceLocator(name=loc_name)[0]

    #locator hide
    cmds.setAttr(f"{loc}.visibility", 0)
    
    # Create offset group at origin
    offset_grp = cmds.group(empty=True, name=offset_name)
    
    # Parent locator under offset group
    cmds.parent(loc, offset_grp)
    
    # Parent offset group under control
    cmds.parent(offset_grp, control)
    
    # Ensure zero transforms
    for node in [loc, offset_grp]:
        cmds.setAttr(f"{node}.translate", 0, 0, 0)
        cmds.setAttr(f"{node}.rotate", 0, 0, 0)
        cmds.setAttr(f"{node}.scale", 1, 1, 1)
    
    # Create addDoubleLinear nodes for each axis
    for axis in ['X', 'Y', 'Z']:
        add_node = cmds.createNode('addDoubleLinear', name=f'{control}_pivot_add_{axis}')
        cmds.connectAttr(f'{offset_grp}.translate{axis}', f'{add_node}.input1')
        cmds.connectAttr(f'{loc}.translate{axis}', f'{add_node}.input2')
        cmds.connectAttr(f'{add_node}.output', f'{control}.rotatePivot{axis}')
    
    # Set up SDK connections
    # Get passing controls
    passing_controls = []
    for i in range(1, 4):
        ctrl = cmds.textField(f"passingField{i}", query=True, text=True)
        if ctrl and cmds.objExists(ctrl):
            passing_controls.append(ctrl)
    
    if not passing_controls:
        cmds.warning("Please specify at least one passing control")
        return
        
    # Set driven keyframes for each position
    for i, ctrl in enumerate(passing_controls):
        # Get transform values from passing control
        trans = cmds.xform(ctrl, query=True, translation=True, worldSpace=True)
        rot = cmds.xform(ctrl, query=True, rotation=True, worldSpace=True)
        
        # Set driven keyframe for this position
        cmds.setAttr(f"{control}.{attr_name}", i)
        
        # Set transform values
        cmds.xform(offset_grp, translation=trans, worldSpace=True)
        cmds.xform(offset_grp, rotation=rot, worldSpace=True)
        
        # Set the driven keyframe
        cmds.setDrivenKeyframe(f"{offset_grp}.translate", currentDriver=f"{control}.{attr_name}")
        cmds.setDrivenKeyframe(f"{offset_grp}.rotate", currentDriver=f"{control}.{attr_name}")
    
    # Reset enum attribute to 0 after setting all keyframes
    cmds.setAttr(f"{control}.{attr_name}", 0)

# create_pivot_space_window()

