import os
import maya.cmds as cmds

def select_object(field_name):
    """Generic function to handle object selection"""
    sel = cmds.ls(selection=True)
    if sel:
        cmds.textField(field_name, edit=True, text=sel[0])

# Modules for SET creation and addition
def rigx_create_set(name="set1"):
    if not cmds.objExists(name):
        cmds.sets(name=name)
        print(f"Created set: {name}")
    else:
        print(f"Set '{name}' already exists.")

def rigx_sets_add_selected():
    sel = cmds.ls(selection=True)
    if len(sel) < 2:
        cmds.error("Select objects and then the set (at least two selections required).")
        return

    set_node = sel[-1]
    add_items = sel[:-1]

    if cmds.nodeType(set_node) != "objectSet":
        cmds.error("The last selected item must be a set!")
        return

    cmds.sets(add_items, add=set_node)
    print(f"Added {add_items} to set '{set_node}'.")

def rigx_sets_remove_selected():
    sel = cmds.ls(selection=True)
    if len(sel) < 2:
        cmds.error("Select objects and then the set (at least two selections required).")
        return

    set_node = sel[-1]
    remove_items = sel[:-1]

    if cmds.nodeType(set_node) != "objectSet":
        cmds.error("The last selected item must be a set!")
        return

    cmds.sets(remove_items, remove=set_node)
    print(f"Removed {remove_items} from set '{set_node}'.")

# Create the Anim set for the puppet
def rigx_create_anim_set(motion_group="MotionSystem", parent_set="Sets", new_set_name="AnimSet"):
    if not cmds.objExists(motion_group):
        cmds.warning(f"Group '{motion_group}' does not exist.")
        return

    # Find all child transforms under MotionSystem
    all_children = cmds.listRelatives(motion_group, allDescendents=True, type="transform") or []
    
    # Filter for those with nurbsCurve shapes and not under IKCurve
    control_transforms = []
    for node in all_children:
        # Get the full path of the node
        node_path = cmds.ls(node, long=True)[0]
        
        # Skip if node is under IKCurve group
        if "|IKCurve|" in node_path:
            continue
            
        shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []
        for shape in shapes:
            if cmds.nodeType(shape) == "nurbsCurve":
                control_transforms.append(node)
                break  

    if not control_transforms:
        cmds.warning("No NURBS curve controls found under MotionSystem.")
        return

    # Create new set if it doesn't exist
    if not cmds.objExists(new_set_name):
        anim_set = cmds.sets(control_transforms, name=new_set_name)
    else:
        anim_set = new_set_name
        cmds.sets(control_transforms, edit=True, forceElement=anim_set)

    # Parent new set under the main 'Sets' set
    if cmds.objExists(parent_set):
        cmds.sets(anim_set, include=parent_set)
    else:
        cmds.warning(f"Parent set '{parent_set}' does not exist. 'AnimSet' created standalone.")

    print(f"Created '{new_set_name}' with {len(control_transforms)} controls.")

