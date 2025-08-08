import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import json, os
from maya import OpenMayaUI as omui


def _get_skin_cluster(mesh):
    """Find skinCluster on a mesh, return None if not found."""
    hist = cmds.listHistory(mesh, pruneDagObjects=True) or []
    for node in hist:
        if cmds.nodeType(node) == 'skinCluster':
            return node
    return None

def _get_safe_filename(mesh_name):
    """Convert mesh name to a safe filename by replacing invalid characters."""
    # Remove any path separators and invalid characters
    safe_name = mesh_name.replace('|', '_').replace('/', '_').replace('\\', '_')
    return safe_name

def _get_folder_name(filepath):
    """Extract folder name from filepath, removing any extension."""
    # Normalize path separators
    filepath = os.path.normpath(filepath)
    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    # Get the directory part
    dir_path = os.path.dirname(filepath)
    # Combine to get the full folder path
    return os.path.normpath(os.path.join(dir_path, base_name))

def _get_all_meshes_in_group(group):
    """Recursively find all meshes in a group hierarchy."""
    all_meshes = []
    
    # Get all descendants of type transform
    descendants = cmds.listRelatives(group, allDescendents=True, type='transform', fullPath=False) or []
    
    # Add the group itself if it's a transform
    if cmds.nodeType(group) == 'transform':
        descendants.append(group)
    
    # Filter for meshes (transforms that have shape nodes)
    for node in descendants:
        shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
        if shapes and any(cmds.nodeType(shape) == 'mesh' for shape in shapes):
            all_meshes.append(node)
            
    return all_meshes

# --- Save Weights ---

def save_weights(mesh, filepath):
    """Save skin weights of one mesh to a file using OpenMaya API for better performance.
    
    Args:
        mesh (str): Name of the mesh to save weights from
        filepath (str): Full path from file dialog, will be used to create a folder
    """
    if not mesh:
        cmds.warning("Select a skinned mesh.")
        return None
        
    # Create folder using the base name of the filepath
    folder_name = _get_folder_name(filepath)
    os.makedirs(folder_name, exist_ok=True)
    
    # Get skinCluster
    sc = _get_skin_cluster(mesh)
    if not sc:
        cmds.warning(f"Mesh '{mesh}' has no skinCluster, skipping.")
        return None
    
    # Generate filename from mesh name
    safe_name = _get_safe_filename(mesh)
    weight_file = os.path.normpath(os.path.join(folder_name, f"{safe_name}.json"))
    
    # API setup
    sel_list = om.MSelectionList()
    sel_list.add(mesh)
    dag_path = sel_list.getDagPath(0)
    sc_sel = om.MSelectionList()
    sc_sel.add(sc)
    sc_node = sc_sel.getDependNode(0)
    fn_skin = oma.MFnSkinCluster(sc_node)

    # Build a component covering all vertices
    iter_geo = om.MItGeometry(dag_path)
    num_verts = iter_geo.count()
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    for i in range(num_verts):
        comp_fn.addElement(i)

    # Bulk retrieve all weights
    weights_flat, inf_count = fn_skin.getWeights(dag_path, comp)
    flat_list = list(weights_flat)
    influences = [p.partialPathName() for p in fn_skin.influenceObjects()]
    nested = [flat_list[i*inf_count:(i+1)*inf_count] for i in range(num_verts)]

    data = {'influences': influences, 'weights': nested}
    try:
        with open(weight_file, 'w') as f:
            json.dump(data, f, separators=(',',':'))
        cmds.inViewMessage(statusMessage=f"Weights saved for {safe_name} in {folder_name}", fade=True)
        return weight_file
    except Exception as e:
        cmds.warning(f"Save failed for {safe_name}: {e}")
        return None


def save_weights_multiple(meshes, filepath):
    """Save skin weights of multiple meshes to individual files in the specified folder."""
    if not meshes:
        cmds.warning("No meshes selected.")
        return []
        
    # Create folder using the base name of the filepath
    folder_name = _get_folder_name(filepath)
    os.makedirs(folder_name, exist_ok=True)
    
    saved_files = []
    skipped_meshes = []
    
    for mesh in meshes:
        if _get_skin_cluster(mesh):
            weight_file = save_weights(mesh, filepath)
            if weight_file:
                saved_files.append(weight_file)
        else:
            skipped_meshes.append(mesh)
            
    if skipped_meshes:
        cmds.warning(f"Skipped {len(skipped_meshes)} meshes without skinClusters: {', '.join(skipped_meshes)}")
            
    if saved_files:
        cmds.inViewMessage(statusMessage=f"Saved weights for {len(saved_files)} meshes in {folder_name}", fade=True)
    return saved_files


