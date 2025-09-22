"""
ControlValues Validation Module
Checks animation set controls for proper TR values (0) and Scale values (1)
"""

import maya.cmds as cmds
import os
from pathlib import Path

DESCRIPTION = "Check animation set controls for proper TR values (0) and Scale values (1)"

def get_asset_prefix():
    """Get asset prefix from JOB_PATH to determine if FaceControlSet should be included"""
    job_path_env = os.environ.get("JOB_PATH")
    if not job_path_env:
        return "unknown"
    
    try:
        JOB_PATH = Path(job_path_env)
        data = str(JOB_PATH).split(os.sep)
        if len(data) >= 4:
            asset_name = data[-2] if len(data) > 1 else "unknown"
            # Extract prefix (first 4 characters)
            prefix = asset_name[:4].lower()
            return prefix
    except Exception:
        pass
    
    return "unknown"

def run_validation(mode="check", objList=None):
    """Run the validation module using 'Sets' → 'AnimSet' membership and unlocked-attr checks"""
    issues = []

    # Step 1: Check if 'Sets' exists
    if not cmds.objExists("Sets"):
        issues.append({
            'object': "Scene",
            'message': "Validation failed: 'Sets' set not found in scene.",
            'fixed': False
        })
        return {
            "status": "success",
            "issues": issues,
            "total_checked": 0,
            "total_issues": len(issues)
        }

    # Step 2: Check if 'AnimSet' exists under 'Sets' and whether 'FaceControlSet' exists (only for char assets)
    sets_members = cmds.sets("Sets", q=True) or []
    asset_prefix = get_asset_prefix()
    
    # Only include FaceControlSet for character assets
    include_face = False
    if asset_prefix == "char" and "FaceControlSet" in sets_members:
        include_face = True
        print(f"Asset prefix '{asset_prefix}' detected - including FaceControlSet in validation")
    else:
        print(f"Asset prefix '{asset_prefix}' detected - skipping FaceControlSet validation")
    
    if "AnimSet" not in sets_members:
        issues.append({
            'object': "Scene",
            'message': "Validation failed: 'AnimSet' not found under 'Sets'.",
            'fixed': False
        })
        return {
            "status": "success",
            "issues": issues,
            "total_checked": 0,
            "total_issues": len(issues)
        }

    # Step 3: Get members of AnimSet (required) and FaceControlSet (optional)
    controls = []
    controls.extend(cmds.sets("AnimSet", q=True) or [])
    if include_face:
        controls.extend(cmds.sets("FaceControlSet", q=True) or [])
    if not controls:
        issues.append({
            'object': "Scene",
            'message': ("No controls found in 'AnimSet' or 'FaceControlSet'." if include_face else "No controls found in 'AnimSet'."),
            'fixed': True
        })
        return {
            "status": "success",
            "issues": issues,
            "total_checked": 0,
            "total_issues": len(issues)
        }

    def _attr_exists_and_unlocked(attribute_name):
        if not cmds.objExists(attribute_name):
            return False
        try:
            return not cmds.getAttr(attribute_name, lock=True)
        except Exception:
            return True

    # Step 4: Validate each control
    any_issues = False
    for ctrl in controls:
        if not cmds.objExists(ctrl):
            issues.append({
                'object': ctrl,
                'message': f"{ctrl} (missing in scene)",
                'fixed': False
            })
            any_issues = True
            continue

        bad_attrs = []

        # Translate
        for axis in ["X", "Y", "Z"]:
            attr = f"{ctrl}.translate{axis}"
            if _attr_exists_and_unlocked(attr):
                try:
                    if cmds.getAttr(attr) != 0:
                        bad_attrs.append(attr)
                except Exception:
                    pass

        # Rotate
        for axis in ["X", "Y", "Z"]:
            attr = f"{ctrl}.rotate{axis}"
            if _attr_exists_and_unlocked(attr):
                try:
                    if cmds.getAttr(attr) != 0:
                        bad_attrs.append(attr)
                except Exception:
                    pass

        # Scale
        for axis in ["X", "Y", "Z"]:
            attr = f"{ctrl}.scale{axis}"
            if _attr_exists_and_unlocked(attr):
                try:
                    if cmds.getAttr(attr) != 1:
                        bad_attrs.append(attr)
                except Exception:
                    pass

        if bad_attrs:
            any_issues = True
            if mode == "check":
                issues.append({
                    'object': ctrl,
                    'message': f"Offending attrs: {', '.join(bad_attrs)}",
                    'fixed': False
                })
            elif mode == "fix":
                fixed_all = True
                for attr in bad_attrs:
                    try:
                        if attr.endswith(('X', 'Y', 'Z')) and '.scale' in attr:
                            cmds.setAttr(attr, 1)
                        elif attr.endswith(('X', 'Y', 'Z')) and ('.translate' in attr or '.rotate' in attr):
                            cmds.setAttr(attr, 0)
                    except Exception:
                        fixed_all = False
                issues.append({
                    'object': ctrl,
                    'message': f"Reset: {', '.join(bad_attrs)}",
                    'fixed': fixed_all
                })

    # Step 5: Report results
    if not any_issues:
        issues.append({
            'object': "Scene",
            'message': "All controls are clean.",
            'fixed': True
        })

    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(controls),
        "total_issues": len(issues)
    }
