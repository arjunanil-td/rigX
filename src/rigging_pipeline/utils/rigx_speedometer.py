import maya.cmds as cmds
import math

'''
# Run the function
add_speedometer()
'''

def add_speedometer():
    """Adds speedometer attributes to selected objects and calculates speed."""
    selected_objects = cmds.ls(selection=True, flatten=True)
    
    # Determine the current FPS
    fps = 24  # Default FPS value (film)
    time_unit = cmds.currentUnit(query=True, time=True)
    
    if time_unit == 'film':
        fps = 24
    elif time_unit == 'pal':
        fps = 25
    elif time_unit == 'ntsc':
        fps = 30
    else:
        cmds.warning("Couldn't determine fps, using 24.")

    # Add the speedometer attributes to the selected objects
    for obj in selected_objects:
        # Add speed, kph, mph attributes if they don't exist
        if not cmds.attributeQuery("speed", node=obj, exists=True):
            cmds.addAttr(obj, longName="speed", attributeType="double", keyable=True)
        if not cmds.attributeQuery("kph", node=obj, exists=True):
            cmds.addAttr(obj, longName="kph", attributeType="double", keyable=True)
        if not cmds.attributeQuery("mph", node=obj, exists=True):
            cmds.addAttr(obj, longName="mph", attributeType="double", keyable=True)

        # Create the expression for speed calculation
        expr = (
            f"// Added by addSpeedometer.py\n"
            f"float $t = `currentTime -q`;\n"
            f"float $fps = {fps};  // seconds-per-frame\n"
            f"float $last[] = `getAttr -time ($t-1) {obj}.translate`;\n"
            f"float $dx = tx - $last[0];\n"
            f"float $dy = ty - $last[1];\n"
            f"float $dz = tz - $last[2];\n"
            f"float $dist = sqrt($dx*$dx + $dy*$dy + $dz*$dz);\n"
            f"speed = $dist;\n"
            f"kph = $dist * $fps * 3600 / 1e5;\n"
            f"mph = kph / 1.609344;\n"
        )

        # Apply the expression to the object
        cmds.expression(s=expr, o=obj, name="speedExpression", ae=0, uc="all")

