#!/usr/bin/env python3
"""
rigX Animation Rigging Tools

This module provides FK control creation tools for animation rigging workflows.
"""

import maya.cmds as cmds
import os
import sys

# Add the rigX path to sys.path if not already there
rigx_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if rigx_path not in sys.path:
    sys.path.append(rigx_path)


class RigXAnimRig:
    """Animation Rigging Tools for rigX pipeline - Logic only."""
    
    def __init__(self):
        self.window_name = "rigX_animRig_window"
        
    def show_ui(self):
        """Show the Animation Rigging Tools UI."""
        # Delete existing window if it exists
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        # Import and create UI
        from rigging_pipeline.tools.ui.rigx_animRig_ui import RigXAnimRigUI
        self.ui = RigXAnimRigUI(tool_instance=self)
        self.ui.show_ui()
        
    # -----------------------
    # Simple Transform Puppet
    # -----------------------
    def create_simple_puppet(self, model_group=None, custom_joints=None, use_matrix=True, ignore_end_joint=False, extra_global_controls=0):
        """Create a simple transform puppet structure with proper hierarchy, joints, controllers and sets."""
        try:
            # Group entire operation in a single undo step
            cmds.undoInfo(openChunk=True, chunkName="Create Simple Transform Puppet")
            # Get asset name from scene/top group
            asset_name = self._get_asset_name()
            
            # Resolve top group: use existing if present, otherwise create
            if cmds.objExists(asset_name):
                top_group = asset_name
            else:
                top_group = cmds.group(empty=True, name=asset_name)
            
            # Ensure rig group under top (do not create geo here)
            rig_group_path = f"{top_group}|rig"
            if cmds.objExists(rig_group_path):
                rig_group = rig_group_path
            else:
                rig_group = cmds.group(empty=True, name="rig", parent=top_group)
            
            # Create MotionSystem and DeformationSystem groups under rig
            motion_group_path = f"{rig_group}|MotionSystem"
            deformation_group_path = f"{rig_group}|DeformationSystem"
            if cmds.objExists(motion_group_path):
                motion_group = motion_group_path
            else:
                motion_group = cmds.group(empty=True, name="MotionSystem", parent=rig_group)
            if cmds.objExists(deformation_group_path):
                deformation_group = deformation_group_path
            else:
                deformation_group = cmds.group(empty=True, name="DeformationSystem", parent=rig_group)
            
            # Create MainSystem under MotionSystem (following test.ma structure)
            main_system_path = f"{motion_group}|MainSystem"
            if cmds.objExists(main_system_path):
                main_system = main_system_path
            else:
                main_system = cmds.group(empty=True, name="MainSystem", parent=motion_group)
            
            # Create Sets structure
            # Create joints and controllers
            joints_created = self._create_joint_hierarchy(asset_name, custom_joints or [], deformation_group)
            controllers_created = self._create_controllers(asset_name, joints_created, use_matrix, main_system, ignore_end_joint, extra_global_controls, model_group)
            
            self._create_sets_structure()
            
            # Create AnimSet from controls (will be empty initially)
            self._create_anim_set()
            
            # Create DeformSet for joints (will be empty initially)
            self._create_deform_set()
            
            # Add joints to DeformSet
            if cmds.objExists("DeformSet") and joints_created:
                try:
                    cmds.sets(joints_created, add="DeformSet")
                except Exception:
                    pass
            
            # Add controllers to AnimSet
            if controllers_created:
                if cmds.objExists("AnimSet"):
                    try:
                        cmds.sets(controllers_created, add="AnimSet")
                    except Exception:
                        pass
            
            # Select the top group
            cmds.select(top_group, replace=True)
            
            # Success - no dialog shown
            print(f"Simple Transform Puppet '{asset_name}' created successfully!")
            print(f"Created {len(joints_created)} joints and {len(controllers_created)} controllers")
            
        except Exception as e:
            cmds.warning(f"Error creating simple puppet: {str(e)}")
            cmds.confirmDialog(
                title="Error",
                message=f"Failed to create simple puppet: {str(e)}",
                button=['OK']
            )
        finally:
            # Close the undo chunk regardless of success or failure
            cmds.undoInfo(closeChunk=True)
    
    def _get_asset_name(self):
        """Derive asset name from the scene (top group), never from external env."""
        # 1) Prefer the selected model/top transform's top-most parent name
        try:
            sel = cmds.ls(selection=True, type="transform") or []
            if sel:
                node = sel[0]
                parent = cmds.listRelatives(node, parent=True)
                while parent:
                    node = parent[0]
                    parent = cmds.listRelatives(node, parent=True)
                short = cmds.ls(node, shortNames=True)[0]
                if short not in ("persp", "top", "front", "side"):
                    return short
        except Exception:
            pass
        
        # 2) Otherwise, look for a single top group in the scene (assemblies)
        try:
            assemblies = [a for a in (cmds.ls(assemblies=True) or []) if cmds.nodeType(a) == "transform"]
            assemblies = [a for a in assemblies if cmds.ls(a, shortNames=True)[0] not in ("persp", "top", "front", "side")]
            if len(assemblies) == 1:
                return cmds.ls(assemblies[0], shortNames=True)[0]
            if len(assemblies) > 1:
                # Prefer an assembly that actually contains meshes (likely the model)
                for a in assemblies:
                    if cmds.listRelatives(a, allDescendents=True, type="mesh"):
                        return cmds.ls(a, shortNames=True)[0]
        except Exception:
            pass
        
        # 3) Fallback to scene filename (without extension)
        try:
            scene_name = cmds.file(query=True, sceneName=True, shortName=True)
            if scene_name and scene_name != "untitled":
                clean_name = os.path.splitext(scene_name)[0]
                clean_name = clean_name.replace(" ", "_").replace("-", "_")
                if clean_name:
                    return clean_name
        except Exception:
            pass
        
        # 4) Final fallback: prompt user
        result = cmds.promptDialog(
            title="Asset Name Required",
            message="Please enter the asset name:",
            button=["OK", "Cancel"],
            defaultButton="OK",
            cancelButton="Cancel",
            dismissString="Cancel"
        )
        if result == "OK":
            asset_name = cmds.promptDialog(query=True, text=True)
            if asset_name and asset_name.strip():
                return asset_name.strip()
        return "UnknownAsset"
    
    def _create_sets_structure(self):
        """Create the Sets structure."""
        # Create main Sets set if it doesn't exist
        if not cmds.objExists("Sets"):
            cmds.sets(name="Sets", empty=True)
    
    def _create_anim_set(self):
        """Create AnimSet for controls."""
        # Create AnimSet if it doesn't exist
        if not cmds.objExists("AnimSet"):
            cmds.sets(name="AnimSet", empty=True)
        
        # Parent AnimSet to Sets
        if cmds.objExists("Sets"):
            try:
                cmds.sets("AnimSet", add="Sets")
            except Exception:
                pass  # Already parented
    
    def _create_deform_set(self):
        """Create DeformSet for joints."""
        # Create DeformSet if it doesn't exist
        if not cmds.objExists("DeformSet"):
            cmds.sets(name="DeformSet", empty=True)
        
        # Parent DeformSet to Sets
        if cmds.objExists("Sets"):
            try:
                cmds.sets("DeformSet", add="Sets")
            except Exception:
                pass  # Already parented
        
    # -----------------------
    # FK Controls
    # -----------------------
    def create_fk_controls(self, parent_in_hierarchy=True, use_matrix=True, *args):
        sel = cmds.ls(sl=True, type="joint")
        if not sel:
            cmds.warning("Please select joint(s) to create FK controls.")
            return

        try:
            # Group entire operation in a single undo step
            cmds.undoInfo(openChunk=True, chunkName="Create FK Controls")

            created = []
            # Derive control sizes from model bounding box (1x of bbox max extent)
            sx, sy, sz = self._get_model_bbox_extents()
            max_extent = max(sx, sy, sz) if all(e is not None for e in (sx, sy, sz)) else 10.0
            root_radius = 1.0 * max_extent
            # subsequent controls will be 0.85x of previous
            prev_radius = root_radius

            # Step 1: create controls + groups first
            for idx, jnt in enumerate(sel):
                radius = root_radius if idx == 0 else (0.85 * prev_radius)
                ctrl = cmds.circle(name=f"{jnt}_CTRL", normal=(1, 0, 0), radius=radius)[0]
                grp = cmds.group(ctrl, name=f"{ctrl}_GRP")
                cmds.delete(cmds.pointConstraint(jnt, grp))  # snap
                created.append((ctrl, grp, jnt))
                prev_radius = radius

            # Step 2: parent groups if needed
            if parent_in_hierarchy:
                for i in range(1, len(created)):
                    parent_ctrl = created[i-1][0]  # previous ctrl
                    this_grp = created[i][1]       # this ctrl's group
                    cmds.parent(this_grp, parent_ctrl)

            # Step 3: make connections
            for i, (ctrl, grp, jnt) in enumerate(created):
                if use_matrix:
                    # Get parent joint for matrix connection
                    parent_jnt = None
                    if i > 0:
                        parent_jnt = created[i-1][2]  # previous joint
                    self.offset_matrix_constraint(ctrl, jnt, grp, parent_jnt)
                else:
                    cmds.parentConstraint(ctrl, jnt, mo=True)
                    cmds.scaleConstraint(ctrl, jnt, mo=True)
                
        except Exception as e:
            cmds.warning(f"Error creating FK controls: {str(e)}")
            cmds.confirmDialog(
                title="Error",
                message=f"Failed to create FK controls: {str(e)}",
                button=['OK']
            )
        finally:
            # Close the undo chunk regardless of success or failure
            cmds.undoInfo(closeChunk=True)

    # -----------------------
    # OffsetParentMatrix Constraint Utility
    # -----------------------
    def offset_matrix_constraint(self, ctrl, jnt, ctrl_grp, parent_jnt=None):
        """Connect control to joint using offsetParentMatrix like prototype setup."""
        try:
            print(f"Setting up offsetParentMatrix connection: {ctrl} -> {jnt}")
            if parent_jnt:
                print(f"Parent joint: {parent_jnt}")
            
            # Create multMatrix node
            mm_name = f"{ctrl}_FK_ParentConstraint_multMatrix"
            if cmds.objExists(mm_name):
                cmds.delete(mm_name)
            
            mm = cmds.createNode("multMatrix", name=mm_name)
            print(f"Created multMatrix: {mm}")
            
            # Build the matrix chain order:
            # [0] control worldMatrix
            # [1] parent joint worldInverseMatrix (if present)

            # [0] Control worldMatrix
            cmds.connectAttr(f"{ctrl}.worldMatrix[0]", f"{mm}.matrixIn[0]", force=True)
            print(f"Connected {ctrl}.worldMatrix[0] -> {mm}.matrixIn[0]")
            
            # [1] Parent joint's worldInverseMatrix
            if parent_jnt and cmds.objExists(parent_jnt):
                cmds.connectAttr(f"{parent_jnt}.worldInverseMatrix[0]", f"{mm}.matrixIn[1]", force=True)
                print(f"Connected {parent_jnt}.worldInverseMatrix[0] -> {mm}.matrixIn[1]")
            
            # Connect multMatrix output to joint offsetParentMatrix
            cmds.connectAttr(f"{mm}.matrixSum", f"{jnt}.offsetParentMatrix", force=True)
            print(f"Connected {mm}.matrixSum -> {jnt}.offsetParentMatrix")
            
            print(f"✓ Successfully connected {ctrl} to {jnt} via offsetParentMatrix")

            # Zero out joint TRS values since we're using offsetParentMatrix
            cmds.setAttr(f"{jnt}.translate", 0, 0, 0)
            cmds.setAttr(f"{jnt}.rotate", 0, 0, 0)
            cmds.setAttr(f"{jnt}.scale", 1, 1, 1)
            print(f"Zeroed out TRS values for {jnt}")
                
        except Exception as e:
            cmds.warning(f"Failed to connect control via offsetParentMatrix: {str(e)}")
            return


    def _matrix_constrain_group_to_joint(self, jnt, grp):
        """Make a group follow a joint using matrix nodes, with scale support.
        Order: group.opm <= multMatrix( jnt.worldMatrix, parent.invMatrix ) where parent is group's parent.
        """
        try:
            if not (cmds.objExists(jnt) and cmds.objExists(grp)):
                return
            mm_name = f"{grp}_follow_{jnt}_mm"
            if cmds.objExists(mm_name):
                cmds.delete(mm_name)
            mm = cmds.createNode("multMatrix", name=mm_name)
            # jnt worldMatrix
            cmds.connectAttr(f"{jnt}.worldMatrix[0]", f"{mm}.matrixIn[0]", force=True)
            # group's parent inverse matrix (if parent exists)
            parent = cmds.listRelatives(grp, parent=True)
            if parent:
                cmds.connectAttr(f"{parent[0]}.worldInverseMatrix[0]", f"{mm}.matrixIn[1]", force=True)
            # drive group's offsetParentMatrix
            cmds.connectAttr(f"{mm}.matrixSum", f"{grp}.offsetParentMatrix", force=True)
            # Ensure grp has zero local TRS to avoid double transforms
            for attr, vals in ("translate", (0,0,0)), ("rotate", (0,0,0)), ("scale", (1,1,1)):
                try:
                    cmds.setAttr(f"{grp}.{attr}", *vals)
                except Exception:
                    pass
        except Exception as e:
            cmds.warning(f"Matrix-constrain failed for {grp} -> {jnt}: {str(e)}")

    def _get_model_bbox_size(self, asset_name=None):
        """Compute an approximate model size from geo's bounding box diagonal.
        Prefers geo under the provided asset_name to avoid ambiguous short names.
        """
        try:
            # Prefer geo group under the specific asset
            geo_group = self._resolve_geo_group(asset_name)
            targets = []
            if geo_group:
                targets = cmds.listRelatives(geo_group, allDescendents=True, type="mesh") or []
                # Convert mesh shapes to transforms
                targets = list(set(cmds.listRelatives(targets, parent=True, type="transform") or []))
            if not targets:
                # Fallback: all visible transforms
                targets = [t for t in (cmds.ls(assemblies=True) or []) if t not in ("persp", "top", "front", "side")]
            if not targets:
                return 10.0
            mins = [float('inf'), float('inf'), float('inf')]
            maxs = [float('-inf'), float('-inf'), float('-inf')]
            for t in targets:
                try:
                    bb = cmds.exactWorldBoundingBox(t)
                    mins[0] = min(mins[0], bb[0]); mins[1] = min(mins[1], bb[1]); mins[2] = min(mins[2], bb[2])
                    maxs[0] = max(maxs[0], bb[3]); maxs[1] = max(maxs[1], bb[4]); maxs[2] = max(maxs[2], bb[5])
                except Exception:
                    pass
            size = ((maxs[0]-mins[0])**2 + (maxs[1]-mins[1])**2 + (maxs[2]-mins[2])**2) ** 0.5
            return max(size, 1.0)
        except Exception:
            return 10.0

    def _get_model_bbox_extents(self, asset_name=None, model_group=None):
        """Return (sx, sy, sz) world extents of the model under geo.
        If unavailable, returns (None, None, None).
        """
        try:
            # If model_group provided and exists, measure its meshes
            targets = []
            if model_group and cmds.objExists(model_group):
                # Collect meshes directly under model_group hierarchy
                meshes = cmds.listRelatives(model_group, allDescendents=True, type="mesh") or []
                targets = list(set(cmds.listRelatives(meshes, parent=True, type="transform") or []))
            else:
                geo_group = self._resolve_geo_group(asset_name)
                if geo_group:
                    meshes = cmds.listRelatives(geo_group, allDescendents=True, type="mesh") or []
                    targets = list(set(cmds.listRelatives(meshes, parent=True, type="transform") or []))
            if not targets:
                return (None, None, None)
            mins = [float('inf'), float('inf'), float('inf')]
            maxs = [float('-inf'), float('-inf'), float('-inf')]
            for t in targets:
                try:
                    bb = cmds.exactWorldBoundingBox(t)
                    mins[0] = min(mins[0], bb[0]); mins[1] = min(mins[1], bb[1]); mins[2] = min(mins[2], bb[2])
                    maxs[0] = max(maxs[0], bb[3]); maxs[1] = max(maxs[1], bb[4]); maxs[2] = max(maxs[2], bb[5])
                except Exception:
                    pass
            sx = maxs[0]-mins[0]; sy = maxs[1]-mins[1]; sz = maxs[2]-mins[2]
            return (sx, sy, sz)
        except Exception:
            return (None, None, None)

    def _get_geo_child_groups(self, asset_name=None):
        """Return transform groups that are immediate children of geo for this asset.
        Avoids relying on ambiguous short names.
        """
        try:
            geo_group = self._resolve_geo_group(asset_name)
            if not geo_group:
                return []
            children = cmds.listRelatives(geo_group, children=True, type="transform") or []
            return children
        except Exception:
            return []

    def _resolve_geo_group(self, asset_name=None):
        """Resolve the geo group's full DAG path, preferring the one under asset_name."""
        try:
            # If asset_name exists, look for its direct child named 'geo'
            if asset_name and cmds.objExists(asset_name):
                children = cmds.listRelatives(asset_name, children=True, type="transform") or []
                for child in children:
                    if cmds.ls(child, shortNames=True)[0].lower() in ("geo", "geometry", "model", "mesh"):
                        return child
            # Fallback: choose a unique geo-like group that actually contains meshes
            candidates = []
            for name in ["geo", "geometry", "model", "mesh"]:
                for node in cmds.ls(name, transforms=True) or []:
                    candidates.append(node)
            # If multiple, pick one that has meshes under it
            for cand in candidates:
                if cmds.listRelatives(cand, allDescendents=True, type="mesh"):
                    return cand
            return None
        except Exception:
            return None
    
    def verify_offset_parent_matrix_connection(self, joint_name):
        """Verify that a joint has proper TRS connections via decomposeMatrix."""
        if not cmds.objExists(joint_name):
            print(f"Joint {joint_name} does not exist")
            return False
        
        # Check connections to TRS attributes
        translate_conn = cmds.listConnections(f"{joint_name}.translate", source=True, destination=False)
        rotate_conn = cmds.listConnections(f"{joint_name}.rotate", source=True, destination=False)
        scale_conn = cmds.listConnections(f"{joint_name}.scale", source=True, destination=False)
        
        print(f"Connections to {joint_name}.translate: {translate_conn}")
        print(f"Connections to {joint_name}.rotate: {rotate_conn}")
        print(f"Connections to {joint_name}.scale: {scale_conn}")
        
        if translate_conn and rotate_conn and scale_conn:
            # Check if all TRS connections come from the same decomposeMatrix node
            common_conn = None
            for conn in translate_conn:
                if conn in rotate_conn and conn in scale_conn:
                    common_conn = conn
                    break
            
            if common_conn and cmds.nodeType(common_conn) == "decomposeMatrix":
                print(f"✓ Found decomposeMatrix connection: {common_conn}")
                
                # Check decomposeMatrix input
                input_conn = cmds.listConnections(f"{common_conn}.inputMatrix", source=True, destination=False)
                print(f"  decomposeMatrix input: {input_conn}")
                
                # Check if input comes from multMatrix
                if input_conn and cmds.nodeType(input_conn[0]) == "multMatrix":
                    print(f"✓ Found multMatrix -> decomposeMatrix -> TRS chain")
                    return True
                else:
                    print(f"  Input type: {cmds.nodeType(input_conn[0]) if input_conn else 'None'}")
            else:
                print(f"✗ No common decomposeMatrix connection found for all TRS attributes")
        else:
            print(f"✗ Missing connections to TRS attributes")
            return False
        
        return False
    
    # -----------------------
    # Push/Publish
    # -----------------------
    def push_rig(self, *args):
        """Push/publish the rig for production use."""
        try:
            # Group entire operation in a single undo step
            cmds.undoInfo(openChunk=True, chunkName="Push Rig")
            # Get current selection
            selection = cmds.ls(selection=True, long=True)
            if not selection:
                cmds.warning("Please select the rig root group to push.")
                return
            
            # Get asset name from the selected rig root's short name
            asset_name = cmds.ls(selection[0], shortNames=True)[0]
            
            # Check if we have a valid rig structure
            if not self._validate_rig_structure(selection[0]):
                cmds.warning("Selected object doesn't appear to be a valid rig structure.")
                return
            
            # Run rigX publish finalize
            self._run_publish_finalize(asset_name)
            
            # Show success message
            cmds.confirmDialog(
                title="Push Complete",
                message=f"Rig '{asset_name}' has been pushed successfully!\n\nPublish operations completed:\n- Rig finalized\n- Sets validated\n- Ready for production",
                button=['OK']
            )
            
        except Exception as e:
            cmds.warning(f"Error pushing rig: {str(e)}")
            cmds.confirmDialog(
                title="Push Error",
                message=f"Failed to push rig: {str(e)}",
                button=['OK']
            )
        finally:
            # Close the undo chunk regardless of success or failure
            cmds.undoInfo(closeChunk=True)
    
    def _validate_rig_structure(self, root_group):
        """Validate that the selected group has a proper rig structure."""
        try:
            # Check if it has geo and rig children
            children = cmds.listRelatives(root_group, children=True, type="transform") or []
            child_names = [cmds.ls(child, shortNames=True)[0] for child in children]
            
            has_geo = "geo" in child_names
            has_rig = "rig" in child_names
            
            return has_geo and has_rig
        except Exception:
            return False
    
    def _run_publish_finalize(self, asset_name):
        """Run the rigX publish finalize process."""
        try:
            # Import the publish finalize module
            from rigging_pipeline.utils.rigx_publishFinalize import rigx_publish
            
            # Run the publish process
            rigx_publish(asset_name)
            
        except ImportError:
            # Fallback: run basic finalize operations
            self._basic_finalize(asset_name)
        except Exception as e:
            # If publish fails, try basic finalize
            cmds.warning(f"Publish finalize failed: {str(e)}. Running basic finalize...")
            self._basic_finalize(asset_name)
    
    def _create_joint_hierarchy(self, asset_name, custom_joints, deformation_group):
        """Create joint hierarchy with standard naming."""
        joints_created = []
        
        try:
            if custom_joints and custom_joints[0].strip():
                # Use custom joints if provided
                print(f"Using custom joints: {custom_joints}")
                
                # Find the custom joint in the scene
                custom_joint_name = custom_joints[0].strip()
                if cmds.objExists(custom_joint_name):
                    # Use the existing joint - find all joints in hierarchy
                    existing_joints = [custom_joint_name]
                    
                    # Get all children joints recursively
                    children = self._get_all_joint_children(custom_joint_name)
                    existing_joints.extend(children)
                    
                    print(f"Found existing joints: {existing_joints}")
                    
                    # Rename joints to standard names
                    joints_created = self._rename_joints_to_standard(existing_joints)
                else:
                    # Create the custom joint if it doesn't exist
                    clean_name = custom_joint_name.replace(" ", "_")
                    joint = cmds.joint(name="main_JNT")
                    cmds.move(0, 0, 0, joint, absolute=True)
                    joints_created.append(joint)
            else:
                # Create default main joint if no custom joints
                main_joint = cmds.joint(name="main_JNT")
                cmds.move(0, 0, 0, main_joint)
                joints_created.append(main_joint)
            
            # Parent the main joint to DeformationSystem
            if deformation_group and cmds.objExists(deformation_group):
                try:
                    cmds.parent(joints_created[0], deformation_group)
                except Exception:
                    pass
            
            return joints_created
            
        except Exception as e:
            cmds.warning(f"Error creating joint hierarchy: {str(e)}")
            return joints_created
    
    def _rename_joints_to_standard(self, existing_joints):
        """Rename joints keeping original names when possible, using transformer naming as fallback."""
        renamed_joints = []
        
        try:
            # Rename root joint to main_JNT if it's not already a proper name
            root_joint = existing_joints[0]
            if self._is_proper_joint_name(root_joint):
                renamed_joints.append(root_joint)  # Keep original name
            else:
                new_name = cmds.rename(root_joint, "main_JNT")
                renamed_joints.append(new_name)
            
            # Rename children - keep original if proper, otherwise use transform naming
            children = existing_joints[1:]
            transformer_count = 1
            
            for child_joint in children:
                if self._is_proper_joint_name(child_joint):
                    renamed_joints.append(child_joint)  # Keep original name
                else:
                    new_name = cmds.rename(child_joint, f"transform{transformer_count}")
                    renamed_joints.append(new_name)
                    transformer_count += 1
            
            return renamed_joints
            
        except Exception as e:
            cmds.warning(f"Error renaming joints: {str(e)}")
            return existing_joints
    
    def _is_proper_joint_name(self, joint_name):
        """Check if joint name is properly named (not generic Maya naming)."""
        # Keep original names that don't contain generic Maya patterns
        generic_patterns = ['joint', 'joint1', 'joint10', 'jnt', 'jointShape']
        
        joint_base = joint_name.lower().replace('_', '').replace(' ', '')
        
        for pattern in generic_patterns:
            if joint_base == pattern or joint_base.startswith(pattern):
                return False
        
        # Also check if it's just numbers
        if joint_base.isdigit():
            return False
            
        return True
    
    def _get_all_joint_children(self, parent_joint):
        """Get all joint children recursively."""
        children = []
        direct_children = cmds.listRelatives(parent_joint, children=True, type="joint") or []
        
        for child in direct_children:
            children.append(child)
            # Recursively get grandchildren
            grandchildren = self._get_all_joint_children(child)
            children.extend(grandchildren)
        
        return children
    
    def _create_controllers(self, asset_name, joints, use_matrix, motion_group, ignore_end_joint=False, extra_global_controls=0, model_group=None):
        """Create individual controllers for each joint."""
        controllers_created = []
        
        try:
            # Compute model size once for control scaling (scoped to this asset)
            sx, sy, sz = self._get_model_bbox_extents(asset_name, model_group)
            max_extent = max(sx, sy, sz) if all(e is not None for e in (sx, sy, sz)) else 10.0
            global_radius = 1.0 * max_extent           # 1x for global
            # Main must be smaller than global
            main_radius = 0.85 * global_radius
            # Create global controller for overall hierarchy
            global_ctrl = cmds.circle(name="global_CTRL", normal=(0, 1, 0), radius=global_radius)[0]
            global_grp = cmds.group(global_ctrl, name=f"{global_ctrl}_GRP")
            cmds.move(0, 0, 0, global_grp, absolute=True)
            
            # Set global controller color to yellow
            cmds.setAttr(f"{global_ctrl}.overrideEnabled", 1)
            cmds.setAttr(f"{global_ctrl}.overrideColor", 17)  # Yellow
            
            # Add ENUM attributes to global controller (keyable for visibility)
            cmds.addAttr(global_ctrl, longName="Joint", attributeType="enum", enumName="Off:On", keyable=True)
            cmds.addAttr(global_ctrl, longName="Control", attributeType="enum", enumName="Off:On", keyable=True)
            cmds.addAttr(global_ctrl, longName="Model", attributeType="enum", enumName="Normal:Template:Reference", keyable=True)
            
            # Set default values
            cmds.setAttr(f"{global_ctrl}.Joint", 0)  # Off
            cmds.setAttr(f"{global_ctrl}.Control", 1)  # On
            cmds.setAttr(f"{global_ctrl}.Model", 2)  # Reference
            
            controllers_created.append(global_ctrl)
            last_global_control = global_ctrl

            # Create additional global controls if requested (global > extras > main)
            if isinstance(extra_global_controls, int) and extra_global_controls > 0:
                parent_name = global_ctrl
                # Space extra radii strictly between main and global (exclusive of both)
                for idx in range(extra_global_controls):
                    t = float(idx + 1) / float(extra_global_controls + 1)
                    radius = main_radius + t * (global_radius - main_radius)
                    name = f"global{idx+2}_CTRL"
                    extra_ctrl = cmds.circle(name=name, normal=(0, 1, 0), radius=radius)[0]
                    extra_grp = cmds.group(extra_ctrl, name=f"{extra_ctrl}_GRP")
                    cmds.move(0, 0, 0, extra_grp, absolute=True)
                    try:
                        cmds.parent(extra_grp, parent_name)
                    except Exception:
                        pass
                    cmds.setAttr(f"{extra_ctrl}.overrideEnabled", 1)
                    cmds.setAttr(f"{extra_ctrl}.overrideColor", 17)
                    controllers_created.append(extra_ctrl)
                    # Next level becomes the parent for subsequent extra globals
                    parent_name = extra_ctrl
                    last_global_control = extra_ctrl
            
            # Parent global controller group to MainSystem
            if motion_group and cmds.objExists(motion_group):
                try:
                    cmds.parent(global_grp, motion_group)
                except Exception:
                    pass
            
            # Create individual controller for each joint
            if joints:
                joint_controllers = []
                
                # Apply ignore_end_joint logic
                joints_to_control = joints[:-1] if ignore_end_joint and len(joints) > 1 else joints
                
                for i, joint in enumerate(joints_to_control):
                    # Create controller name based on joint name
                    joint_base = joint.replace("_JNT", "").replace("_jnt", "")
                    
                    # Check if joint has a proper name or use transformer naming
                    if self._is_proper_joint_name(joint):
                        ctrl_name = f"{joint_base}_CTRL"
                    elif i == 0:
                        ctrl_name = "main_CTRL"
                    else:
                        # Find transformer count for this joint
                        transformer_count = sum(1 for j in joints_to_control[:i] if not self._is_proper_joint_name(joints[joints.index(j)]))
                        ctrl_name = f"transform{transformer_count}_CTRL"
                    
                    # Create control shape
                    if i == 0:  # Root joint gets larger control
                        joint_ctrl = cmds.circle(name=ctrl_name, normal=(0, 1, 0), radius=main_radius)[0]
                        prev_ctrl_radius = main_radius
                    else:
                        next_radius = 0.85 * prev_ctrl_radius
                        joint_ctrl = cmds.circle(name=ctrl_name, normal=(0, 1, 0), radius=next_radius)[0]
                        prev_ctrl_radius = next_radius
                    
                    # Set controller colors
                    if ctrl_name == "main_CTRL":
                        # Red for main controller
                        cmds.setAttr(f"{joint_ctrl}.overrideEnabled", 1)
                        cmds.setAttr(f"{joint_ctrl}.overrideColor", 13)  # Red
                    else:
                        # Blue for all other controllers
                        cmds.setAttr(f"{joint_ctrl}.overrideEnabled", 1)
                        cmds.setAttr(f"{joint_ctrl}.overrideColor", 6)  # Blue
                    
                    # Create control group
                    ctrl_grp = cmds.group(joint_ctrl, name=f"{joint_ctrl}_GRP")
                    
                    # Match control group to joint's pivot and orientation
                    cmds.matchTransform(ctrl_grp, joint, position=True, rotation=True, scale=False)
                    
                    # Zero out control's transform values (control stays at origin relative to group)
                    cmds.setAttr(f"{joint_ctrl}.translate", 0, 0, 0)
                    cmds.setAttr(f"{joint_ctrl}.rotate", 0, 0, 0)
                    cmds.setAttr(f"{joint_ctrl}.scale", 1, 1, 1)
                    
                    # Parent to parent controller following intersection hierarchy
                    parent_joint_index = None
                    if i > 0:
                        for j in range(i-1, -1, -1):  # Look for previous controller
                            prev_joint = joints_to_control[j]
                            if prev_joint in joints:
                                parent_joint_index = j
                                break
                    
                    if parent_joint_index is not None:
                        # Find the parent controller name
                        parent_joint = joints_to_control[parent_joint_index]
                        parent_joint_base = parent_joint.replace("_JNT", "").replace("_jnt", "")
                        if self._is_proper_joint_name(parent_joint):
                            parent_ctrl_name = f"{parent_joint_base}_CTRL"
                        elif parent_joint_index == 0:
                            parent_ctrl_name = "main_CTRL"
                        else:
                            transformer_count = sum(1 for k in joints_to_control[:parent_joint_index] if not self._is_proper_joint_name(joints[joints.index(joints_to_control[k])]))
                            parent_ctrl_name = f"transform{transformer_count}_CTRL"
                        
                        if cmds.objExists(parent_ctrl_name):
                            cmds.parent(ctrl_grp, parent_ctrl_name)
                        else:
                            cmds.parent(ctrl_grp, last_global_control)
                    else:
                        cmds.parent(ctrl_grp, last_global_control)
                    
                    controllers_created.append(joint_ctrl)
                    joint_controllers.append((joint_ctrl, ctrl_grp, joint))
                
                # Connect controllers to their respective joints
                for i, (joint_ctrl, ctrl_grp, joint) in enumerate(joint_controllers):
                    try:
                        if use_matrix:
                            # Get parent joint for matrix connection
                            parent_jnt = None
                            if i > 0:
                                parent_jnt = joint_controllers[i-1][2]  # previous joint
                            self.offset_matrix_constraint(joint_ctrl, joint, ctrl_grp, parent_jnt)
                        else:
                            # Use constraints
                            cmds.parentConstraint(joint_ctrl, joint, mo=True)
                            cmds.scaleConstraint(joint_ctrl, joint, mo=True)
                    except Exception as e:
                        cmds.warning(f"Failed to connect {joint_ctrl} to {joint}: {str(e)}")
                
                # Connect global controller ENUM attributes to visibility and display
                self._connect_global_controller_attributes(global_ctrl, joint_controllers, joints)
                
                # Constrain groups directly under geo to follow the main joint
                try:
                    if joints:
                        main_joint = joints[0]
                        geo_children = self._get_geo_child_groups(asset_name)
                        for child_grp in geo_children:
                            if use_matrix:
                                self._matrix_constrain_group_to_joint(main_joint, child_grp)
                                print(f"Matrix-constrained {child_grp} to follow {main_joint}")
                            else:
                                try:
                                    cmds.parentConstraint(main_joint, child_grp, mo=True)
                                except Exception:
                                    pass
                                try:
                                    cmds.scaleConstraint(main_joint, child_grp, mo=True)
                                except Exception:
                                    pass
                                print(f"Constrained {child_grp} to follow {main_joint} (parent+scale)")
                except Exception as e:
                    cmds.warning(f"Failed to constrain geo child groups: {str(e)}")
            
            return controllers_created
            
        except Exception as e:
            cmds.warning(f"Error creating controllers: {str(e)}")
            return controllers_created
    
    def _connect_global_controller_attributes(self, global_ctrl, joint_controllers, joints):
        """Connect global controller ENUM attributes to visibility and display."""
        try:
            # Get main control group (main_CTRL_GRP)
            main_ctrl_grp = None
            if joint_controllers:
                main_ctrl_grp = joint_controllers[0][1]  # First controller's group
            
            # Get main joint (first joint)
            main_joint = None
            if joints:
                main_joint = joints[0]
            
            # Connect Control ENUM to main control group visibility (direct connection)
            if main_ctrl_grp and cmds.objExists(main_ctrl_grp):
                cmds.connectAttr(f"{global_ctrl}.Control", f"{main_ctrl_grp}.visibility")
                print(f"Connected {global_ctrl}.Control -> {main_ctrl_grp}.visibility")
            
            # Connect Joint ENUM to main joint visibility (direct connection)
            if main_joint and cmds.objExists(main_joint):
                cmds.connectAttr(f"{global_ctrl}.Joint", f"{main_joint}.visibility")
                print(f"Connected {global_ctrl}.Joint -> {main_joint}.visibility")
            
            # Connect Model ENUM to geo group enable override and display type
            # Look for geo group (usually named "geo" or similar)
            geo_group = None
            possible_names = ["geo", "geometry", "model", "mesh"]
            for name in possible_names:
                if cmds.objExists(name):
                    geo_group = name
                    break
            
            if geo_group and cmds.objExists(geo_group):
                # Enable override first
                cmds.setAttr(f"{geo_group}.overrideEnabled", 1)
                
                # Connect Model ENUM to geo group display type
                # 0=Normal, 1=Template, 2=Reference
                cmds.connectAttr(f"{global_ctrl}.Model", f"{geo_group}.overrideDisplayType")
                print(f"Connected {global_ctrl}.Model -> {geo_group}.overrideDisplayType")
            
        except Exception as e:
            cmds.warning(f"Failed to connect global controller attributes: {str(e)}")
    
    def _basic_finalize(self, asset_name):
        """Basic finalize operations when publish module is not available."""
        try:
            # Hide joints
            joints = cmds.ls(type="joint")
            for joint in joints:
                try:
                    cmds.setAttr(f"{joint}.visibility", 0)
                except Exception:
                    pass
            
            # Ensure sets are properly organized
            self._create_sets_structure()
            self._create_anim_set()
            self._create_deform_set()
            
            # Add joints to DeformSet
            if cmds.objExists("DeformSet"):
                joints = cmds.ls(type="joint")
                if joints:
                    try:
                        cmds.sets(joints, add="DeformSet")
                    except Exception:
                        pass
            
            print(f"Basic finalize completed for {asset_name}")
            
        except Exception as e:
            cmds.warning(f"Basic finalize failed: {str(e)}")
    
    


def launch_AnimRig():
    """Launch the Animation Rigging Tools."""
    try:
        tool = RigXAnimRig()
        tool.show_ui()
        return tool
    except Exception as e:
        cmds.warning(f"Failed to launch Animation Rigging Tools: {str(e)}")
        return None


if __name__ == "__main__":
    launch_AnimRig()
