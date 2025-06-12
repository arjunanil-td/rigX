import maya.cmds as cmds
import maya.mel as mel
import os

def duplicate_joint_chain(root_joint):
    new_root = cmds.duplicate(root_joint, po=True, name=root_joint + "_bake")[0]
    joint_map = {root_joint: new_root}

    def duplicate_children(orig_joint, dup_joint):
        children = cmds.listRelatives(orig_joint, type='joint', children=True) or []
        for child in children:
            dup_child = cmds.duplicate(child, po=True, name=child + "_bake")[0]
            cmds.parent(dup_child, dup_joint)
            joint_map[child] = dup_child
            duplicate_children(child, dup_child)

    duplicate_children(root_joint, new_root)
    return new_root, joint_map

def transfer_opm_to_duplicate(orig_joint, dup_joint):
    pos = cmds.xform(orig_joint, q=True, ws=True, t=True)
    rot = cmds.xform(orig_joint, q=True, ws=True, ro=True)
    
    cmds.xform(dup_joint, ws=True, t=pos)
    cmds.xform(dup_joint, ws=True, ro=rot)

def bake_duplicate_chain(joint_map, start_frame, end_frame, step=1):
    cmds.refresh(suspend=True)
    try:
        for frame in range(start_frame, end_frame + 1, step):
            cmds.currentTime(frame, edit=True)
            for orig_joint, dup_joint in joint_map.items():
                transfer_opm_to_duplicate(orig_joint, dup_joint)
                for attr in ['translateX', 'translateY', 'translateZ',
                             'rotateX', 'rotateY', 'rotateZ']:
                    cmds.setKeyframe(dup_joint, at=attr, t=frame)
    finally:
        cmds.refresh(suspend=False)

def create_crowd_group(joint_root):
    group_name = "crowdDeformation"
    if not cmds.objExists(group_name):
        group_name = cmds.group(em=True, name=group_name)
    cmds.parent(joint_root, group_name)
    return group_name

def export_fbx(group_node, export_path, start_frame, end_frame):
    cmds.select(group_node, hi=True)
    
    mel.eval('FBXExportBakeComplexAnimation -v true')
    mel.eval(f'FBXExportBakeComplexStart -v {start_frame}')
    mel.eval(f'FBXExportBakeComplexEnd -v {end_frame}')
    mel.eval('FBXExportUseSceneName -v false')
    mel.eval('FBXExportInputConnections -v false')
    mel.eval('FBXExportSkeletonDefinitions -v true')
    mel.eval('FBXExportShapes -v false')
    mel.eval('FBXExportCameras -v false')
    mel.eval('FBXExportLights -v false')
    mel.eval('FBXExportConstraints -v false')
    mel.eval('FBXExportEmbeddedTextures -v false')
    mel.eval('FBXExportInAscii -v false')

    mel.eval(f'FBXExport -f "{export_path}" -s')
    print(f"✅ FBX exported to: {export_path}")

# === Full Pipeline ===

def bake_and_export_for_crowd(root_joint, export_folder="C:/_exports", file_name="crowd_agent.fbx"):
    if not cmds.objExists(root_joint):
        cmds.error(f"Root joint '{root_joint}' does not exist.")
        return

    start = int(cmds.playbackOptions(q=True, min=True))
    end = int(cmds.playbackOptions(q=True, max=True))

    # Ensure export folder exists
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    export_path = os.path.join(export_folder, file_name).replace("\\", "/")

    # Step 1: Duplicate & bake
    new_root, joint_map = duplicate_joint_chain(root_joint)
    bake_duplicate_chain(joint_map, start, end)

    # Step 2: Group it
    crowd_group = create_crowd_group(new_root)

    # Step 3: Export as FBX
    export_fbx(crowd_group, export_path, start, end)

# === USAGE ===
# Replace with your rig's root joint name
#bake_and_export_for_crowd(root_joint="root_joint", export_folder="C:/your/export/folder", file_name="crowdAgent.fbx")