def save_weights_group(group, filepath):
    """Save weights for all meshes under a group, including nested groups."""
    meshes = _get_all_meshes_in_group(group)
    if not meshes:
        cmds.warning(f"No meshes found in group '{group}' or its hierarchy.")
        return []
    return save_weights_multiple(meshes, filepath)

# --- Load Weights ---

def load_weights(mesh, filepath):
    """Load skin weights for one mesh from its corresponding file in the folder."""
    if not mesh:
        cmds.warning("Select a mesh.")
        return False
        
    # Get folder name from filepath
    folder_name = _get_folder_name(filepath)
        
    # Generate expected filename from mesh name
    safe_name = _get_safe_filename(mesh)
    weight_file = os.path.normpath(os.path.join(folder_name, f"{safe_name}.json"))
    
    if not os.path.isfile(weight_file):
        cmds.warning(f"No weight file found for {safe_name} in {folder_name}")
        return False
        
    try:
        with open(weight_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        cmds.warning(f"Load failed for {safe_name}: {e}")
        return False

    saved_influences = data.get('influences', [])
    nested = data.get('weights', [])
    num_verts = len(nested)
    if num_verts == 0:
        cmds.warning(f"No weights in JSON for {safe_name}.")
        return False

    # Get all joints in the scene (not just under DeformationSystem)
    all_scene_joints = cmds.ls(type='joint', long=True) or []
    
    # Create a mapping of base names to full paths
    scene_joint_map = {}
    for joint in all_scene_joints:
        # Get the base name without any path or namespace
        base_name = joint.split('|')[-1].split(':')[-1]
        # Store both the full path and the base name
        scene_joint_map[base_name] = joint
    
    # Create mapping between saved influences and scene joints
    influence_mapping = {}
    missing_influences = []
    name_variations = {}
    
    for saved_inf in saved_influences:
        # Get the base name of the saved influence
        base_name = saved_inf.split('|')[-1].split(':')[-1]
        
        # Try exact match first
        if base_name in scene_joint_map:
            influence_mapping[saved_inf] = scene_joint_map[base_name]
            continue
            
        # Try to find similar names
        found_match = False
        for scene_name, scene_path in scene_joint_map.items():
            # Check if names are similar (ignoring numbers)
            if ''.join(filter(str.isalpha, base_name)) == ''.join(filter(str.isalpha, scene_name)):
                influence_mapping[saved_inf] = scene_path
                name_variations[saved_inf] = scene_name
                found_match = True
                break
                
        if not found_match:
            missing_influences.append(saved_inf)
    
    # Print detailed information about the mapping
    if name_variations:
        print("\nJoint name variations found:")
        for saved, scene in name_variations.items():
            print(f"  {saved} -> {scene}")
    
    if missing_influences:
        print("\nMissing influences:")
        for inf in missing_influences:
            print(f"  {inf}")
        if not influence_mapping:
            cmds.warning("No valid influences found. Cannot create skinCluster.")
            return False
    
    # Get the actual joint names to use for skinCluster
    scene_influences = list(influence_mapping.values())
    
    # Bind new skinCluster
    try:
        sc = cmds.skinCluster(scene_influences, mesh, toSelectedBones=True)[0]
    except Exception as e:
        cmds.warning(f"Failed to create skinCluster: {e}")
        return False

    # API setup
    sel_list = om.MSelectionList()
    sel_list.add(mesh)
    dag_path = sel_list.getDagPath(0)
    sc_sel = om.MSelectionList()
    sc_sel.add(sc)
    sc_node = sc_sel.getDependNode(0)
    fn_skin = oma.MFnSkinCluster(sc_node)

    # Create component covering all verts
    comp_fn = om.MFnSingleIndexedComponent()
    comp_obj = comp_fn.create(om.MFn.kMeshVertComponent)
    for i in range(num_verts):
        comp_fn.addElement(i)

    # Build indices & weights arrays
    idx_array = om.MIntArray()
    for idx in range(len(scene_influences)):
        idx_array.append(idx)
    
    # Map the weights to the new influence order
    mapped_weights = []
    for vert_weights in nested:
        new_vert_weights = []
        for saved_inf in saved_influences:
            if saved_inf in influence_mapping:
                weight_idx = saved_influences.index(saved_inf)
                new_vert_weights.append(vert_weights[weight_idx])
            else:
                new_vert_weights.append(0.0)
        mapped_weights.append(new_vert_weights)
    
    flat_weights = [w for vert in mapped_weights for w in vert]
    weight_array = om.MDoubleArray(flat_weights)

    # Apply all weights in one call
    fn_skin.setWeights(dag_path, comp_obj, idx_array, weight_array, False)
    cmds.inViewMessage(statusMessage=f"Weights loaded for {safe_name} from {folder_name}", fade=True)
    return True


def load_weights_multiple(meshes, filepath):
    """Load skin weights for multiple meshes from their corresponding files in the folder."""
    if not meshes:
        cmds.warning("No meshes selected.")
        return 0
        
    # Get folder name from filepath
    folder_name = _get_folder_name(filepath)
        
    loaded_count = 0
    for mesh in meshes:
        if load_weights(mesh, filepath):
            loaded_count += 1
            
    if loaded_count:
        cmds.inViewMessage(statusMessage=f"Loaded weights for {loaded_count} meshes from {folder_name}", fade=True)
    return loaded_count


def load_weights_group(group, filepath):
    """Load weights for all meshes under the group, including nested groups."""
    meshes = _get_all_meshes_in_group(group)
    if not meshes:
        cmds.warning(f"No meshes found in group '{group}' or its hierarchy.")
        return 0
    return load_weights_multiple(meshes, filepath)

def load_weights_from_file(mesh, weight_file):
    """Load skin weights for one mesh from a specific weight file.
    
    Args:
        mesh (str): Name of the mesh to load weights onto
        weight_file (str): Full path to the weight file to load from
    """
    if not mesh:
        cmds.warning("Select a mesh.")
        return False
        
    # Normalize the weight file path
    weight_file = os.path.normpath(weight_file)
        
    if not os.path.isfile(weight_file):
        cmds.warning(f"Weight file not found: {weight_file}")
        return False
        
    try:
        with open(weight_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        cmds.warning(f"Load failed: {e}")
        return False

    influences = data.get('influences', [])
    nested = data.get('weights', [])
    num_verts = len(nested)
    if num_verts == 0:
        cmds.warning("No weights in JSON file.")
        return False

    # Check if mesh exists
    if not cmds.objExists(mesh):
        cmds.warning(f"Mesh '{mesh}' does not exist.")
        return False

    # Check if mesh has a skinCluster
    existing_sc = _get_skin_cluster(mesh)
    if existing_sc:
        # Remove existing skinCluster
        cmds.delete(existing_sc)

    # Bind new skinCluster
    try:
        sc = cmds.skinCluster(influences, mesh, toSelectedBones=True)[0]
    except Exception as e:
        cmds.warning(f"Failed to create skinCluster: {e}")
        return False

    # API setup
    sel_list = om.MSelectionList()
    sel_list.add(mesh)
    dag_path = sel_list.getDagPath(0)
    sc_sel = om.MSelectionList()
    sc_sel.add(sc)
    sc_node = sc_sel.getDependNode(0)
    fn_skin = oma.MFnSkinCluster(sc_node)

    # Create component covering all verts
    comp_fn = om.MFnSingleIndexedComponent()
    comp_obj = comp_fn.create(om.MFn.kMeshVertComponent)
    for i in range(num_verts):
        comp_fn.addElement(i)

    # Build indices & weights arrays
    idx_array = om.MIntArray()
    for idx in range(len(influences)):
        idx_array.append(idx)
    flat_weights = [w for vert in nested for w in vert]
    weight_array = om.MDoubleArray(flat_weights)

    # Apply all weights in one call
    try:
        fn_skin.setWeights(dag_path, comp_obj, idx_array, weight_array, False)
        cmds.inViewMessage(statusMessage=f"Weights loaded for {mesh} from {weight_file}", fade=True)
        return True
    except Exception as e:
        cmds.warning(f"Failed to apply weights: {e}")
        return False

# --- Copy Weights ---

def copy_weights_one_to_many(source_mesh, target_meshes):
    """Copy skin weights from one source mesh to multiple targets.
    
    Args:
        source_mesh (str): Name of the source mesh to copy weights from
        target_meshes (list): List of target meshes to copy weights to
    """
    if not source_mesh or not target_meshes:
        cmds.warning("Please select a skinned source mesh first, followed by one or more target meshes.")
        return

    source_skin_cluster = cmds.ls(cmds.listHistory(source_mesh), type="skinCluster")
    
    if not source_skin_cluster:
        cmds.warning(f"No skin cluster found on {source_mesh}. Make sure the source is skinned.")
        return

    source_skin_cluster = source_skin_cluster[0]
    influences = cmds.skinCluster(source_skin_cluster, query=True, influence=True)
    
    if not influences:
        cmds.warning("No influences found on the source skin cluster.")
        return

    for target in target_meshes:
        target_skin_cluster = cmds.ls(cmds.listHistory(target), type="skinCluster")

        if not target_skin_cluster:
            target_skin_cluster = cmds.skinCluster(influences, target, toSelectedBones=True, normalizeWeights=1)[0]
            cmds.inViewMessage(amg=f'<hl>Created new skinCluster</hl> on {target}', pos='topCenter', fade=True)
        else:
            target_skin_cluster = target_skin_cluster[0]

        cmds.copySkinWeights(
            sourceSkin=source_skin_cluster,
            destinationSkin=target_skin_cluster,
            noMirror=True,
            surfaceAssociation="closestPoint",
            influenceAssociation=["closestJoint", "oneToOne", "label"]
        )
        
        cmds.inViewMessage(amg=f'<hl>Copied Skin Weights</hl> from {source_mesh} to {target}', pos='topCenter', fade=True)

    cmds.select(target_meshes) 
    cmds.inViewMessage(amg='<hl>Skin Copy Completed!</hl>', pos='topCenter', fade=True)


def copy_weights_many_to_one(source_meshes, target_mesh):
    """Copy skin weights from multiple source meshes to one target.
    
    Args:
        source_meshes (list): List of source meshes to copy weights from
        target_mesh (str): Target mesh to copy weights to
    """
    if not source_meshes or not target_mesh:
        cmds.warning("Please select source meshes first, followed by the target mesh.")
        return

    # Check if target mesh exists
    if not cmds.objExists(target_mesh):
        cmds.warning(f"Target mesh '{target_mesh}' does not exist.")
        return

    # Get the first source mesh's skinCluster and influences
    first_source = source_meshes[0]
    source_skin_cluster = cmds.ls(cmds.listHistory(first_source), type="skinCluster")
    
    if not source_skin_cluster:
        cmds.warning(f"No skin cluster found on {first_source}. Make sure at least one source is skinned.")
        return

    source_skin_cluster = source_skin_cluster[0]
    influences = cmds.skinCluster(source_skin_cluster, query=True, influence=True)
    
    if not influences:
        cmds.warning("No influences found on the source skin cluster.")
        return

    # Check if target has a skinCluster
    target_skin_cluster = cmds.ls(cmds.listHistory(target_mesh), type="skinCluster")

    if not target_skin_cluster:
        # Create new skinCluster on target using influences from first source
        target_skin_cluster = cmds.skinCluster(influences, target_mesh, toSelectedBones=True, normalizeWeights=1)[0]
        cmds.inViewMessage(amg=f'<hl>Created new skinCluster</hl> on {target_mesh}', pos='topCenter', fade=True)
    else:
        target_skin_cluster = target_skin_cluster[0]

    # Copy weights from each source to target
    copied_count = 0
    for source in source_meshes:
        source_skin = cmds.ls(cmds.listHistory(source), type="skinCluster")
        if not source_skin:
            cmds.warning(f"Skipping {source} - no skinCluster found.")
            continue

        source_skin = source_skin[0]
        try:
            cmds.copySkinWeights(
                sourceSkin=source_skin,
                destinationSkin=target_skin_cluster,
                noMirror=True,
                surfaceAssociation="closestPoint",
                influenceAssociation=["closestJoint", "oneToOne", "label"]
            )
            copied_count += 1
            cmds.inViewMessage(amg=f'<hl>Copied Skin Weights</hl> from {source} to {target_mesh}', pos='topCenter', fade=True)
        except Exception as e:
            cmds.warning(f"Failed to copy weights from {source}: {e}")

    if copied_count:
        cmds.select(target_mesh)
        cmds.inViewMessage(amg=f'<hl>Skin Copy Completed!</hl> Copied from {copied_count} sources to {target_mesh}', pos='topCenter', fade=True)
    else:
        cmds.warning("No weights were copied successfully.")

# --- Skin Utilities: Influences, Bind/Unbind ---

def add_influence(joint, mesh):
    """Add a new joint influence to the mesh's skinCluster.
    
    Args:
        mesh (str): Name of the mesh to add influence to
        joint (str): Name of the joint to add as influence
    """
    if not mesh or not joint:
        cmds.warning("Select a mesh and a joint.")
        return False
        
    # Get the skinCluster
    sk = _get_skin_cluster(mesh)
    if not sk:
        cmds.warning(f"No skinCluster found on {mesh}.")
        return False
        
    try:
        # Add influence with zero weights
        cmds.skinCluster(sk, edit=True, addInfluence=joint, lockWeights=True)
        cmds.inViewMessage(amg=f'<hl>Added influence</hl> {joint} to {mesh}', pos='topCenter', fade=True)
        return True
    except Exception as e:
        cmds.warning(f"Failed to add influence: {e}")
        return False


def remove_influence(joint, mesh):
    """Remove a joint influence from the mesh's skinCluster.
    
    Args:
        mesh (str): Name of the mesh to remove influence from
        joint (str): Name of the joint to remove as influence
    """
    if not mesh or not joint:
        cmds.warning("Select a mesh and a joint.")
        return False
        
    # Get the skinCluster
    sk = _get_skin_cluster(mesh)
    if not sk:
        cmds.warning(f"No skinCluster found on {mesh}.")
        return False
        
    try:
        # Remove influence
        cmds.skinCluster(sk, edit=True, removeInfluence=joint)
        cmds.inViewMessage(amg=f'<hl>Removed influence</hl> {joint} from {mesh}', pos='topCenter', fade=True)
        return True
    except Exception as e:
        cmds.warning(f"Failed to remove influence: {e}")
        return False


def bind_skin(meshes, joints=None):
    """Bind skin for given meshes and joints (defaults to selected joints)."""
    if joints is None:
        joints = cmds.ls(selection=True, type='joint')
    cmds.skinCluster(joints, meshes, toSelectedBones=True)


def unbind_skin(mesh):
    """Remove skinCluster from the mesh using the unbind operation and clean up orig shape.
    
    Args:
        mesh (str): Name of the mesh to unbind
    """
    if not mesh:
        cmds.warning("Select a mesh to unbind.")
        return False
        
    # Get the skinCluster
    sk = _get_skin_cluster(mesh)
    if not sk:
        cmds.warning(f"No skinCluster found on {mesh}.")
        return False
        
    try:
        # Get the shape node and its orig node
        shapes = cmds.listRelatives(mesh, shapes=True, fullPath=True) or []
        if not shapes:
            cmds.warning(f"No shape node found on {mesh}.")
            return False
            
        shape = shapes[0]
        orig_shape = f"{shape}Orig"
        
        # Unbind the skin using the skinCluster command
        cmds.skinCluster(sk, edit=True, unbind=True)
        
        # Delete the orig shape if it exists
        if cmds.objExists(orig_shape):
            cmds.delete(orig_shape)
            
        cmds.inViewMessage(amg=f'<hl>Unbound skin</hl> from {mesh} and cleaned up orig shape', pos='topCenter', fade=True)
        return True
    except Exception as e:
        cmds.warning(f"Failed to unbind skin: {e}")
        return False


def remove_unused_influences(mesh):
    """Remove influences with zero weights from the mesh's skinCluster.
    
    Args:
        mesh (str): Name of the mesh to clean up influences
    """
    if not mesh:
        cmds.warning("Select a mesh to clean up influences.")
        return False
        
    # Get the skinCluster
    sk = _get_skin_cluster(mesh)
    if not sk:
        cmds.warning(f"No skinCluster found on {mesh}.")
        return False
        
    try:
        # Remove unused influences
        cmds.skinCluster(sk, edit=True, removeUnusedInfluence=True)
        cmds.inViewMessage(amg=f'<hl>Removed unused influences</hl> from {mesh}', pos='topCenter', fade=True)
        return True
    except Exception as e:
        cmds.warning(f"Failed to remove unused influences: {e}")
        return False

# --- Convert to Skin ---

def curve_to_skin(curve, mesh):
    """Bake skin weights from curve deformation to a skinCluster on mesh."""
    # Example: cluster curve then copy to skin (placeholder)
    cl = cmds.cluster(curve, n=f"{curve}_cluster")[1]
    cmds.copySkinWeights(ss=cl, ds=mesh)


def lattice_to_skin(lattice, mesh):
    """Bake lattice deformer weights to skinCluster on mesh."""
    # placeholder: connect lattice weights to cluster then to skin
    pass


def cluster_to_skin(cluster, mesh):
    """Copy cluster deformation to skin weights on mesh."""
    cmds.copySkinWeights(ss=cluster, ds=mesh)