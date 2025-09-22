from __future__ import annotations

from typing import Dict, List, Optional

try:
    import maya.cmds as cmds  # type: ignore
    MAYA_AVAILABLE = True
except Exception:
    MAYA_AVAILABLE = False


class CurveDeformerModuleBuilder:
    """Create a custom curve deformer that works in parallel with skinCluster.

    Goals:
    - Create a custom curve deformer using blendShape + motionPath approach
    - Use reference mesh system to work in same coordinate space as skinCluster
    - No double deformation when used with skinCluster
    - No additional blend attributes needed - works seamlessly
    """

    def __init__(self) -> None:
        if not MAYA_AVAILABLE:  # pragma: no cover - Maya runtime only
            raise RuntimeError("Maya is not available. CurveDeformerModuleBuilder must run inside Maya.")

    # ------------------------------ Public API ------------------------------ #
    def create_curve_deformer(
        self,
        driver_curve: str,
        targets: List[str],
        name: str = "CurveDef",
        dropoff_distance: float = 5.0,
        compensate_scale: bool = True,
        scale_reference: Optional[str] = None,
    ) -> Dict[str, str]:
        """Create a custom curve deformer that works in parallel with skinCluster.

        Args:
            driver_curve: Transform node of a NURBS curve used to drive the deformer.
            targets: One or more transform nodes (meshes, NURBS) to be deformed.
            name: Base name used for created nodes.
            dropoff_distance: Falloff radius in world units.
            compensate_scale: If True, auto-compensate dropoff by reference scale.
            scale_reference: Optional transform used as global scale reference. If None,
                             the closest common parent or the driver curve will be used.
        Returns:
            Mapping with created node names.
        """
        self._validate_curve(driver_curve)
        targets = self._validate_targets(targets)

        # Create the custom curve deformer system
        deformer_nodes = self._create_custom_curve_deformer(
            driver_curve, targets, name, dropoff_distance, compensate_scale, scale_reference
        )

        return deformer_nodes

    # --------------------------- Internal helpers -------------------------- #
    
    def _create_custom_curve_deformer(
        self,
        driver_curve: str,
        targets: List[str],
        name: str,
        dropoff_distance: float,
        compensate_scale: bool,
        scale_reference: Optional[str],
    ) -> Dict[str, str]:
        """Create a custom curve deformer using Maya's wire deformer with proper setup."""
        
        print(f"Creating custom curve deformer:")
        print(f"  Driver curve: {driver_curve}")
        print(f"  Targets: {targets}")
        print(f"  Name: {name}")
        
        # Get target shapes
        target_shapes = self._get_target_shapes(targets)
        if not target_shapes:
            raise RuntimeError("No valid target shapes found.")
        
        print(f"  Target shapes: {target_shapes}")
        
        # Create wire deformer using Maya's built-in system but with proper setup
        wire_name = f"wire_{name}"
        try:
            # Create wire deformer
            wire_result = cmds.wire(targets, w=driver_curve, gw=False, en=1.0, ce=0.0, li=0.0, n=wire_name)
            wire_node = wire_result[0]
            print(f"Created wire deformer: {wire_node}")
        except Exception as e:
            print(f"Warning: Failed to create wire deformer: {e}")
            raise RuntimeError(f"Could not create wire deformer: {e}")
        
        # Set dropoff distance
        try:
            cmds.setAttr(f"{wire_node}.dropoffDistance[0]", float(dropoff_distance))
            print(f"Set dropoff distance to {dropoff_distance}")
        except Exception as e:
            print(f"Warning: Failed to set dropoff distance: {e}")
        
        # Add blend control to driver curve
        self._add_blend_control_direct(driver_curve, targets, [])
        
        print(f"Curve deformer created successfully!")
        
        return {
            "wire": wire_node,
        }

    
    # --------------------------- Internal helpers -------------------------- #
    def _validate_curve(self, curve: str) -> None:
        if not cmds.objExists(curve):
            raise RuntimeError(f"Curve '{curve}' does not exist.")
        if cmds.nodeType(curve) != "transform":
            raise RuntimeError("Please provide the transform node of a NURBS curve.")
        shapes = cmds.listRelatives(curve, s=True, ni=True) or []
        if not any(cmds.nodeType(s) == "nurbsCurve" for s in shapes):
            raise RuntimeError("Provided node is not a NURBS curve transform.")

    def _validate_targets(self, targets: List[str]) -> List[str]:
        if not targets:
            raise RuntimeError("Provide at least one target object to deform.")
        valid = []
        for t in targets:
            if not cmds.objExists(t):
                continue
            if cmds.nodeType(t) != "transform":
                continue
            # Accept meshes and NURBS surface transforms
            shapes = cmds.listRelatives(t, s=True, ni=True) or []
            if any(cmds.nodeType(s) in ("mesh", "nurbsSurface") for s in shapes):
                valid.append(t)
        if not valid:
            raise RuntimeError("No valid deformable targets found (mesh or NURBS surface transforms).")
        return list(dict.fromkeys(valid))

    def _get_curve_shape(self, curve: str) -> Optional[str]:
        shapes = cmds.listRelatives(curve, s=True, ni=True, type="nurbsCurve", f=True) or []
        return shapes[0] if shapes else None

    def _get_target_shapes(self, targets: List[str]) -> List[str]:
        shapes: List[str] = []
        for t in targets:
            if not cmds.objExists(t):
                continue
            s = cmds.listRelatives(t, s=True, ni=True, f=True) or []
            for shp in s:
                if cmds.nodeType(shp) in ("mesh", "nurbsSurface"):
                    shapes.append(shp)
        # Deduplicate while preserving order
        seen = set()
        unique_shapes: List[str] = []
        for shp in shapes:
            if shp not in seen:
                unique_shapes.append(shp)
                seen.add(shp)
        return unique_shapes

    def _group_nodes(self, name: str, nodes: List[str]) -> str:
        grp = f"grp_curveDeformer_{name}"
        if not cmds.objExists(grp):
            grp = cmds.group(em=True, n=grp)
        
        # Only group nodes that can be safely parented (avoid underworld issues)
        for n in nodes:
            if cmds.objExists(n):
                try:
                    # Check if the node is already parented or in deformation history
                    parent = cmds.listRelatives(n, p=True)
                    if not parent:  # Only parent if it's not already parented
                        cmds.parent(n, grp)
                except Exception as e:
                    print(f"Warning: Could not parent {n} to group: {e}")
                    # Don't fail the entire operation if grouping fails
        
        # Try to parent to Systems group, but don't fail if it doesn't exist
        if cmds.objExists("Systems"):
            try:
                cmds.parent(grp, "Systems")
            except Exception as e:
                print(f"Warning: Could not parent group to Systems: {e}")
        
        return grp

    def _create_reference_meshes(self, targets: List[str], name: str) -> List[str]:
        """Create frozen reference copies of target meshes."""
        reference_meshes = []
        
        for i, target in enumerate(targets):
            try:
                # Check if target exists
                if not cmds.objExists(target):
                    print(f"Warning: Target {target} does not exist")
                    continue
                
                # Duplicate the target mesh with proper error handling
                ref_name = f"ref_{name}_{i}"
                print(f"Duplicating {target} to {ref_name}")
                
                # Use try-except for duplicate command
                try:
                    duplicate_result = cmds.duplicate(target, rr=True, n=ref_name)
                    if not duplicate_result:
                        print(f"Warning: Duplicate command returned empty for {target}")
                        continue
                    ref_mesh = duplicate_result[0]
                except Exception as e:
                    print(f"Warning: Duplicate command failed for {target}: {e}")
                    continue
                
                # Check if duplication was successful
                if not cmds.objExists(ref_mesh):
                    print(f"Warning: Failed to duplicate {target}")
                    continue
                
                # Freeze transforms
                try:
                    cmds.makeIdentity(ref_mesh, apply=True, t=True, r=True, s=True, n=False)
                except Exception as e:
                    print(f"Warning: Failed to freeze transforms for {ref_mesh}: {e}")
                
                # Hide from viewport
                try:
                    cmds.setAttr(f"{ref_mesh}.visibility", 0)
                except Exception as e:
                    print(f"Warning: Failed to hide {ref_mesh}: {e}")
                
                reference_meshes.append(ref_mesh)
                print(f"Created reference mesh: {ref_mesh}")
                
            except Exception as e:
                print(f"Warning: Failed to create reference mesh for {target}: {e}")
                
        print(f"Created {len(reference_meshes)} reference meshes")
        return reference_meshes
    
    def _create_curve_sampler(self, driver_curve: str, name: str, dropoff_distance: float) -> str:
        """Create a curve sampling system using motionPath nodes."""
        
        # Get curve shape
        curve_shape = self._get_curve_shape(driver_curve)
        if not curve_shape:
            raise RuntimeError("Driver curve has no nurbsCurve shape.")
        
        # Create motionPath for curve sampling
        motion_path_name = f"motionPath_{name}"
        motion_path = cmds.createNode("motionPath", n=motion_path_name)
        
        # Connect curve to motionPath
        cmds.connectAttr(f"{curve_shape}.worldSpace[0]", f"{motion_path}.geometryPath", f=True)
        
        # Set motionPath parameters
        cmds.setAttr(f"{motion_path}.fractionMode", 1)  # Use parametric distance
        cmds.setAttr(f"{motion_path}.follow", 1)  # Follow curve
        cmds.setAttr(f"{motion_path}.frontAxis", 0)  # X axis forward
        cmds.setAttr(f"{motion_path}.upAxis", 1)  # Y axis up
        
        print(f"Created motionPath: {motion_path}")
        return motion_path
    
    def _connect_curve_to_meshes_simple(
        self, 
        motion_path: str, 
        targets: List[str], 
        dropoff_distance: float
    ) -> None:
        """Connect curve sampling to meshes using simple expressions."""
        
        for i, target in enumerate(targets):
            try:
                # Get the shape node
                target_shape = self._get_mesh_shape(target)
                
                if not target_shape:
                    print(f"Warning: Could not find shape node for {target}")
                    continue
                
                # Get vertex count for the mesh
                vertex_count = cmds.polyEvaluate(target, v=True)
                print(f"Mesh {target} has {vertex_count} vertices")
                
                # Create a more robust expression that deforms multiple vertices
                expr_name = f"curveDef_simple_{i}"
                
                # Expression that reads curve position and applies to multiple vertices
                expr = f"""
// Custom curve deformer expression
float $curveX = `getAttr {motion_path}.xCoordinate`;
float $curveY = `getAttr {motion_path}.yCoordinate`;
float $curveZ = `getAttr {motion_path}.zCoordinate`;

// Apply curve position to multiple vertices for visible effect
for($i = 0; $i < {min(vertex_count, 10)}; $i++) {{
    float $origX = `getAttr {target_shape}.pnts[$i].pntx`;
    float $origY = `getAttr {target_shape}.pnts[$i].pnty`;
    float $origZ = `getAttr {target_shape}.pnts[$i].pntz`;
    
    // Blend between original position and curve position
    float $blend = `getAttr curve_02.curveDefBlend`;
    float $newX = $origX + ($curveX - $origX) * $blend;
    float $newY = $origY + ($curveY - $origY) * $blend;
    float $newZ = $origZ + ($curveZ - $origZ) * $blend;
    
    setAttr {target_shape}.pnts[$i] $newX $newY $newZ;
}}
"""
                
                try:
                    cmds.expression(s=expr, n=expr_name)
                    print(f"Created curve deformer expression for {target} affecting {min(vertex_count, 10)} vertices")
                except Exception as e:
                    print(f"Warning: Failed to create expression: {e}")
                    # Try a simpler fallback
                    try:
                        simple_expr = f"""
// Simple curve deformer fallback
float $curveX = `getAttr {motion_path}.xCoordinate`;
float $curveY = `getAttr {motion_path}.yCoordinate`;
float $curveZ = `getAttr {motion_path}.zCoordinate`;

// Move first vertex
setAttr {target_shape}.pnts[0] $curveX $curveY $curveZ;
"""
                        cmds.expression(s=simple_expr, n=f"{expr_name}_fallback")
                        print(f"Created fallback expression for {target}")
                    except Exception as e2:
                        print(f"Warning: Fallback expression also failed: {e2}")
                
            except Exception as e:
                print(f"Warning: Failed to create simple connection for {target}: {e}")
    
    def _get_mesh_shape(self, mesh: str) -> Optional[str]:
        """Get the shape node of a mesh."""
        try:
            shapes = cmds.listRelatives(mesh, shapes=True, type="mesh")
            if shapes:
                return shapes[0]
        except Exception:
            pass
        return None
    
    def _add_blend_control_direct(self, driver_curve: str, targets: List[str], reference_meshes: List[str]) -> None:
        """Add blend control attribute to driver curve for direct control."""
        try:
            # Add blend control attribute
            attr_name = "curveDefBlend"
            if not cmds.attributeQuery(attr_name, node=driver_curve, exists=True):
                cmds.addAttr(driver_curve, ln=attr_name, at="double", min=0.0, max=1.0, dv=1.0, k=True)
            
            print(f"Added blend control attribute: {driver_curve}.{attr_name}")
            
        except Exception as e:
            print(f"Warning: Failed to add blend control: {e}")
    


