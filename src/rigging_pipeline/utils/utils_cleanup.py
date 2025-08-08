import maya.cmds as cmds

"""
Maya Scene Cleanup Utilities

Provides a collection of functions to streamline and automate common scene cleanup tasks in Maya.
"""


def delete_unknown_nodes():
    """
    Remove unknown plugin requirements from the scene to prevent runtime errors when loading.
    Uses the Maya 2016.5+ 'unknownPlugin' command to list and remove plugin entries.
    """
    # Query unknown plugins required by the scene
    unknowns = cmds.unknownPlugin(q=True, list=True) or []
    if not unknowns:
        print("No unknown plugin requirements found.")
        return
    for plugin in unknowns:
        try:
            cmds.unknownPlugin(plugin, remove=True)
            print(f"Removed unknown plugin requirement: {plugin}")
        except Exception as e:
            print(f"Failed to remove unknown plugin '{plugin}': {e}")


def remove_empty_groups():
    """
    Remove all transform nodes that have no children.
    """
    empties = []
    for grp in cmds.ls(type='transform'):
        if not cmds.listRelatives(grp, children=True):
            empties.append(grp)
    if empties:
        cmds.delete(empties)
        print(f"Deleted empty groups: {empties}")
    else:
        print("No empty groups to delete.")


def cleanup_mesh_history():
    """
    Delete construction history on all mesh transforms.
    """
    meshes = cmds.ls(type='mesh', long=True) or []
    for mesh in meshes:
        transform = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
        cmds.delete(transform, constructionHistory=True)
    print(f"Cleared construction history on {len(meshes)} meshes.")


def freeze_transforms():
    """
    Freeze transforms on all transform nodes.
    """
    transforms = cmds.ls(type='transform') or []
    for t in transforms:
        cmds.makeIdentity(t, apply=True, translate=True, rotate=True, scale=True, normal=False)
    print(f"Froze transforms on {len(transforms)} nodes.")


def delete_default_cameras():
    """
    Delete Maya's default cameras (persp, top, front, side).
    """
    defaults = ['persp', 'top', 'front', 'side']
    found = [cam for cam in defaults if cmds.objExists(cam)]
    if found:
        cmds.delete(found)
        print(f"Deleted default cameras: {found}")
    else:
        print("No default cameras found.")


def delete_default_lights():
    """
    Delete Maya's default directional light.
    """
    # Maya creates an initial directionalLight named 'directionalLight1'
    lights = cmds.ls(type='directionalLight') or []
    if lights:
        cmds.delete(lights)
        print(f"Deleted default lights: {lights}")
    else:
        print("No default directional lights found.")


def remove_unused_uv_sets(default_uv='map1'):
    """
    For each mesh shape, delete all UV sets except the default.
    """
    shapes = cmds.ls(type='mesh', long=True) or []
    for shape in shapes:
        uvsets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
        for uv in uvsets:
            if uv != default_uv:
                cmds.polyUVSet(shape, delete=True, uvSet=uv)
                print(f"Deleted UV set '{uv}' on {shape}")
    print("Completed UV set cleanup.")


def delete_unused_materials():
    """
    Remove materials (shadingEngines) not assigned to any geometry.
    """
    sgs = cmds.ls(type='shadingEngine') or []
    removed = []
    for sg in sgs:
        if sg in ('initialShadingGroup', 'initialParticleSE'):
            continue
        members = cmds.sets(sg, query=True) or []
        if not members:
            cmds.delete(sg)
            removed.append(sg)
    print(f"Deleted unused shadingEngines: {removed}")


def delete_unknown_plugins():
    """
    Unload any plugins that are loaded but not in use.
    """
    loaded = cmds.pluginInfo(query=True, listPlugins=True) or []
    for plugin in loaded:
        # Try to unload, ignore errors
        try:
            cmds.unloadPlugin(plugin)
            print(f"Unloaded plugin: {plugin}")
        except:
            pass
    print("Plugin cleanup complete.")


def delete_unused_nodes():
    """
    Delete nodes that are not connected to the DAG (Directed Acyclic Graph).
    This helps remove unused nodes that might be cluttering the scene.
    """
    unused = cmds.ls(dag=False, transforms=False) or []
    if unused:
        cmds.delete(unused)
        print(f"Deleted unused nodes: {unused}")
    else:
        print("No unused nodes found.")

