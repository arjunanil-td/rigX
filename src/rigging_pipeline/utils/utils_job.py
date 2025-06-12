# src/rigging_pipeline/utils/utils_job.py

import maya.cmds as cmds
import os

def detect_show_from_workspace():
    """
    Examine Maya’s current workspace root and return the folder name
    under Q:/METAL/projects/ (preserving its original case). If the
    workspace isn’t under that path, return None.
    """
    try:
        workspace_root = cmds.workspace(query=True, rootDirectory=True)
    except Exception:
        return None

    if not workspace_root:
        return None

    original = workspace_root.replace("\\", "/")
    lowered   = original.lower()

    prefix = "q:/metal/projects/"
    idx = lowered.find(prefix)
    if idx == -1:
        return None

    start = idx + len(prefix)
    remainder = original[start:]  

    parts = remainder.split("/", 1)
    show = parts[0]  

    return show
