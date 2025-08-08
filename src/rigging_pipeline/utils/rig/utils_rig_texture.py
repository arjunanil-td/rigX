'''
This is mostly for the tiger workflow. The shaders are depended on a offline file where i manually created and assigned the shaders
Update the geometry or the shader list to use for any other character.

'''


import maya.cmds as cmds

def assign_eye_shaders():
    # 1. Define your left-side geos and the mapping to shader names
    left_geos = [
        'l_cornea_IDcharCornea_GEO',
        'l_limbus_IDcharLimbus_GEO',
        'l_membrane_IDcharSkin_GEO',
        'l_lens_IDcharEye_GEO',
        'l_iris_IDcharEye_GEO',
        'l_meniscus_IDcharMeniscus_GEO'
    ]
    shader_map = {
        'cornea': 'limbus',   # cornea & limbus both use limbus shader
        'limbus': 'limbus',
        'membrane': 'membrane',
        'lens': 'lens',
        'iris': 'iris',
        'meniscus': 'meniscus'
    }

    def assign_shader(shader, geo):
        """Assign the given shader to geo via its shadingEngine."""
        if not cmds.objExists(shader):
            cmds.warning(f"Shader not found: {shader}")
            return
        sgs = cmds.listConnections(f"{shader}.outColor", type='shadingEngine') or []
        if not sgs:
            cmds.warning(f"No shadingGroup on {shader}")
            return
        sg = sgs[0]
        if not cmds.objExists(geo):
            cmds.warning(f"Geometry not found: {geo}")
            return
        cmds.sets(geo, edit=True, forceElement=sg)

    # 2. Loop through left-side geos
    for geo in left_geos:
        # extract part key (e.g. 'cornea', 'limbus', etc.)
        parts = geo.split('_')
        if len(parts) < 2:
            cmds.warning(f"Skipping malformed name: {geo}")
            continue
        part = parts[1]
        shader = shader_map.get(part)
        if not shader:
            cmds.warning(f"No shader mapping for part '{part}'")
            continue

        # assign left side
        assign_shader(shader, geo)
        # assign right side
        right_geo = geo.replace('l_', 'r_', 1)
        assign_shader(shader, right_geo)

    print("Done assigning eye shaders.")
