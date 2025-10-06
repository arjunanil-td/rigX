# src/rigging_pipeline/tools/hierarchy_utils.py

"""
Hierarchy presets for your pipeline. Each key is a group name, and its value
is either None (no children) or another dict describing its children.
You may use the placeholder '<assetName>' which will be replaced at runtime.
"""

# Character hierarchy preset (existing structure)
CHAR_HIERARCHY_PRESET = {
    "geo": {
        "<assetName>": {
            "proxy": {
                "boneGeometry_GRP": None,
            },
            "hiRes": {
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

# Prop hierarchy preset
PROP_HIERARCHY_PRESET = {
    "geo": {
        "<assetName>": {
            "hiRes": None,
            "proxy": None,
            "allModel": None,
        }
    }
}

# Vehicle hierarchy preset
VHCL_HIERARCHY_PRESET = {
    "geo": {
        "<assetName>": {
            "deformModel": None,
            "transformModel": None,
        }
    }
}



import maya.cmds as cmds
import os
from pathlib import Path

def get_job_info():
    """Get job information from JOB_PATH environment variable."""
    job_path_env = os.environ.get("JOB_PATH")
    job_path = Path(job_path_env) if job_path_env else None
    
    if job_path is None:
        return {
            "show": "unknown",
            "asset": "unknown", 
            "shot": "unknown",
            "department": "unknown",
            "path": None
        }
    
    try:
        data = str(job_path).split(os.sep)
        if len(data) >= 4:
            return {
                "show": data[3] if len(data) > 3 else "unknown",
                "asset": data[-2] if len(data) > 1 else "unknown",
                "shot": data[-2] if len(data) > 1 else "unknown", 
                "department": data[-1] if len(data) > 0 else "unknown",
                "path": job_path
            }
        else:
            return {
                "show": "unknown",
                "asset": "unknown",
                "shot": "unknown", 
                "department": "unknown",
                "path": job_path
            }
    except Exception:
        return {
            "show": "unknown",
            "asset": "unknown",
            "shot": "unknown", 
            "department": "unknown", 
            "path": job_path
        }

def _add_metadata_attributes(node_path, asset_name, root_name, verbose=False):
    """
    Add metadata attributes to the specified node for asset tracking.
    Gets job information from environment variables.
    
    Args:
        node_path (str): Path to the node to add attributes to
        asset_name (str): The asset name (variant)
        root_name (str): The root group name (actual asset name with prefix)
        verbose (bool): Enable verbose output
    """
    try:
        # Get job information from environment variables
        job_info = get_job_info()
        
        # Add assetName attribute
        if not cmds.attributeQuery("assetName", node=node_path, exists=True):
            cmds.addAttr(node_path, longName="assetName", dataType="string")
        cmds.setAttr(f"{node_path}.assetName", root_name, type="string")
        
        # Add variant attribute
        if not cmds.attributeQuery("variant", node=node_path, exists=True):
            cmds.addAttr(node_path, longName="variant", dataType="string")
        cmds.setAttr(f"{node_path}.variant", asset_name, type="string")
        
        
        # Add show attribute from job info
        if not cmds.attributeQuery("show", node=node_path, exists=True):
            cmds.addAttr(node_path, longName="show", dataType="string")
        cmds.setAttr(f"{node_path}.show", job_info["show"], type="string")
        
        # Add department attribute from job info
        if not cmds.attributeQuery("department", node=node_path, exists=True):
            cmds.addAttr(node_path, longName="department", dataType="string")
        cmds.setAttr(f"{node_path}.department", job_info["department"], type="string")
        
        # Add jobPath attribute
        if not cmds.attributeQuery("jobPath", node=node_path, exists=True):
            cmds.addAttr(node_path, longName="jobPath", dataType="string")
        job_path_str = str(job_info["path"]) if job_info["path"] else "unknown"
        cmds.setAttr(f"{node_path}.jobPath", job_path_str, type="string")
        
        # Add user information
        import getpass
        current_user = getpass.getuser()
        if not cmds.attributeQuery("createdBy", node=node_path, exists=True):
            cmds.addAttr(node_path, longName="createdBy", dataType="string")
        cmds.setAttr(f"{node_path}.createdBy", current_user, type="string")
        
        # Add creation timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not cmds.attributeQuery("createdDate", node=node_path, exists=True):
            cmds.addAttr(node_path, longName="createdDate", dataType="string")
        cmds.setAttr(f"{node_path}.createdDate", timestamp, type="string")
        
        if verbose:
            print(f"[_add_metadata_attributes] Added metadata to {node_path}")
            print(f"  - assetName: {root_name}")
            print(f"  - variant: {asset_name}")
            print(f"  - show: {job_info['show']}")
            print(f"  - department: {job_info['department']}")
            print(f"  - jobPath: {job_path_str}")
            print(f"  - createdBy: {current_user}")
            print(f"  - createdDate: {timestamp}")
            
    except Exception as e:
        if verbose:
            print(f"[_add_metadata_attributes] Error adding metadata to {node_path}: {e}")

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
    Convenience wrapper. Ensures `root` exists, then builds the appropriate preset under it
    based on asset name prefix (char, prop, vhcl).
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

    # Determine hierarchy preset based on root name prefix (root is the actual asset name in UI)
    root_lower = root.lower()
    print(f"[create_model_hierarchy] Debug - Root: '{root}', Lower: '{root_lower}'")
    print(f"[create_model_hierarchy] Debug - Asset name (variant): '{asset_name}'")
    
    if root_lower.startswith('char'):
        preset = CHAR_HIERARCHY_PRESET
        asset_type = "character"
        print(f"[create_model_hierarchy] Selected CHARACTER preset for root: {root}")
    elif root_lower.startswith('prop'):
        preset = PROP_HIERARCHY_PRESET
        asset_type = "prop"
        print(f"[create_model_hierarchy] Selected PROP preset for root: {root}")
    elif root_lower.startswith('vhcl'):
        preset = VHCL_HIERARCHY_PRESET
        asset_type = "vehicle"
        print(f"[create_model_hierarchy] Selected VEHICLE preset for root: {root}")
    else:
        # Default to character hierarchy for unknown prefixes
        preset = CHAR_HIERARCHY_PRESET
        asset_type = "character (default)"
        print(f"[create_model_hierarchy] Unknown root prefix, using CHARACTER (default) preset for: {root}")

    if verbose:
        print(f"[create_model_hierarchy] Using {asset_type} hierarchy for asset: {asset_name}")

    creator = HierarchyCreator(preset)
    top = creator.create(asset_name, parent=root, verbose=verbose)
    
    # Add metadata attributes to the root node (not the variant node)
    _add_metadata_attributes(root, asset_name, root, verbose)
    
    if verbose:
        print(f"[create_model_hierarchy] Finished creating {asset_type} hierarchy: {top}")
    return top
