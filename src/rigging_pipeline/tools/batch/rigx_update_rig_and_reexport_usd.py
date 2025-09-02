# Maya 2024 / Python 3.10
# Run with: mayabatch.exe -command "python(\"import rigx_update_rig_and_reexport_usd as U; U.run(char='Tiger', old='v012', new='v013', anim_files=[r'P:/show/seq/shot01/anim_v005.ma'], dry_run=False)\")"

import os, re, json, traceback
from collections import namedtuple
import maya.standalone  # only if launching from plain python
import maya.cmds as cmds

Result = namedtuple("Result", "scene updated refs usd_nodes notes ok")

def _find_maya_references():
    refs = []
    for ref_node in cmds.ls(type='reference') or []:
        if ref_node == 'sharedReferenceNode':  # skip
            continue
        try:
            fpath = cmds.referenceQuery(ref_node, f=True)
            if fpath:
                refs.append((ref_node, os.path.normpath(fpath)))
        except:
            pass
    return refs

def _replace_maya_reference(ref_node, new_path):
    cmds.file(new_path, loadReference=ref_node)

def _find_usd_proxies():
    # mayaUsdProxyShape or mayaUsdProxyShapeBase depending on plugin version
    shapes = cmds.ls(type='mayaUsdProxyShape') or []
    if not shapes:
        shapes = cmds.ls(type='mayaUsdProxyShapeBase') or []
    nodes = []
    for s in shapes:
        try:
            fpath = cmds.getAttr(s + ".filePath")
            nodes.append((s, os.path.normpath(fpath) if fpath else ""))
        except:
            pass
    return nodes

def _replace_usd_proxy_path(shape, new_path):
    cmds.setAttr(shape + ".filePath", new_path, type="string")
    # Force reload
    try:
        cmds.setAttr(shape + ".reload", 1)
    except:
        pass

def _collect_time_range():
    start = cmds.playbackOptions(q=True, min=True)
    end   = cmds.playbackOptions(q=True, max=True)
    return float(start), float(end)

def _export_usd(out_path, root_selection=None):
    # Prefer mayaUSDExport; fall back to file -es
    start, end = _collect_time_range()
    try:
        kwargs = dict(
            file=out_path,
            selection=False if not root_selection else True,
            frameRange=(start, end),
            animation=True,
            # tune to your pipeline below:
            mergeTransformAndShape=True,
            stripNamespaces=True,
            materialsScopeName="materials",
            # skeleton export options — adapt as needed
            skel="auto",              # MayaUSD uses "skel" or "skeletons" depending on version
            exportSkels="auto",       # safety for older builds
            exportSkin="auto",
            exportBlendShapes=True,
            worldspace=False,
        )
        if root_selection:
            cmds.select(root_selection, r=True)
        cmds.mayaUSDExport(**kwargs)
    except Exception:
        # Fallback to legacy exporter (adjust your options string!)
        opt = "animation=1;mergeTransformAndShape=1;stripNamespaces=1;exportBlendShapes=1"
        if root_selection:
            cmds.select(root_selection, r=True)
        cmds.file(out_path, force=True, options=opt, typ="USD Export", pr=True, es=True)

def _path_version_swap(path, old_token, new_token):
    # e.g. .../char/Tiger/rig/v012/rig.usda -> v013
    return re.sub(rf"(?:^|/|\\){re.escape(old_token)}(?=/|\\|$)", new_token, path)

def _looks_like_char(path, char):
    low = path.replace("\\", "/").lower()
    return f"/{char.lower()}/" in low or f"_{char.lower()}_" in low

def update_scene(scene_path, char, old_version_token, new_version_token, usd_out_func, dry_run=False):
    notes = []
    updated = False
    usd_nodes = []

    cmds.file(new=True, f=True)
    cmds.file(scene_path, o=True, f=True, iv=True)

    # 1) Maya references
    for ref_node, ref_path in _find_maya_references():
        if _looks_like_char(ref_path, char) and old_version_token in ref_path:
            new_path = _path_version_swap(ref_path, old_version_token, new_version_token)
            notes.append(f"REF {ref_node}: {ref_path} -> {new_path}")
            if not dry_run:
                _replace_maya_reference(ref_node, new_path)
            updated = True

    # 2) USD proxies
    for shape, fpath in _find_usd_proxies():
        if _looks_like_char(fpath, char) and old_version_token in fpath:
            new_path = _path_version_swap(fpath, old_version_token, new_version_token)
            notes.append(f"USD {shape}: {fpath} -> {new_path}")
            if not dry_run:
                _replace_usd_proxy_path(shape, new_path)
            updated = True
            usd_nodes.append(shape)

    # 3) Optional: quick compatibility checks (joint names / topo hash)
    # TODO: hook your validator here. For now just log.
    # notes.append("VALIDATION: skipped (hook your joint/topology checks here)")

    # 4) Re-export USD if something changed
    if updated and not dry_run:
        try:
            out_path = usd_out_func(scene_path, char)
            _export_usd(out_path)
            notes.append(f"EXPORTED: {out_path}")
        except Exception as ex:
            notes.append("EXPORT FAILED: " + repr(ex) + "\n" + traceback.format_exc())
            return Result(scene_path, updated, [], usd_nodes, notes, False)

    return Result(scene_path, updated, _find_maya_references(), usd_nodes, notes, True)

# ------- PUBLIC ENTRY --------
def run(char, old, new, anim_files, dry_run=False):
    """
    char: 'Tiger'
    old: 'v012'
    new: 'v013'
    anim_files: list of .ma/.mb or scene templates to process
    dry_run: True prints planned edits, no writes
    """
    # Customize this to your rigX show layout
    def usd_out_func(scene_path, character):
        # e.g. P:/show/seq/shotXX/publish/usd/anim/<char>/<sceneName>_rigUpdate_<new>.usda
        base = os.path.splitext(os.path.basename(scene_path))[0]
        shot_dir = os.path.dirname(scene_path)
        out_dir = os.path.normpath(os.path.join(shot_dir, "publish", "usd", "anim", character))
        os.makedirs(out_dir, exist_ok=True)
        return os.path.join(out_dir, f"{base}_{character}_{new}.usda")

    results = []
    for scn in anim_files:
        try:
            res = update_scene(scn, char, old, new, usd_out_func, dry_run=dry_run)
        except Exception as ex:
            res = Result(scn, False, [], [], ["CRASH: " + repr(ex) + "\n" + traceback.format_exc()], False)
        results.append(res)

    # Simple report
    report = []
    for r in results:
        status = "OK" if r.ok else "FAIL"
        report.append({
            "scene": r.scene,
            "status": status,
            "updated": r.updated,
            "notes": r.notes,
        })
    print(json.dumps(report, indent=2))
    return results
