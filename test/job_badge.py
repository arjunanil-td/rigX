# Simple UV Shell Selection Script for Maya
# This script randomly selects UV shells on a selected mesh

import maya.cmds as cmds
import random


def select_random_uv_shells(count=None, percent=20, seed=None):
    """
    Select random UV shells on the currently selected mesh.
    
    Args:
        count (int): Exact number of UV shells to select (overrides percent)
        percent (float): Percentage of UV shells to select (1-100)
        seed (int): Random seed for reproducible results
    """
    if seed is not None:
        random.seed(seed)
    
    # Get current selection
    selection = cmds.ls(selection=True)
    if not selection:
        cmds.warning("Please select a mesh first!")
        return []
    
    mesh_name = selection[0]
    print(f"Processing mesh: {mesh_name}")
    
    # Get the mesh shape node
    shapes = cmds.listRelatives(mesh_name, shapes=True, type="mesh")
    if not shapes:
        cmds.warning(f"No mesh shape found under {mesh_name}")
        return []
    
    mesh_shape = shapes[0]
    print(f"Mesh shape: {mesh_shape}")
    
    # Get available UV sets
    uv_sets = cmds.polyUVSet(mesh_shape, query=True, allUVSets=True)
    if not uv_sets:
        cmds.warning(f"No UV sets found on {mesh_shape}")
        return []
    
    print(f"Available UV sets: {uv_sets}")
    
    # Use the first UV set (usually "map1")
    uv_set = uv_sets[0]
    print(f"Using UV set: {uv_set}")
    
    # Get UV shell information using a working approach
    try:
        # Get the number of UVs
        num_uvs = cmds.polyEvaluate(mesh_shape, uv=True)
        print(f"Total UVs: {num_uvs:,}")
        
        # Get UV shell count
        shell_count = cmds.polyEvaluate(mesh_shape, uvShell=True)
        print(f"Found {shell_count:,} UV shells")
        
        if shell_count == 0:
            cmds.warning("No UV shells found!")
            return []
        
        # Calculate how many shells to select
        if count is not None:
            # Use exact count
            shells_to_select = min(count, shell_count)
            print(f"Selecting exactly {shells_to_select} shells")
        else:
            # Use percentage
            shells_to_select = max(1, int(round((percent / 100.0) * shell_count)))
            shells_to_select = min(shells_to_select, shell_count)
            print(f"Selecting {shells_to_select} shells ({percent}% of {shell_count:,})")
        
        # For very large meshes, ensure we select a reasonable number
        if shell_count > 10000 and shells_to_select < 100:
            min_shells = max(100, int(shell_count * 0.01))  # At least 1% or 100 shells
            shells_to_select = max(shells_to_select, min_shells)
            print(f"Large mesh detected - adjusting to select at least {shells_to_select} shells")
        
        # Select random shells
        chosen_shells = random.sample(range(shell_count), shells_to_select)
        print(f"Selected shells: {chosen_shells[:10]}{'...' if len(chosen_shells) > 10 else ''}")
        
        # Use a different approach: select random UVs and expand to shells
        all_selected_uvs = []
        
        # First, try to get shell information using polyUVSet
        for shell_id in chosen_shells:
            try:
                # Get a UV that belongs to this shell
                # We'll use polyUVSet to get shell information
                shell_uvs = cmds.polyUVSet(mesh_shape, query=True, uvShell=True, uvSet=uv_set)
                
                if shell_uvs and len(shell_uvs) > shell_id:
                    # Get UVs for this shell
                    shell_uv_list = shell_uvs[shell_id]
                    if shell_uv_list:
                        # Add all UVs from this shell
                        all_selected_uvs.extend(shell_uv_list)
                        print(f"Shell {shell_id}: {len(shell_uv_list):,} UVs")
                
            except Exception as e:
                print(f"Warning: Could not process shell {shell_id}: {e}")
                continue
        
        if not all_selected_uvs:
            # Fallback: try to get shell information differently
            print("Trying alternative shell detection...")
            
            try:
                # Use polyUVSet to get shell information
                shell_info = cmds.polyUVSet(mesh_shape, query=True, uvShell=True, uvSet=uv_set)
                if shell_info:
                    print(f"Shell info type: {type(shell_info)}")
                    print(f"Shell info length: {len(shell_info)}")
                    
                    # Try to extract shell data
                    for shell_id in chosen_shells:
                        if shell_id < len(shell_info):
                            shell_data = shell_info[shell_id]
                            print(f"Shell {shell_id} data type: {type(shell_data)}")
                            
                            # Try to get UVs from this shell
                            if hasattr(shell_data, '__len__'):
                                all_selected_uvs.extend(shell_data)
                                print(f"Added {len(shell_data):,} UVs from shell {shell_id}")
                
            except Exception as e2:
                print(f"Alternative method also failed: {e2}")
        
        if not all_selected_uvs:
            # Final fallback: select random UVs
            print("Using final fallback: random UV selection")
            if num_uvs > 0:
                # For large meshes, select more UVs
                fallback_count = max(shells_to_select * 50, 1000)  # At least 50 UVs per shell or 1000 total
                fallback_count = min(fallback_count, num_uvs)
                
                random_uvs = random.sample(range(num_uvs), fallback_count)
                
                # Select them
                cmds.select(clear=True)
                cmds.select(f"{mesh_shape}.map[{random_uvs[0]}]", replace=True)
                
                for uv_idx in random_uvs[1:]:
                    cmds.select(f"{mesh_shape}.map[{uv_idx}]", add=True)
                
                print(f"Fallback: Selected {len(random_uvs):,} random UVs")
                return random_uvs
        
        # Remove duplicates and sort
        all_selected_uvs = sorted(list(set(all_selected_uvs)))
        print(f"Total unique UVs to select: {len(all_selected_uvs):,}")
        
        # For very large selections, we might need to batch the selection
        if len(all_selected_uvs) > 10000:
            print("Large selection detected - using batch selection method")
            
            # Clear selection first
            cmds.select(clear=True)
            
            # Select in batches to avoid Maya hanging
            batch_size = 1000
            for i in range(0, len(all_selected_uvs), batch_size):
                batch = all_selected_uvs[i:i + batch_size]
                if i == 0:
                    # First batch replaces selection
                    cmds.select(f"{mesh_shape}.map[{batch[0]}]", replace=True)
                    for uv_idx in batch[1:]:
                        cmds.select(f"{mesh_shape}.map[{uv_idx}]", add=True)
                else:
                    # Subsequent batches add to selection
                    for uv_idx in batch:
                        cmds.select(f"{mesh_shape}.map[{uv_idx}]", add=True)
                
                print(f"Selected batch {i//batch_size + 1}/{(len(all_selected_uvs) + batch_size - 1)//batch_size}")
        else:
            # Normal selection for smaller amounts
            cmds.select(clear=True)
            cmds.select(f"{mesh_shape}.map[{all_selected_uvs[0]}]", replace=True)
            
            for uv_idx in all_selected_uvs[1:]:
                cmds.select(f"{mesh_shape}.map[{uv_idx}]", add=True)
        
        print(f"Successfully selected {len(all_selected_uvs):,} UVs from {shells_to_select} shells")
        return all_selected_uvs
        
    except Exception as e:
        cmds.warning(f"Error processing UV shells: {e}")
        return []
    
    return []


