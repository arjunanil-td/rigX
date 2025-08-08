import maya.cmds as cmds

from rigging_pipeline.io import rigx_buildInfo as buildInfo
from rigging_pipeline.io import rigx_file_import_flat as import_file
from rigging_pipeline.utils.rig import utils_rig_texture as rig_texture


def rigx_publish(build_name, facial_Vis=0):
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
        cmds.setAttr(joint_vis_attr, lock=True)
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

    if facial_Vis:
        cmds.addAttr(main_ctrl, longName="facial_Vis", attributeType="bool",
                        keyable=True)
        
        cmds.connectAttr((main_ctrl + ".facial_Vis"), ("FaceGroup.visibility"))


    # 6. Delete all non-default display layers
    all_layers = cmds.ls(type='displayLayer')
    custom_layers = [layer for layer in all_layers if layer != 'defaultLayer']
    if custom_layers:
        cmds.delete(custom_layers)
        print(f"Deleted display layers: {', '.join(custom_layers)}")
    else:
        print("No custom display layers to delete.")


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


    # Disable override on children if it's enabled
    if cmds.objExists('geo'):
        cmds.setAttr("geo.overrideEnabled", 1)

    if cmds.objExists('geo'):
        cmds.parent('geo', top_group)
        print("Parented 'geo' under top group")

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


    # Character specific post-finalize
    if build_name == "charTiger":
        MAIN_MESH = "body_IDcharSkin_GEO"
        FINAL_MESH = "body_finalMesh_GEO"

        if cmds.objExists(MAIN_MESH):
            cmds.rename(MAIN_MESH, FINAL_MESH)
            cmds.parent(FINAL_MESH, "extraGeometry")
            print(f"Renamed {MAIN_MESH} to {FINAL_MESH}")
        else:
            cmds.warning(f"{MAIN_MESH} does not exist, skipping rename.")

        # Importing the textures (Because of the shape name mess up in ADS) - NOT IDEAL..!! Updating soon..
        import_file.import_flat(r"Q:/METAL/projects/Kantara/Production/Assets/charTiger/rig/maya/arjun_a/scene/texture.ma")

        cmds.parent(MAIN_MESH, "HiRes")
        cmds.blendShape(FINAL_MESH, MAIN_MESH, name='finalBS', w=[0,1.0])
        cmds.connectAttr(main_ctrl + ".modelVis", MAIN_MESH + ".visibility")

        cmds.delete("eyesProxy_GRP")

        # Assign shaders for the eye geometries
        rig_texture.assign_eye_shaders()
        



        # Special case for tiger rig
        cmds.delete("whiskers_GRP")
        cmds.delete("muscleGeometry_GRP")
        cmds.setAttr("Geometry.visibility", 0)
        cmds.setAttr("Main.modelVis", 0)
        cmds.setAttr("Proxy.overrideEnabled", 0)
        cmds.setAttr("HiRes.overrideEnabled", 0)
        cmds.setAttr("bodyProxy_GEOBase.overrideEnabled", 0)

        wrap_bases = ["body_IDcharSkin_GEOBase", "body_IDcharSkin_GEOBase1", "body_IDcharSkin_GEOBase2"]
        for base in wrap_bases:
            if cmds.objExists(base):
                cmds.parent(base, "extraGeometry")
            else:
                cmds.warning(f"{base} does not exist, skipping.")




    print("✅ Rig finalize complete.")


