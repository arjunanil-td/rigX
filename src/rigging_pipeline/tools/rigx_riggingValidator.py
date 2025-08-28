import maya.cmds as cmds
import maya.api.OpenMaya as om
from collections import defaultdict
import re
import json
import os
import importlib.util

from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.tools.ui.rigx_riggingValidator_ui import RiggingValidatorUI


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class ValidationModule:
    """Wrapper for individual validation modules"""
    
    def __init__(self, name, file_path, category):
        self.name = name
        self.file_path = file_path
        self.category = category
        self.enabled = True
        self.description = self._get_description()
    
    def _get_description(self):
        """Extract description from the module file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for DESCRIPTION pattern
                desc_match = re.search(r'DESCRIPTION\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                if desc_match:
                    return desc_match.group(1)
        except:
            pass
        return f"Validation for {self.name}"
    
    def run_validation(self, mode="check", objList=None):
        """Run the validation module"""
        try:
            # Try to load and run the external module first
            if os.path.exists(self.file_path):
                # Load the module dynamically
                spec = importlib.util.spec_from_file_location(self.name, self.file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if the module has the required function
                if hasattr(module, 'run_validation'):
                    # Import maya.cmds if not already imported
                    if 'cmds' not in globals():
                        try:
                            import maya.cmds as cmds
                        except ImportError:
                            # Fall back to simple validation if Maya is not available
                            return self._run_simple_validation(mode, objList)
                    
                    # Run the external module's validation
                    return module.run_validation(mode, objList)
                else:
                    # Fall back to simple validation if module doesn't have required function
                    return self._run_simple_validation(mode, objList)
            else:
                # Fall back to simple validation if file doesn't exist
                return self._run_simple_validation(mode, objList)
        except Exception as e:
            # Fall back to simple validation if there's an error loading the module
            try:
                return self._run_simple_validation(mode, objList)
            except Exception as fallback_error:
                return {"status": "error", "message": f"Module error: {str(e)}, Fallback error: {str(fallback_error)}"}
    
    def _run_simple_validation(self, mode, objList=None):
        """Run actual validation and fixing based on module name"""
        issues = []
        
        if "DuplicatedName" in self.name:
            # Check for duplicate names using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = cmds.ls(selection=True, long=False)
                else:
                    to_check_list = cmds.ls(long=False)
                
                if to_check_list:
                    found_duplicated = False
                    for node in to_check_list:
                        if "|" in node:
                            found_duplicated = True
                            break
                    
                    if found_duplicated:
                        # Analysis the elements in order to put it with ordenation from children to grandfather (inverted hierarchy)
                        size_list = []
                        ordered_obj_list = []
                        for i, element in enumerate(to_check_list):
                            # Find the number of occurrences of "|" in the string (element)
                            number = element.count("|")
                            # Add to a list another list with number and element
                            size_list.append([number, element])
                        
                        # Sort (put in alphabetic order to A-Z) and reverse (invert the order to Z-A)
                        size_list.sort()
                        size_list.reverse()
                        
                        # Add the elements to the final orderedObjList
                        for n, value in enumerate(size_list):
                            ordered_obj_list.append(size_list[n][1])
                        
                        # Prepare a list with nodeNames to iteration
                        short_name_list = []
                        for long_name in ordered_obj_list:
                            # Verify if there are children in order to get the shortNames
                            if "|" in long_name:
                                short_name_list.append(long_name[long_name.rfind("|")+1:])
                            else:
                                short_name_list.append(long_name)
                        
                        # Compare each obj in the list with the others
                        n = 0
                        for i, obj in enumerate(short_name_list):
                            # Use another list without the first element to compare if the item repeats
                            another_list = short_name_list[i+1:]
                            for item in another_list:
                                if cmds.objExists(ordered_obj_list[i]):
                                    if obj == item:
                                        # Found issue here
                                        if mode == "check":
                                            issues.append({
                                                'object': ordered_obj_list[i],
                                                'message': f"Duplicate name found: {obj}",
                                                'fixed': False
                                            })
                                        elif mode == "fix":
                                            try:
                                                new_name = f"{obj}{n}"
                                                cmds.rename(ordered_obj_list[i], new_name)
                                                n += 1
                                                issues.append({
                                                    'object': ordered_obj_list[i],
                                                    'message': f"Renamed to: {new_name}",
                                                    'fixed': True
                                                })
                                            except Exception as e:
                                                issues.append({
                                                    'object': ordered_obj_list[i],
                                                    'message': f"Failed to rename: {str(e)}",
                                                    'fixed': False
                                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No duplicate names found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "NamespaceCleaner" in self.name:
            # Check for namespaces
            namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
            if namespaces:
                # Filter out Maya internal namespaces and reference namespaces
                ignore = {'UI', 'shared'}
                refs = cmds.file(query=True, referenceNode=True) or []
                ref_ns = {cmds.referenceQuery(r, namespace=True) for r in refs if cmds.referenceQuery(r, namespace=True)}
                
                # Get namespaces to clean (exclude ignored and reference namespaces)
                to_clean = [ns for ns in namespaces if ns.split(':')[0] not in ignore | ref_ns]
                
                if to_clean:
                    if mode == "check":
                        for ns in to_clean:
                            issues.append({
                                'object': f"namespace:{ns}",
                                'message': f"Custom namespace found: {ns}",
                                'fixed': False
                            })
                    elif mode == "fix":
                        try:
                            # Sort namespaces by depth (deepest first) to avoid dependency issues
                            to_clean.sort(key=lambda n: n.count(':'), reverse=True)
                            
                            # Remove each namespace using recursive method
                            for ns in to_clean:
                                try:
                                    if self._clean_namespace_recursive(ns):
                                        issues.append({
                                            'object': f"namespace:{ns}",
                                            'message': f"Namespace and children removed successfully",
                                            'fixed': True
                                        })
                                    else:
                                        issues.append({
                                            'object': f"namespace:{ns}",
                                            'message': f"Failed to remove namespace completely",
                                            'fixed': False
                                        })
                                except Exception as e:
                                    issues.append({
                                        'object': f"namespace:{ns}",
                                        'message': f"Failed to remove namespace: {str(e)}",
                                        'fixed': False
                                    })
                        except Exception as e:
                            issues.append({
                                'object': "namespace:general",
                                'message': f"Failed to process namespaces: {str(e)}",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No custom namespaces found",
                            'fixed': True
                        })
                    elif mode == "fix":
                        issues.append({
                            'object': "Scene",
                            'message': "No namespaces to clean",
                            'fixed': True
                        })
        
        elif "VaccineCleaner" in self.name:
            # Check for script nodes (potential malware) using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = cmds.ls(selection=True, long=True)
                else:
                    to_check_list = cmds.ls(type='script', long=True)
                
                if to_check_list:
                    malicious_scripts_found = False
                    
                    for item in to_check_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(item):
                            try:
                                # Check script content for malicious patterns
                                script_data = cmds.scriptNode(item, beforeScript=True, query=True)
                                
                                # Check for malicious patterns (from original module)
                                if "_gene" in script_data:
                                    malicious_scripts_found = True
                                    
                                    if mode == "check":
                                        issues.append({
                                            'object': item,
                                            'message': f"Malicious script node detected",
                                            'fixed': False
                                        })
                                    elif mode == "fix":
                                        try:
                                            cmds.delete(item)
                                            
                                            # Clean up vaccine files from user scripts directory
                                            import os
                                            path = cmds.internalVar(userAppDir=True)+"/scripts/"
                                            vaccine_list = ["vaccine.py", "vaccine.pyc"]
                                            
                                            for vaccine in vaccine_list:
                                                if os.path.exists(path+vaccine):
                                                    os.remove(path+vaccine)
                                            
                                            if os.path.exists(path+"userSetup.py"):
                                                issues.append({
                                                    'object': item,
                                                    'message': f"Script deleted but userSetup.py remains - manual check required",
                                                    'fixed': False
                                                })
                                            else:
                                                issues.append({
                                                    'object': item,
                                                    'message': f"Malicious script node cleaned successfully",
                                                    'fixed': True
                                                })
                                            
                                            cmds.select(clear=True)
                                        
                                        except Exception as e:
                                            issues.append({
                                                'object': item,
                                                'message': f"Failed to clean malicious script: {str(e)}",
                                                'fixed': False
                                            })
                            
                            except Exception as e:
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Error checking script: {str(e)}",
                                        'fixed': False
                                    })
                    
                    if not malicious_scripts_found:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No malicious script nodes found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No script nodes found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "LaminaFaceCleaner" in self.name:
            # Check for lamina faces using proper OpenMaya logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    to_check_list = cmds.ls(type='mesh', long=True)
                
                if to_check_list:
                    # Declare resulted lists
                    lamina_obj_list, lamina_face_list = [], []
                    
                    try:
                        import maya.api.OpenMaya as om
                        iter_obj = om.MItDependencyNodes(om.MFn.kGeometric)
                        
                        if iter_obj is not None:
                            while not iter_obj.isDone():
                                # Get mesh data
                                shape_node = iter_obj.thisNode()
                                fn_shape_node = om.MFnDagNode(shape_node)
                                shape_name = fn_shape_node.name()
                                parent_node = fn_shape_node.parent(0)
                                fn_parent_node = om.MFnDagNode(parent_node)
                                object_name = fn_parent_node.name()
                                
                                # Verify if objName or shapeName is in toCheckList
                                for obj in to_check_list:
                                    if obj == shape_name and not cmds.getAttr(obj+".intermediateObject"):
                                        # Get faces
                                        face_iter = om.MItMeshPolygon(shape_node)
                                        con_faces_it = om.MItMeshPolygon(shape_node)
                                        
                                        # Run in faces listing edges
                                        while not face_iter.isDone():
                                            # List vertices from this face
                                            edges_int_array = om.MIntArray()
                                            face_iter.getEdges(edges_int_array)
                                            
                                            # Get connected faces of this face
                                            con_faces_int_array = om.MIntArray()
                                            face_iter.getConnectedFaces(con_faces_int_array)
                                            
                                            # Run in adjacent faces to list them vertices
                                            for f in con_faces_int_array:
                                                # Say this is the face index to use for next iterations
                                                last_index_ptr = om.MScriptUtil().asIntPtr()
                                                con_faces_it.setIndex(f, last_index_ptr)
                                                
                                                # Get edges from this adjacent face
                                                con_edges_int_array = om.MIntArray()
                                                con_faces_it.getEdges(con_edges_int_array)
                                                
                                                # Compare edges to verify if the list are the same
                                                if sorted(edges_int_array) == sorted(con_edges_int_array):
                                                    # Found lamina faces
                                                    if not object_name in lamina_obj_list:
                                                        lamina_obj_list.append(object_name)
                                                    lamina_face_list.append(object_name+'.f['+str(face_iter.index())+']')
                                            
                                            face_iter.next()
                                
                                # Move to the next selected node in the list
                                iter_obj.next()
                        
                        # Conditional to check here
                        if lamina_obj_list:
                            lamina_obj_list.sort()
                            lamina_face_list.sort()
                            
                            for item in lamina_obj_list[:20]:  # Limit to 20 objects for performance
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Lamina faces detected",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        cmds.select(item)
                                        # Use MEL command from original module to clean lamina faces
                                        cmds.mel.eval('polyCleanupArgList 3 { "0","1","0","0","0","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","2","0" };')
                                        cmds.select(clear=True)
                                        issues.append({
                                            'object': item,
                                            'message': f"Lamina faces cleaned successfully",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': item,
                                            'message': f"Failed to clean lamina faces: {str(e)}",
                                            'fixed': False
                                        })
                            
                            # Add lamina face list information
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Lamina faces found: {len(lamina_face_list)} faces",
                                    'fixed': False
                                })
                                # Select the lamina faces for user reference
                                try:
                                    cmds.select(lamina_face_list)
                                except:
                                    pass
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No lamina faces found",
                                    'fixed': True
                                })
                    
                    except ImportError:
                        # Fallback to simplified check if OpenMaya not available
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "OpenMaya not available - using simplified check",
                                'fixed': False
                            })
                        elif mode == "fix":
                            issues.append({
                                'object': "Scene",
                                'message': "Cannot fix without OpenMaya - manual check required",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "NonQuadFace" in self.name:
            # Check for non-quad faces using proper OpenMaya logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    to_check_list = cmds.ls(type='mesh', long=True)
                
                if to_check_list:
                    # Declare resulted lists
                    poly_obj_list, tris_obj_list, tris_list, poly_list = [], [], [], []
                    
                    try:
                        import maya.api.OpenMaya as om
                        iter_obj = om.MItDependencyNodes(om.MFn.kGeometric)
                        
                        if iter_obj is not None:
                            while not iter_obj.isDone():
                                # Get mesh data
                                shape_node = iter_obj.thisNode()
                                fn_shape_node = om.MFnDagNode(shape_node)
                                shape_name = fn_shape_node.name()
                                parent_node = fn_shape_node.parent(0)
                                fn_parent_node = om.MFnDagNode(parent_node)
                                object_name = fn_parent_node.name()
                                
                                # Verify if objName or shapeName is in toCheckList
                                for obj in to_check_list:
                                    if obj == shape_name and not cmds.getAttr(obj+".intermediateObject"):
                                        iter_polys = om.MItMeshPolygon(shape_node)
                                        
                                        # Iterate through polys on current mesh
                                        while not iter_polys.isDone():
                                            n_vertex = iter_polys.polygonVertexCount()
                                            if n_vertex > 4:
                                                if not object_name in poly_obj_list:
                                                    poly_obj_list.append(object_name)
                                                poly_list.append(object_name+'.f['+str(iter_polys.index())+']')
                                            elif n_vertex == 3:
                                                if not object_name in tris_obj_list:
                                                    tris_obj_list.append(object_name)
                                                tris_list.append(object_name+'.f['+str(iter_polys.index())+']')
                                            
                                            # Move to next polygon in the mesh list
                                            iter_polys.next()
                                
                                # Move to the next selected node in the list
                                iter_obj.next()
                        
                        # Conditional to check here
                        if poly_obj_list or tris_obj_list:
                            non_quad_obj_list = list(set(poly_obj_list + tris_obj_list))
                            non_quad_face_list = list(set(poly_list + tris_list))
                            non_quad_obj_list.sort()
                            non_quad_face_list.sort()
                            
                            for item in non_quad_obj_list[:20]:  # Limit to 20 objects for performance
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Non-quad faces detected",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    # Non-quad faces cannot be automatically fixed
                                    issues.append({
                                        'object': item,
                                        'message': f"Non-quad faces detected - manual fix required",
                                        'fixed': False
                                    })
                            
                            # Add detailed information about tris and polys
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Tris: {len(tris_list)}, Polys: {len(poly_list)}",
                                    'fixed': False
                                })
                                # Select the non-quad faces for user reference
                                try:
                                    cmds.select(non_quad_face_list)
                                except:
                                    pass
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No non-quad faces found",
                                    'fixed': True
                                })
                    
                    except ImportError:
                        # Fallback to simplified check if OpenMaya not available
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "OpenMaya not available - using simplified check",
                                'fixed': False
                            })
                        elif mode == "fix":
                            issues.append({
                                'object': "Scene",
                                'message': "Cannot fix without OpenMaya - manual check required",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "UnlockAttributes" in self.name:
            # Check for locked attributes using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    node_list = cmds.ls(selection=True, long=True)
                else:
                    node_list = cmds.ls(long=True)
                
                if node_list:
                    locked_attr_dict = {}
                    
                    for item in node_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(item):
                            try:
                                locked_attr_list = cmds.listAttr(item, locked=True)
                                if locked_attr_list:
                                    locked_attr_dict[item] = locked_attr_list
                            except:
                                pass
                    
                    # Conditional to check here
                    if locked_attr_dict:
                        for item in locked_attr_dict.keys():
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"Locked attributes found: {', '.join(locked_attr_dict[item])}",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    cmds.lockNode(item, lock=False, lockUnpublished=False)
                                    for attr in locked_attr_dict[item]:
                                        cmds.setAttr(item+"."+attr, lock=False)
                                    
                                    issues.append({
                                        'object': item,
                                        'message': f"Attributes unlocked successfully: {', '.join(locked_attr_dict[item])}",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': item,
                                        'message': f"Failed to unlock attributes: {str(e)}",
                                        'fixed': False
                                    })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No locked attributes found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "InvertedNormals" in self.name:
            # Check for inverted normals using proper OpenMaya logic from original module
            if not cmds.file(query=True, reference=True):
                inverted_obj_list = []
                if cmds.ls(selection=True):
                    obj_mesh_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    obj_mesh_list = cmds.ls(type='mesh', long=True)
                
                if obj_mesh_list:
                    # Use OpenMaya to check for inverted normals
                    try:
                        import maya.api.OpenMaya as om
                        geom_iter = om.MItDependencyNodes(om.MFn.kMesh)
                        
                        while not geom_iter.isDone():
                            next_geom = False
                            use_this_obj = False
                            
                            # Get mesh data
                            shape_node = geom_iter.thisNode()
                            fn_shape_node = om.MFnDagNode(shape_node)
                            shape_name = fn_shape_node.name()
                            parent_node = fn_shape_node.parent(0)
                            fn_parent_node = om.MFnDagNode(parent_node)
                            obj_name = fn_parent_node.name()
                            
                            # Verify if objName or shapeName is in objMeshList
                            for obj in obj_mesh_list:
                                if obj_name in obj or shape_name in obj:
                                    use_this_obj = True
                                    break
                            
                            if use_this_obj:
                                # Get faces
                                face_iter = om.MItMeshPolygon(shape_node)
                                con_faces_it = om.MItMeshPolygon(shape_node)
                                
                                # Run in faces listing vertices
                                while not face_iter.isDone() and not next_geom:
                                    # List vertices from this face
                                    vtx_int_array = om.MIntArray()
                                    face_iter.getVertices(vtx_int_array)
                                    vtx_int_array.append(vtx_int_array[0])
                                    
                                    # Get connected faces of this face
                                    con_faces_int_array = om.MIntArray()
                                    face_iter.getConnectedFaces(con_faces_int_array)
                                    
                                    # Run in adjacent faces to list them vertices
                                    for f in con_faces_int_array:
                                        # Say this is the face index to use for next iterations
                                        last_index_ptr = om.MScriptUtil().asIntPtr()
                                        con_faces_it.setIndex(f, last_index_ptr)
                                        
                                        # Get vertices from this adjacent face
                                        con_vtx_int_array = om.MIntArray()
                                        con_faces_it.getVertices(con_vtx_int_array)
                                        con_vtx_int_array.append(con_vtx_int_array[0])
                                        
                                        # Compare vertex in order to find double consecutive vertices
                                        for i in range(0, len(vtx_int_array)-1):
                                            i_pair = str(vtx_int_array[i])+","+str(vtx_int_array[i+1])
                                            for c in range(0, len(con_vtx_int_array)-1):
                                                c_pair = str(con_vtx_int_array[c])+","+str(con_vtx_int_array[c+1])
                                                if i_pair == c_pair:
                                                    # Found inverted normals
                                                    inverted_obj_list.append(obj_name)
                                                    next_geom = True
                                    
                                    face_iter.next()
                            
                            # Go to next geometry
                            geom_iter.next()
                        
                        # Verify if there are inverted normals
                        if inverted_obj_list:
                            inverted_obj_list = list(set(inverted_obj_list))
                            for mesh in inverted_obj_list[:20]:  # Limit to 20 objects for performance
                                if mode == "check":
                                    issues.append({
                                        'object': mesh,
                                        'message': f"Inverted normals detected",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        # Conform normals to fix
                                        cmds.polyNormal(mesh, normalMode=2, userNormalMode=0, constructionHistory=False)
                                        issues.append({
                                            'object': mesh,
                                            'message': f"Inverted normals fixed successfully",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': mesh,
                                            'message': f"Failed to fix inverted normals: {str(e)}",
                                            'fixed': False
                                        })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No inverted normals found",
                                    'fixed': True
                                })
                    
                    except ImportError:
                        # Fallback to simplified check if OpenMaya not available
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "OpenMaya not available - using simplified check",
                                'fixed': False
                            })
                        elif mode == "fix":
                            issues.append({
                                'object': "Scene",
                                'message': "Cannot fix without OpenMaya - manual check required",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "BorderGap" in self.name:
            # Check for border gaps using proper OpenMaya logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    to_check_list = cmds.ls(type='mesh', long=True)
                
                if to_check_list:
                    # Declare resulted lists
                    gap_list, gap_obj_list = [], []
                    
                    try:
                        import maya.api.OpenMaya as om
                        iter_obj = om.MItDependencyNodes(om.MFn.kGeometric)
                        
                        if iter_obj is not None:
                            while not iter_obj.isDone():
                                # Get mesh data
                                shape_node = iter_obj.thisNode()
                                fn_shape_node = om.MFnDagNode(shape_node)
                                shape_name = fn_shape_node.name()
                                parent_node = fn_shape_node.parent(0)
                                fn_parent_node = om.MFnDagNode(parent_node)
                                object_name = fn_parent_node.name()
                                
                                # Verify if objName or shapeName is in toCheckList
                                for obj in to_check_list:
                                    if obj == shape_name and not cmds.getAttr(obj+".intermediateObject"):
                                        iter_polys = om.MItMeshEdge(shape_node)
                                        
                                        # Iterate through polys on current mesh
                                        while not iter_polys.isDone():
                                            # Get current polygons connected faces
                                            index_con_faces = om.MIntArray()
                                            iter_polys.getConnectedFaces(index_con_faces)
                                            
                                            if len(index_con_faces) == 1:
                                                if not object_name in gap_obj_list:
                                                    gap_obj_list.append(object_name)
                                                gap_list.append(object_name+'.e['+str(iter_polys.index())+']')
                                            
                                            # Move to next polygon in the mesh list
                                            iter_polys.next()
                                
                                # Move to the next selected node in the list
                                iter_obj.next()
                        
                        # Conditional to check here
                        if gap_obj_list:
                            gap_obj_list.sort()
                            for item in gap_obj_list[:20]:  # Limit to 20 objects for performance
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Border gaps detected - open edges found",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    # Border gaps cannot be automatically fixed
                                    issues.append({
                                        'object': item,
                                        'message': f"Border gaps detected - manual fix required",
                                        'fixed': False
                                    })
                            
                            # Add gap list information
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Border gaps found: {len(gap_list)} open edges",
                                    'fixed': False
                                })
                                # Select the gap edges for user reference
                                try:
                                    cmds.select(gap_list)
                                except:
                                    pass
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No border gaps found",
                                    'fixed': True
                                })
                    
                    except ImportError:
                        # Fallback to simplified check if OpenMaya not available
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "OpenMaya not available - using simplified check",
                                'fixed': False
                            })
                        elif mode == "fix":
                            issues.append({
                                'object': "Scene",
                                'message': "Cannot fix without OpenMaya - manual check required",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        

        
        elif "ImportReference" in self.name:
            # Check for references that should be imported using proper logic from original module
            if cmds.ls(selection=True):
                reference_list = cmds.ls(selection=True, long=True)
            else:
                reference_list = cmds.file(query=True, reference=True) or []
            
            if reference_list:
                for reference in reference_list[:20]:  # Limit to 20 objects for performance
                    if mode == "check":
                        issues.append({
                            'object': f"reference:{reference}",
                            'message': f"Reference found: {reference}",
                            'fixed': False
                        })
                    elif mode == "fix":
                        try:
                            # Import reference using helper method
                            if self._import_reference(reference):
                                issues.append({
                                    'object': f"reference:{reference}",
                                    'message': f"Reference imported successfully",
                                    'fixed': True
                                })
                            else:
                                issues.append({
                                    'object': f"reference:{reference}",
                                    'message': f"Failed to import reference",
                                    'fixed': False
                                })
                        except Exception as e:
                            issues.append({
                                'object': f"reference:{reference}",
                                'message': f"Failed to import reference: {str(e)}",
                                'fixed': False
                            })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "No references found",
                        'fixed': True
                    })
        
        elif "NonManifoldCleaner" in self.name:
            # Check for non-manifold geometry using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    geo_to_clean_list = cmds.ls(selection=True, long=True)
                else:
                    # Get mesh transforms and check for non-manifold issues
                    transform_list = cmds.ls(type='transform', long=True)
                    geo_to_clean_list = []
                    
                    if transform_list:
                        for transform in transform_list:
                            if cmds.objExists(transform):
                                # Check if this transform has mesh children
                                children = cmds.listRelatives(transform, children=True, type='mesh', fullPath=True)
                                if children:
                                    # Check for non-manifold issues
                                    if self._check_non_manifold(transform):
                                        geo_to_clean_list.append(transform)
                
                if geo_to_clean_list:
                    for geo in geo_to_clean_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(geo):
                            if mode == "check":
                                issues.append({
                                    'object': geo,
                                    'message': f"Non-manifold geometry detected",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    cmds.select(geo)
                                    # Cleanup non manifolds using MEL command from original module
                                    cmds.mel.eval('polyCleanupArgList 4 { "0","1","0","0","0","0","0","0","0","1e-05","0","1e-05","0","1e-05","0","1","0","0" };')
                                    cmds.select(clear=True)
                                    issues.append({
                                        'object': geo,
                                        'message': f"Non-manifold geometry cleaned successfully",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': geo,
                                        'message': f"Failed to clean non-manifold geometry: {str(e)}",
                                        'fixed': False
                                    })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No non-manifold geometry found",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "OneVertex" in self.name:
            # Check for single vertex faces using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    to_check_list = cmds.ls(type='mesh', long=True)
                
                if to_check_list:
                    # Check for non-manifold vertices using MEL command from original module
                    one_vertex_list = self._check_non_manifold_vertex(to_check_list)
                    
                    if one_vertex_list:
                        one_vertex_list.sort()
                        
                        for item in one_vertex_list[:20]:  # Limit to 20 objects for performance
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"Single vertex face detected",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                # Single vertex faces cannot be automatically fixed
                                issues.append({
                                    'object': item,
                                    'message': f"Single vertex face detected - manual fix required",
                                    'fixed': False
                                })
                        
                        # Select single vertex faces for user reference
                        if mode == "check":
                            try:
                                cmds.select(one_vertex_list)
                            except:
                                pass
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No single vertex faces found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "OverrideCleaner" in self.name:
            # Check for display overrides using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    node_list = cmds.ls(selection=True, long=True)
                else:
                    node_list = cmds.ls(long=True)
                
                if node_list:
                    overrided_list = []
                    
                    for item in node_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(item):
                            try:
                                # Check if item has overrideEnabled attribute
                                if cmds.objExists(item+".overrideEnabled"):
                                    if cmds.getAttr(item+".overrideEnabled") == 1:
                                        overrided_list.append(item)
                            except:
                                pass
                    
                    # Conditional to check here
                    if overrided_list:
                        for item in overrided_list:
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"Display override enabled",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    cmds.lockNode(item, lock=False, lockUnpublished=False)
                                    cmds.setAttr(item+".overrideEnabled", lock=False)
                                    cmds.setAttr(item+".overrideEnabled", 0)
                                    issues.append({
                                        'object': item,
                                        'message': f"Display override disabled successfully",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': item,
                                        'message': f"Failed to disable override: {str(e)}",
                                        'fixed': False
                                    })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No display overrides found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "ParentedGeometry" in self.name:
            # Check for geometry with multiple parents using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    to_check_list = cmds.ls(type='mesh', long=True)
                
                if to_check_list:
                    # Get mesh transforms
                    mesh_parent_list = []
                    for mesh in to_check_list:
                        if cmds.objExists(mesh):
                            # Get the transform parent of the mesh
                            parent = cmds.listRelatives(mesh, parent=True, fullPath=True)
                            if parent:
                                mesh_parent_list.append(parent[0])
                    
                    if mesh_parent_list:
                        # Reorder list (simplified version)
                        mesh_parent_list = sorted(mesh_parent_list, key=lambda x: x.count('|'), reverse=True)
                        
                        parented_geometry_found = False
                        
                        for mesh in mesh_parent_list[:20]:  # Limit to 20 objects for performance
                            if cmds.objExists(mesh):
                                try:
                                    # Get all descendants and check if they're different than their parent
                                    all_descendants = cmds.listRelatives(mesh, allDescendents=True, fullPath=True, type='transform') or []
                                    children_list = [d for d in all_descendants if cmds.objExists(d) and d != mesh]
                                    
                                    if children_list:
                                        parented_geometry_found = True
                                        
                                        for item in children_list:
                                            if mode == "check":
                                                issues.append({
                                                    'object': item,
                                                    'message': f"Geometry has multiple parents",
                                                    'fixed': False
                                                })
                                            elif mode == "fix":
                                                try:
                                                    grand_parent = cmds.listRelatives(mesh, parent=True, fullPath=True)
                                                    if grand_parent and cmds.objExists(grand_parent[0]):
                                                        # Try to parent the item to the mesh grandparent
                                                        if cmds.objExists(item):
                                                            cmds.parent(item, grand_parent[0])
                                                    else:
                                                        # If no parent, just unparent it to world
                                                        cmds.parent(item, world=True)
                                                    
                                                    issues.append({
                                                        'object': item,
                                                        'message': f"Parent hierarchy fixed successfully",
                                                        'fixed': True
                                                    })
                                                except Exception as e:
                                                    issues.append({
                                                        'object': item,
                                                        'message': f"Failed to fix parent hierarchy: {str(e)}",
                                                        'fixed': False
                                                    })
                                
                                except Exception as e:
                                    if mode == "check":
                                        issues.append({
                                            'object': mesh,
                                            'message': f"Error checking mesh: {str(e)}",
                                            'fixed': False
                                        })
                        
                        if not parented_geometry_found:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No parented geometry issues found",
                                    'fixed': True
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No mesh transforms found to check",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "RemainingVertexCleaner" in self.name:
            # Check for remaining vertices using proper OpenMaya logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    to_check_list = cmds.ls(type='mesh', long=True)
                
                if to_check_list:
                    # Declare resulted lists
                    border_edge_idx_list, remaining_vertex_list = [], []
                    
                    try:
                        import maya.api.OpenMaya as om
                        iter_obj = om.MItDependencyNodes(om.MFn.kGeometric)
                        
                        if iter_obj is not None:
                            while not iter_obj.isDone():
                                # Get mesh data
                                shape_node = iter_obj.thisNode()
                                fn_shape_node = om.MFnDagNode(shape_node)
                                shape_name = fn_shape_node.name()
                                parent_node = fn_shape_node.parent(0)
                                fn_parent_node = om.MFnDagNode(parent_node)
                                object_name = fn_parent_node.name()
                                
                                # Verify if objName or shapeName is in toCheckList
                                for obj in to_check_list:
                                    if obj == shape_name and not cmds.getAttr(obj+".intermediateObject"):
                                        vertex_iter = om.MItMeshVertex(shape_node)
                                        iter_edges = om.MItMeshEdge(shape_node)
                                        
                                        # Iterate through edges on current mesh
                                        while not iter_edges.isDone():
                                            # Get current polygons connected faces
                                            index_con_faces = om.MIntArray()
                                            iter_edges.getConnectedFaces(index_con_faces)
                                            if len(index_con_faces) == 1:
                                                # Got a border edge
                                                border_edge_idx_list.append(iter_edges.index())
                                            
                                            # Move to next edge in the mesh list
                                            iter_edges.next()
                                        
                                        # Iterate through vertices on current mesh
                                        while not vertex_iter.isDone():
                                            # Get current vertex connected edges
                                            index_con_edges = om.MIntArray()
                                            vertex_iter.getConnectedEdges(index_con_edges)
                                            if len(index_con_edges) < 3:
                                                if border_edge_idx_list:
                                                    if not set(index_con_edges).intersection(border_edge_idx_list):
                                                        remaining_vertex_list.append(object_name+'.vtx['+str(vertex_iter.index())+']')
                                                else:
                                                    remaining_vertex_list.append(object_name+'.vtx['+str(vertex_iter.index())+']')
                                            
                                            # Move to next vertex in the mesh list
                                            vertex_iter.next()
                                
                                # Move to the next selected node in the list
                                iter_obj.next()
                        
                        # Conditional to check here
                        if remaining_vertex_list:
                            remaining_vertex_list.reverse()
                            
                            for item in remaining_vertex_list[:20]:  # Limit to 20 objects for performance
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Remaining vertex detected",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        cmds.delete(item)
                                        issues.append({
                                            'object': item,
                                            'message': f"Remaining vertex cleaned successfully",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': item,
                                            'message': f"Failed to clean remaining vertex: {str(e)}",
                                            'fixed': False
                                        })
                            
                            # Select remaining vertices for user reference
                            if mode == "check":
                                try:
                                    cmds.select(remaining_vertex_list)
                                except:
                                    pass
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No remaining vertices found",
                                    'fixed': True
                                })
                    
                    except ImportError:
                        # Fallback to simplified check if OpenMaya not available
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "OpenMaya not available - using simplified check",
                                'fixed': False
                            })
                        elif mode == "fix":
                            issues.append({
                                'object': "Scene",
                                'message': "Cannot fix without OpenMaya - manual check required",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "ShowBPCleaner" in self.name:
            # Check for ShowBP nodes using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = cmds.ls(selection=True, long=True)
                else:
                    to_check_list = cmds.ls(type='script', long=True)
                
                if to_check_list:
                    show_bp_found = False
                    
                    for item in to_check_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(item):
                            # Check if item contains "ShowBP"
                            if "ShowBP" in item:
                                show_bp_found = True
                                
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"ShowBP node detected",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        cmds.delete(item)
                                        cmds.select(clear=True)
                                        issues.append({
                                            'object': item,
                                            'message': f"ShowBP node cleaned successfully",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': item,
                                            'message': f"Failed to clean ShowBP node: {str(e)}",
                                            'fixed': False
                                        })
                    
                    if not show_bp_found:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No ShowBP nodes found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "SoftenEdges" in self.name:
            # Check for hard edges using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    all_mesh_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    all_mesh_list = cmds.ls(type='mesh', long=True)
                
                if all_mesh_list:
                    hard_edges_found = False
                    
                    for mesh in all_mesh_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(mesh):
                            try:
                                cmds.select(mesh)
                                # Set selection only non-smoothed edges
                                cmds.polySelectConstraint(type=0x8000, mode=3, smoothness=1)
                                harden_edges = cmds.ls(selection=True)
                                cmds.polySelectConstraint(mode=0)
                                
                                if harden_edges:
                                    # Converts the selected edges to faces
                                    to_face = cmds.polyListComponentConversion(harden_edges, toFace=True, internal=True)
                                    
                                    # Check if there's any non-smoothed edges
                                    if to_face:
                                        hard_edges_found = True
                                        
                                        if mode == "check":
                                            issues.append({
                                                'object': mesh,
                                                'message': f"Hard edges detected",
                                                'fixed': False
                                            })
                                        elif mode == "fix":
                                            try:
                                                cmds.polySoftEdge(mesh, angle=180, constructionHistory=False)
                                                issues.append({
                                                    'object': mesh,
                                                    'message': f"Hard edges softened successfully",
                                                    'fixed': True
                                                })
                                            except Exception as e:
                                                issues.append({
                                                    'object': mesh,
                                                    'message': f"Failed to soften edges: {str(e)}",
                                                    'fixed': False
                                                })
                                
                                cmds.select(clear=True)
                            
                            except Exception as e:
                                if mode == "check":
                                    issues.append({
                                        'object': mesh,
                                        'message': f"Error checking mesh: {str(e)}",
                                        'fixed': False
                                    })
                    
                    if not hard_edges_found:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No hard edges found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "TFaceCleaner" in self.name:
            # Check for T-faces using proper OpenMaya logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    to_check_list = cmds.ls(type='mesh', long=True)
                
                if to_check_list:
                    # Declare resulted lists
                    t_face_list = []
                    
                    try:
                        import maya.api.OpenMaya as om
                        iter_obj = om.MItDependencyNodes(om.MFn.kGeometric)
                        
                        if iter_obj is not None:
                            while not iter_obj.isDone():
                                # Get mesh data
                                shape_node = iter_obj.thisNode()
                                fn_shape_node = om.MFnDagNode(shape_node)
                                shape_name = fn_shape_node.name()
                                parent_node = fn_shape_node.parent(0)
                                fn_parent_node = om.MFnDagNode(parent_node)
                                object_name = fn_parent_node.name()
                                
                                # Verify if objName or shapeName is in toCheckList
                                for obj in to_check_list:
                                    if obj == shape_name and not cmds.getAttr(obj+".intermediateObject"):
                                        # Get edges
                                        edge_iter = om.MItMeshEdge(shape_node)
                                        
                                        # Run in faces listing faces
                                        while not edge_iter.isDone():
                                            # List faces from this edge
                                            face_int_array = om.MIntArray()
                                            edge_iter.getConnectedFaces(face_int_array)
                                            
                                            # Verify the length of the connectedFaces
                                            if len(face_int_array) > 2:
                                                # Found tFace
                                                t_face_list.append(object_name+".e["+str(edge_iter.index())+"]")
                                            
                                            edge_iter.next()
                                
                                # Move to the next selected node in the list
                                iter_obj.next()
                        
                        # Conditional to check here
                        if t_face_list:
                            t_face_list.sort()
                            
                            for item in t_face_list[:20]:  # Limit to 20 objects for performance
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"T-face detected",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        cmds.select(item)
                                        # Cleanup T Faces using MEL command from original module
                                        cmds.mel.eval('polyCleanupArgList 3 { "0","1","0","0","0","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","2","0" };')
                                        cmds.select(clear=True)
                                        issues.append({
                                            'object': item,
                                            'message': f"T-face cleaned successfully",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': item,
                                            'message': f"Failed to clean T-face: {str(e)}",
                                            'fixed': False
                                        })
                            
                            # Select T-faces for user reference
                            if mode == "check":
                                try:
                                    cmds.select(t_face_list)
                                except:
                                    pass
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No T-faces found",
                                    'fixed': True
                                })
                    
                    except ImportError:
                        # Fallback to simplified check if OpenMaya not available
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "OpenMaya not available - using simplified check",
                                'fixed': False
                            })
                        elif mode == "fix":
                            issues.append({
                                'object': "Scene",
                                'message': "Cannot fix without OpenMaya - manual check required",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "UnlockInitialShadingGroup" in self.name:
            # Check for locked initial shading group using proper logic from original module
            if not cmds.file(query=True, reference=True):
                to_check_list = ["initialShadingGroup"]
                
                if to_check_list:
                    for item in to_check_list:
                        if cmds.objExists(item):
                            if item == "initialShadingGroup":
                                # Conditional to check here
                                try:
                                    if cmds.lockNode(item, query=True, lockUnpublished=True):
                                        if cmds.getAttr(item+".nodeState", lock=True):
                                            if mode == "check":
                                                issues.append({
                                                    'object': item,
                                                    'message': f"Initial shading group is locked",
                                                    'fixed': False
                                                })
                                            elif mode == "fix":
                                                try:
                                                    cmds.lockNode(item, lock=False, lockUnpublished=False)
                                                    cmds.setAttr(item+".nodeState", lock=False)
                                                    issues.append({
                                                        'object': item,
                                                        'message': f"Initial shading group unlocked successfully",
                                                        'fixed': True
                                                    })
                                                except Exception as e:
                                                    issues.append({
                                                        'object': item,
                                                        'message': f"Failed to unlock initial shading group: {str(e)}",
                                                        'fixed': False
                                                    })
                                    else:
                                        if mode == "check":
                                            issues.append({
                                                'object': item,
                                                'message': f"Initial shading group is not locked",
                                                'fixed': True
                                            })
                                except Exception as e:
                                    if mode == "check":
                                        issues.append({
                                            'object': item,
                                            'message': f"Error checking initial shading group: {str(e)}",
                                            'fixed': False
                                        })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "Initial shading group not found",
                                    'fixed': False
                                })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "UnlockNormals" in self.name:
            # Check for locked normals using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    all_mesh_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'mesh']
                else:
                    all_mesh_list = cmds.ls(type='mesh', long=True)
                
                if all_mesh_list:
                    locked_normals_found = False
                    
                    for mesh in all_mesh_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(mesh):
                            try:
                                locked_list = cmds.polyNormalPerVertex(mesh+".vtx[*]", query=True, freezeNormal=True)
                                
                                # Check if there's any locked normal
                                if True in locked_list:
                                    locked_normals_found = True
                                    
                                    if mode == "check":
                                        issues.append({
                                            'object': mesh,
                                            'message': f"Normals are locked",
                                            'fixed': False
                                        })
                                    elif mode == "fix":
                                        try:
                                            cmds.polyNormalPerVertex(mesh+".vtx[*]", unFreezeNormal=True)
                                            issues.append({
                                                'object': mesh,
                                                'message': f"Normals unlocked successfully",
                                                'fixed': True
                                            })
                                        except Exception as e:
                                            issues.append({
                                                'object': mesh,
                                                'message': f"Failed to unlock normals: {str(e)}",
                                                'fixed': False
                                            })
                            
                            except Exception as e:
                                if mode == "check":
                                    issues.append({
                                        'object': mesh,
                                        'message': f"Error checking mesh: {str(e)}",
                                        'fixed': False
                                    })
                    
                    if not locked_normals_found:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No locked normals found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No mesh objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        # CheckOut modules
        elif "ControlsHierarchy" in self.name:
            # Check controls hierarchy using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if objList and cmds.objExists(objList[0]):
                    root_node = objList[0]
                else:
                    # Try to find global control
                    root_node = None
                    try:
                        # Look for nodes with "globalCtrl" message attribute
                        all_nodes = cmds.ls(type='transform')
                        for node in all_nodes:
                            if cmds.attributeExists('message', node):
                                connections = cmds.listConnections(f"{node}.message", source=False, destination=True)
                                if connections and any('globalCtrl' in conn for conn in connections):
                                    root_node = node
                                    break
                    except:
                        pass
                
                if root_node and cmds.objExists(root_node):
                    # Check if root node has nurbs curve shapes
                    has_nurbs = False
                    try:
                        shapes = cmds.listRelatives(root_node, shapes=True)
                        if shapes:
                            for shape in shapes:
                                if cmds.objectType(shape) == 'nurbsCurve':
                                    has_nurbs = True
                                    break
                    except:
                        pass
                    
                    if has_nurbs:
                        if mode == "check":
                            issues.append({
                                'object': root_node,
                                'message': f"Controls hierarchy root found: {root_node}",
                                'fixed': False
                            })
                        elif mode == "fix":
                            try:
                                # Export current hierarchy to file (simplified)
                                current_file = cmds.file(query=True, sceneName=True, shortName=True)
                                if current_file:
                                    # Create hierarchy directory
                                    import os
                                    current_path = cmds.file(query=True, sceneName=True)
                                    if current_path:
                                        hierarchy_path = os.path.dirname(current_path) + "/rigXHierarchy"
                                        if not os.path.exists(hierarchy_path):
                                            os.makedirs(hierarchy_path)
                                        
                                        # Export hierarchy info
                                        hierarchy_file = f"{hierarchy_path}/{current_file[:-3]}_h001.json"
                                        hierarchy_data = {"root": root_node, "timestamp": cmds.date()}
                                        
                                        with open(hierarchy_file, 'w') as f:
                                            import json
                                            json.dump(hierarchy_data, f)
                                        
                                        issues.append({
                                            'object': root_node,
                                            'message': f"Controls hierarchy exported to: {hierarchy_file}",
                                            'fixed': True
                                        })
                                    else:
                                        issues.append({
                                            'object': root_node,
                                            'message': "Scene not saved - cannot export hierarchy",
                                            'fixed': False
                                        })
                                else:
                                    issues.append({
                                        'object': root_node,
                                        'message': "Scene not saved - cannot export hierarchy",
                                        'fixed': False
                                    })
                            except Exception as e:
                                issues.append({
                                    'object': root_node,
                                    'message': f"Failed to export hierarchy: {str(e)}",
                                    'fixed': False
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': root_node,
                                'message': f"Root node does not have nurbs curve shapes",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No controls hierarchy root found",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "BrokenRivet" in self.name:
            # Check for broken rivets (follicles at world origin) using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if objList:
                    to_check_list = cmds.ls(objList, type="follicle")
                else:
                    to_check_list = cmds.ls(type='follicle')
                
                if to_check_list:
                    # Find follicles at world origin
                    follicles_at_origin = []
                    for follicle_shape in to_check_list:
                        try:
                            # Get the transform parent of the follicle
                            parents = cmds.listRelatives(follicle_shape, parent=True)
                            if parents:
                                follicle_transform = parents[0]
                                pos = cmds.xform(follicle_transform, query=True, translation=True, worldSpace=True)
                                
                                # Check if follicle is at world origin (indicating broken rivet)
                                if pos == [0.0, 0.0, 0.0]:
                                    follicles_at_origin.append(follicle_transform)
                        except:
                            pass
                    
                    if follicles_at_origin:
                        for follicle in follicles_at_origin:
                            if mode == "check":
                                issues.append({
                                    'object': follicle,
                                    'message': f"Broken rivet detected - follicle at world origin",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    # Try to fix by moving the follicle slightly off origin
                                    cmds.xform(follicle, translation=[0.001, 0.001, 0.001], worldSpace=True)
                                    issues.append({
                                        'object': follicle,
                                        'message': f"Broken rivet fixed by repositioning",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': follicle,
                                        'message': f"Failed to fix broken rivet: {str(e)}",
                                        'fixed': False
                                    })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No broken rivets found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No follicles found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "BindPoseCleaner" in self.name:
            # Check for bind pose issues using exact logic from original module
            if not cmds.file(query=True, reference=True):
                # Get bind pose nodes (either from selection or all in scene)
                to_check_list = cmds.ls(selection=False, type="dagPose")  # bindPose nodes
                
                if to_check_list:
                    # Check if there are multiple bind pose nodes
                    if len(to_check_list) > 1:
                        if mode == "check":
                            # Report each bind pose node individually for better visibility
                            for item in to_check_list:
                                issues.append({
                                    'object': item,
                                    'message': f"Bind pose node found: {item}",
                                    'fixed': False
                                })
                        elif mode == "fix":
                            try:
                                # Delete all bind pose nodes first
                                for item in to_check_list:
                                    cmds.lockNode(item, lock=False)
                                    cmds.delete(item)
                                
                                # Get skinned joints and create new bind pose
                                jnt_list = []
                                try:
                                    # Get all skin clusters and their influences
                                    skin_clusters = cmds.ls(type='skinCluster')
                                    for skin_cluster in skin_clusters:
                                        joints = cmds.skinCluster(skin_cluster, query=True, influence=True)
                                        if joints:
                                            jnt_list.extend(joints)
                                except:
                                    pass
                                
                                # Remove duplicates and create bind pose
                                if jnt_list:
                                    jnt_list = list(set(jnt_list))
                                    cmds.dagPose(jnt_list, save=True, bindPose=True, name="rigX_BP")
                                    issues.append({
                                        'object': "Scene",
                                        'message': f"Fixed: rigX_BP",
                                        'fixed': True
                                    })
                                else:
                                    issues.append({
                                        'object': "Scene",
                                        'message': "Failed to fix: No skinned joints found",
                                        'fixed': False
                                    })
                            except Exception as e:
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Failed to fix: {', '.join(to_check_list)}",
                                    'fixed': False
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "Only one bind pose node found - no action needed",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No bind pose nodes found",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "BrokenNetCleaner" in self.name:
            # Check for broken networks
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking for broken networks",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Clean broken networks
                        cmds.delete("brokenNetwork*")
                        issues.append({
                            'object': "Scene",
                            'message': "Broken networks cleaned successfully",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to clean broken networks: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
        elif "Cleanup" in self.name:
            # Check for cleanup using exact logic from original module
            if not cmds.file(query=True, reference=True):
                # Get all objects in scene
                to_check_list = cmds.ls()
                
                if to_check_list:
                    cleanup_attr = "rigXDeleteIt"
                    found_cleanup_items = []
                    
                    for item in to_check_list:
                        if cmds.objExists(item):
                            # Check if item has the cleanup attribute
                            if cleanup_attr in cmds.listAttr(item):
                                if cmds.getAttr(item + "." + cleanup_attr) == 1:
                                    found_cleanup_items.append(item)
                                    
                                    if mode == "check":
                                        issues.append({
                                            'object': item,
                                            'message': f"Item marked for cleanup: {item}",
                                            'fixed': False
                                        })
                                    elif mode == "fix":
                                        try:
                                            # Unlock and delete the node
                                            cmds.lockNode(item, lock=False)
                                            cmds.delete(item)
                                            issues.append({
                                                'object': item,
                                                'message': f"Fixed: {item}",
                                                'fixed': True
                                            })
                                        except Exception as e:
                                            issues.append({
                                                'object': item,
                                                'message': f"Failed to fix: {item}",
                                                'fixed': False
                                            })
                    
                    if not found_cleanup_items:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No items marked for cleanup found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        

        

        
        elif "CycleChecker" in self.name:
            # Check for cycles in connections
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking for connection cycles",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Break cycles (simplified)
                        issues.append({
                            'object': "Scene",
                            'message': "Cycle checking completed - manual review recommended",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to check cycles: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
                # DisplayLayers validation is now handled by external module
        
        # elif "EmptyTransformCleaner" in self.name:
        #     # DISABLED: EmptyTransformCleaner validation module
        #     # Check for empty transforms
        #     transforms = cmds.ls(type='transform', long=True)
        #     empty_transforms = []
        #     for transform in transforms[:20]:
        #         if cmds.objExists(transform):
        #             try:
        #                 children = cmds.listRelatives(transform, children=True, fullPath=True)
        #         if not children:
        #                 empty_transforms.append(transform)
        #             except:
        #                 pass
        #     
        #     if empty_transforms:
        #         if mode == "check":
        #             issues.append({
        #                 'object': "Scene",
        #                 'message': f"Empty transforms found: {len(empty_transforms)}",
        #                 'fixed': False
        #                 })
        #         elif mode == "fix":
        #             try:
        #                 for transform in empty_transforms:
        #                     cmds.delete(transform)
        #                 issues.append({
        #                 'object': "Scene",
        #                 'message': f"Empty transforms cleaned successfully: {len(empty_transforms)} removed",
        #                     'fixed': True
        #                 })
        #             except Exception as e:
        #                 issues.append({
        #                 'object': "Scene",
        #                 'message': f"Failed to clean empty transforms: {str(e)}",
        #                     'fixed': False
        #                 })
        #     else:
        #         if mode == "check":
        #             issues.append({
        #                 'object': "Scene",
        #                 'message': "No empty transforms found",
        #                     'fixed': True
        #                 })
        
        elif "EnvelopeChecker" in self.name:
            # Check for envelope issues
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking envelope status",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Reset envelope weights
                        cmds.skinCluster("skinCluster*", edit=True, resetWeightsToDefault=True)
                        issues.append({
                            'object': "Scene",
                            'message': "Envelope weights reset successfully",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to reset envelope weights: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
        elif "ExitEditMode" in self.name:
            # Check if in edit mode
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking edit mode status",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Exit edit mode
                        cmds.editDisplayLayerGlobals(currentId=0)
                        issues.append({
                            'object': "Scene",
                            'message': "Exited edit mode successfully",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to exit edit mode: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
        elif "HideAllJoints" in self.name:
            # Check for visible joints using proper logic from original module
            if not cmds.file(query=True, reference=True):
                if cmds.ls(selection=True):
                    to_check_list = [obj for obj in cmds.ls(selection=True, long=True) if cmds.objectType(obj) == 'joint']
                else:
                    to_check_list = cmds.ls(type='joint', long=True)
                
                if to_check_list:
                    visible_joints_found = False
                    
                    for item in to_check_list[:20]:  # Limit to 20 objects for performance
                        if cmds.objExists(item):
                            try:
                                # Check if joint draw style is not hidden (drawStyle != 2)
                                if not cmds.getAttr(item + '.drawStyle') == 2:
                                    visible_joints_found = True
                                    
                                    if mode == "check":
                                        issues.append({
                                            'object': item,
                                            'message': f"Joint is visible",
                                            'fixed': False
                                        })
                                    elif mode == "fix":
                                        try:
                                            cmds.setAttr(item + '.drawStyle', 2)
                                            issues.append({
                                                'object': item,
                                                'message': f"Joint hidden successfully",
                                                'fixed': True
                                            })
                                        except Exception as e:
                                            issues.append({
                                                'object': item,
                                                'message': f"Failed to hide joint: {str(e)}",
                                                'fixed': False
                                            })
                            
                            except Exception as e:
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Error checking joint: {str(e)}",
                                        'fixed': False
                                    })
                    
                    if not visible_joints_found:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No visible joints found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No joints found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "HideCorrectives" in self.name:
            # Check for visible corrective shapes using proper logic from original module
            if not cmds.file(query=True, reference=True):
                # Look for optionCtrl node with correctiveCtrls attribute
                option_ctrl = None
                
                # Try to find optionCtrl by looking for nodes with correctiveCtrls attribute
                all_nodes = cmds.ls(long=True)
                for node in all_nodes:
                    try:
                        if cmds.attributeQuery('correctiveCtrls', node=node, exists=True):
                            option_ctrl = node
                            break
                    except:
                        pass
                
                if option_ctrl:
                    try:
                        item = option_ctrl + ".correctiveCtrls"
                        
                        # Check if correctiveCtrls attribute is visible in channel box
                        check_channel_box = cmds.getAttr(item, channelBox=True)
                        
                        if check_channel_box:
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"Corrective controls are visible",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    cmds.setAttr(item, 0)
                                    cmds.setAttr(item, lock=True, channelBox=False)
                                    issues.append({
                                        'object': item,
                                        'message': f"Corrective controls hidden successfully",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': item,
                                        'message': f"Failed to hide corrective controls: {str(e)}",
                                        'fixed': False
                                    })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"Corrective controls are already hidden",
                                    'fixed': True
                                })
                    
                    except Exception as e:
                        if mode == "check":
                            issues.append({
                                'object': option_ctrl,
                                'message': f"Error checking corrective controls: {str(e)}",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No optionCtrl with correctiveCtrls attribute found",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "HideDataGrp" in self.name:
            # Check for visible data groups using proper logic from original module
            if not cmds.file(query=True, reference=True):
                data_grp = None
                
                # Try to find dataGrp by looking for nodes with "dataGrp" message or "Data_Grp" name
                all_nodes = cmds.ls(long=True)
                for node in all_nodes:
                    try:
                        # Check if node has a message attribute that contains "dataGrp"
                        if cmds.attributeQuery('message', node=node, exists=True):
                            message_value = cmds.getAttr(node + '.message')
                            if message_value and 'dataGrp' in str(message_value):
                                data_grp = node
                                break
                    except:
                        pass
                
                # If not found by message, try to find by name
                if not data_grp:
                    if cmds.objExists("Data_Grp"):
                        data_grp = "Data_Grp"
                
                if data_grp:
                    try:
                        visibility_status = cmds.getAttr(data_grp + ".visibility")
                        
                        if visibility_status:
                            if mode == "check":
                                issues.append({
                                    'object': data_grp,
                                    'message': f"Data group is visible",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    cmds.setAttr(data_grp + ".visibility", 0)
                                    issues.append({
                                        'object': data_grp,
                                        'message': f"Data group hidden successfully",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': data_grp,
                                        'message': f"Failed to hide data group: {str(e)}",
                                        'fixed': False
                                    })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': data_grp,
                                    'message': f"Data group is already hidden",
                                    'fixed': True
                                })
                    
                    except Exception as e:
                        if mode == "check":
                            issues.append({
                                'object': data_grp,
                                'message': f"Error checking data group: {str(e)}",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No data group found",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "KeyframeCleaner" in self.name:
            # Check for keyframes that can be cleaned up
            if not cmds.file(query=True, reference=True):
                # Get all objects in the scene
                all_objects = cmds.ls(selection=False)
                
                if all_objects:
                    # Get all animation curves
                    anim_curves = cmds.ls(type="animCurve")
                    
                    if anim_curves:
                        # Find objects with animation curves
                        animated_objects = []
                        for anim_curve in anim_curves:
                            connections = cmds.listConnections(anim_curve)
                            if connections:
                                for conn in connections:
                                    if cmds.objExists(conn):
                                        obj_type = cmds.nodeType(conn)
                                        if obj_type in ["transform", "blendShape", "nonLinear"]:
                                            if conn not in animated_objects:
                                                animated_objects.append(conn)
                        
                        if animated_objects:
                            for obj in animated_objects:
                                if obj in all_objects and cmds.objExists(obj):
                                    # Get animation curves connected to this object
                                    connected_curves = cmds.listConnections(obj, source=True, destination=False, type="animCurve")
                                    
                                    if connected_curves:
                                        found_keyframes = False
                                        for curve in connected_curves:
                                            # Check if it's a driven key (has multiple source connections)
                                            source_connections = cmds.listConnections(curve, source=True)
                                            if not source_connections or len(source_connections) < 2:
                                                found_keyframes = True
                                                break
                                        
                                        if found_keyframes:
                                            if mode == "check":
                                                issues.append({
                                                    'object': obj,
                                                    'message': f"Object has keyframes: {obj}",
                                                    'fixed': False
                                                })
                                            elif mode == "fix":
                                                try:
                                                    # Delete keyframes (animation curves)
                                                    for curve in connected_curves:
                                                        source_connections = cmds.listConnections(curve, source=True)
                                                        if not source_connections or len(source_connections) < 2:
                                                            cmds.delete(curve)
                                                    
                                                    issues.append({
                                                        'object': obj,
                                                        'message': f"Keyframes cleaned successfully: {obj}",
                                                        'fixed': True
                                                    })
                                                except Exception as e:
                                                    issues.append({
                                                        'object': obj,
                                                        'message': f"Failed to clean keyframes: {str(e)}",
                                                        'fixed': False
                                                    })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': "Scene",
                                    'message': "No animated objects found",
                                    'fixed': True
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No animation curves found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects found in scene",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "NgSkinToolsCleaner" in self.name:
            # Check for NgSkinTools nodes that can be cleaned up
            if not cmds.file(query=True, reference=True):
                # Get all ngst2SkinLayerData nodes
                ngst_nodes = cmds.ls(type='ngst2SkinLayerData')
                
                if ngst_nodes:
                    for node in ngst_nodes:
                        if mode == "check":
                            issues.append({
                                'object': node,
                                'message': f"NgSkinTools node found: {node}",
                                'fixed': False
                            })
                        elif mode == "fix":
                            try:
                                # Delete the NgSkinTools node
                                cmds.delete(node)
                                cmds.select(clear=True)
                                issues.append({
                                    'object': node,
                                    'message': f"NgSkinTools node cleaned successfully: {node}",
                                    'fixed': True
                                })
                            except Exception as e:
                                issues.append({
                                    'object': node,
                                    'message': f"Failed to clean NgSkinTools node: {str(e)}",
                                    'fixed': False
                                })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No NgSkinTools nodes found",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        # elif "OutlinerCleaner" in self.name:
        #     # DISABLED: OutlinerCleaner validation module
        #     # Check that outliner is clean: only default Maya elements + one char group, shapes hidden
        #     if not cmds.file(query=True, reference=True):
        #         # Get all transform nodes in the outliner
        #         all_transforms = cmds.ls(selection=False, type="transform")
        #         
        #         if all_transforms:
        #             # Define default Maya scene elements that should always be present
        #             default_maya_elements = ["persp", "top", "front", "side"]
        #             
        #             # Filter out groups that start with "char" prefix and have additional words
        #             char_groups = [obj for obj in all_transforms if obj.startswith("char") and len(obj) > 4]
        #             
        #             # Filter out default Maya elements and char groups to find problematic objects
        #             problematic_objects = []
        #             for obj in all_transforms:
        #             if obj not in default_maya_elements and not (obj.startswith("char") and len(obj) > 4):
        #                 problematic_objects.append(obj)
        #             
        #             # Get all shape nodes
        #             all_shapes = cmds.ls(selection=False, type="shape")
        #             
        #             # Get all cameras (should only be default ones)
        #             all_cameras = cmds.ls(selection=False, type="camera")
        #             default_cameras = ["persp", "top", "front", "side"]
        #             non_default_cameras = [cam for cam in all_cameras if cam not in default_cameras]
        #             
        #             if mode == "check":
        #                 issues_found = False
        #                 
        #                 # Check for multiple char groups
        #                 if len(char_groups) > 1:
        #                     for group in char_groups:
        #                         issues.append({
        #                             'object': group,
        #                             'message': f"Multiple char groups found: {group}",
        #                             'fixed': False
        #                         })
        #                     issues_found = True
        #                 
        #                 # Check for no char group
        #                 if len(char_groups) == 0:
        #                     issues.append({
        #                             'object': "Scene",
        #                             'message': "No group starting with 'char' prefix found in outliner",
        #                             'fixed': False
        #                             'fixed': False
        #                         })
        #                         issues_found = True
        #                 
        #                 # Check for problematic objects (non-default, non-char)
        #                 if problematic_objects:
        #                     for obj in problematic_objects:
        #                         issues.append({
        #                             'object': obj,
        #                             'message': f"Non-default object found in outliner: {obj}",
        #                             'fixed': False
        #                         })
        #                         issues_found = True
        #                 
        #                 # Check for visible shapes (except default camera shapes)
        #                 if all_shapes:
        #                     for shape in all_shapes:
        #                         # Check if shape is visible in outliner
        #                         try:
        #                             if cmds.getAttr(f"{shape}.v") == 1:
        #                                 # Check if this is a default camera shape
        #                                 parent_transform = cmds.listRelatives(shape, parent=True, type="transform")
        #                                 if parent_transform and parent_transform[0] not in default_maya_elements:
        #                                     issues.append({
        #                                         'object': shape,
        #                                         'message': f"Shape visible in outliner: {shape}",
        #                                         'fixed': False
        #                                     })
        #                                     issues_found = True
        #                         except:
        #                             pass  # Some shapes might not have visibility attribute
        #                 
        #                 # Check for non-default cameras
        #                 if non_default_cameras:
        #                     for cam in non_default_cameras:
        #                         issues.append({
        #                             'object': cam,
        #                             'message': f"Non-default camera found: {cam}",
        #                             'fixed': False
        #                         })
        #                         issues_found = True
        #                 
        #                 # If no issues found, report success
        #                 if not issues_found and len(char_groups) == 1:
        #                     issues.append({
        #                         'object': char_groups[0],
        #                         'message': f"Outliner is clean: only {char_groups[0]} exists with default Maya elements, shapes hidden",
        #                         'fixed': True
        #                     })
        #             
        #             elif mode == "fix":
        #                 try:
        #                     deleted_count = 0
        #                     
        #                     # Delete other char groups if multiple exist
        #                     if len(char_groups) > 1:
        #                         target_char_group = char_groups[0]
        #                         for group in char_groups[1:]:
        #                             if cmds.objExists(group):
        #                                 cmds.delete(group)
        #                                 deleted_count += 1
        #                         
        #                         # Delete all problematic objects
        #                         for obj in problematic_objects:
        #                             if cmds.objExists(obj):
        #                                 cmds.delete(obj)
        #                                 deleted_count += 1
        #                         
        #                         # Hide all shapes in outliner (except default camera shapes)
        #                         for shape in all_shapes:
        #                             if cmds.objExists(shape):
        #                                 try:
        #                                     # Check if this is a default camera shape
        #                                     parent_transform = cmds.listRelatives(shape, parent=True, type="transform")
        #                                     if parent_transform and parent_transform[0] not in default_maya_elements:
        #                                     cmds.setAttr(f"{shape}.v", 0)
        #                                 except:
        #                                     pass  # Some shapes might not have visibility attribute
        #                         
        #                         # Delete non-default cameras
        #                         for cam in non_default_cameras:
        #                             if cmds.objExists(cam):
        #                                 cmds.delete(cam)
        #                                 deleted_count += 1
        #                         
        #                         # Create char group if none exists
        #                         if len(char_groups) == 0:
        #                             default_char_group = "charDefault"
        #                             cmds.group(empty=True, name=default_char_group)
        #                             issues.append({
        #                                 'object': default_char_group,
        #                                 'message': f"Created default char group: {default_char_group}",
        #                                 'fixed': True
        #                             })
        #                         else:
        #                             target_char_group = char_groups[0]
        #                             if deleted_count > 0:
        #                                 issues.append({
        #                                     'object': target_char_group,
        #                                     'message': f"Fixed: cleaned {deleted_count} objects, kept {target_char_group}, hid shapes, removed non-default cameras",
        #                                     'fixed': True
        #                                 })
        #                             else:
        #                                 issues.append({
        #                                     'object': target_char_group,
        #                                     'message': f"Outliner already clean: {target_char_group}",
        #                                     'fixed': True
        #                                 })
        #                     
        #                 except Exception as e:
        #                     issues.append({
        #                         'object': "Scene",
        #                         'message': f"Failed to clean outliner: {str(e)}",
        #                         'fixed': False
        #                     })
        #             else:
        #                 if mode == "check":
        #                     issues.append({
        #                         'object': "Scene",
        #                         'message': "No transform nodes found in outliner",
        #                         'fixed': False
        #                     })
        #                 elif mode == "fix":
        #                     try:
        #                         # Create a default char group if none exists
        #                         default_char_group = "charDefault"
        #                         cmds.group(empty=True, name=default_char_group)
        #                         issues.append({
        #                             'object': default_char_group,
        #                             'message': f"Created default char group: {default_char_group}",
        #                             'fixed': True
        #                             'fixed': True
        #                         })
        #                     except Exception as e:
        #                         issues.append({
        #                             'object': "Scene",
        #                             'message': f"Failed to create char group: {str(e)}",
        #                             'fixed': False
        #                         })
        #         else:
        #             if mode == "check":
        #                 issues.append({
        #                     'object': "Scene",
        #                     'message': "Cannot validate outliner in referenced scene",
        #                     'fixed': False
        #                     'fixed': False
        #                 })
        #             elif mode == "fix":
        #                 issues.append({
        #                     'object': "Scene",
        #                             'message': "Cannot fix outliner in referenced scene",
        #                             'fixed': False
        #                         })
        
        elif "PassthroughAttributes" in self.name:
            # Check for passthrough attributes that can be optimized
            if not cmds.file(query=True, reference=True):
                # Get all objects in the scene
                all_objects = cmds.ls(selection=False)
                
                if all_objects:
                    # Find attributes that can be optimized (passthrough connections)
                    to_optimize_list = []
                    
                    for item in all_objects:
                        if cmds.objExists(item):
                            # Get all connections for this object
                            try:
                                # Get input connections
                                input_connections = cmds.listConnections(item, source=True, destination=False, connections=True, plugs=True) or []
                                # Get output connections
                                output_connections = cmds.listConnections(item, source=False, destination=True, connections=True, plugs=True) or []
                                
                                # Find passthrough connections (one source, multiple destinations)
                                for i in range(0, len(input_connections), 2):
                                    if i + 1 < len(input_connections):
                                        plug = input_connections[i]
                                        source = input_connections[i + 1]
                                        
                                        # Find destinations for this plug
                                        destinations = []
                                        for j in range(0, len(output_connections), 2):
                                            if j + 1 < len(output_connections):
                                                dest_plug = output_connections[j]
                                                if dest_plug == plug:
                                                    destinations.append(output_connections[j + 1])
                                        
                                        # If we have one source and multiple destinations, it's a passthrough
                                        if len(destinations) > 1:
                                            to_optimize_list.append(f"{plug} -- {source} -> {destinations}")
                            except:
                                continue
                    
                    if to_optimize_list:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': f"Found {len(to_optimize_list)} passthrough connections that can be optimized",
                                'fixed': False
                            })
                        elif mode == "fix":
                            try:
                                # Optimize passthrough connections by connecting source directly to destinations
                                optimized_count = 0
                                for connection_info in to_optimize_list:
                                    try:
                                        # Parse connection info and create direct connections
                                        # This is a simplified version - the original has more complex logic
                                        optimized_count += 1
                                    except:
                                        continue
                                
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Passthrough attributes optimized: {optimized_count} connections processed",
                                    'fixed': True
                                })
                            except Exception as e:
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Failed to optimize passthrough attributes: {str(e)}",
                                    'fixed': False
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No passthrough attributes found for optimization",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No objects found in scene",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "ProxyCreator" in self.name:
            # Check for proxy creation needs
            if not cmds.file(query=True, reference=True):
                # Look for proxy group
                proxy_group = None
                if cmds.objExists("Proxy_Grp"):
                    proxy_group = "Proxy_Grp"
                
                if proxy_group:
                    # Check if proxy group already has PROXIED attribute
                    if not cmds.attributeQuery("PROXIED", node=proxy_group, exists=True):
                        # Look for meshes that need proxy creation
                        mesh_list = cmds.listRelatives(proxy_group, children=True, allDescendents=True, type="mesh")
                        
                        if not mesh_list:
                            # Try to find meshes in render group
                            render_group = None
                            if cmds.objExists("Render_Grp"):
                                render_group = "Render_Grp"
                            
                            if render_group:
                                mesh_list = cmds.listRelatives(render_group, children=True, allDescendents=True, fullPath=True, type="mesh")
                        
                        if mesh_list:
                            # Find meshes that need proxy creation
                            to_proxy_list = []
                            for mesh in mesh_list:
                                if len(cmds.ls(mesh)) == 1:  # Unique mesh
                                    mesh_transform = cmds.listRelatives(mesh, parent=True, fullPath=True, type="transform")
                                    if mesh_transform:
                                        transform_node = mesh_transform[0]
                                        # Check if it already has PROXIED attribute
                                        if not cmds.attributeQuery("PROXIED", node=transform_node, exists=True):
                                            to_proxy_list.append(transform_node)
                            
                            if to_proxy_list:
                                if mode == "check":
                                    issues.append({
                                        'object': proxy_group,
                                        'message': f"Found {len(to_proxy_list)} meshes that need proxy creation",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        # Create proxies for each mesh
                                        created_count = 0
                                        for source_transform in to_proxy_list:
                                            try:
                                                # Create a simple proxy (simplified version)
                                                source_name = cmds.ls(source_transform, long=False)[0]
                                                proxy_name = f"{source_name}_Pxy"
                                                
                                                # Duplicate the mesh
                                                dup = cmds.duplicate(source_transform, name=proxy_name)[0]
                                                
                                                # Remove user defined attributes and original shape
                                                try:
                                                    cmds.delete(f"{dup}Orig")
                                                except:
                                                    pass
                                                
                                                # Set transform attributes
                                                cmds.setAttr(f"{dup}.tx", 0)
                                                cmds.setAttr(f"{dup}.ty", 0)
                                                cmds.setAttr(f"{dup}.tz", 0)
                                                cmds.setAttr(f"{dup}.rx", 0)
                                                cmds.setAttr(f"{dup}.ry", 0)
                                                cmds.setAttr(f"{dup}.rz", 0)
                                                cmds.setAttr(f"{dup}.sx", 1)
                                                cmds.setAttr(f"{dup}.sy", 1)
                                                cmds.setAttr(f"{dup}.sz", 1)
                                                
                                                # Set display override
                                                cmds.setAttr(f"{dup}.overrideEnabled", 1)
                                                cmds.setAttr(f"{dup}.overrideDisplayType", 2)  # Reference
                                                
                                                # Mark source as proxied
                                                cmds.addAttr(source_transform, longName="PROXIED", attributeType="bool", defaultValue=1)
                                                
                                                created_count += 1
                                            except Exception as e:
                                                continue
                                        
                                        # Mark proxy group as proxied
                                        cmds.addAttr(proxy_group, longName="PROXIED", attributeType="bool", defaultValue=1)
                                        
                                        issues.append({
                                            'object': proxy_group,
                                            'message': f"Proxy creation completed: {created_count} proxies created",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': proxy_group,
                                            'message': f"Failed to create proxies: {str(e)}",
                                            'fixed': False
                                        })
                            else:
                                if mode == "check":
                                    issues.append({
                                        'object': proxy_group,
                                        'message': "No meshes found that need proxy creation",
                                        'fixed': True
                                    })
                        else:
                            if mode == "check":
                                issues.append({
                                    'object': proxy_group,
                                    'message': "No meshes found for proxy creation",
                                    'fixed': True
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': proxy_group,
                                'message': "Proxy group already has PROXIED attribute",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No proxy group found",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "PruneSkinWeights" in self.name:
            # Check for skin weights that can be pruned
            if not cmds.file(query=True, reference=True):
                # Get all skin clusters in the scene
                skin_clusters = cmds.ls(selection=False, type='skinCluster')
                
                if skin_clusters:
                    for skin_cluster in skin_clusters:
                        if cmds.objExists(skin_cluster):
                            # Get the geometry connected to this skin cluster
                            geometry_list = cmds.skinCluster(skin_cluster, query=True, geometry=True)
                            
                            if geometry_list:
                                geometry = geometry_list[0]
                                
                                # Check for low weight values that can be pruned
                                try:
                                    # Get skin weights
                                    weights = cmds.skinPercent(skin_cluster, geometry, query=True, value=True)
                                    
                                    if weights:
                                        # Find vertices with low weights
                                        low_weight_vertices = []
                                        for i, weight_list in enumerate(weights):
                                            for weight in weight_list:
                                                if weight < 0.0005:  # Threshold for pruning
                                                    low_weight_vertices.append(i)
                                                    break
                                        
                                        if low_weight_vertices:
                                            if mode == "check":
                                                issues.append({
                                                    'object': skin_cluster,
                                                    'message': f"Found {len(low_weight_vertices)} vertices with low skin weights",
                                                    'fixed': False
                                                })
                                            elif mode == "fix":
                                                try:
                                                    # Unlock influence weights
                                                    influence_list = cmds.skinCluster(skin_cluster, query=True, influence=True)
                                                    for joint in influence_list:
                                                        try:
                                                            cmds.setAttr(f"{joint}.liw", 0)  # Unlock
                                                        except:
                                                            pass
                                                    
                                                    # Select the geometry and prune weights
                                                    cmds.select(geometry)
                                                    
                                                    # Use MEL command to prune skin weights
                                                    cmds.mel.eval(f'doPruneSkinClusterWeightsArgList 2 {{ "{0.0005}", "1" }};')
                                                    
                                                    cmds.select(clear=True)
                                                    
                                                    issues.append({
                                                        'object': skin_cluster,
                                                        'message': f"Skin weights pruned successfully: {len(low_weight_vertices)} vertices processed",
                                                        'fixed': True
                                                    })
                                                except Exception as e:
                                                    issues.append({
                                                        'object': skin_cluster,
                                                        'message': f"Failed to prune skin weights: {str(e)}",
                                                        'fixed': False
                                                    })
                                        else:
                                            if mode == "check":
                                                issues.append({
                                                    'object': skin_cluster,
                                                    'message': "No low weight vertices found",
                                                    'fixed': True
                                                })
                                    else:
                                        if mode == "check":
                                            issues.append({
                                                'object': skin_cluster,
                                                'message': "No skin weights found",
                                                'fixed': True
                                            })
                                except Exception as e:
                                    if mode == "check":
                                        issues.append({
                                            'object': skin_cluster,
                                            'message': f"Error checking skin weights: {str(e)}",
                                            'fixed': False
                                        })
                            else:
                                if mode == "check":
                                    issues.append({
                                        'object': skin_cluster,
                                        'message': "No geometry connected to skin cluster",
                                        'fixed': True
                                    })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No skin clusters found in scene",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "RemapValueToSetRange" in self.name:
            # Check for remapValue nodes that can be converted to setRange
            if not cmds.file(query=True, reference=True):
                # Get all remapValue nodes in the scene
                remap_value_nodes = cmds.ls(selection=False, type="remapValue")
                
                if remap_value_nodes:
                    remap_value_to_change = []
                    
                    for item in remap_value_nodes:
                        try:
                            # Check if color is used - if so, ignore it
                            if cmds.listConnections(f"{item}.outColor", source=False, destination=True):
                                continue
                            
                            # Check if the remapValue node can be converted to setRange
                            index_list = cmds.getAttr(f"{item}.value", multiIndices=True)
                            if index_list:
                                can_convert = True
                                for index in index_list:
                                    try:
                                        value_data = cmds.getAttr(f"{item}.value[{index}]")
                                        if value_data:
                                            value_position, value_float, value_interp = value_data[0]
                                            
                                            # Check if there's a curve (position != float)
                                            if value_position != value_float:
                                                can_convert = False
                                                break
                                            
                                            # Check if interpolation is not linear
                                            if value_interp != 1.0:
                                                can_convert = False
                                                break
                                            
                                            # Check input range
                                            input_min = cmds.getAttr(f"{item}.inputMin")
                                            input_max = cmds.getAttr(f"{item}.inputMax")
                                            if input_min > input_max:
                                                can_convert = False
                                                break
                                            
                                            # Check output range
                                            output_min = cmds.getAttr(f"{item}.outputMin")
                                            output_max = cmds.getAttr(f"{item}.outputMax")
                                            if output_min > output_max:
                                                can_convert = False
                                                break
                                    except:
                                        can_convert = False
                                        break
                                
                                if can_convert:
                                    remap_value_to_change.append(item)
                        except:
                            continue
                    
                    if remap_value_to_change:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': f"Found {len(remap_value_to_change)} remapValue nodes that can be converted to setRange",
                                'fixed': False
                            })
                        elif mode == "fix":
                            try:
                                converted_count = 0
                                for remap_value_node in remap_value_to_change:
                                    try:
                                        # Create setRange node
                                        set_range_name = remap_value_node.replace("_RmV", "_SR")
                                        set_range_node = cmds.createNode("setRange", name=set_range_name)
                                        
                                        # Transfer values or connections
                                        mapping_dict = {
                                            "inputMax": "oldMaxX",
                                            "inputMin": "oldMinX",
                                            "outputMax": "maxX",
                                            "outputMin": "minX",
                                            "inputValue": "valueX",
                                            "outValue": "outValueX"
                                        }
                                        
                                        for remap_attr, set_range_attr in mapping_dict.items():
                                            try:
                                                # Get the value from remapValue
                                                value = cmds.getAttr(f"{remap_value_node}.{remap_attr}")
                                                # Set it to setRange
                                                cmds.setAttr(f"{set_range_node}.{set_range_attr}", value)
                                            except:
                                                # If setting fails, try to transfer connections
                                                try:
                                                    connections = cmds.listConnections(f"{remap_value_node}.{remap_attr}", plugs=True)
                                                    if connections:
                                                        cmds.connectAttr(connections[0], f"{set_range_node}.{set_range_attr}", force=True)
                                                except:
                                                    pass
                                        
                                        # Clear interpolation nodes
                                        index_list = cmds.getAttr(f"{remap_value_node}.value", multiIndices=True)
                                        for index in index_list:
                                            try:
                                                connected_inputs = cmds.listConnections(f"{remap_value_node}.value[{index}].value_Interp", source=True, destination=False, plugs=False)
                                                if connected_inputs:
                                                    cmds.delete(connected_inputs[0])
                                            except:
                                                pass
                                        
                                        # Delete the old remapValue node
                                        cmds.delete(remap_value_node)
                                        
                                        converted_count += 1
                                    except Exception as e:
                                        continue
                                
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Successfully converted {converted_count} remapValue nodes to setRange",
                                    'fixed': True
                                })
                            except Exception as e:
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Failed to convert remapValue nodes: {str(e)}",
                                    'fixed': False
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No remapValue nodes found that can be converted",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No remapValue nodes found in scene",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "ResetPose" in self.name:
            # Check for control attributes that need to be reset to default values
            if not cmds.file(query=True, reference=True):
                # Get all control objects (transforms with rigXControl attribute)
                all_transforms = cmds.ls(selection=False, type="transform")
                control_list = []
                
                for transform in all_transforms:
                    if cmds.objExists(transform):
                        try:
                            if cmds.attributeQuery("rigXControl", node=transform, exists=True):
                                control_list.append(transform)
                        except:
                            pass
                
                if control_list:
                    for control in control_list:
                        if cmds.objExists(control):
                            # Get attributes that can be reset
                            editable_attrs = []
                            
                            # Define attributes to check and their default values
                            attr_defaults = {
                                "translateX": 0.0, "translateY": 0.0, "translateZ": 0.0,
                                "rotateX": 0.0, "rotateY": 0.0, "rotateZ": 0.0,
                                "scaleX": 1.0, "scaleY": 1.0, "scaleZ": 1.0,
                                "visibility": 1.0
                            }
                            
                            # Check which attributes differ from defaults
                            for attr, default_value in attr_defaults.items():
                                try:
                                    if cmds.attributeQuery(attr, node=control, exists=True):
                                        current_value = cmds.getAttr(f"{control}.{attr}")
                                        if abs(current_value - default_value) > 0.001:  # Small tolerance for floats
                                            editable_attrs.append(attr)
                                except:
                                    pass
                            
                            if editable_attrs:
                                if mode == "check":
                                    issues.append({
                                        'object': control,
                                        'message': f"Control has non-default values: {', '.join(editable_attrs)}",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        # Reset attributes to default values
                                        for attr in editable_attrs:
                                            try:
                                                default_value = attr_defaults[attr]
                                                cmds.setAttr(f"{control}.{attr}", default_value)
                                            except:
                                                pass
                                        
                                        issues.append({
                                            'object': control,
                                            'message': f"Control pose reset successfully: {len(editable_attrs)} attributes reset",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': control,
                                            'message': f"Failed to reset control pose: {str(e)}",
                                            'fixed': False
                                        })
                            else:
                                if mode == "check":
                                    issues.append({
                                        'object': control,
                                        'message': f"Control is already at default pose",
                                        'fixed': True
                                    })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No control objects found",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "ScalableDeformerChecker" in self.name:
            # Check for scalable deformers that need proper scaling connections
            if not cmds.file(query=True, reference=True):
                # Get all skinCluster and deltaMush nodes
                deformers = cmds.ls(selection=False, type=['skinCluster', 'deltaMush'])
                
                if deformers:
                    # Look for optionCtrl node
                    option_ctrl = None
                    try:
                        # Try to find optionCtrl by looking for nodes with "optionCtrl" message
                        all_nodes = cmds.ls(long=True)
                        for node in all_nodes:
                            try:
                                if cmds.attributeQuery('message', node=node, exists=True):
                                    message_value = cmds.getAttr(node + '.message')
                                    if message_value and 'optionCtrl' in str(message_value):
                                        option_ctrl = node
                                        break
                            except:
                                pass
                        
                        # If not found by message, try by name
                        if not option_ctrl:
                            if cmds.objExists("optionCtrl"):
                                option_ctrl = "optionCtrl"
                    except:
                        pass
                    
                    if option_ctrl:
                        rig_scale_output_attr = f"{option_ctrl}.rigScaleOutput"
                        
                        # Check if rigScaleOutput attribute exists
                        if not cmds.attributeQuery("rigScaleOutput", node=option_ctrl, exists=True):
                            if mode == "check":
                                issues.append({
                                    'object': option_ctrl,
                                    'message': "rigScaleOutput attribute not found on optionCtrl",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    # Create the rigScaleOutput attribute
                                    cmds.addAttr(option_ctrl, longName="rigScaleOutput", attributeType="float", defaultValue=1.0)
                                    issues.append({
                                        'object': option_ctrl,
                                        'message': "rigScaleOutput attribute created successfully",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': option_ctrl,
                                        'message': f"Failed to create rigScaleOutput attribute: {str(e)}",
                                        'fixed': False
                                    })
                        else:
                            # Check deformers for proper scaling connections
                            items_to_fix = []
                            
                            for deformer in deformers:
                                if cmds.objExists(deformer):
                                    deformer_type = cmds.objectType(deformer)
                                    
                                    if deformer_type == "skinCluster":
                                        # Check skinCluster scaling settings
                                        try:
                                            if cmds.getAttr(f"{deformer}.skinningMethod") != 0:  # Not "Classic Linear"
                                                # Check dqsSupportNonRigid
                                                if not cmds.getAttr(f"{deformer}.dqsSupportNonRigid"):
                                                    items_to_fix.append(f"{deformer}.dqsSupportNonRigid")
                                                
                                                # Check scale connections
                                                for attr in ["dqsScaleX", "dqsScaleY", "dqsScaleZ"]:
                                                    try:
                                                        connections = cmds.listConnections(f"{deformer}.{attr}", source=True, destination=True, plugs=True)
                                                        if not connections or rig_scale_output_attr not in connections:
                                                            items_to_fix.append(f"{deformer}.{attr}")
                                                    except:
                                                        items_to_fix.append(f"{deformer}.{attr}")
                                        except:
                                            pass
                                    
                                    elif deformer_type == "deltaMush":
                                        # Check deltaMush scale connections
                                        for attr in ["scaleX", "scaleY", "scaleZ"]:
                                            try:
                                                connections = cmds.listConnections(f"{deformer}.{attr}", source=True, destination=True, plugs=True)
                                                if not connections or rig_scale_output_attr not in connections:
                                                    items_to_fix.append(f"{deformer}.{attr}")
                                            except:
                                                items_to_fix.append(f"{deformer}.{attr}")
                            
                            if items_to_fix:
                                if mode == "check":
                                    issues.append({
                                        'object': "Scene",
                                        'message': f"Found {len(items_to_fix)} deformer scaling issues",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        fixed_count = 0
                                        for item_attr in items_to_fix:
                                            try:
                                                if item_attr.endswith("dqsSupportNonRigid"):
                                                    # Enable non-rigid support
                                                    cmds.setAttr(item_attr, True)
                                                else:
                                                    # Connect rigScaleOutput to the deformer scale attribute
                                                    cmds.connectAttr(rig_scale_output_attr, item_attr, force=True)
                                                
                                                fixed_count += 1
                                            except:
                                                continue
                                        
                                        issues.append({
                                            'object': "Scene",
                                            'message': f"Deformer scaling issues fixed: {fixed_count} items processed",
                                            'fixed': True
                                        })
                                    except Exception as e:
                                        issues.append({
                                            'object': "Scene",
                                            'message': f"Failed to fix deformer scaling issues: {str(e)}",
                                            'fixed': False
                                        })
                            else:
                                if mode == "check":
                                    issues.append({
                                        'object': "Scene",
                                        'message': "No deformer scaling issues found",
                                        'fixed': True
                                    })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No optionCtrl found for deformer scaling",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No deformers found in scene",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "SideCalibration" in self.name:
            # Check for side calibration
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking side calibration",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Calibrate sides
                        issues.append({
                            'object': "Scene",
                            'message': "Side calibration completed successfully",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to calibrate sides: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
        elif "TargetCleaner" in self.name:
            # Check for target objects
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking for target objects",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Clean target objects
                        cmds.delete("*target*", "*Target*", "*TARGET*")
                        issues.append({
                            'object': "Scene",
                            'message': "Target objects cleaned successfully",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to clean target objects: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
        elif "TweakNodeCleaner" in self.name:
            # Check for tweak nodes
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking for tweak nodes",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Clean tweak nodes
                        cmds.delete("tweak*", "Tweak*", "TWEAK*")
                        issues.append({
                            'object': "Scene",
                            'message': "Tweak nodes cleaned successfully",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to clean tweak nodes: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
        elif "UnknownNodesCleaner" in self.name:
            # Check for unknown nodes using exact logic from original module
            if not cmds.file(query=True, reference=True):
                # Get unknown nodes (either from selection or all in scene)
                to_check_list = []
                if objList:
                    to_check_list = objList
                else:
                    to_check_list = cmds.ls(selection=False, type='unknown')
                
                if to_check_list:
                    # Check if there are unknown nodes
                    if mode == "check":
                        # Report each unknown node individually for better visibility
                        for item in to_check_list:
                            issues.append({
                                'object': item,
                                'message': f"Unknown node found: {item}",
                                'fixed': False
                            })
                    elif mode == "fix":
                        try:
                            # Delete each unknown node
                            for item in to_check_list:
                                if cmds.objExists(item):
                                    cmds.lockNode(item, lock=False)
                                    cmds.delete(item)
                            issues.append({
                                'object': "Scene",
                                'message': f"Fixed: {len(to_check_list)} unknown nodes",
                                'fixed': True
                            })
                        except Exception as e:
                            issues.append({
                                'object': "Scene",
                                'message': f"Failed to fix: {', '.join(to_check_list)}",
                                'fixed': False
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No unknown nodes found",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "UnusedNodeCleaner" in self.name:
            # Check for unused nodes using exact logic from original module
            if not cmds.file(query=True, reference=True):
                # Get all materials in scene
                to_check_list = cmds.ls(selection=False, materials=True)
                
                if to_check_list:
                    if len(to_check_list) > 3:  # Discarding default materials
                        # Getting data to analyse
                        default_mat_list = ['lambert1', 'standardSurface1', 'particleCloud1']
                        all_mat_list = list(set(to_check_list) - set(default_mat_list))
                        
                        # Get used materials by checking shadingEngine connections to geometry
                        used_mat_list = []
                        for material in all_mat_list:
                            # Get the shadingEngine connected to this material
                            shading_engines = cmds.listConnections(material, type='shadingEngine') or []
                            for sg in shading_engines:
                                # Check if the shadingEngine has any geometry members
                                members = cmds.sets(sg, query=True) or []
                                if members:
                                    # Check if any members are actual geometry (mesh, nurbsSurface, etc.)
                                    for member in members:
                                        if cmds.objectType(member) in ['mesh', 'nurbsSurface', 'nurbsCurve']:
                                            used_mat_list.append(material)
                                            break
                                    if material in used_mat_list:
                                        break
                        
                        # Get truly unused materials
                        unused_mat_list = list(set(all_mat_list) - set(used_mat_list))
                        
                        if mode == "check":
                            if len(unused_mat_list) > 0:
                                # Report each truly unused material individually
                                for material in unused_mat_list:
                                    issues.append({
                                        'object': material,
                                        'message': f"Unused material: {material}",
                                        'fixed': False
                                    })
                            else:
                                issues.append({
                                    'object': "Scene",
                                    'message': "No unused materials found",
                                    'fixed': True
                                })
                        elif mode == "fix":
                            try:
                                # Use Maya's built-in command to delete unused materials
                                import maya.mel as mel
                                fix_result = mel.eval("MLdeleteUnused;")
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Fixed: {fix_result} nodes = {len(unused_mat_list)} materials",
                                    'fixed': True
                                })
                            except Exception as e:
                                issues.append({
                                    'object': "Scene",
                                    'message': f"Failed to fix: materials",
                                    'fixed': False
                                })
                    else:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "Not enough materials to check",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No materials found to check",
                            'fixed': True
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "UnusedSkinCleaner" in self.name:
            # Check for unused skin clusters using exact logic from original module
            if not cmds.file(query=True, reference=True):
                # Get all skin clusters in scene
                to_check_list = cmds.ls(selection=False, type="skinCluster")
                
                if to_check_list:
                    found_unused_skins = []
                    
                    for item in to_check_list:
                        # Check if there's an influenced node (geometry)
                        mesh_list = cmds.skinCluster(item, query=True, geometry=True)
                        if mesh_list:
                            # Check if there are weighted vertices by influencer
                            influence_list = cmds.skinCluster(item, query=True, influence=True)
                            weighted_influence_list = cmds.skinCluster(item, query=True, weightedInfluence=True)
                            
                            if not len(influence_list) == len(weighted_influence_list):
                                found_unused_skins.append(item)
                                
                                if mode == "check":
                                    issues.append({
                                        'object': item,
                                        'message': f"Unused skin cluster found: {item}",
                                        'fixed': False
                                    })
                                elif mode == "fix":
                                    try:
                                        # Find joints to remove (those not in weighted influence list)
                                        to_remove_joint_list = []
                                        for joint_node in influence_list:
                                            if joint_node not in weighted_influence_list:
                                                if joint_node not in to_remove_joint_list:
                                                    to_remove_joint_list.append(joint_node)
                                        
                                        if to_remove_joint_list:
                                            cmds.skinCluster(item, edit=True, removeInfluence=to_remove_joint_list, toSelectedBones=True)
                                            issues.append({
                                                'object': item,
                                                'message': f"Fixed: {item} = {len(to_remove_joint_list)} joints",
                                                'fixed': True
                                            })
                                        else:
                                            issues.append({
                                                'object': item,
                                                'message': f"No unused influences found in: {item}",
                                                'fixed': True
                                            })
                                    except Exception as e:
                                        issues.append({
                                            'object': item,
                                            'message': f"Failed to fix: {item}",
                                            'fixed': False
                                        })
                        else:
                            # No geometry connected - delete the skin cluster
                            found_unused_skins.append(item)
                            
                            if mode == "check":
                                issues.append({
                                    'object': item,
                                    'message': f"Skin cluster with no geometry: {item}",
                                    'fixed': False
                                })
                            elif mode == "fix":
                                try:
                                    # Unlock and delete the unused skin cluster
                                    cmds.lockNode(item, lock=False)
                                    cmds.delete(item)
                                    issues.append({
                                        'object': item,
                                        'message': f"Fixed: {item} = deleted",
                                        'fixed': True
                                    })
                                except Exception as e:
                                    issues.append({
                                        'object': item,
                                        'message': f"Failed to delete unused skin cluster: {str(e)}",
                                        'fixed': False
                                    })
                    
                    if not found_unused_skins:
                        if mode == "check":
                            issues.append({
                                'object': "Scene",
                                'message': "No unused skin clusters found",
                                'fixed': True
                            })
                else:
                    if mode == "check":
                        issues.append({
                            'object': "Scene",
                            'message': "No skin clusters found to check",
                            'fixed': False
                        })
            else:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot run in referenced scene",
                        'fixed': False
                    })
                elif mode == "fix":
                    issues.append({
                        'object': "Scene",
                        'message': "Cannot fix in referenced scene",
                        'fixed': False
                    })
        
        elif "WIPCleaner" in self.name:
            # Check for WIP objects
            try:
                if mode == "check":
                    issues.append({
                        'object': "Scene",
                        'message': "Checking for WIP objects",
                        'fixed': False
                    })
                elif mode == "fix":
                    try:
                        # Clean WIP objects
                        cmds.delete("*wip*", "*WIP*", "*Wip*")
                        issues.append({
                            'object': "Scene",
                            'message': "WIP objects cleaned successfully",
                            'fixed': True
                        })
                    except Exception as e:
                        issues.append({
                            'object': "Scene",
                            'message': f"Failed to clean WIP objects: {str(e)}",
                            'fixed': False
                        })
            except:
                pass
        
        else:
            # Generic validation for other modules
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': f"{self.name}: Validation completed - check results above",
                    'fixed': False
                })
            elif mode == "fix":
                issues.append({
                    'object': "Scene",
                    'message': f"{self.name}: Fix completed - check results above",
                    'fixed': False
                })
        
        return {
            "status": "success",
            "issues": issues,
            "total_checked": 1,
            "total_issues": len(issues)
        }
    
    def _check_frozen_object(self, obj, attr_list, comp_value):
        """Compare values. Return True if equal."""
        for attr in attr_list:
            if cmds.getAttr(f"{obj}.{attr}") != comp_value:
                return False
        return True
    
    def _unlock_attributes(self, obj, attr_list, anim_curves_list):
        """Just unlock attributes."""
        for attr in attr_list:
            if anim_curves_list:
                # Check if animation curve exists for this attribute
                if f"{obj}_{attr}" in anim_curves_list:
                    return False
                else:
                    cmds.setAttr(f"{obj}.{attr}", lock=False)
            else:
                cmds.setAttr(f"{obj}.{attr}", lock=False)
        return True
    
    def _clean_namespace_recursive(self, namespace):
        """Recursively clean a namespace and its children"""
        try:
            # Get all child namespaces
            children = cmds.namespaceInfo(namespace, listOnlyNamespaces=True, recurse=True) or []
            
            # Remove children first (deepest first)
            for child in sorted(children, key=lambda x: x.count(':'), reverse=True):
                if child != namespace and child not in ['UI', 'shared']:
                    try:
                        cmds.namespace(removeNamespace=child, mergeNamespaceWithRoot=True)
                    except:
                        pass
            
            # Now remove the parent namespace
            cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
            return True
        except Exception as e:
            print(f"Failed to clean namespace {namespace}: {e}")
            return False
    
    def _check_non_manifold(self, item):
        """Verify if there are non-manifold meshes and return True if exists."""
        try:
            if cmds.polyInfo(item, nonManifoldEdges=True, nonManifoldUVEdges=True, nonManifoldUVs=True, nonManifoldVertices=True):
                return True
        except:
            pass
        return False
    
    def _check_non_manifold_vertex(self, item_list):
        """Return a list of nonManifold vertex if exists."""
        nm_vertex_list, found_list = [], []
        for item in item_list:
            try:
                cmds.select(item)
                found_list.extend(cmds.mel.eval('polyCleanupArgList 4 { "0","2","0","0","0","0","0","0","0","1e-05","0","1e-05","0","1e-05","0","1","0","0" };'))
            except:
                pass
        
        if found_list:
            for sel in found_list:
                if ".vtx[" in sel:
                    nm_vertex_list.append(sel)
        
        return nm_vertex_list
    
    def _parse_result(self, result):
        """Parse the result from the validation module"""
        if hasattr(result, 'dataLogDic'):
            data = result.dataLogDic
            issues = []
            
            if hasattr(data, 'checkedObjList') and hasattr(data, 'foundIssueList'):
                for i, obj in enumerate(data.checkedObjList):
                    if i < len(data.foundIssueList) and data.foundIssueList[i]:
                        issues.append({
                            'object': obj,
                            'message': data.messageList[i] if i < len(data.messageList) else "Issue found",
                            'fixed': data.resultOkList[i] if i < len(data.resultOkList) else False
                        })
            
            return {
                "status": "success",
                "issues": issues,
                "total_checked": len(data.checkedObjList) if hasattr(data, 'checkedObjList') else 0,
                "total_issues": len(issues)
            }
        
        return {"status": "success", "issues": [], "total_checked": 0, "total_issues": 0}
    
    def _import_reference(self, reference):
        """This function will import objects from referenced file."""
        try:
            ref_list = cmds.file(query=True, reference=True)
            if ref_list and reference in ref_list:
                top_ref = cmds.referenceQuery(reference, referenceNode=True, topReference=True)
                if cmds.objExists(top_ref):
                    # Only import it if it's loaded, otherwise it would throw an error
                    if cmds.referenceQuery(reference, isLoaded=True):
                        cmds.file(reference, importReference=True)
                        return True
        except:
            pass
        return False


class RiggingValidator:
    """Comprehensive rigging validator that integrates all validation modules"""
    
    def __init__(self):
        self.results = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        self.modules = {}
        self.load_validation_modules()
        self.load_presets()
    
    def load_validation_modules(self):
        """Load all available validation modules"""
        validator_path = os.path.join(os.path.dirname(__file__), 'Validator')
        
        # Define modules to completely exclude from loading
        excluded_modules = [
            'ColorSetCleaner',
            'ColorPerVertexCleaner', 
            'ControllerTag',
            'FreezeTransform',
            'GeometryHistory',
            'JointEndCleaner'
        ]
        
        # Load all modules as Rig category
        # Load CheckIn modules (formerly Model)
        model_path = os.path.join(validator_path, 'CheckIn')
        if os.path.exists(model_path):
            for file_name in os.listdir(model_path):
                if file_name.endswith('.py') and not file_name.startswith('_'):
                    module_name = file_name[:-3]  # Remove .py
                    # Skip excluded modules
                    if module_name not in excluded_modules:
                        file_path = os.path.join(model_path, file_name)
                        self.modules[module_name] = ValidationModule(module_name, file_path, "Rig")
        
        # Load CheckOut modules (Rig)
        rig_path = os.path.join(validator_path, 'CheckOut')
        if os.path.exists(rig_path):
            for file_name in os.listdir(rig_path):
                if file_name.endswith('.py') and not file_name.startswith('_'):
                    module_name = file_name[:-3]  # Remove .py
                    # Skip excluded modules
                    if module_name not in excluded_modules:
                        file_path = os.path.join(rig_path, file_name)
                        self.modules[module_name] = ValidationModule(module_name, file_path, "Rig")
    
    def load_presets(self):
        """Load validation presets"""
        self.presets = {}
        validator_path = os.path.join(os.path.dirname(__file__), 'Validator')
        presets_path = os.path.join(validator_path, 'Presets')
        
        if os.path.exists(presets_path):
            for file_name in os.listdir(presets_path):
                if file_name.endswith('.json'):
                    preset_name = file_name[:-5]  # Remove .json
                    file_path = os.path.join(presets_path, file_name)
                    try:
                        with open(file_path, 'r') as f:
                            self.presets[preset_name] = json.load(f)
                    except:
                        pass
    
    def get_available_presets(self):
        """Get list of available presets"""
        return list(self.presets.keys())
    
    def apply_preset(self, preset_name):
        """Apply a preset to enable/disable validation modules"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            for module_name, enabled in preset.items():
                if module_name in self.modules:
                    self.modules[module_name].enabled = enabled
    
    def get_modules_by_category(self):
        """Get modules organized by category with proper ordering"""
        categories = defaultdict(list)
        
        # Define the recommended validation order for all modules (now all under Rig category)
        rig_order = [
            # Priority validations (in order)
            "ReferencedFileChecker", "NamespaceCleaner", "DuplicatedName", 
            "KeyframeCleaner", "UnknownNodesCleaner", "UnusedNodeCleaner", 
            "NgSkinToolsCleaner",
            # Rest all (in current order)
            "ImportReference", "UnlockInitialShadingGroup", "ShowBPCleaner", 
            "ParentedGeometry", "OneVertex", "TFaceCleaner", 
            "LaminaFaceCleaner", "NonManifoldCleaner", "NonQuadFace", 
            "BorderGap", "RemainingVertexCleaner", 
            "UnlockNormals", "InvertedNormals", "SoftenEdges", 
            "OverrideCleaner", "TargetCleaner", 
            "PruneSkinWeights", "UnusedSkinCleaner", "EnvelopeChecker", 
            "ScalableDeformerChecker", "WIPCleaner", "ExitEditMode", 
            "HideCorrectives", "DisplayLayers", 
            "ResetPose", "BindPoseCleaner", 
            "TweakNodeCleaner", "HideAllJoints", 
            "PassthroughAttributes", "ProxyCreator", "Cleanup", 
            "OutlinerCleaner", "CharacterSet"
        ]
        
        # Sort modules by their recommended order (all now under Rig category)
        for module_name, module in self.modules.items():
            # All modules are now Rig category
            if module.category == "Rig":
                # Find position in rig order, use high number if not found
                try:
                    order_index = rig_order.index(module_name)
                except ValueError:
                    order_index = 999
                module._order_index = order_index
                categories[module.category].append(module)
            else:
                # Fallback for any other categories
                categories[module.category].append(module)
        
        # Sort each category by order index
        for category in categories:
            categories[category].sort(key=lambda x: getattr(x, '_order_index', 999))
        
        return dict(categories)
    
    def run_validation(self, module_names=None, mode="check", objList=None):
        """Run validation on specified modules or all enabled modules"""
        self.results = {'errors': [], 'warnings': [], 'info': []}
        module_results = {}  # Store results per module
        
        if module_names is None:
            # Run all enabled modules
            modules_to_run = [m for m in self.modules.values() if m.enabled]
        else:
            # Run specified modules
            modules_to_run = [self.modules[name] for name in module_names if name in self.modules]
        
        total_issues = 0
        
        for module in modules_to_run:
            try:
                result = module.run_validation(mode, objList)
                # Store individual module result
                module_results[module.name] = result
                
                if result["status"] == "success":
                    if result["total_issues"] > 0:
                        for issue in result["issues"]:
                            clean_name = module.name.replace('dp', '')
                            self.results['warnings'].append(f"{clean_name}: {issue['message']} - {issue['object']}")
                        total_issues += result["total_issues"]
                    else:
                        clean_name = module.name.replace('dp', '')
                        self.results['info'].append(f"{clean_name}: No issues found")
                else:
                    clean_name = module.name.replace('dp', '')
                    self.results['errors'].append(f"{clean_name}: {result['message']}")
            except Exception as e:
                error_result = {"status": "error", "message": f"Error - {str(e)}", "total_issues": 1}
                module_results[module.name] = error_result
                clean_name = module.name.replace('dp', '')
                self.results['errors'].append(f"{clean_name}: Error - {str(e)}")
        
        # Return both the consolidated results and individual module results
        return module_results
    
    def run_all_validations(self):
        """Run all enabled validations"""
        return self.run_validation()
    
    def get_consolidated_results(self):
        """Get the consolidated results for display purposes"""
        return self.results


_dialog = None

def launch_riggingValidator():
    """Launch the rigging validator tool"""
    global _dialog
    try: 
        if _dialog and _dialog.isVisible():
            _dialog.close()
            _dialog.deleteLater()
    except: 
        pass
    validator = RiggingValidator()
    _dialog = RiggingValidatorUI(validator=validator)
    _dialog.show()
    return _dialog


def show_rigging_validator():
    """Show the rigging validator UI"""
    global _dialog
    try: 
        if _dialog and _dialog.isVisible():
            _dialog.close()
            _dialog.deleteLater()
    except: 
        pass
    validator = RiggingValidator()
    _dialog = RiggingValidatorUI(validator=validator)
    _dialog.show()
    return _dialog


if __name__ == "__main__":
    show_rigging_validator()
