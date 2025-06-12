import maya.cmds as cmds
import os

HIRES_MESH = "bodyHiRes_GEO"
PROXY_MESH = "bodyProxy_GEO"
ALL_MODEL_GROUP = "allModel_GRP"
TEXTURE_PATH = "Q:/METAL/projects/Kantara/Production/Assets/charBoarPiglet/texture/release/AvA/v001/jpeg"

def get_target_meshes():
    """
    Returns a list of target meshes that should be processed:
    - The high-res mesh
    - The proxy mesh
    - All meshes inside the 'allModel_GRP' group
    
    :return: List of mesh shapes to process
    """
    target_meshes = []
    
    # Add high-res mesh if it exists
    if cmds.objExists(HIRES_MESH):
        target_meshes.append(cmds.listRelatives(HIRES_MESH, shapes=True, fullPath=True)[0])
    
    # Add proxy mesh if it exists
    if cmds.objExists(PROXY_MESH):
        target_meshes.append(cmds.listRelatives(PROXY_MESH, shapes=True, fullPath=True)[0])
    
    # Add all meshes from allModel group if it exists
    if cmds.objExists(ALL_MODEL_GROUP):
        model_meshes = cmds.listRelatives(ALL_MODEL_GROUP, allDescendents=True, type="mesh", fullPath=True) or []
        target_meshes.extend(model_meshes)
    
    return target_meshes

def get_subgroup_meshes():
    """
    Returns a dictionary of meshes grouped by their sub-groups (nails_GRP, teeth_GRP, eyes_GRP).
    Each sub-group's meshes will share a single shader.
    
    :return: Dictionary with sub-group names as keys and lists of mesh shapes as values
    """
    subgroup_meshes = {}
    
    if not cmds.objExists(ALL_MODEL_GROUP):
        return subgroup_meshes
        
    for subgroup in SUB_GROUPS:
        subgroup_path = f"{ALL_MODEL_GROUP}|{subgroup}"
        if cmds.objExists(subgroup_path):
            meshes = cmds.listRelatives(subgroup_path, allDescendents=True, type="mesh", fullPath=True) or []
            if meshes:
                # Use the base name without _GRP for the shader
                base_name = subgroup.replace("_GRP", "")
                subgroup_meshes[base_name] = meshes
    
    return subgroup_meshes

def ensure_furUVs_on_geo(verbose=False):
    """
    Ensures there is a UV set named "map1" and makes it the current UV set
    for all target meshes. If "map1" doesn't exist on a mesh, it's created
    from the mesh's existing UVs.

    :param verbose: if True, prints out each step for debugging
    """
    target_meshes = get_target_meshes()
    if not target_meshes:
        cmds.warning("No target meshes found to process.")
        return

    if verbose:
        print(f"[ensure_furUVs_on_geo] Found {len(target_meshes)} mesh(es) to process: {target_meshes}")

    for shape in target_meshes:
        try:
            # Get existing UV sets
            uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            
            # If map1 doesn't exist, create it
            if "map1" not in uv_sets:
                if verbose:
                    print(f"    – Creating 'map1' UV set on {shape}")
                cmds.polyUVSet(shape, create=True, uvSet="map1")
            
            # Set map1 as current
            cmds.polyUVSet(shape, uvSet="map1", currentUVSet=True)
            if verbose:
                print(f"    – Set 'map1' as current on {shape}")
        except Exception as e:
            cmds.warning(f"Could not set 'map1' as current on {shape}: {e}")
            continue

    cmds.select(clear=True)
    if verbose:
        print("[ensure_furUVs_on_geo] Done.")

def assign_udim_textures(verbose=False):
    """
    Assigns a single shader with UDIM textures to all target meshes.
    The textures are loaded from the specified TEXTURE_PATH directory.

    :param verbose: if True, prints out each step for debugging
    """
    if not os.path.exists(TEXTURE_PATH):
        cmds.warning(f"Texture path does not exist: {TEXTURE_PATH}")
        return

    # Create a single shader for all meshes
    shader_name = "rigX_lambert"
    shading_group = f"{shader_name}SG"

    if cmds.objExists(shader_name):
        if verbose:
            print(f"  • Shader '{shader_name}' already exists, reusing it.")
    else:
        if verbose:
            print(f"  • Creating lambert shader '{shader_name}'")
        shader_name = cmds.shadingNode("lambert", asShader=True, name=shader_name)

    if cmds.objExists(shading_group):
        if verbose:
            print(f"  • Shading group '{shading_group}' already exists.")
    else:
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=shading_group)
        cmds.connectAttr(f"{shader_name}.outColor", f"{shading_group}.surfaceShader", force=True)
        if verbose:
            print(f"  • Created shading group '{shading_group}' and connected to '{shader_name}.outColor'")

    # Create file node for UDIM textures
    file_node = cmds.shadingNode("file", asTexture=True, name="rigX_texture")
    cmds.connectAttr(f"{file_node}.outColor", f"{shader_name}.color", force=True)

    # Set UDIM mode and other file node attributes
    cmds.setAttr(f"{file_node}.uvTilingMode", 3)  # 3 is the value for UDIM mode
    cmds.setAttr(f"{file_node}.useFrameExtension", 0)  # Don't use frame extension
    cmds.setAttr(f"{file_node}.defaultColor", 0.5, 0.5, 0.5, type="double3")  # Set default color to gray

    # Find all UDIM texture files in the directory
    texture_files = [f for f in os.listdir(TEXTURE_PATH) if f.endswith('.jpg') or f.endswith('.jpeg')]
    if not texture_files:
        cmds.warning(f"No texture files found in {TEXTURE_PATH}")
        return

    # Set the first texture file as the base
    base_texture = os.path.join(TEXTURE_PATH, texture_files[0])
    cmds.setAttr(f"{file_node}.fileTextureName", base_texture, type="string")

    # Create place2dTexture node and connect it
    place2d = cmds.shadingNode("place2dTexture", asUtility=True, name="rigX_place2dTexture")
    cmds.connectAttr(f"{place2d}.outUV", f"{file_node}.uvCoord")
    cmds.connectAttr(f"{place2d}.outUvFilterSize", f"{file_node}.uvFilterSize")

    # Assign the shader to all target meshes
    target_meshes = get_target_meshes()
    for shape in target_meshes:
        transform = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        try:
            # Ensure the mesh has map1 UV set
            uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            if "map1" not in uv_sets:
                cmds.polyUVSet(shape, create=True, uvSet="map1")
            cmds.polyUVSet(shape, uvSet="map1", currentUVSet=True)
            
            # Assign the shader
            cmds.sets(transform, edit=True, forceElement=shading_group)
            if verbose:
                print(f"    → Assigned '{shader_name}' to mesh '{transform}'")
        except Exception as e:
            cmds.warning(f"[assign_udim_textures] Could not assign '{shader_name}' to '{transform}': {e}")

    # Create UV linking through relationship editor
    for shape in target_meshes:
        try:
            # Get the UV set
            uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            if "furUVs" in uv_sets:
                # Create the UV linking
                cmds.uvLink(texture=file_node, uvSet=f"{shape}.furUVs")
                if verbose:
                    print(f"    → Created UV link between '{file_node}' and '{shape}.furUVs'")
        except Exception as e:
            cmds.warning(f"[assign_udim_textures] Could not create UV link for '{shape}': {e}")

    cmds.select(clear=True)
    if verbose:
        print("[assign_udim_textures] Done.")
