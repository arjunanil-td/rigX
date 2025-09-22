from __future__ import annotations

try:
    import maya.cmds as cmds  # type: ignore
    import maya.mel as mel  # type: ignore
    MAYA_AVAILABLE = True
except Exception:
    MAYA_AVAILABLE = False

from typing import Any, Dict, List, Optional, Tuple

from rigging_pipeline.utils.rigx_splineRig import SplineRig  # type: ignore
from rigging_pipeline.utils.rigx_dynamicParent import setup_dynamic_parent  # type: ignore


class TailModuleBuilder:
    """Builds an advanced Tail module using Spline IK with optional nHair dynamics.

    Workflow (expects a NURBS curve path selected or provided):
    - Create chain joints along the curve
    - Create offset/object curve and set Skin Joints
    - Build advanced spline rig (IK/FK, twist, stretch)
    - Optional: Add nHair dynamics on a duplicate curve and blend into IK curve
    - Optional: Add dynamic parent options for the base control
    """

    def __init__(self) -> None:
        if not MAYA_AVAILABLE:  # pragma: no cover - runtime-specific
            raise RuntimeError("Maya is not available. TailModuleBuilder must run inside Maya.")
        self._spline = SplineRig()

    # ------------------------------ Public API ------------------------------ #
    def build_tail_from_selection(
        self,
        rig_name: str = "Tail",
        spans: int = 5,
        use_dynamics: bool = True,
        dynamic_parent_targets: Optional[List[str]] = None,
        num_controls: Optional[int] = None,
    ) -> Dict[str, Any]:
        sel = cmds.ls(sl=True) or []
        if not sel:
            raise RuntimeError("Select a NURBS curve to build the Tail module.")
        curve = sel[0]
        return self.build_tail_from_curve(curve, rig_name, spans, use_dynamics, dynamic_parent_targets, num_controls)

    def build_tail_from_curve(
        self,
        curve: str,
        rig_name: str = "Tail",
        spans: int = 5,
        use_dynamics: bool = True,
        dynamic_parent_targets: Optional[List[str]] = None,
        num_controls: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not cmds.objExists(curve):
            raise RuntimeError(f"Curve '{curve}' does not exist.")
        if cmds.nodeType(curve) != "transform":
            raise RuntimeError("Please provide the transform of the NURBS curve.")
        if not any(s for s in (cmds.listRelatives(curve, s=True) or []) if cmds.nodeType(s) == "nurbsCurve"):
            raise RuntimeError("Provided node is not a NURBS curve transform.")

        # Optionally rebuild the curve to achieve the requested number of controls
        if num_controls is not None and num_controls > 0:
            try:
                shape = next((s for s in cmds.listRelatives(curve, s=True) or [] if cmds.nodeType(s) == "nurbsCurve"), None)
                if shape:
                    degree = cmds.getAttr(f"{shape}.degree")
                else:
                    degree = 3
            except Exception:
                degree = 3
            # setRig uses cvs = spans + degree; number of control drivers is roughly cvs - 2
            # So cvs_target = num_controls + 2  => spans_target = cvs_target - degree
            spans_target = max(1, int(num_controls + 2 - degree))
            try:
                cmds.rebuildCurve(curve, ch=False, rpo=True, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=spans_target, d=degree)
            except Exception:
                pass

        # 1) Create joints along curve
        ik_curve = self._spline.createJoints(curve, spans, rig_name)

        # 2) Offset/object curve and SJ (robust path without temp locator)
        try:
            bb = cmds.exactWorldBoundingBox(curve)
            max_dim = max(abs(bb[3]-bb[0]), abs(bb[4]-bb[1]), abs(bb[5]-bb[2]))
            dist = max(0.01, max_dim * 0.05)
        except Exception:
            dist = 0.5
        self._spline.setOffsetCrv(ik_curve, dist=dist, tol=0.1)
        self._spline.setSJ(ik_curve, par=None)

        # 3) Build advanced rig (returns handles we will reuse)
        sys_grp, ctl_grp, ik_joints, sj_joints, main_ctl, extra_ctls, fk_ctls, ik_anchors = self._spline.setRig(ik_curve)

        dynamics_info: Dict[str, Any] = {}
        if use_dynamics:
            dynamics_info = self._setup_dynamics(ik_curve, main_ctl, rig_name)

        # 4) Optional dynamic parent choices for the base control
        if dynamic_parent_targets:
            try:
                setup_dynamic_parent(main_ctl, dynamic_parent_targets)
            except Exception as exc:  # pragma: no cover
                cmds.warning(f"Dynamic parent setup failed: {exc}")

        return {
            "system_group": sys_grp,
            "controls_group": ctl_grp,
            "ik_joints": ik_joints,
            "sj_joints": sj_joints,
            "main_control": main_ctl,
            "extra_controls": extra_ctls,
            "fk_controls": fk_ctls,
            "ik_curve": ik_curve,
            "ik_anchors": ik_anchors,
            "dynamics": dynamics_info,
        }

    # ---------------------- Build from selected joints ---------------------- #
    def build_tail_from_joints(
        self,
        joints: Optional[List[str]] = None,
        rig_name: str = "Tail",
        use_dynamics: bool = True,
        dynamic_parent_targets: Optional[List[str]] = None,
        num_controls: Optional[int] = None,
    ) -> Dict[str, Any]:
        # New independent rope/tail setup (no legacy SplineRig dependency)
        if joints is None:
            joints = cmds.ls(sl=True, type="joint") or []
        if not joints:
            raise RuntimeError("Select or pass a chain of joints to build the Tail/Rope module.")

        bind_chain = self._order_joint_chain(joints)
        if len(bind_chain) < 2:
            raise RuntimeError("Provide at least 2 joints in a single chain.")

        # Duplicate IK and FK chains
        ik_chain = self._duplicate_chain(bind_chain, prefix=f"IK_{rig_name}")
        fk_chain = self._duplicate_chain(bind_chain, prefix=f"FK_{rig_name}")
        for j in ik_chain + fk_chain:
            try:
                cmds.setAttr(f"{j}.segmentScaleCompensate", 1)
            except Exception:
                pass

        # Create curve and IK Spline
        ik_curve = self._create_curve_from_joints(ik_chain, rig_name, num_controls)
        crv_shape = cmds.listRelatives(ik_curve, s=True, ni=True, type='nurbsCurve', fullPath=True)[0]
        ik_handle = cmds.ikHandle(sj=ik_chain[0], ee=ik_chain[-1], sol='ikSplineSolver', c=ik_curve, ccv=False, pcv=False, n=f"ik_{rig_name}")[0]

        # Advanced Twist: start/end up objects
        up_start = cmds.spaceLocator(n=f"loc_upStart_{rig_name}")[0]
        up_end = cmds.spaceLocator(n=f"loc_upEnd_{rig_name}")[0]
        cmds.matchTransform(up_start, ik_chain[0], pos=True, rot=True)
        cmds.matchTransform(up_end, ik_chain[-1], pos=True, rot=True)
        cmds.setAttr(f"{ik_handle}.dTwistControlEnable", 1)
        cmds.setAttr(f"{ik_handle}.dWorldUpType", 4)  # Object Up (Start/End)
        cmds.connectAttr(f"{up_start}.worldMatrix[0]", f"{ik_handle}.dWorldUpMatrix")
        cmds.connectAttr(f"{up_end}.worldMatrix[0]", f"{ik_handle}.dWorldUpMatrixEnd")

        # Controls on curve via clusters (internal CVs)
        deg = cmds.getAttr(f"{crv_shape}.degree")
        spans = cmds.getAttr(f"{crv_shape}.spans")
        total_cvs = deg + spans
        # Rebuild to accommodate num_controls if requested
        if num_controls and num_controls > 0:
            cvs_target = num_controls + 2
            spans_target = max(1, int(cvs_target - deg))
            try:
                cmds.rebuildCurve(ik_curve, ch=False, rpo=True, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=spans_target, d=deg)
                # refresh shape reference after rebuild (shape node can be replaced)
                crv_shape = cmds.listRelatives(ik_curve, s=True, ni=True, type='nurbsCurve', fullPath=True)[0]
                spans = cmds.getAttr(f"{crv_shape}.spans")
                total_cvs = deg + spans
            except Exception:
                pass

        interior_indices = list(range(1, max(2, total_cvs - 1)))
        # Spread controls evenly across internal CVs if count specified
        if num_controls and num_controls > 0 and len(interior_indices) > num_controls:
            step = float(len(interior_indices)) / float(num_controls)
            picks = [interior_indices[int(round(i * step))] for i in range(num_controls)]
            interior_indices = sorted(list(set([min(max(1, p), total_cvs - 2) for p in picks])))

        ctrl_grp = cmds.group(em=True, n=f"GRP_CTRL_{rig_name}")
        extras_grp = cmds.group(em=True, n=f"GRP_EXTRA_{rig_name}")
        jnt_grp = cmds.group(em=True, n=f"GRP_JNT_{rig_name}")
        root_grp = cmds.group(ctrl_grp, extras_grp, jnt_grp, n=f"GRP_{rig_name}")

        # Main control
        main_ctl = cmds.circle(n=f"Ctrl_main{rig_name}", nr=(0,1,0), r=1.5)[0]
        main_nul = cmds.group(main_ctl, n=f"nul_{main_ctl}")
        cmds.matchTransform(main_nul, ik_chain[0])
        cmds.parent(main_nul, ctrl_grp)
        for attr, args in (('IKFK', (0,1,1)), ('stretch',(0,1,1)), ('dynamics',(0,1,1)), ('dynamicsDrag',(0,None,0.1)), ('dynamicsStiffness',(0,None,0.2)), ('dynamicsMomentum',(0,None,0.1))):
            if not cmds.attributeQuery(attr, node=main_ctl, exists=True):
                if attr in ('IKFK','stretch','dynamics'):
                    cmds.addAttr(main_ctl, ln=attr, at='double', min=args[0], max=args[1], dv=args[2], k=True)
                else:
                    cmds.addAttr(main_ctl, ln=attr, at='double', min=args[0], dv=args[2], k=True)

        # Clusters + controls
        cluster_ctls: List[str] = []
        for idx in interior_indices:
            clu, hdl = cmds.cluster(f"{crv_shape}.cv[{idx}]", n=f"clu_{rig_name}_{idx}")
            ctl = cmds.circle(n=f"Ctrl_{rig_name}_{idx}", nr=(0,1,0), r=1.0)[0]
            nul = cmds.group(ctl, n=f"nul_{ctl}")
            # Position control at current CV position
            pos = cmds.pointPosition(f"{crv_shape}.cv[{idx}]", w=True)
            cmds.xform(nul, ws=True, t=pos)
            # Parent cluster handle under control so moving the control deforms the curve
            cmds.parent(hdl, ctl)
            cmds.parent(nul, ctrl_grp)
            cluster_ctls.append(ctl)

        # Curve length based stretch
        curve_info = cmds.createNode('curveInfo', n=f"ci_{rig_name}")
        cmds.connectAttr(f"{crv_shape}.worldSpace[0]", f"{curve_info}.inputCurve", f=True)
        base_len = cmds.getAttr(f"{curve_info}.arcLength")
        # Clamp stretch to base length of the IK curve (do not exceed base length * stretch factor)
        md = cmds.createNode('multiplyDivide', n=f"md_stretch_{rig_name}")
        cmds.setAttr(f"{md}.operation", 2)  # ratio = current/base
        cmds.setAttr(f"{md}.input2X", max(0.001, base_len))
        cmds.connectAttr(f"{curve_info}.arcLength", f"{md}.input1X", f=True)
        for j in ik_chain[:-1]:  # skip tip scale
            try:
                cmds.connectAttr(f"{md}.outputX", f"{j}.scaleX", f=True)
            except Exception:
                pass
        # clamp ratio to [1, maxStretch]; do not exceed base curve length * stretch attr
        cond = cmds.createNode('condition', n=f"cond_stretchClamp_{rig_name}")
        # First gate: prevent compression (min 1)
        cmds.setAttr(f"{cond}.operation", 2)  # Less Than
        cmds.setAttr(f"{cond}.secondTerm", 1)
        cmds.setAttr(f"{cond}.colorIfTrueR", 1)
        cmds.connectAttr(f"{md}.outputX", f"{cond}.firstTerm", f=True)
        cmds.connectAttr(f"{md}.outputX", f"{cond}.colorIfFalseR", f=True)

        # Second gate: cap by user stretch amount (stretch acts as max multiplier over base)
        md_cap = cmds.createNode('multiplyDivide', n=f"md_stretchCap_{rig_name}")
        # maxRatio = 1 + stretch * 2 (allow up to 3x at stretch=1 by default); tune if needed
        # Here keep conservative: maxRatio = 1 + stretch * 1.0
        cmds.setAttr(f"{md_cap}.operation", 1)
        cmds.setAttr(f"{md_cap}.input1X", 1)
        cmds.connectAttr(f"{main_ctl}.stretch", f"{md_cap}.input2X", f=True)
        cap_cond = cmds.createNode('condition', n=f"cond_stretchMax_{rig_name}")
        cmds.setAttr(f"{cap_cond}.operation", 4)  # Greater Than
        cmds.connectAttr(f"{cond}.outColorR", f"{cap_cond}.firstTerm", f=True)
        cmds.connectAttr(f"{md_cap}.outputX", f"{cap_cond}.secondTerm", f=True)
        cmds.connectAttr(f"{md_cap}.outputX", f"{cap_cond}.colorIfTrueR", f=True)
        cmds.connectAttr(f"{cond}.outColorR", f"{cap_cond}.colorIfFalseR", f=True)

        # stretch toggle (blended) and gate by IKFK so FK mode isn't affected
        bc = cmds.createNode('blendColors', n=f"bc_stretch_{rig_name}")
        cmds.setAttr(f"{bc}.color2R", 1)
        cmds.connectAttr(f"{cap_cond}.outColorR", f"{bc}.color1R", f=True)
        cmds.connectAttr(f"{main_ctl}.stretch", f"{bc}.blender", f=True)
        mdl_gate = cmds.createNode('multDoubleLinear', n=f"mdl_stretchGate_{rig_name}")
        cmds.connectAttr(f"{bc}.outputR", f"{mdl_gate}.input1", f=True)
        cmds.connectAttr(f"{main_ctl}.IKFK", f"{mdl_gate}.input2", f=True)
        for j in ik_chain[:-1]:
            # Use scaleX for stretch to avoid forward sliding; tx remains at rest length
            try:
                # Clean previous scaleX drivers
                sx_src = cmds.listConnections(f"{j}.scaleX", s=True, d=False, plugs=True) or []
                for s in sx_src:
                    try:
                        cmds.disconnectAttr(s, f"{j}.scaleX")
                    except Exception:
                        pass
                cmds.setAttr(f"{j}.scaleX", 1)
                cmds.connectAttr(f"{mdl_gate}.output", f"{j}.scaleX", f=True)
            except Exception:
                pass

        # IKFK: bind joints constrained between IK and FK chains
        rev = cmds.createNode('reverse', n=f"rev_IKFK_{rig_name}")
        cmds.connectAttr(f"{main_ctl}.IKFK", f"{rev}.inputX", f=True)
        for b, i, f in zip(bind_chain, ik_chain, fk_chain):
            # Constrain bind between IK and FK (order matters only for aliases)
            pc = cmds.parentConstraint(i, f, b, mo=False)[0]
            # Use weight alias list for reliable connections
            wal = cmds.parentConstraint(pc, q=True, wal=True) or []
            tl = cmds.parentConstraint(pc, q=True, tl=True) or []
            for alias, target in zip(wal, tl):
                wAttr = f"{pc}.{alias}"
                if target == i:
                    cmds.connectAttr(f"{main_ctl}.IKFK", wAttr, f=True)
                elif target == f:
                    cmds.connectAttr(f"{rev}.outputX", wAttr, f=True)

        # ------------------------- FK controls ------------------------- #
        fk_ctls: List[str] = []
        parent_ctrl = None
        for idx, j in enumerate(fk_chain):
            fk_ctl = cmds.circle(n=f"Ctrl_FK_{rig_name}_{idx+1}", nr=(1,0,0), r=1.0)[0]
            fk_nul = cmds.group(fk_ctl, n=f"nul_{fk_ctl}")
            cmds.matchTransform(fk_nul, j, pos=True, rot=True)
            if parent_ctrl:
                cmds.parent(fk_nul, parent_ctrl)
            else:
                cmds.parent(fk_nul, ctrl_grp)
            cmds.orientConstraint(fk_ctl, j, mo=False)
            fk_ctls.append(fk_ctl)
            parent_ctrl = fk_ctl

        # Visibility switching for IK (cluster controls) and FK controls
        for ctl in cluster_ctls:
            try:
                cmds.connectAttr(f"{main_ctl}.IKFK", f"{ctl}.v", f=True)
            except Exception:
                pass
        for ctl in fk_ctls:
            try:
                cmds.connectAttr(f"{rev}.outputX", f"{ctl}.v", f=True)
            except Exception:
                pass

        # Parenting groups
        try:
            cmds.parent(ik_chain[0], fk_chain[0], jnt_grp)
        except Exception:
            pass
        try:
            cmds.parent(ik_handle, ik_curve, up_start, up_end, extras_grp)
        except Exception:
            pass

        dynamics_info: Dict[str, Any] = {}
        if use_dynamics:
            dynamics_info = self._setup_dynamics(ik_curve, main_ctl, rig_name)

        if dynamic_parent_targets:
            try:
                setup_dynamic_parent(main_ctl, dynamic_parent_targets)
            except Exception as exc:
                cmds.warning(f"Dynamic parent setup failed: {exc}")

        # Color controls
        def _color(ctrls: List[str], idx: int):
            for c in ctrls:
                try:
                    for s in cmds.listRelatives(c, s=True, ni=True) or []:
                        cmds.setAttr(f"{s}.overrideEnabled", 1)
                        cmds.setAttr(f"{s}.overrideColor", idx)
                except Exception:
                    pass
        _color([main_ctl], 17)
        _color(cluster_ctls, 18)

        return {
            "root_group": root_grp,
            "ctrl_group": ctrl_grp,
            "jnt_group": jnt_grp,
            "extra_group": extras_grp,
            "main_control": main_ctl,
            "cluster_controls": cluster_ctls,
            "ik_curve": ik_curve,
            "ik_handle": ik_handle,
            "ik_chain": ik_chain,
            "fk_chain": fk_chain,
            "bind_chain": bind_chain,
            "dynamics": dynamics_info,
        }

    # --------------------------- Helper functions -------------------------- #
    def _order_joint_chain(self, joints: List[str]) -> List[str]:
        """Order a list of joints from root to tip within the same chain."""
        joints = [j for j in joints if cmds.objExists(j) and cmds.nodeType(j) == 'joint']
        joint_set = set(joints)
        # find root (no parent in the given set)
        root = None
        for j in joints:
            p = cmds.listRelatives(j, parent=True, fullPath=False)
            if not p or p[0] not in joint_set:
                root = j
                break
        if not root:
            return joints
        ordered = [root]
        current = root
        while True:
            children_list = cmds.listRelatives(current, children=True, type='joint')
            children = [c for c in (children_list or []) if c in joint_set]
            if not children:
                break
            # pick the first child that is in the set and not already used
            next_child = None
            for c in children:
                if c not in ordered:
                    next_child = c
                    break
            if not next_child:
                break
            ordered.append(next_child)
            current = next_child
            if len(ordered) == len(joint_set):
                break
        return ordered

    def _create_curve_from_joints(self, joints: List[str], rig_name: str, num_controls: Optional[int]) -> str:
        if not joints:
            raise RuntimeError("No joints provided for curve creation")
        
        positions = []
        for j in joints:
            if not cmds.objExists(j):
                raise RuntimeError(f"Joint '{j}' does not exist")
            pos = cmds.xform(j, q=True, ws=True, t=True)
            if not pos or len(pos) < 3:
                raise RuntimeError(f"Failed to get position for joint '{j}'")
            positions.append(pos)
        
        # ensure positions as list of 3-tuples
        pts = [(positions[i][0], positions[i][1], positions[i][2]) for i in range(len(positions))]
        degree = 3 if len(pts) >= 4 else (2 if len(pts) >= 3 else 1)
        
        try:
            crv = cmds.curve(p=pts, d=degree, name=f"crv_ik{rig_name}")
            if not crv:
                raise RuntimeError("Failed to create curve")
        except Exception as e:
            raise RuntimeError(f"Failed to create curve: {e}")
        
        # Optionally rebuild to target number of controls
        if num_controls is not None and num_controls > 0:
            cvs_target = num_controls + 2
            spans_target = max(1, int(cvs_target - degree))
            try:
                cmds.rebuildCurve(crv, ch=False, rpo=True, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=spans_target, d=degree)
            except Exception:
                pass
        return crv

    def _create_sj_chain_from_joints(self, source_joints: List[str], rig_name: str) -> List[str]:
        sj_chain: List[str] = []
        dLen = len(str(len(source_joints)))
        parent = None
        for i, j in enumerate(source_joints, start=1):
            name = f"SJ_{rig_name}{str(i).zfill(dLen)}"
            cmds.select(clear=True)
            sj = cmds.joint(name=name)
            # Match transform
            try:
                cmds.matchTransform(sj, j, pos=True, rot=True)
            except Exception:
                pos = cmds.xform(j, q=True, ws=True, t=True)
                rot = cmds.xform(j, q=True, ws=True, ro=True)
                cmds.xform(sj, ws=True, t=pos)
                cmds.xform(sj, ws=True, ro=rot)
            if parent:
                cmds.parent(sj, parent)
            parent = sj
            sj_chain.append(sj)
        # Group for cleanliness
        grp = f"grp_jnt{rig_name}"
        if not cmds.objExists(grp):
            cmds.group(em=True, name=grp)
        cmds.parent(sj_chain[0], grp)
        return sj_chain

    def _duplicate_chain(self, source_chain: List[str], prefix: str) -> List[str]:
        """Duplicate a joint chain by matching transforms in order.

        - Names joints as f"{prefix}{i:0Nd}" where N is digits of chain length
        - Parents sequentially to preserve hierarchy
        - Returns list ordered root->tip
        """
        if not source_chain:
            return []
        dup_chain: List[str] = []
        dLen = len(str(len(source_chain)))
        parent = None
        for i, j in enumerate(source_chain, start=1):
            name = f"{prefix}{str(i).zfill(dLen)}"
            try:
                cmds.select(clear=True)
                nj = cmds.joint(name=name)
            except Exception:
                # Ensure unique name
                nj = cmds.joint(name=f"{name}_jnt")
            # Match transform
            try:
                cmds.matchTransform(nj, j, pos=True, rot=True)
            except Exception:
                pos = cmds.xform(j, q=True, ws=True, t=True)
                rot = cmds.xform(j, q=True, ws=True, ro=True)
                cmds.xform(nj, ws=True, t=pos)
                cmds.xform(nj, ws=True, ro=rot)
            # Parent under previous
            if parent:
                try:
                    cmds.parent(nj, parent)
                except Exception:
                    pass
            parent = nj
            dup_chain.append(nj)
        return dup_chain

    # --------------------------- Internal utilities ------------------------- #
    def _setup_dynamics(self, ik_curve: str, main_ctl: str, rig_name: str) -> Dict[str, Any]:
        """Create an nHair dynamic duplicate of the IK curve and blend to IK.

        - Duplicates IK curve to crv_dyn{Rig}
        - Runs makeCurvesDynamic
        - Finds dynamic output curve
        - BlendShapes dynamic output into IK curve
        - Adds attrs on main control to drive dynamic weight and key hair params
        """
        if not cmds.objExists(ik_curve):
            cmds.warning(f"IK curve '{ik_curve}' does not exist for dynamics setup.")
            return {}
        
        # Duplicate and ensure selection for MEL command expectations
        dyn_curve_result = cmds.duplicate(ik_curve, name=f"crv_dyn{rig_name}")
        if not dyn_curve_result:
            cmds.warning(f"Failed to duplicate IK curve '{ik_curve}' for dynamics.")
            return {}
        dyn_curve = dyn_curve_result[0]
        
        # Some Maya MEL procedures require an active selection. Preserve current selection.
        prev_sel = cmds.ls(sl=True) or []
        try:
            success = False
            # Try both selection targets and both MEL procedures in a robust manner
            for sel_target in ("shape", "transform"):
                try:
                    cmds.selectMode(object=True)
                    if sel_target == "shape":
                        shapes = cmds.listRelatives(dyn_curve, s=True, ni=True, type='nurbsCurve', fullPath=True) or []
                        if shapes:
                            cmds.select(shapes, r=True)
                        else:
                            continue
                    else:
                        cmds.select(dyn_curve, r=True)

                    # First try makeCurvesDynamicHairs
                    try:
                        mel.eval('makeCurvesDynamicHairs 1 0 1;')
                        success = True
                    except Exception:
                        # Then try makeCurvesDynamic with two param sets
                        try:
                            mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0" };')
                            success = True
                        except Exception:
                            try:
                                mel.eval('makeCurvesDynamic 2 { "0", "0", "1", "1", "0" };')
                                success = True
                            except Exception:
                                success = False
                finally:
                    if success:
                        break

            if not success:
                cmds.warning("Dynamics setup failed (makeCurvesDynamic/CurvesDynamicHairs). Skipping dynamics.")
                return {}
        finally:
            # Restore previous selection
            try:
                if prev_sel:
                    cmds.select(prev_sel, r=True)
                else:
                    cmds.select(clear=True)
            except Exception:
                pass

        dyn_output_curve = self._find_dynamic_output_curve_for_input(dyn_curve)
        if not dyn_output_curve:
            cmds.warning("Could not locate dynamic output curve; dynamics will be skipped.")
            return {}

        # Create blendshape dynamic -> IK curve
        bs_node = cmds.blendShape(dyn_output_curve, ik_curve, name=f"bs_dynToIk_{rig_name}")[0]

        # Add control attrs
        if not cmds.attributeQuery("dynamics", node=main_ctl, exists=True):
            cmds.addAttr(main_ctl, ln="dynamics", at="double", min=0, max=1, dv=1, k=True)
        if not cmds.attributeQuery("dynamicsDrag", node=main_ctl, exists=True):
            cmds.addAttr(main_ctl, ln="dynamicsDrag", at="double", min=0, dv=0.1, k=True)
        if not cmds.attributeQuery("dynamicsStiffness", node=main_ctl, exists=True):
            cmds.addAttr(main_ctl, ln="dynamicsStiffness", at="double", min=0, dv=0.2, k=True)
        if not cmds.attributeQuery("dynamicsMomentum", node=main_ctl, exists=True):
            cmds.addAttr(main_ctl, ln="dynamicsMomentum", at="double", min=0, dv=0.1, k=True)

        # Connect blendshape weight 0 to main_ctl.dynamics
        try:
            alias_pairs = cmds.aliasAttr(bs_node, q=True) or []
            weight_alias = None
            for i in range(0, len(alias_pairs), 2):
                alias_name = alias_pairs[i]
                real_attr = alias_pairs[i + 1] if i + 1 < len(alias_pairs) else ""
                if "weight[" in real_attr:
                    weight_alias = alias_name
                    break
            if weight_alias:
                cmds.connectAttr(f"{main_ctl}.dynamics", f"{bs_node}.{weight_alias}", f=True)
            else:
                cmds.connectAttr(f"{main_ctl}.dynamics", f"{bs_node}.weight[0]", f=True)
        except Exception:
            try:
                cmds.connectAttr(f"{main_ctl}.dynamics", f"{bs_node}.weight[0]", f=True)
            except Exception:
                pass

        # Hook hairSystem params if present
        hair = self._find_latest_hair_system()
        if hair:
            for src_attr, dst_attr in (("dynamicsDrag", "drag"), ("dynamicsStiffness", "stiffness")):
                try:
                    cmds.connectAttr(f"{main_ctl}.{src_attr}", f"{hair}.{dst_attr}", f=True)
                except Exception:
                    pass
            # Momentum -> damp (acts like momentum/damping in nHair)
            try:
                cmds.connectAttr(f"{main_ctl}.dynamicsMomentum", f"{hair}.damp", f=True)
            except Exception:
                pass

        # Housekeeping
        grp = cmds.group(dyn_curve, dyn_output_curve, name=f"grp_dyn_{rig_name}")
        if cmds.objExists("Systems"):
            cmds.parent(grp, "Systems")

        return {
            "dynamic_input_curve": dyn_curve,
            "dynamic_output_curve": dyn_output_curve,
            "blendshape": bs_node,
            "hairSystem": hair if hair else None,
            "group": grp,
        }

    def _find_dynamic_output_curve_for_input(self, input_curve: str) -> Optional[str]:
        """Best-effort: locate the dynamic output curve driven by the input_curve after makeCurvesDynamic.
        This walks follicles and output groups created by the command and finds the connected output curve.
        """
        # The typical structure: input curve -> follicleShape.inputCurve; follicleShape.outCurve -> dynCurveShape.create
        # Try to locate a follicle connected to our input curve history
        shapes = cmds.listRelatives(input_curve, s=True, fullPath=True) or []
        for shape in shapes:
            fols = cmds.listConnections(shape, type="follicle") or []
            if not fols:
                continue
            for fol in fols:
                outs = cmds.listConnections(f"{fol}.outCurve", d=True, s=False) or []
                for node in outs:
                    if cmds.nodeType(node) == "nurbsCurve":
                        dyn_shape = node
                    else:
                        # maybe connected to shape.create
                        if cmds.nodeType(node) == "shape":
                            dyn_shape = node
                        else:
                            # check downstream shapes
                            dyn_shape = None
                            if cmds.objExists(node):
                                cands = cmds.listConnections(node, d=True, s=False) or []
                                dyn_shape = next((c for c in cands if cmds.nodeType(c) == "nurbsCurve"), None)
                    if dyn_shape:
                        dyn_tr = cmds.listRelatives(dyn_shape, p=True, f=False) or []
                        if dyn_tr:
                            return dyn_tr[0]

        # Fallback: search for last created output curve group
        out_groups = [g for g in (cmds.ls("*OutputCurves*", type="transform") or [])]
        if out_groups:
            curves = cmds.listRelatives(out_groups[-1], type="transform", f=False) or []
            if curves:
                return curves[-1]
        return None

    def _find_latest_hair_system(self) -> Optional[str]:
        hairs = cmds.ls(type="hairSystem") or []
        return hairs[-1] if hairs else None