def cleanup_namespaces():
        all_ns = cmds.namespaceInfo(listOnlyNamespaces=True,recurse=True) or []
        ignore = {'UI','shared'}
        refs = cmds.file(query=True,referenceNode=True) or []
        ref_ns = {cmds.referenceQuery(r, namespace=True) for r in refs if cmds.referenceQuery(r, namespace=True)}
        to_remove = [ns for ns in all_ns if ns.split(':')[0] not in ignore|ref_ns]
        to_remove.sort(key=lambda n: n.count(':'), reverse=True)
        for ns in to_remove:
            try: cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
            except: pass
        cmds.inViewMessage(statusMessage="Namespaces cleared",fade=True)
        print("Namespace Removed.")


def delete_unused_curves():
    """
    Delete curves that are not connected to any other nodes.
    """
    curves = cmds.ls(type='nurbsCurve', long=True) or []
    unused = []
    for curve in curves:
        connections = cmds.listConnections(curve, source=True, destination=True) or []
        if not connections:
            unused.append(curve)
    if unused:
        cmds.delete(unused)
        print(f"Deleted unused curves: {unused}")
    else:
        print("No unused curves found.")


def cleanup_reference_nodes():
    """
    Remove reference nodes that are no longer valid or needed.
    """
    refs = cmds.ls(type='reference') or []
    for ref in refs:
        try:
            if not cmds.referenceQuery(ref, isLoaded=True):
                cmds.file(removeReference=True, referenceNode=ref)
                print(f"Removed invalid reference: {ref}")
        except:
            pass
    print("Reference cleanup complete.")


def delete_unused_anim_layers():
    """
    Delete animation layers that contain no animation data.
    """
    layers = cmds.ls(type='animLayer') or []
    unused = []
    for layer in layers:
        if layer == 'BaseAnimation':
            continue
        if not cmds.animLayer(layer, query=True, animCurves=True):
            unused.append(layer)
    if unused:
        cmds.delete(unused)
        print(f"Deleted unused animation layers: {unused}")
    else:
        print("No unused animation layers found.")


def create_clean_mesh_duplicate():
    """
    Creates a clean duplicate of selected geometry meshes.
    The duplicate will:
    - Have no construction history
    - Have frozen transforms
    - Have no custom attributes
    - Have no connections
    - Have no orig shapes
    - Have all attributes unlocked (including channel box)
    - Be properly named with '_clean' suffix
    
    Returns:
        list: Names of the created clean duplicates
    """
    # Get selected transforms
    selection = cmds.ls(selection=True, long=True) or []
    if not selection:
        print("No objects selected.")
        return []
    
    # Filter for transforms that have mesh shapes
    mesh_transforms = []
    for obj in selection:
        if cmds.objectType(obj) == 'transform':
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            has_mesh = False
            for shape in shapes:
                if cmds.objectType(shape) == 'mesh':
                    has_mesh = True
                    break
            if has_mesh:
                mesh_transforms.append(obj)
    
    if not mesh_transforms:
        print("No mesh objects selected.")
        return []
    
    clean_duplicates = []
    for transform in mesh_transforms:
        # Create duplicate of the transform
        duplicate = cmds.duplicate(transform, name=f"{transform.split('|')[-1]}_clean")[0]
        
        # Get all shape nodes including intermediate objects
        all_shapes = cmds.listRelatives(duplicate, shapes=True, allDescendants=True, fullPath=True) or []
        
        # Remove all orig shapes and intermediate objects
        for shape in all_shapes:
            if shape.endswith('Orig') or cmds.getAttr(f"{shape}.intermediateObject"):
                try:
                    cmds.delete(shape)
                except:
                    pass
        
        # Delete construction history
        cmds.delete(duplicate, constructionHistory=True)

        # Unlock all transform attributes
        transform_attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
        for attr in transform_attrs:
            try:
                cmds.setAttr(f"{duplicate}.{attr}", lock=False)
                cmds.setAttr(f"{duplicate}.{attr}", keyable=True)
            except:
                pass
        
        # Freeze transforms
        cmds.makeIdentity(duplicate, apply=True, translate=True, rotate=True, scale=True)
        
        # Remove custom attributes
        custom_attrs = cmds.listAttr(duplicate, userDefined=True) or []
        for attr in custom_attrs:
            try:
                cmds.deleteAttr(f"{duplicate}.{attr}")
            except:
                pass
        
        # Break connections
        connections = cmds.listConnections(duplicate, source=True, destination=True, plugs=True) or []
        for conn in connections:
            try:
                cmds.disconnectAttr(conn)
            except:
                pass
        
              
    
        
        clean_duplicates.append(duplicate)
        print(f"Created clean duplicate: {duplicate}")
    
    return clean_duplicates