# Create control pivot space switch
def rigx_create_pivot_space(control, attr_name, enum_values, passing_controls):
    """
    Create a pivot space setup on the given control using passed transform positions.
    
    Args:
        control (str): The name of the control to add enum and connect pivot to.
        attr_name (str): The name of the enum attribute to add.
        enum_values (list): List of enum labels (e.g., ["pos1", "pos2", "pos3"]).
        passing_controls (list): List of transform names used as pivot positions.
    """
    if not cmds.objExists(control):
        cmds.warning(f"Control '{control}' does not exist.")
        return

    if not enum_values or not passing_controls:
        cmds.warning("Enum values and passing controls must be provided.")
        return

    if len(enum_values) != len(passing_controls):
        cmds.warning("Enum values count must match passing controls count.")
        return

    # Create enum attribute
    enum_string = ":".join(enum_values)
    if not cmds.attributeQuery(attr_name, node=control, exists=True):
        cmds.addAttr(control, longName=attr_name, attributeType='enum', enumName=enum_string, keyable=True)

    # Create locator and offset group
    loc_name = f"{control}_pivot_ctrl"
    offset_name = f"{control}_pivot_offset"

    loc = cmds.spaceLocator(name=loc_name)[0]
    cmds.setAttr(f"{loc}.visibility", 0)

    offset_grp = cmds.group(empty=True, name=offset_name)
    cmds.parent(loc, offset_grp)
    cmds.parent(offset_grp, control)

    # Zero out transforms
    for node in [loc, offset_grp]:
        cmds.setAttr(f"{node}.translate", 0, 0, 0)
        cmds.setAttr(f"{node}.rotate", 0, 0, 0)
        cmds.setAttr(f"{node}.scale", 1, 1, 1)

    # Connect offset + locator to control's rotatePivot using addDoubleLinear
    for axis in ['X', 'Y', 'Z']:
        add_node = cmds.createNode('addDoubleLinear', name=f'{control}_pivot_add_{axis}')
        cmds.connectAttr(f'{offset_grp}.translate{axis}', f'{add_node}.input1')
        cmds.connectAttr(f'{loc}.translate{axis}', f'{add_node}.input2')
        cmds.connectAttr(f'{add_node}.output', f'{control}.rotatePivot{axis}')

    # Set driven keyframes for each enum value
    for i, ctrl in enumerate(passing_controls):
        if not cmds.objExists(ctrl):
            cmds.warning(f"Passing control '{ctrl}' does not exist.")
            continue

        trans = cmds.xform(ctrl, query=True, translation=True, worldSpace=True)
        rot = cmds.xform(ctrl, query=True, rotation=True, worldSpace=True)

        # Set enum attr value
        cmds.setAttr(f"{control}.{attr_name}", i)

        # Set offset group to the passing control's transform
        cmds.xform(offset_grp, translation=trans, rotation=rot, worldSpace=True)

        # Set driven keys
        cmds.setDrivenKeyframe(f"{offset_grp}.translate", currentDriver=f"{control}.{attr_name}")
        cmds.setDrivenKeyframe(f"{offset_grp}.rotate", currentDriver=f"{control}.{attr_name}")

    # Reset enum to default (first)
    cmds.setAttr(f"{control}.{attr_name}", 0)
    print(f"Pivot space setup complete for {control}.")

def unlock_all_attributes(node):
    """
    Unlock all attributes on a node.
    
    Args:
        node (str): Name of the node to unlock attributes on
    """
    if not cmds.objExists(node):
        cmds.warning(f"Node '{node}' does not exist")
        return
        
    # Get all attributes
    attrs = cmds.listAttr(node, keyable=True) or []
    attrs.extend(cmds.listAttr(node, locked=True) or [])
    
    # Unlock each attribute
    for attr in attrs:
        try:
            cmds.setAttr(f"{node}.{attr}", lock=False)
        except:
            continue

def unhide_all_attributes(node):
    """
    Unhide all attributes on a node.
    
    Args:
        node (str): Name of the node to unhide attributes on
    """
    if not cmds.objExists(node):
        cmds.warning(f"Node '{node}' does not exist")
        return
        
    # Get all attributes
    attrs = cmds.listAttr(node, keyable=True) or []
    attrs.extend(cmds.listAttr(node, locked=True) or [])
    attrs.extend(cmds.listAttr(node, userDefined=True) or [])
    
    # Unhide each attribute
    for attr in attrs:
        try:
            # Make attribute keyable and visible
            cmds.setAttr(f"{node}.{attr}", keyable=True)
            # Remove any channel box restrictions
            cmds.setAttr(f"{node}.{attr}", channelBox=True)
        except:
            continue

def strip_custom_attributes(node):
    """
    Remove all custom attributes from a node.
    
    Args:
        node (str): Name of the node to strip custom attributes from
    """
    if not cmds.objExists(node):
        cmds.warning(f"Node '{node}' does not exist")
        return
        
    # Get all custom attributes
    custom_attrs = cmds.listAttr(node, userDefined=True) or []
    
    # Remove each custom attribute
    for attr in custom_attrs:
        try:
            cmds.deleteAttr(f"{node}.{attr}")
        except:
            continue