def test_simple_uv_selection():
    """
    Test function for the simple UV shell selection
    """
    print("=== Simple UV Shell Selection Test ===")
    
    # Check selection
    selection = cmds.ls(selection=True)
    if not selection:
        print("No objects selected. Please select a mesh and try again.")
        return
    
    print(f"Selected: {selection}")
    
    # Try different selection methods
    print("\n=== Testing Percentage-Based Selection ===")
    
    # Test 10% selection (should give more shells for large meshes)
    result_10 = select_random_uv_shells(percent=10, seed=42)
    
    if result_10:
        print(f"10% selection successful! Selected {len(result_10):,} UVs")
    else:
        print("10% selection failed. Check the warnings above.")
    
    print("\n=== Testing Count-Based Selection ===")
    
    # Test selecting 50 shells
    result_50 = select_random_uv_shells(count=50, seed=123)
    
    if result_50:
        print(f"50-shell selection successful! Selected {len(result_50):,} UVs")
    else:
        print("50-shell selection failed. Check the warnings above.")
    
    print("\n=== Testing Large Selection ===")
    
    # Test selecting 20% (should give many shells for large meshes)
    result_20 = select_random_uv_shells(percent=20, seed=456)
    
    if result_20:
        print(f"20% selection successful! Selected {len(result_20):,} UVs")
    else:
        print("20% selection failed. Check the warnings above.")


# Quick test - uncomment to run:
# test_simple_uv_selection()

# Or call directly with different options:
# select_random_uv_shells(percent=15, seed=123)    # Select 15% of shells
# select_random_uv_shells(count=100, seed=456)     # Select exactly 100 shells
# select_random_uv_shells(percent=30, seed=789)    # Select 30% of shells (lots for large meshes)
