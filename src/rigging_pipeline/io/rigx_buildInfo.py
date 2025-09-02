import maya.cmds as mc
import os

def get_build_info():
    # Get the full scene path
    scene_path = mc.file(q=True, sn=True)
    if not scene_path:
        mc.warning("Scene has not been saved yet.")
        return

    print(f"Scene Path: {scene_path}")

    # Break the path into components
    path_parts = scene_path.replace("\\", "/").split("/")
    
    # Example: get the build name (folder before artist folder)
    try:
        build_name = path_parts[6]  # "charTiger"
        file_name = os.path.basename(scene_path)  # "kntr_tigerA_ri_v19.mb"
        version = os.path.splitext(file_name)[0].split("_")[-1]  # "v19"
        asset_code = file_name.split("_")[1]  # "tigerA"

        return {
            "build_name": build_name,
            "file_name": file_name,
            "version": version,
            "asset_code": asset_code,
            "full_path": scene_path
        }
    except IndexError as e:
        mc.warning(f"Failed to parse path: {e}")
        return



