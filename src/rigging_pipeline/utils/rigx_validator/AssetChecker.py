import os
from pathlib import Path
import maya.cmds as cmds

DESCRIPTION = "Asset Checker: derive asset from JOB_PATH, verify/rename top node to match."


def get_job_info():
    if JOB_PATH is None:
        return {
            "show": "unknown",
            "asset": "unknown",
            "shot": "unknown",
            "department": "unknown",
            "path": None
        }
    try:
        data = str(JOB_PATH).split(os.sep)
        if len(data) >= 4:
            return {
                "show": data[3] if len(data) > 3 else "unknown",
                "asset": data[-2] if len(data) > 1 else "unknown",
                "shot": data[-2] if len(data) > 1 else "unknown",
                "department": data[-1] if len(data) > 0 else "unknown",
                "path": JOB_PATH
            }
        else:
            return {
                "show": "unknown",
                "asset": "unknown",
                "shot": "unknown",
                "department": "unknown",
                "path": JOB_PATH
            }
    except Exception:
        return {
            "show": "unknown",
            "asset": "unknown",
            "shot": "unknown",
            "department": "unknown",
            "path": JOB_PATH
        }


def run_validation(mode="check", objList=None, action=None):
    issues = []

    def _short_non_ns(name):
        n = name.split('|')[-1]
        return n.split(':')[-1]

    if mode == "check":
        try:
            job_path_env = os.environ.get("JOB_PATH")
            global JOB_PATH
            JOB_PATH = Path(job_path_env) if job_path_env else None

            info = get_job_info() if JOB_PATH is not None else {
                "show": "unknown",
                "asset": "unknown",
                "shot": "unknown",
                "department": "unknown",
                "path": None,
            }

            os.environ["RIGX_SHOW"] = str(info.get("show", ""))
            os.environ["RIGX_ASSET"] = str(info.get("asset", ""))
            os.environ["RIGX_DEPARTMENT"] = str(info.get("department", ""))

            asset_name = (info.get("asset") or "unknown").strip()

            # Determine top-level outliner groups (assemblies) excluding default cameras
            top_nodes = cmds.ls(assemblies=True) or []
            excluded = {"persp", "top", "front", "side"}
            filtered_top_nodes = []
            for node in top_nodes:
                if node in excluded:
                    continue
                shapes = cmds.listRelatives(node, shapes=True) or []
                if any(cmds.nodeType(s) == "camera" for s in shapes):
                    continue
                filtered_top_nodes.append(node)

            # Check match
            if asset_name == "unknown":
                # Cannot validate without a known asset name
                return {
                    "status": "error",
                    "message": "Top node check failed: asset unknown (JOB_PATH not set)",
                    "issues": [{
                        "object": "TopNode",
                        "message": "Asset unknown; cannot verify top node",
                        "fixed": False
                    }],
                    "total_issues": 1
                }

            normalized_nodes = [_short_non_ns(n) for n in filtered_top_nodes]
            
            # Check for exact match (case-insensitive)
            exact_match = None
            for node in normalized_nodes:
                if node.lower() == asset_name.lower():
                    exact_match = node
                    break
            
            if not exact_match:
                return {
                    "status": "error",
                    "message": f"Top group prefix is not matching with '{asset_name}'. Please update it manually according to the asset.",
                    "issues": [{
                        "object": "TopNode",
                        "message": f"Top group prefix is not matching with '{asset_name}'. Please update it manually according to the asset.",
                        "fixed": False
                    }],
                    "total_issues": 1
                }

            # Matched
            return {
                "status": "success",
                "issues": [{
                    "object": exact_match,
                    "message": f"Top node '{exact_match}' matches asset '{asset_name}'",
                    "fixed": True
                }],
                "total_issues": 1
            }
        except Exception as e:
            return {"status": "error", "message": f"TopNode check failed: {e}", "total_issues": 1}

    if mode == "fix":
        try:
            job_path_env = os.environ.get("JOB_PATH")
            global JOB_PATH
            JOB_PATH = Path(job_path_env) if job_path_env else None

            info = get_job_info() if JOB_PATH is not None else {
                "show": "unknown",
                "asset": "unknown",
                "shot": "unknown",
                "department": "unknown",
                "path": None,
            }

            asset_name = (info.get("asset") or "unknown").strip()
            if asset_name == "unknown":
                return {
                    "status": "error",
                    "message": "Cannot fix: asset unknown (JOB_PATH not set)",
                    "issues": [{
                        "object": "TopNode",
                        "message": "Asset unknown; cannot rename top node",
                        "fixed": False
                    }],
                    "total_issues": 1
                }

            # Determine current top-level nodes (exclude default cameras)
            top_nodes = cmds.ls(assemblies=True) or []
            excluded = {"persp", "top", "front", "side"}
            filtered_top_nodes = []
            for node in top_nodes:
                if node in excluded:
                    continue
                shapes = cmds.listRelatives(node, shapes=True) or []
                if any(cmds.nodeType(s) == "camera" for s in shapes):
                    continue
                filtered_top_nodes.append(node)

            if not filtered_top_nodes:
                return {
                    "status": "error",
                    "message": "Cannot fix: no top-level nodes found",
                    "issues": [{
                        "object": "TopNode",
                        "message": "No top-level outliner groups to rename",
                        "fixed": False
                    }],
                    "total_issues": 1
                }

            normalized_nodes = [_short_non_ns(n) for n in filtered_top_nodes]
            
            # Check if already matches exactly
            for node in normalized_nodes:
                if node.lower() == asset_name.lower():
                    return {
                        "status": "success",
                        "issues": [{
                            "object": node,
                            "message": f"Top node '{node}' already matches asset name '{asset_name}'",
                            "fixed": True
                        }],
                        "total_issues": 1
                    }

            # Select a candidate to rename
            source_node = None
            # Prefer a case-insensitive match to enforce exact casing
            for dag in filtered_top_nodes:
                if _short_non_ns(dag).lower() == asset_name.lower():
                    source_node = dag
                    break
            # Next, a node containing the asset substring
            if source_node is None:
                for dag in filtered_top_nodes:
                    if asset_name.lower() in _short_non_ns(dag).lower():
                        source_node = dag
                        break
            # If still none, use single candidate if only one exists
            if source_node is None and len(filtered_top_nodes) == 1:
                source_node = filtered_top_nodes[0]
            # If still ambiguous, error
            if source_node is None:
                return {
                    "status": "error",
                    "message": "Cannot auto-fix: multiple top-level nodes present",
                    "issues": [{
                        "object": "TopNode",
                        "message": f"Found multiple top nodes: {', '.join(normalized_nodes)}",
                        "fixed": False
                    }],
                    "total_issues": 1
                }

            # Avoid conflicting name
            if cmds.objExists(asset_name) and source_node != asset_name:
                return {
                    "status": "error",
                    "message": f"Cannot fix: node named '{asset_name}' already exists",
                    "issues": [{
                        "object": source_node,
                        "message": f"Target name '{asset_name}' already exists",
                        "fixed": False
                    }],
                    "total_issues": 1
                }
            try:
                new_name = cmds.rename(source_node, asset_name)
                fixed = (new_name.split('|')[-1] == asset_name)
                return {
                    "status": "success" if fixed else "error",
                    "issues": [{
                        "object": new_name,
                        "message": f"Renamed top node to '{asset_name}'" if fixed else f"Rename did not result in exact name '{asset_name}'",
                        "fixed": fixed
                    }],
                    "total_issues": 1
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Rename failed: {e}",
                    "issues": [{
                        "object": source_node,
                        "message": f"Failed to rename to '{asset_name}'",
                        "fixed": False
                    }],
                    "total_issues": 1
                }
        except Exception as e:
            return {"status": "error", "message": f"TopNode fix failed: {e}", "total_issues": 1}

    return {"status": "success", "issues": issues, "total_issues": len(issues)}


