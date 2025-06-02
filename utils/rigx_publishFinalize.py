import maya.cmds as cmds
from file import rigx_buildInfo as buildInfo

def rigx_publish(build_name):
    top_group = "Group"
    main_ctrl = "Main"
    geometry_grp = "Geometry"
    geo_grp = "geo"

    info = buildInfo.get_build_info()
    if not info:
        print("⚠️ Failed to extract scene info.")
        return
    build_name = info["build_name"]

    # 1. Rename top group
    if not cmds.objExists(top_group):
        cmds.warning(f"Top group '{top_group}' not found.")
        return
    if cmds.objExists(build_name):
        cmds.warning(f"An object with name '{build_name}' already exists.")
        return
    top_group = cmds.rename(top_group, build_name)
    print(f"Renamed top group to: {top_group}")

    # 2. Set Main.jointVis = 0
    joint_vis_attr = f"{main_ctrl}.jointVis"
    if cmds.objExists(joint_vis_attr):
        cmds.setAttr(joint_vis_attr, 0)
        print(f"Set {joint_vis_attr} to 0")
    else:
        cmds.warning(f"Attribute '{joint_vis_attr}' not found.")

    # 3. Import objects from reference under Geometry and remove namespace
    if cmds.objExists(geometry_grp):
        geo_children = cmds.listRelatives(geometry_grp, children=True, fullPath=True) or []
        imported_refs = set()

        for child in geo_children:
            if cmds.referenceQuery(child, isNodeReferenced=True):
                try:
                    ref_node = cmds.referenceQuery(child, referenceNode=True)
                    if ref_node in imported_refs:
                        continue
                    ref_file = cmds.referenceQuery(ref_node, filename=True)
                    cmds.file(ref_file, importReference=True)
                    imported_refs.add(ref_node)
                    print(f"Imported objects from reference: {ref_node}")
                except Exception as e:
                    cmds.warning(f"Failed to import reference for {child}: {e}")

        # Remove namespaces after import
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True) or []
        for ns in namespaces:
            if ns not in ['UI', 'shared'] and not ns.startswith(":"):
                try:
                    cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
                    print(f"Removed namespace: {ns}")
                except Exception as e:
                    cmds.warning(f"Failed to remove namespace '{ns}': {e}")
    else:
        cmds.warning(f"'{geometry_grp}' group not found.")

    # 4. Add 'Display_Mode' enum to Main control
    display_attr = f"{main_ctrl}.Display_Mode"
    if not cmds.objExists(display_attr):
        cmds.addAttr(main_ctrl, longName="Display_Mode", attributeType="enum",
                     enumName="Normal:Template:Reference", keyable=True)
        print(f"Added enum attribute 'Display_Mode' to {main_ctrl}")
    else:
        print(f"Attribute 'Display_Mode' already exists on {main_ctrl}")

    cmds.setAttr(display_attr, 2)  # Set default to Reference
    print(f"Set {display_attr} to Reference (2)")

    # 5. Set Geometry override and connect to Display_Mode
    if cmds.objExists(geo_grp):
        try:
            cmds.setAttr(f"{geo_grp}.overrideEnabled", 1)
        except Exception as e:
            cmds.warning(f"Could not enable override on {geo_grp}: {e}")

        dest_attr = f"{geo_grp}.overrideDisplayType"
        src_attr = display_attr
        if not cmds.listConnections(dest_attr, source=True, destination=False):
            try:
                cmds.connectAttr(src_attr, dest_attr, force=True)
                print(f"Connected {src_attr} to {dest_attr}")
            except Exception as e:
                cmds.warning(f"Could not connect display mode: {e}")
        else:
            print(f"{dest_attr} is already connected.")


    else:
        cmds.warning(f"'{geo_grp}' group not found.")

    # 6. Delete all non-default display layers
    all_layers = cmds.ls(type='displayLayer')
    custom_layers = [layer for layer in all_layers if layer != 'defaultLayer']
    if custom_layers:
        cmds.delete(custom_layers)
        print(f"Deleted display layers: {', '.join(custom_layers)}")
    else:
        print("No custom display layers to delete.")


    # Disable override on children if it's enabled
    if cmds.objExists('geo'):
        cmds.setAttr("geo.overrideEnabled", 1)

    if cmds.objExists('geo'):
        cmds.parent('geo', top_group)
        print("Parented 'geo' under top group")

    if cmds.objExists(geometry_grp):
        try:
            cmds.delete(geometry_grp)
            print("Deleted 'Geometry' group")
        except Exception as e:
            cmds.warning(f"Could not delete '{geometry_grp}': {e}")

    rig_group = "rig"
    if cmds.objExists(rig_group):
        cmds.warning(f"Rig group '{rig_group}' already exists, using it.")
    else:
        rig_group = cmds.group(empty=True, name=rig_group, parent=top_group)
        print(f"Created rig group: {rig_group}")



    children = cmds.listRelatives(top_group, children=True, fullPath=True) or []
    exclude = {geo_grp, rig_group} 

    for child_path in children:
        child_name = child_path.split("|")[-1]
        if child_name in exclude:
            continue

        try:
            cmds.parent(child_path, rig_group)
            print(f"Parented '{child_name}' under '{rig_group}'")
        except Exception as e:
            cmds.warning(f"Could not parent '{child_name}' under '{rig_group}': {e}")


    print("✅ Rig finalize complete.")


