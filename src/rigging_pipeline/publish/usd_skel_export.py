"""
usd_skel_export.py  —  MayaUSD UsdSkel publisher (REST + ANIM)
Maya 2024+, Python 3.10

Usage (inside Maya Python):
    from rigging_pipeline.publish import usd_skel_export as skelx

    # 1) Select your character's top group (or any DAG roots under which the bound meshes live)
    # 2) REST publish (once per rig version)
    skelx.export_rest(
        out_path=r"X:/show/ASSET/charTiger/publish/rig/tiger_skel_rest.usdc",
        default_mesh_scheme="catmullClark"
    )

    # 3) ANIM publish (per shot/range)
    skelx.export_anim(
        out_path=r"X:/show/SHOT/010/anim/tiger_skel_anim_1001_1100.usdc",
        start=1001, end=1100,
        samples_per_frame=1,         # 1–3 is typical; don't write substeps
        include_blendshapes=True
    )

Notes:
- This wrapper exports **selection only**. Select your character root(s) first.
- It auto-collects: (a) skinned meshes under selection, (b) their influence joints.
- It passes the correct MayaUSD options for UsdSkel (skeletons/skins/blendshapes).
- Use export_rest_with_cleanup() to automatically fix blendshape targets with zero-length component indices.
- Optional: use build_value_clip_manifest_usda(...) to author a Value-Clip manifest file.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Set

from maya import cmds

# ----------------------------- Utils -----------------------------------------

def _ensure_mayausd_loaded() -> None:
    """Load the MayaUSD plugin if needed."""
    if not cmds.pluginInfo("mayaUsdPlugin", q=True, loaded=True):
        cmds.loadPlugin("mayaUsdPlugin")

def _is_mesh_skinned(mesh_shape: str) -> bool:
    """Return True if the mesh has a skinCluster in its history."""
    hist = cmds.listHistory(mesh_shape, pruneDagObjects=True) or []
    return any(cmds.nodeType(n) == "skinCluster" for n in hist)

def _mesh_skincluster(mesh_shape: str) -> str | None:
    """Return the first skinCluster deforming this mesh (if any)."""
    hist = cmds.listHistory(mesh_shape, pruneDagObjects=True) or []
    for n in hist:
        if cmds.nodeType(n) == "skinCluster":
            return n
    return None

def _get_meshes_under(roots: Iterable[str]) -> List[str]:
    """All mesh shapes under the given roots (non-intermediate)."""
    meshes: List[str] = []
    for root in roots:
        shapes = cmds.listRelatives(root, allDescendents=True, path=True, type="mesh") or []
        for s in shapes:
            if not cmds.getAttr(s + ".intermediateObject"):
                meshes.append(s)
    return sorted(set(meshes))

def _gather_skinned_selection_from(roots: Iterable[str]) -> Tuple[List[str], List[str]]:
    """
    From the given DAG roots, collect:
      - bound mesh transforms
      - influence joints needed for those meshes
    Returns (mesh_transforms, influence_joints)
    """
    mesh_shapes = _get_meshes_under(roots)
    skinned_mesh_transforms: Set[str] = set()
    influences: Set[str] = set()

    for s in mesh_shapes:
        if not _is_mesh_skinned(s):
            continue
        xform = cmds.listRelatives(s, parent=True, path=True) or []
        if xform:
            skinned_mesh_transforms.add(xform[0])
        sc = _mesh_skincluster(s)
        if sc:
            infs = cmds.skinCluster(sc, q=True, inf=True) or []
            influences.update(infs)

    if not skinned_mesh_transforms:
        raise RuntimeError("No skinned meshes found under the current selection. "
                          "Select your character root and try again.")

    # Filter influences to only valid joints
    influences = {j for j in influences if cmds.objExists(j) and cmds.nodeType(j) == "joint"}
    return sorted(skinned_mesh_transforms), sorted(influences)

def _warn_on_history_order(mesh_shapes: Iterable[str]) -> None:
    """
    Warn if any mesh has blendShape AFTER skinCluster in the history.
    UsdSkel applies blendshapes BEFORE skinning; mismatched order can cause diffs.
    """
    offenders = []
    for s in mesh_shapes:
        hist = cmds.listHistory(s, pruneDagObjects=True) or []
        # capture order index
        idx = {n: i for i, n in enumerate(hist)}
        bss = [n for n in hist if cmds.nodeType(n) == "blendShape"]
        scs = [n for n in hist if cmds.nodeType(n) == "skinCluster"]
        if bss and scs:
            if idx[bss[0]] > idx[scs[0]]:
                offenders.append(s)
    if offenders:
        cmds.warning(
            "[UsdSkel] Some meshes have blendShape AFTER skinCluster (should be before):\n  "
            + "\n  ".join(offenders)
        )


def _cleanup_problematic_blendshape_targets(mesh_shapes: Iterable[str]) -> List[str]:
    """
    Clean up blendshape targets with zero-length component indices.
    Returns list of cleaned up targets.
    """
    cleaned_targets = []
    
    for mesh_shape in mesh_shapes:
        hist = cmds.listHistory(mesh_shape, pruneDagObjects=True) or []
        blend_shapes = [n for n in hist if cmds.nodeType(n) == "blendShape"]
        
        for bs in blend_shapes:
            try:
                # Get all target groups
                target_groups = cmds.listAttr(f"{bs}.weight", multi=True) or []
                
                for group in target_groups:
                    # Check each target item in the group
                    target_items = cmds.listAttr(f"{bs}.{group}", multi=True) or []
                    
                    for item in target_items:
                        if not item.endswith("Target"):
                            continue
                            
                        # Check if this target has zero-length component indices
                        try:
                            component_attr = f"{bs}.{group}.{item}"
                            component_indices = cmds.getAttr(component_attr)
                            
                            if component_indices is None or len(component_indices) == 0:
                                # Try to remove this problematic target
                                try:
                                    # Remove the target item
                                    cmds.removeMultiInstance(f"{bs}.{group}.{item}", b=True)
                                    cleaned_targets.append(f"{bs}.{group}.{item}")
                                except Exception as e:
                                    cmds.warning(f"Could not remove problematic target {component_attr}: {e}")
                                    
                        except Exception as e:
                            # If we can't read the attribute, try to remove it
                            try:
                                cmds.removeMultiInstance(f"{bs}.{group}.{item}", b=True)
                                cleaned_targets.append(f"{bs}.{group}.{item} (removed due to error)")
                            except Exception as remove_error:
                                cmds.warning(f"Could not remove problematic target {bs}.{group}.{item}: {remove_error}")
                            
            except Exception as e:
                cmds.warning(f"Error cleaning up blendshape {bs}: {e}")
    
    return cleaned_targets


def _validate_blendshape_targets(mesh_shapes: Iterable[str]) -> None:
    """
    Validate blendshape targets and warn about problematic ones.
    Specifically checks for zero-length component indices which cause USD export errors.
    """
    problematic_targets = []
    
    for mesh_shape in mesh_shapes:
        hist = cmds.listHistory(mesh_shape, pruneDagObjects=True) or []
        blend_shapes = [n for n in hist if cmds.nodeType(n) == "blendShape"]
        
        for bs in blend_shapes:
            try:
                # Get all target groups
                target_groups = cmds.listAttr(f"{bs}.weight", multi=True) or []
                
                for group in target_groups:
                    # Check each target item in the group
                    target_items = cmds.listAttr(f"{bs}.{group}", multi=True) or []
                    
                    for item in target_items:
                        if not item.endswith("Target"):
                            continue
                            
                        # Check if this target has zero-length component indices
                        try:
                            # Try to get the component indices
                            component_attr = f"{bs}.{group}.{item}"
                            component_indices = cmds.getAttr(component_attr)
                            
                            if component_indices is None or len(component_indices) == 0:
                                problematic_targets.append(f"{bs}.{group}.{item}")
                                
                        except Exception as e:
                            # If we can't read the attribute, it might be problematic
                            problematic_targets.append(f"{bs}.{group}.{item} (error: {str(e)})")
                            
            except Exception as e:
                cmds.warning(f"Error validating blendshape {bs}: {e}")
    
    if problematic_targets:
        cmds.warning(
            "[UsdSkel] Found blendshape targets with zero-length component indices:\n  "
            + "\n  ".join(problematic_targets[:10])  # Show first 10
            + f"\n  ... and {len(problematic_targets) - 10} more" if len(problematic_targets) > 10 else ""
            + "\n  These may cause USD export errors. Consider cleaning up the blendshape."
        )

def _build_options_string(
    *,
    animation: bool,
    start: float | None = None,
    end: float | None = None,
    samples_per_frame: int = 1,
    export_skels: str = "auto",            # "none" | "auto" | "all"
    export_skins: str = "auto",            # "none" | "auto" | "all"
    export_blendshapes: bool = True,
    default_mesh_scheme: str = "catmullClark",
    merge_transform_and_shape: bool = True,
    strip_namespaces: bool = True,
    euler_filter: bool = True,
    shading_mode: str = "useRegistry",     # keep materials intact via registry
    materials_scope_name: str = "materials",
    export_display_color: bool = True
) -> str:
    """
    Compose the 'USD Export' options string for cmds.file(..., type='USD Export', options=...).
    These keys match MayaUSD exporter flags.
    """
    kv = []
    # UsdSkel core
    kv.append(f"exportSkels={export_skels}")
    kv.append(f"exportSkins={export_skins}")
    kv.append(f"exportBlendShapes={(1 if export_blendshapes else 0)}")

    # Animation / sampling
    kv.append(f"animation={(1 if animation else 0)}")
    if animation:
        if start is None or end is None:
            raise ValueError("Animation export requires start and end times.")
        kv.append("frameRange=1")
        kv.append(f"startTime={float(start)}")
        kv.append(f"endTime={float(end)}")
        kv.append(f"samplesPerFrame={int(samples_per_frame)}")
        kv.append(f"eulerFilter={(1 if euler_filter else 0)}")
    else:
        kv.append("frameRange=0")

    # Mesh defaults & scene hygiene
    kv.append(f"defaultMeshScheme={default_mesh_scheme}")
    kv.append(f"mergeTransformAndShape={(1 if merge_transform_and_shape else 0)}")
    kv.append(f"stripNamespaces={(1 if strip_namespaces else 0)}")

    # Shading
    kv.append(f"shadingMode={shading_mode}")
    kv.append(f"materialsScopeName={materials_scope_name}")
    kv.append(f"exportDisplayColor={(1 if export_display_color else 0)}")

    # Always write binary crate (.usdc) via file extension; no ascii unless you ask for it.
    return ";".join(kv)

def _do_usd_export_selected(out_path: str, options_str: str) -> None:
    """Call the MayaUSD file exporter for the current selection."""
    _ensure_mayausd_loaded()
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # Ensure .usd/.usdc extension is correct for binary; recommend .usdc
    if not out_path.lower().endswith((".usd", ".usdc", ".usda")):
        out_path += ".usdc"

    # Export selection
    cmds.file(
        out_path,
        force=True,
        options=options_str,
        typ="USD Export",
        pr=True,             # preserve references on export
        es=True              # export selected
    )

# --------------------------- Public API --------------------------------------

@dataclass
class RestExportSettings:
    default_mesh_scheme: str = "catmullClark"
    merge_transform_and_shape: bool = True
    strip_namespaces: bool = True
    shading_mode: str = "useRegistry"
    materials_scope_name: str = "materials"
    export_display_color: bool = True
    export_blendshapes: bool = True
    export_skels: str = "auto"
    export_skins: str = "auto"

def export_rest(
    out_path: str,
    *,
    default_mesh_scheme: str = "catmullClark",
    merge_transform_and_shape: bool = True,
    strip_namespaces: bool = True,
    shading_mode: str = "useRegistry",
    materials_scope_name: str = "materials",
    export_display_color: bool = True,
    export_blendshapes: bool = True,
    export_skels: str = "auto",
    export_skins: str = "auto"
) -> None:
    """
    REST publish: writes meshes (topology once), skin weights/bind, skeleton, blendshape targets.
    No time samples.

    Precondition: Select your character DAG root(s) in Maya.
    """
    sel = cmds.ls(sl=True, long=True) or []
    if not sel:
        raise RuntimeError("Nothing selected. Select your character root(s) and try again.")

    # Build clean selection: skinned mesh transforms + influence joints
    mesh_xforms, influences = _gather_skinned_selection_from(sel)

    # Warn if blendshape order is after skinCluster (UsdSkel assumes BS before skin)
    _warn_on_history_order(_get_meshes_under(sel))
    
    # Validate and warn about problematic blendshape targets
    _validate_blendshape_targets(_get_meshes_under(sel))

    cmds.select(clear=True)
    cmds.select(mesh_xforms + influences, r=True)

    opts = _build_options_string(
        animation=False,
        export_skels=export_skels,
        export_skins=export_skins,
        export_blendshapes=export_blendshapes,
        default_mesh_scheme=default_mesh_scheme,
        merge_transform_and_shape=merge_transform_and_shape,
        strip_namespaces=strip_namespaces,
        shading_mode=shading_mode,
        materials_scope_name=materials_scope_name,
        export_display_color=export_display_color
    )
    _do_usd_export_selected(out_path, opts)
    cmds.select(sel, r=True)  # restore selection
    cmds.inViewMessage(amg=f"<hl>UsdSkel REST</hl> exported to: {out_path}", pos="botLeft", fade=True)

def export_anim(
    out_path: str,
    *,
    start: float,
    end: float,
    samples_per_frame: int = 1,
    include_blendshapes: bool = True,
    export_skels: str = "auto",
    export_skins: str = "auto",
    default_mesh_scheme: str = "catmullClark",
    merge_transform_and_shape: bool = True,
    strip_namespaces: bool = True,
    shading_mode: str = "useRegistry",
    materials_scope_name: str = "materials",
    export_display_color: bool = True,
    euler_filter: bool = True
) -> None:
    """
    ANIM publish: writes SkelAnimation curves (joints + optional blendshape channel weights).
    Tiny files vs baked geometry.

    Important:
    - Keep Skeletons export enabled so the exporter targets the right Skel.
    - Include at least one bound mesh in selection in some MayaUSD versions for BS channel export.
    """
    if start > end:
        raise ValueError("start must be <= end")

    sel = cmds.ls(sl=True, long=True) or []
    if not sel:
        raise RuntimeError("Nothing selected. Select your character root(s) and try again.")

    mesh_xforms, influences = _gather_skinned_selection_from(sel)
    _warn_on_history_order(_get_meshes_under(sel))
    
    # Validate and warn about problematic blendshape targets
    _validate_blendshape_targets(_get_meshes_under(sel))

    # Depending on MayaUSD version, blendshape channel export can require a bound mesh in selection
    # We include both joints and bound mesh transforms for safety.
    cmds.select(clear=True)
    cmds.select(mesh_xforms + influences, r=True)

    opts = _build_options_string(
        animation=True,
        start=start,
        end=end,
        samples_per_frame=samples_per_frame,
        export_skels=export_skels,
        export_skins=export_skins,
        export_blendshapes=include_blendshapes,
        default_mesh_scheme=default_mesh_scheme,
        merge_transform_and_shape=merge_transform_and_shape,
        strip_namespaces=strip_namespaces,
        shading_mode=shading_mode,
        materials_scope_name=materials_scope_name,
        export_display_color=export_display_color,
        euler_filter=euler_filter
    )
    _do_usd_export_selected(out_path, opts)
    cmds.select(sel, r=True)
    cmds.inViewMessage(amg=f"<hl>UsdSkel ANIM</hl> exported to: {out_path}", pos="botLeft", fade=True)


def export_rest_with_cleanup(
    out_path: str,
    *,
    cleanup_blendshapes: bool = True,
    default_mesh_scheme: str = "catmullClark",
    merge_transform_and_shape: bool = True,
    strip_namespaces: bool = True,
    shading_mode: str = "useRegistry",
    materials_scope_name: str = "materials",
    export_display_color: bool = True,
    export_blendshapes: bool = True,
    export_skels: str = "auto",
    export_skins: str = "auto"
) -> None:
    """
    REST publish with automatic cleanup of problematic blendshape targets.
    This version will automatically remove blendshape targets with zero-length component indices
    that cause USD export errors.
    
    Precondition: Select your character DAG root(s) in Maya.
    """
    sel = cmds.ls(sl=True, long=True) or []
    if not sel:
        raise RuntimeError("Nothing selected. Select your character root(s) and try again.")

    # Build clean selection: skinned mesh transforms + influence joints
    mesh_xforms, influences = _gather_skinned_selection_from(sel)

    # Warn if blendshape order is after skinCluster (UsdSkel assumes BS before skin)
    _warn_on_history_order(_get_meshes_under(sel))
    
    # Validate and warn about problematic blendshape targets
    _validate_blendshape_targets(_get_meshes_under(sel))
    
    # Clean up problematic blendshape targets if requested
    cleaned_targets = []
    if cleanup_blendshapes:
        cleaned_targets = _cleanup_problematic_blendshape_targets(_get_meshes_under(sel))
        if cleaned_targets:
            cmds.inViewMessage(
                amg=f"Cleaned up {len(cleaned_targets)} problematic blendshape targets", 
                pos="topCenter", 
                fade=True
            )

    cmds.select(clear=True)
    cmds.select(mesh_xforms + influences, r=True)

    opts = _build_options_string(
        animation=False,
        export_skels=export_skels,
        export_skins=export_skins,
        export_blendshapes=export_blendshapes,
        default_mesh_scheme=default_mesh_scheme,
        merge_transform_and_shape=merge_transform_and_shape,
        strip_namespaces=strip_namespaces,
        shading_mode=shading_mode,
        materials_scope_name=materials_scope_name,
        export_display_color=export_display_color
    )
    _do_usd_export_selected(out_path, opts)
    cmds.select(sel, r=True)  # restore selection
    
    cleanup_msg = f" (cleaned {len(cleaned_targets)} blendshape targets)" if cleaned_targets else ""
    cmds.inViewMessage(amg=f"<hl>UsdSkel REST{cleanup_msg}</hl> exported to: {out_path}", pos="botLeft", fade=True)


# # --------------------- Optional: Value Clip Manifest --------------------------

# def build_value_clip_manifest_usda(
#     manifest_path: str,
#     skel_root_path: str,
#     clip_asset_paths: List[str],
#     clip_ranges: List[Tuple[float, float]]
# ) -> None:
#     """
#     Write a minimal USDA manifest that attaches Value Clips to the given Skel root prim.
#     This is a simple text authoring utility (safe for automation). You can layer this
#     manifest over your REST file in your shot's composed stage.

