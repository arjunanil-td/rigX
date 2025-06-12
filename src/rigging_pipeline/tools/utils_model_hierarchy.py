# src/rigging_pipeline/tools/hierarchy_utils.py

"""
Hierarchy presets for your pipeline. Each key is a group name, and its value
is either None (no children) or another dict describing its children.
You may use the placeholder '<assetName>' which will be replaced at runtime.
"""

MODEL_HIERARCHY_PRESET = {
    "geo": {
        "<assetName>": {
            "Proxy": {
                "boneGeometry_GRP": None,
            },
            "HiRes": {
                "muscleGeometry_GRP": None,
            },
            "allModel": {
                "nails_GRP": None,
                "teeth_GRP": None,
                "eyes_GRP": None,         
            },
        }
    }
}



import maya.cmds as cmds

class HierarchyCreator:

    def __init__(self, preset):
        self.preset = preset

    def create(self, asset_name, parent=None, verbose=False):

        created_top = None

        def _recurse(level_dict, parent_node):
            nonlocal created_top
            for key, children in level_dict.items():
                # substitute the assetName placeholder
                grp_basename = key.replace("<assetName>", asset_name)
                full_name = grp_basename if not parent_node else f"{parent_node}|{grp_basename}"

                # create or reuse
                if cmds.objExists(full_name):
                    node = full_name
                    if verbose:
                        print(f"[Hierarchy] Re-using: {node}")
                else:
                    node = cmds.group(empty=True, name=grp_basename, parent=parent_node) \
                           if parent_node else cmds.group(empty=True, name=grp_basename)
                    if verbose:
                        print(f"[Hierarchy] Created: {node}")

                # capture the top-level asset group
                if key == "<assetName>":
                    created_top = node

                # recurse if there are further children
                if isinstance(children, dict):
                    _recurse(children, node)

        # launch the recursion
        _recurse(self.preset, parent)

        if not created_top:
            raise RuntimeError(f"Failed to create top-level '<assetName>' under {parent!r}")
        return created_top


def create_model_hierarchy(asset_name, root="geo", verbose=False):
    """
    Convenience wrapper. Ensures `root` exists, then builds the preset under it.
    Returns the path to root|asset_name.
    """
    # ensure the top group
    if not cmds.objExists(root):
        cmds.group(empty=True, name=root)
        if verbose:
            print(f"[create_model_hierarchy] Created root: {root}")
    else:
        if verbose:
            print(f"[create_model_hierarchy] Root already exists: {root}")

    creator = HierarchyCreator(MODEL_HIERARCHY_PRESET)
    top = creator.create(asset_name, parent=root, verbose=verbose)
    if verbose:
        print(f"[create_model_hierarchy] Finished creating hierarchy: {top}")
    return top
