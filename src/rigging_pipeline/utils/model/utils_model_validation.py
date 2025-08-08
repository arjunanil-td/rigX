from collections import defaultdict
import maya.cmds as cmds
import maya.api.OpenMaya as om

def _check_geo_group_exists():
    """Check if the top-level 'geo' group exists."""
    if not cmds.objExists("geo"):
        return ["ERROR: Top‐level group 'geo' not found."]
    return []

def _get_mesh_shapes():
    """Get all mesh shapes under the 'geo' group."""
    shapes = cmds.ls("geo", dag=True, type="mesh", noIntermediate=True) or []
    if not shapes:
        return [], ["WARN: No mesh shapes found under 'geo'."]
    return shapes, []

def _check_uv_sets(shape, transform):
    """Check UV sets for a given shape."""
    results = []
    uv_sets = cmds.polyUVSet(shape, q=True, allUVSets=True) or []
    current_uv = cmds.polyUVSet(shape, q=True, currentUVSet=True)[0]
    
    if "furUVs" not in uv_sets:
        results.append(f"ERROR: '{transform}' missing UV‐set 'furUVs'.")
    elif current_uv != "furUVs":
        results.append(f"WARN: '{transform}' current UV‐set is '{current_uv}', expected 'furUVs'.")
    
    return results

def _check_shaders(shape, transform):
    """Check shader assignments for a given shape."""
    results = []
    sgs = cmds.listConnections(shape, type="shadingEngine") or []
    
    if not sgs:
        results.append(f"ERROR: '{transform}' has no shading group assigned.")
    else:
        good = any("lambert" in sg for sg in sgs)
        if not good:
            results.append(f"WARN: '{transform}' not using a lambert shader (found: {sgs}).")
    
    return results

def _check_z_tag(transform):
    """Check zTag attribute for a given transform."""
    results = []
    
    if cmds.attributeQuery("zTag", node=transform, exists=True):
        val = cmds.getAttr(f"{transform}.zTag") or ""
        locked = cmds.getAttr(f"{transform}.zTag", lock=True)
        
        if not val:
            results.append(f"WARN: '{transform}' has empty zTag.")
        if not locked:
            results.append(f"WARN: '{transform}' zTag is unlocked.")
    else:
        results.append(f"ERROR: '{transform}' missing zTag attribute.")
    
    return results

def _check_pivot_at_origin(transform):
    """Check if a transform's pivot is at the origin."""
    pivot = cmds.xform(transform, q=True, ws=True, rp=True)
    if any(abs(v) > 1e-4 for v in pivot):
        return [f"WARN: '{transform}' pivot is not at origin: {pivot}"]
    return []

def _noneManifoldEdges(_, SLMesh):
    noneManifoldEdges = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        edgeIt = om.MItMeshEdge(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not edgeIt.isDone():
            if edgeIt.numConnectedFaces() > 2:
                noneManifoldEdges[uuid].append(edgeIt.index())
            edgeIt.next()
        selIt.next()
    return "edge", noneManifoldEdges

def _getNodeName(uuid):
    nodeName = cmds.ls(uuid, uuid=True)
    if nodeName:
        return nodeName[0]
    return None

def _trailingNumbers(nodes, _):
    trailingNumbers = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName and nodeName[-1].isdigit():
                trailingNumbers.append(node)
    return "nodes", trailingNumbers

def _duplicatedNames(nodes, _):
    nodesByShortName = defaultdict(list)
    for node in nodes:
        nodeName = _getNodeName(node)
        name = nodeName.rsplit('|', 1)[-1]
        nodesByShortName[name].append(node)
    invalid = []
    for name, shortNameNodes in nodesByShortName.items():
        if len(shortNameNodes) > 1:
            invalid.extend(shortNameNodes)
    return "nodes", invalid

def _namespaces(nodes, _):
    namespaces = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName and ':' in nodeName:
            namespaces.append(node)
    return "nodes", namespaces

def _shapeNames(nodes, _):
    shapeNames = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName:
            new = nodeName.split('|')
            shape = cmds.listRelatives(nodeName, shapes=True)
            if shape:
                shapename = new[-1] + "Shape"
                if shape[0] != shapename:
                    shapeNames.append(node)
    return "nodes", shapeNames

def _triangles(_, SLMesh):
    triangles = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            numOfEdges = faceIt.getEdges()
            if len(numOfEdges) == 3:
                triangles[uuid].append(faceIt.index())
            faceIt.next()
        selIt.next()
    return "polygon", triangles

def _ngons(_, SLMesh):
    ngons = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            numOfEdges = faceIt.getEdges()
            if len(numOfEdges) > 4:
                ngons[uuid].append(faceIt.index())
            faceIt.next()
        selIt.next()
    return "polygon", ngons

def _hardEdges(_, SLMesh):
    hardEdges = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        edgeIt = om.MItMeshEdge(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not edgeIt.isDone():
            if edgeIt.isSmooth() is False and edgeIt.onBoundary() is False:
                hardEdges[uuid].append(edgeIt.index())
            edgeIt.next()
        selIt.next()
    return "edge", hardEdges

def _selfPenetratingUVs(transformNodes, _):
    selfPenetratingUVs = defaultdict(list)
    for node in transformNodes:
        nodeName = _getNodeName(node)
        shapes = cmds.listRelatives(
            nodeName,
            shapes=True,
            type="mesh",
            noIntermediate=True)
        if shapes:
            overlapping = cmds.polyUVOverlap("{}.f[*]".format(shapes[0]), oc=True)
            if overlapping:
                formatted = [ overlap.split("{}.f[".format(shapes[0]))[1][:-1] for overlap in overlapping ]
                selfPenetratingUVs[node].extend(formatted)
    return "polygon", selfPenetratingUVs

def _check_non_manifold(shape, transform):
    """Check for non-manifold edges in a mesh."""
    results = []
    sel_list = om.MSelectionList()
    sel_list.add(shape)
    none_manifold_edges = _noneManifoldEdges(None, sel_list)
    if none_manifold_edges[1]:
        results.append(f"ERROR: '{transform}' has non-manifold edges.")
    return results

def qc_validation_check():
    """
    Run a series of checks on the scene and return a list of result strings.
    Errors are prefixed with "ERROR:", warnings with "WARN:".
    """
    results = []
    
    # Check if geo group exists
    results.extend(_check_geo_group_exists())
    if results:  # If geo group doesn't exist, return early
        return results
    
    # Get all mesh shapes
    shapes, shape_results = _get_mesh_shapes()
    results.extend(shape_results)
    if not shapes:  # If no shapes found, return early
        return results
    
    # Check each shape
    for shape in shapes:
        transform = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
        
        # Check UV sets
        results.extend(_check_uv_sets(shape, transform))
        
        # Check shaders
        results.extend(_check_shaders(shape, transform))
        
        # Check zTag
        results.extend(_check_z_tag(transform))
        
        # Check non-manifold geometry
        results.extend(_check_non_manifold(shape, transform))
    
    # Check pivots for all transforms
    transforms = cmds.ls("geo", dag=True, type="transform", long=True) or []
    for transform in transforms:
        results.extend(_check_pivot_at_origin(transform))
    
    return results 