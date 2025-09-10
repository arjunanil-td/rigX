import maya.cmds as cmds
from collections import Counter, defaultdict


# Short description used by the validator UI
DESCRIPTION = "Check if there are any nodes with duplicate short names and report them."


def run_validation(mode="check", objList=None):
    """Detect duplicate short names in the DAG.

    Returns a dictionary in the standard validator format.
    No automatic fix is provided.
    """
    try:
        issues = []

        # Get all DAG nodes (with long paths so we can detect duplicates properly)
        nodes = cmds.ls(dag=True, long=True) or []

        if not nodes:
            return {
                "status": "success",
                "issues": [{
                    'object': "Scene",
                    'message': "No nodes found to check",
                    'fixed': True
                }],
                "total_checked": 0,
                "total_issues": 1
            }

        # Build map: short name -> list of full paths (O(N))
        name_to_paths = defaultdict(list)
        for node in nodes:
            short = node.rsplit('|', 1)[-1]
            name_to_paths[short].append(node)

        # Duplicates are entries with more than one path
        duplicates = {name: paths for name, paths in name_to_paths.items() if len(paths) > 1}

        if duplicates:
            # Report each duplicate short name; include full paths for clarity
            for short_name, paths in duplicates.items():
                issues.append({
                    'object': short_name,
                    'message': "Duplicate name found: {} -> {} instance(s)\n{}".format(
                        short_name, len(paths), "\n".join(["   - " + p for p in paths])
                    ),
                    'fixed': False
                })
        else:
            issues.append({
                'object': "Scene",
                'message': "No duplicate names found",
                'fixed': True
            })

        return {
            "status": "success",
            "issues": issues,
            "total_checked": len(nodes),
            "total_issues": len(issues)
        }

    except Exception as e:
        return {"status": "error", "message": str(e), "total_issues": 1}