#     Args:
#         manifest_path: where to write the .usda (recommend alongside your clips)
#         skel_root_path: e.g. "/charTiger" or "/charTiger/SkelRoot"
#         clip_asset_paths: list of file-relative paths to your ANIM clip files (.usdc)
#         clip_ranges: list of (startTime, endTime) pairs for each corresponding clip

#     Note:
#         - This uses identity mapping (stageTime == clipTime) at the clip boundaries.
#         - If you need advanced remapping, extend the writer to emit double2[] with
#           non-identity pairs per USD spec.
#     """
#     if len(clip_asset_paths) != len(clip_ranges):
#         raise ValueError("clip_asset_paths and clip_ranges must be same length")

#     # Build clipTimes entries as (startTime, startTime) and (endTime, endTime) per clip
#     # For identity mapping at boundaries, it is common to list both endpoints.
#     times_entries = []
#     for (s, e) in clip_ranges:
#         times_entries.append(f"({float(s)}, {float(s)})")
#         times_entries.append(f"({float(e)}, {float(e)})")

#     # Asset path array
#     asset_entries = []
#     for ap in clip_asset_paths:
#         # USDA requires @asset@ syntax; keep paths as given (relative or absolute)
#         asset_entries.append(f"@{ap}@")

#     txt = f"""#usda 1.0
# (
#     defaultPrim = "{os.path.basename(skel_root_path).strip('/') or 'SkelRoot'}"
# )

# over "{skel_root_path}" (
#     clips = {{
#         dictionary default = {{
#             string clipPrimPath = "{skel_root_path}"
#             asset[] clipAssetPaths = [
#                 {",\\n                ".join(asset_entries)}
#             ]
#             double2[] clipTimes = [
#                 {",\\n                ".join(times_entries)}
#             ]
#         }}
#     }}
# )
# """
#     out_dir = os.path.dirname(manifest_path)
#     if out_dir and not os.path.exists(out_dir):
#         os.makedirs(out_dir, exist_ok=True)
#     with open(manifest_path, "w", encoding="utf-8") as f:
#         f.write(txt)