def delete_all_children(node):
    """
    Delete all children under a node.
    
    Args:
        node (str): Name of the node to delete children from
    """
    if not cmds.objExists(node):
        cmds.warning(f"Node '{node}' does not exist")
        return
        
    # Get all children
    children = cmds.listRelatives(node, children=True, fullPath=True, shapes=False, type='transform') or []
    
    # Delete each child
    if children:
        cmds.delete(children)

def clean_duplicated_control(control):
    """
    Clean up a duplicated control by unlocking attributes, unhiding attributes,
    stripping custom attributes, and deleting children.
    
    Args:
        control (str): Name of the control to clean up
    """
    if not cmds.objExists(control):
        cmds.warning(f"Control '{control}' does not exist")
        return
        
    unlock_all_attributes(control)
    unhide_all_attributes(control)
    strip_custom_attributes(control)
    delete_all_children(control)

def export_control_shapes(anim_set, export_path):
    """
    Gather all transforms in `anim_set`, duplicate them cleanly into a temp group,
    rename to strip namespaces and ensure unique names, then export that group to
    a Maya file at `export_path`.

    Args:
        anim_set (str): name of the Maya objectSet containing controls.
        export_path (str): full path to save the Maya ASCII file (must end in .ma).
    """
    # validate set
    if not cmds.objExists(anim_set) or cmds.nodeType(anim_set) != 'objectSet':
        cmds.error(f"Set '{anim_set}' not found or not an objectSet.")
    members = cmds.sets(anim_set, q=True) or []
    # create temp group
    tmp_grp = 'controlShapes_GRP'
    if cmds.objExists(tmp_grp):
        cmds.delete(tmp_grp)
    tmp_grp = cmds.group(empty=True, name=tmp_grp)

    seen = set()
    for ctrl in members:
        if not cmds.objExists(ctrl) or cmds.nodeType(ctrl)!='transform':
            continue
        # strip namespace and duplicates
        short = ctrl.split(':')[-1]
        name = short
        # ensure unique
        i = 1
        while name in seen:
            name = f"{short}_{i:02d}"
            i += 1
        seen.add(name)
        # duplicate transform only (no shape?)  duplicate with shapes
        dup = cmds.duplicate(ctrl)[0]
        # Clean up the duplicated control
        clean_duplicated_control(dup)
        # parent under tmp_grp and zero out transforms
        cmds.parent(dup, tmp_grp)
        cmds.xform(dup, matrix=cmds.xform(ctrl, q=True, matrix=True, worldSpace=True), worldSpace=True)
        cmds.rename(dup, ctrl)
    # export the tmp_grp
    # ensure directory exists
    d = os.path.dirname(export_path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    # select and export
    cmds.select(tmp_grp, replace=True)
    cmds.file(export_path, force=True, type='mayaAscii', exportSelected=True)
    cmds.select(clear=True)
    # cleanup
    cmds.delete(tmp_grp)
    cmds.inViewMessage(statusMessage=f"Exported control shapes to {export_path}", fade=True)

def rigx_import_control_shapes(file_path, scale=1.0):
    """
    Imports control shapes from a file and applies them to existing controls.
    
    Args:
        file_path (str): Path to the file containing control shapes
        scale (float): Scale factor for the imported shapes
    """
    if not os.path.exists(file_path):
        cmds.warning(f"File '{file_path}' does not exist.")
        return

    # Generate unique namespace
    base_ns = "temp_import"
    ns = base_ns
    counter = 1
    while cmds.namespace(exists=ns):
        ns = f"{base_ns}_{counter}"
        counter += 1

    try:
        # Import the file
        cmds.file(file_path, i=True, namespace=ns, mergeNamespacesOnClash=True)
        
        # Get all controls in the imported namespace that have shapes
        imported_controls = []
        for ctrl in cmds.ls(f"{ns}:*", type="transform"):
            shapes = cmds.listRelatives(ctrl, shapes=True, fullPath=True) or []
            if shapes:
                imported_controls.append(ctrl)
        
        if not imported_controls:
            cmds.warning("No controls with shapes found in the imported file.")
            return

        # Apply shapes to existing controls
        for imported_control in imported_controls:
            # Get the base name without namespace
            base_name = imported_control.split(":")[-1]
            
            # Find matching control in the scene, excluding the imported namespace
            existing_controls = [ctrl for ctrl in cmds.ls(base_name, type="transform", long=True) 
                               if not ctrl.startswith(f"{ns}:")]
            
            if not existing_controls:
                cmds.warning(f"No matching control found for '{base_name}'")
                continue
                
            if len(existing_controls) > 1:
                cmds.warning(f"Multiple matches found for '{base_name}'. Using first match.")
            
            # Verify the existing control has shapes to replace
            existing_shapes = cmds.listRelatives(existing_controls[0], shapes=True, fullPath=True) or []
            if not existing_shapes:
                cmds.warning(f"Control '{base_name}' has no shapes to replace.")
                continue
            
            # Use the new swap function to update the shape
            try:
                rigx_swap_control_shape([existing_controls[0]], imported_control)
                print(f"Successfully updated shapes for control '{base_name}'")
            except Exception as e:
                cmds.warning(f"Failed to update shape for '{base_name}': {str(e)}")
                continue

    except Exception as e:
        cmds.warning(f"Error during import: {str(e)}")
    finally:
        # Clean up
        try:
            cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
        except Exception as e:
            cmds.warning(f"Error during cleanup: {str(e)}")

    cmds.delete("controlShapes_GRP")        
    cmds.inViewMessage(statusMessage="Imported and applied control shapes.", fade=True)

def rigx_swap_control_shape(controls, new_shape):
    """
    Swaps the shape of controls with a new shape while preserving connections and set memberships.
    
    Args:
        controls (list): List of control transforms to update
        new_shape (str): Transform node containing the new shape to use
    """
    if not controls or not new_shape:
        cmds.warning("Please select both controls to replace and the new curve to use")
        return
        
    # Check if we're dealing with edges
    is_edge_selection = any("e[" in ctrl for ctrl in controls)
    
    if is_edge_selection:
        # Handle edge-based curve creation
        if cmds.objExists("combinedEdgesAsCurve"):
            cmds.delete("combinedEdgesAsCurve")
            
        # Get edges and controls
        edges = [ctrl for ctrl in controls if "e[" in ctrl]
        ctrls = [ctrl for ctrl in controls if "e[" not in ctrl]
        
        if not ctrls:
            cmds.warning("No Controller found in the selection")
            return
            
        # Select edges and create curve
        cmds.select(edges, replace=True)
        cmds.duplicateCurve(ch=0)
        cmds.delete(constructionHistory=True)
        
        # Get created curves
        created_curves = cmds.ls(selection=True)
        
        if len(created_curves) == 1:
            cmds.duplicate(created_curves[0], name="combinedEdgesAsCurve")
        else:
            # Attach multiple curves
            cmds.attachCurve(created_curves, name="combinedEdgesAsCurve", 
                           constructionHistory=0, replaceOriginal=0, 
                           keepMultipleKnots=1, blendBias=0.5, 
                           blendKnotInsertion=0, parameter=0.1)
            
        cmds.delete(created_curves)
        
        # Create temporary transform and position curve
        temp_xform = cmds.createNode("transform", name="tempXform", parent=ctrls[0])
        cmds.parent("combinedEdgesAsCurve", temp_xform)
        cmds.xform(temp_xform, objectSpace=True, translation=[0,0,0], rotation=[0,0,0])
        cmds.parent("combinedEdgesAsCurve", world=True)
        cmds.makeIdentity("combinedEdgesAsCurve", apply=True, translate=True, rotate=True, scale=True)
        cmds.xform("combinedEdgesAsCurve", worldSpace=True, pivots=[0,0,0])
        cmds.scale(1.3, 1.3, 1.3, "combinedEdgesAsCurve.cv[0:999]", relative=True, pivot=[0,0,0])
        
        # Set override color
        cmds.setAttr("combinedEdgesAsCurveShape.overrideEnabled", 1)
        old_shape = cmds.listRelatives(ctrls[0], shapes=True)[0]
        override_color = cmds.getAttr(f"{old_shape}.overrideColor")
        cmds.setAttr("combinedEdgesAsCurveShape.overrideColor", override_color)
        
        # Clean up
        cmds.delete(temp_xform)
        new_shape = "combinedEdgesAsCurve"
        controls = ctrls
    
    # Process each control
    for control in controls:
        # Get old shape and its connections
        old_shapes = cmds.listRelatives(control, shapes=True, fullPath=True) or []
        
        # Store set memberships
        was_in_allset = False
        was_in_face_allset = False
        if old_shapes:
            if cmds.objExists("AllSet"):
                was_in_allset = cmds.sets(old_shapes[0], isMember="AllSet")
            if cmds.objExists("FaceAllSet"):
                was_in_face_allset = cmds.sets(old_shapes[0], isMember="FaceAllSet")
        
        # Store visibility connections
        visibility_connections = []
        if old_shapes:
            visibility_connections = cmds.listConnections(old_shapes[0], 
                                                        source=True, 
                                                        destination=False, 
                                                        plugs=True) or []
        
        # Get new shapes
        new_shapes = cmds.listRelatives(new_shape, shapes=True, fullPath=True) or []
        if not new_shapes:
            cmds.warning(f"No shapes found on '{new_shape}'")
            continue
            
        # Delete old shapes
        if old_shapes:
            cmds.delete(old_shapes)
        
        # Create and connect new shapes
        for i, shape in enumerate(new_shapes):
            # Get the shape type
            shape_type = cmds.nodeType(shape)
            
            # Create new shape node with proper name
            base_name = control.split("|")[-1]  # Get the short name
            new_shape_name = f"{base_name}Shape"
            if i > 0:  # Add index for multiple shapes
                new_shape_name = f"{base_name}Shape{i+1}"
            
            if cmds.objExists(new_shape_name):
                cmds.delete(new_shape_name)
            
            # Create new shape and copy data
            new_shape_node = cmds.createNode(shape_type, name=new_shape_name)
            cmds.connectAttr(f"{shape}.worldSpace[0]", f"{new_shape_node}.create", force=True)
            
            # Parent to control
            cmds.parent(new_shape_node, control, shape=True, relative=True)
            
            # Handle rotation
            # rotation = cmds.xform(control, query=True, worldSpace=True, rotation=True)
            # if not all(r == 0 for r in rotation):
            #     cmds.rotate(-90, -90, 0, f"{new_shape_name}.cv[0:9999]", relative=True, objectSpace=True)
            
            # Copy drawing overrides from imported shape
            override_enabled = cmds.getAttr(f"{shape}.overrideEnabled")
            cmds.setAttr(f"{new_shape_node}.overrideEnabled", override_enabled)
            if override_enabled:
                override_color = cmds.getAttr(f"{shape}.overrideColor")
                override_visibility = cmds.getAttr(f"{shape}.overrideVisibility")
                cmds.setAttr(f"{new_shape_node}.overrideColor", override_color)
                cmds.setAttr(f"{new_shape_node}.overrideVisibility", override_visibility)
            
            # Copy visibility from imported shape
            visibility = cmds.getAttr(f"{shape}.visibility")
            cmds.setAttr(f"{new_shape_node}.visibility", visibility)
            
            # Restore set memberships
            if was_in_allset:
                cmds.sets(new_shape_node, addElement="AllSet")
            if was_in_face_allset:
                cmds.sets(new_shape_node, addElement="FaceAllSet")
            
            # Restore visibility connections
            for conn in visibility_connections:
                try:
                    cmds.connectAttr(conn, f"{new_shape_node}.visibility", force=True)
                except:
                    pass
    
    # Final cleanup
    if is_edge_selection:
        cmds.delete("combinedEdgesAsCurve")
    
    # Update DG
    cmds.dgdirty(a=True)
    print("Control shapes swapped successfully.")


# UTILS FOR CROWD
def attribute_to_attribute_connection(source, destination):
    attrs = cmds.listAttr(source + '.w', m=True) or []
    for attr in attrs[1:]:  # Skip the first attribute
        if attr == "FaceJointsLayer":
            continue
        clean_attr = attr.replace('_', '')
        src_attr = f"{source}.{attr}"
        dest_attr = f"{destination}.{clean_attr}"
        cmds.addAttr(destination, longName=clean_attr, attributeType='double', defaultValue=0.0, keyable=True)
        existing = cmds.listConnections(dest_attr, s=True, d=False, plugs=True) or []
        if src_attr not in existing:
            try:
                cmds.connectAttr(dest_attr, src_attr, force=True)
            except Exception as e:
                print(f"Could not connect {src_attr} to {dest_attr}: {e}")
    
    


def extract_shape_from_facialNode(FACIAL_NODE):

    weight_attrs = cmds.listAttr(FACIAL_NODE + '.w', m=True) or []
    return weight_attrs

def add_blendshape_attrs_to_locator(facial_node, locator):

    targets = extract_shape_from_facialNode(facial_node)
    for attr in targets[1:]:  # Skip the first attribute
        if attr == "FaceJointsLayer":
            continue
        if not cmds.attributeQuery(attr, node=locator, exists=True):
            cmds.addAttr(locator, longName=attr, attributeType='double', defaultValue=0.0, keyable=True)
        # Connect locator.attr to facial_node.attr (blendShape weight)
        src = f"{facial_node}.{attr}"
        dest = f"{locator}.{attr}"
        # Only connect if not already connected
        existing = cmds.listConnections(dest, s=True, d=False, plugs=True) or []
        if src not in existing:
            try:
                cmds.connectAttr(src, dest, force=True)
            except Exception as e:
                print(f"Could not connect {src} to {dest}: {e}")

def add_blendshape_attrs_to_skeleton(facial_node, FACIAL_LOC, ROOT_JOINT):

    targets = extract_shape_from_facialNode(facial_node)
    for attr in targets[1:]:  # Skip the first attribute
        if attr == "FaceJointsLayer":
            continue
        if not cmds.attributeQuery(attr, node=ROOT_JOINT, exists=True):
            cmds.addAttr(ROOT_JOINT, longName=attr, attributeType='double', defaultValue=0.0, keyable=True)
        
        src = f"{FACIAL_LOC}.{attr}"
        dest = f"{ROOT_JOINT}.{attr}"
        # Only connect if not already connected
        existing = cmds.listConnections(dest, s=True, d=False, plugs=True) or []
        if src not in existing:
            try:
                cmds.connectAttr(src, dest, force=True)
            except Exception as e:
                print(f"Could not connect {src} to {dest}: {e}")

# Adding facial connection to crowd joint
def rigx_crowd_facial_offset_connection(BODY_MESH, FACIAL_NODE, ROOT_JOINT):

    BODY_MESH = "body_IDcharSkin_GEO"
    FACIAL_NODE = "asFaceBS"
    ROOT_JOINT = "spineJA_JNT"

    FACIAL_LOC = cmds.spaceLocator(n="facial_LOC")

    if not cmds.objExists("FaceGroup"):
        cmds.warning(f"FaceGroup does not exist")
        return

    cmds.parent(FACIAL_LOC, "FaceGroup")

    add_blendshape_attrs_to_locator(FACIAL_NODE, FACIAL_LOC[0])
    add_blendshape_attrs_to_skeleton(FACIAL_NODE, FACIAL_LOC[0], ROOT_JOINT)

