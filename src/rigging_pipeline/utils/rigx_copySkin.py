import maya.cmds as cmds

def copy_skin_cluster():
    """Copies the skin cluster from the first selected geometry to all other selected geometries in Maya.
       If the target meshes do not have a skin cluster, a new one is created and weights are transferred.
    """

    # Get the current selection
    selection = cmds.ls(selection=True, long=True)
    
    if len(selection) < 2:
        cmds.warning("Please select a skinned source mesh first, followed by one or more target meshes.")
        return

    source_mesh = selection[0]  # The first selected mesh is the source
    target_meshes = selection[1:]  # Remaining selected meshes are the targets

    # Find the skin cluster on the source mesh
    source_skin_cluster = cmds.ls(cmds.listHistory(source_mesh), type="skinCluster")
    
    if not source_skin_cluster:
        cmds.warning(f"No skin cluster found on {source_mesh}. Make sure the source is skinned.")
        return

    source_skin_cluster = source_skin_cluster[0]

    # Get influences (joints) from the source skin cluster
    influences = cmds.skinCluster(source_skin_cluster, query=True, influence=True)
    
    if not influences:
        cmds.warning("No influences found on the source skin cluster.")
        return

    for target in target_meshes:
        # Check if the target already has a skin cluster
        target_skin_cluster = cmds.ls(cmds.listHistory(target), type="skinCluster")

        if not target_skin_cluster:
            # If no skinCluster exists, create a new one using the same influences as the source
            target_skin_cluster = cmds.skinCluster(influences, target, toSelectedBones=True, normalizeWeights=1)[0]
            cmds.inViewMessage(amg=f'<hl>Created new skinCluster</hl> on {target}', pos='topCenter', fade=True)
        else:
            target_skin_cluster = target_skin_cluster[0]

        # Copy skin weights from source to target
        cmds.copySkinWeights(
            sourceSkin=source_skin_cluster,
            destinationSkin=target_skin_cluster,
            noMirror=True,
            surfaceAssociation="closestPoint",
            influenceAssociation=["closestJoint", "oneToOne", "label"]
        )
        
        cmds.inViewMessage(amg=f'<hl>Copied Skin Weights</hl> from {source_mesh} to {target}', pos='topCenter', fade=True)

    cmds.select(target_meshes)  # Select target meshes for visual confirmation
    cmds.inViewMessage(amg='<hl>Skin Copy Completed!</hl>', pos='topCenter', fade=True)

# Run the function
# copy_skin_cluster()
