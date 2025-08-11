import maya.cmds as cmds

'''
breatheShapeConnect(controller, blendShape_node, attributes)

@ ZebuFX 2025
'''

controller = 'RootX_M'
blendShape_node = 'breatheShapes_Bs'
attributes = ['breatheThroatUpper', 'breatheChest', 'breatheBelly', 'breatheThroatLower']

def breatheShapeConnect(controller, blendShape_node, attributes):
    """
    Sets driven keys for blendShapes based on the given controller and blendShape node.

    Args:
        controller (str): The name of the controller object.
        blendShape_node (str): The name of the blendShape node.
        attributes (list): List of attribute names to create and set driven keys.
    """
    for attr in attributes:
        driver_attr = f'{controller}.{attr}'
        in_target = f'{blendShape_node}.{attr}In'
        out_target = f'{blendShape_node}.{attr}Out'

        # Add the attribute if it doesn't exist
        if not cmds.attributeQuery(attr, node=controller, exists=True):
            cmds.addAttr(controller, longName=attr, attributeType='float', min=-1, max=1, keyable=True)

        # Set Driven Keys for -1, 0, +1
        for value, in_weight, out_weight in [(-1, 1, 0), (0, 0, 0), (1, 0, 1)]:
            cmds.setAttr(driver_attr, value)
            cmds.setAttr(in_target, in_weight)
            cmds.setAttr(out_target, out_weight)
            cmds.setDrivenKeyframe(in_target, currentDriver=driver_attr)
            cmds.setDrivenKeyframe(out_target, currentDriver=driver_attr)

        # After setting the driven keys, set the default value to 0 last
        cmds.setAttr(driver_attr, 0)
        cmds.setKeyframe(driver_attr, value=0, time=0)
        cmds.cutKey(driver_attr, time=(0, 0), option="keys")

        print(f"✅ breatheShape Connected for {driver_attr} -> {in_target}, {out_target}, Default set to 0")



