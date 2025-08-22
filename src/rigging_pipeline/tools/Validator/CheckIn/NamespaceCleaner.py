"""
NamespaceCleaner Validation Module
Cleans up namespaces
"""

import maya.cmds as cmds

DESCRIPTION = "Clean namespaces"

def run_validation(mode="check", objList=None):
    """Run the validation module"""
    issues = []
    
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
                            if _clean_namespace_recursive(ns):
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
    
    return {
        "status": "success",
        "issues": issues,
        "total_checked": len(namespaces) if namespaces else 0,
        "total_issues": len(issues)
    }

def _clean_namespace_recursive(namespace):
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
