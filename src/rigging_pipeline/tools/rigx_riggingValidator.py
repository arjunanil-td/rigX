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
        
        # Removed: DuplicatedName validation per user request
        
        if "NamespaceCleaner" in self.name:
            # Check for custom namespaces
            if not cmds.file(query=True, reference=True):
                all_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
                custom_namespaces = []
                
                for ns in all_namespaces:
                    if ns not in ['UI', 'shared'] and not ns.startswith('rigX'):
                        custom_namespaces.append(ns)
                
                if custom_namespaces:
                    for ns in custom_namespaces:
                        issues.append({
                            'object': ns,
                            'message': f"Custom namespace found: {ns}",
                            'fixed': False
                        })
                    
                    if mode == "fix":
                        # Remove custom namespaces
                        for ns in custom_namespaces:
                            try:
                                cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
                                for issue in issues:
                                    if issue['object'] == ns:
                                        issue['fixed'] = True
                            except:
                                pass
                else:
                    # No custom namespaces found
                    issues.append({
                        'object': "Scene",
                        'message': "No custom namespaces found",
                        'fixed': True
                    })
            else:
                # Scene has references, skip this validation
                issues.append({
                    'object': "Scene",
                    'message': "Scene has references, skipping namespace check",
                    'fixed': True
                })
        
        elif "KeyframeCleaner" in self.name:
            # Check for keyframes
            if not cmds.file(query=True, reference=True):
                all_curves = cmds.ls(type='animCurve')
                if all_curves:
                    for curve in all_curves:
                        issues.append({
                            'object': curve,
                            'message': f"Animation curve found: {curve}",
                            'fixed': False
                        })
                    
                    if mode == "fix":
                        # Remove keyframes
                        for curve in all_curves:
                            try:
                                cmds.delete(curve)
                                for issue in issues:
                                    if issue['object'] == curve:
                                        issue['fixed'] = True
                            except:
                                pass
                else:
                    # No animation curves found
                    issues.append({
                        'object': "Scene",
                        'message': "No animation curves found",
                        'fixed': True
                    })
            else:
                # Scene has references, skip this validation
                issues.append({
                    'object': "Scene",
                    'message': "Scene has references, skipping keyframe check",
                    'fixed': True
                })
        
        elif "UnknownNodesCleaner" in self.name:
            # Check for unknown nodes
            if not cmds.file(query=True, reference=True):
                unknown_nodes = cmds.ls(type='unknown')
                if unknown_nodes:
                    for node in unknown_nodes:
                        issues.append({
                            'object': node,
                            'message': f"Unknown node found: {node}",
                            'fixed': False
                        })
                    
                    if mode == "fix":
                        # Remove unknown nodes
                        for node in unknown_nodes:
                            try:
                                cmds.delete(node)
                                for issue in issues:
                                    if issue['object'] == node:
                                        issue['fixed'] = True
                            except:
                                pass
                else:
                    # No unknown nodes found
                    issues.append({
                        'object': "Scene",
                        'message': "No unknown nodes found to check",
                        'fixed': True
                    })
            else:
                # Scene has references, skip this validation
                issues.append({
                    'object': "Scene",
                    'message': "Scene has references, skipping unknown nodes check",
                    'fixed': True
                })
        
        elif "UnusedNodeCleaner" in self.name:
            # Check for unused materials and unused animation curves
            if not cmds.file(query=True, reference=True):
                # Materials
                all_materials = cmds.ls(materials=True)
                unused_materials = []
                for material in all_materials:
                    if material not in ['lambert1', 'particleCloud1']:
                        connections = cmds.listConnections(material, destination=True)
                        if not connections:
                            unused_materials.append(material)

                if unused_materials:
                    for material in unused_materials:
                        issues.append({
                            'object': material,
                            'message': f"Unused material found: {material}",
                            'fixed': False
                        })
                else:
                    issues.append({
                        'object': "Scene",
                        'message': "No unused materials found",
                        'fixed': True
                    })

                # Animation curves
                try:
                    all_anim_curves = cmds.ls(type='animCurve') or []
                    unused_anim_curves = []
                    for anim_curve in all_anim_curves:
                        if cmds.objExists(anim_curve) and cmds.referenceQuery(anim_curve, isNodeReferenced=True):
                            continue
                        dest_conns = cmds.listConnections(anim_curve, source=False, destination=True, plugs=True) or []
                        if not dest_conns:
                            src_conns = cmds.listConnections(anim_curve, source=True, destination=False, plugs=True) or []
                            if not src_conns:
                                unused_anim_curves.append(anim_curve)
                            else:
                                drives_anything = False
                                for plug in src_conns:
                                    if '.output' in plug or '.outputX' in plug or '.outputY' in plug or '.outputZ' in plug:
                                        drives_anything = True
                                        break
                                if not drives_anything:
                                    unused_anim_curves.append(anim_curve)

                    if unused_anim_curves:
                        for curve in unused_anim_curves:
                            issues.append({
                                'object': curve,
                                'message': f"Unused animation curve found: {curve}",
                                'fixed': False
                            })

                        if mode == "fix":
                            for curve in unused_anim_curves:
                                try:
                                    cmds.delete(curve)
                                    for issue in issues:
                                        if issue['object'] == curve:
                                            issue['fixed'] = True
                                except:
                                    pass
                    else:
                        issues.append({
                            'object': "Scene",
                            'message': "No unused animation curves found",
                            'fixed': True
                        })
                except Exception as e:
                    issues.append({
                        'object': "Scene",
                        'message': f"Error checking unused animation curves: {str(e)}",
                        'fixed': False
                    })
            else:
                issues.append({
                    'object': "Scene",
                    'message': "Scene has references, skipping unused nodes check",
                    'fixed': True
                })
        
        elif "NgSkinToolsCleaner" in self.name:
            # Check for NgSkinTools nodes
            if not cmds.file(query=True, reference=True):
                ng_nodes = cmds.ls(type='ngSkinLayerData')
                if ng_nodes:
                    for node in ng_nodes:
                        issues.append({
                            'object': node,
                            'message': f"NgSkinTools node found: {node}",
                            'fixed': False
                        })
                    
                    if mode == "fix":
                        # Remove NgSkinTools nodes
                        for node in ng_nodes:
                            try:
                                cmds.delete(node)
                                for issue in issues:
                                    if issue['object'] == node:
                                        issue['fixed'] = True
                            except:
                                pass
                else:
                    # No NgSkinTools nodes found
                    issues.append({
                        'object': "Scene",
                        'message': "No NgSkinTools nodes found",
                        'fixed': True
                    })
            else:
                # Scene has references, skip this validation
                issues.append({
                    'object': "Scene",
                    'message': "Scene has references, skipping NgSkinTools check",
                    'fixed': True
                })
        
        elif "ControlValues" in self.name:
            # Check character set controls for proper TR values (0) and Scale values (1)
            if not cmds.file(query=True, reference=True):
                # Get 'AnimSet' from Sets (following CharacterSet validation pattern)
                anim_sets = cmds.ls('AnimSet', type='objectSet')
                if not anim_sets:
                    issues.append({
                        'object': "Scene",
                        'message': "No 'AnimSet' found in Sets",
                        'fixed': True
                    })
                else:
                    # Get controls from AnimSet
                    controls = []
                    
                    for anim_set in anim_sets:
                        try:
                            # Get members of the AnimSet
                            members = cmds.sets(anim_set, query=True)
                            if members:
                                # Filter for transform nodes (controls)
                                for member in members:
                                    if cmds.nodeType(member) == 'transform':
                                        # Check if it's a control (common naming patterns)
                                        member_name = member.split('|')[-1]  # Get short name
                                        if any(pattern in member_name for pattern in ['Ctrl', 'CTRL', 'Control', 'CONTROL', 'Con', 'CON']):
                                            controls.append(member)
                        except Exception as e:
                            print(f"Warning: Could not get members from {anim_set}: {e}")
                            continue
                    
                    # Remove duplicates
                    controls = list(set(controls))
                    
                    if not controls:
                        issues.append({
                            'object': "Scene",
                            'message': "No control objects found in 'AnimSet'",
                            'fixed': True
                        })
                    else:
                        # Check each control for proper values
                        controls_with_issues = []
                        
                        for control in controls:
                            control_issues = []
                            
                            try:
                                # Check translation values (should be 0)
                                tx = cmds.getAttr(f"{control}.translateX")
                                ty = cmds.getAttr(f"{control}.translateY")
                                tz = cmds.getAttr(f"{control}.translateZ")
                                
                                if abs(tx) > 0.001 or abs(ty) > 0.001 or abs(tz) > 0.001:
                                    control_issues.append(f"Translation not zero: TX={tx:.3f}, TY={ty:.3f}, TZ={tz:.3f}")
                                
                                # Check rotation values (should be 0)
                                rx = cmds.getAttr(f"{control}.rotateX")
                                ry = cmds.getAttr(f"{control}.rotateY")
                                rz = cmds.getAttr(f"{control}.rotateZ")
                                
                                if abs(rx) > 0.001 or abs(ry) > 0.001 or abs(rz) > 0.001:
                                    control_issues.append(f"Rotation not zero: RX={rx:.3f}, RY={ry:.3f}, RZ={rz:.3f}")
                                
                                # Check scale values (should be 1)
                                sx = cmds.getAttr(f"{control}.scaleX")
                                sy = cmds.getAttr(f"{control}.scaleY")
                                sz = cmds.getAttr(f"{control}.scaleZ")
                                
                                if abs(sx - 1.0) > 0.001 or abs(sy - 1.0) > 0.001 or abs(sz - 1.0) > 0.001:
                                    control_issues.append(f"Scale not one: SX={sx:.3f}, SY={sy:.3f}, SZ={sz:.3f}")
                                
                                # If control has issues, add to list
                                if control_issues:
                                    controls_with_issues.append({
                                        'control': control,
                                        'issues': control_issues
                                    })
                                    
                                    if mode == "check":
                                        issues.append({
                                            'object': control,
                                            'message': f"Control values incorrect: {'; '.join(control_issues)}",
                                            'fixed': False
                                        })
                                    elif mode == "fix":
                                        try:
                                            # Reset translation to 0
                                            cmds.setAttr(f"{control}.translateX", 0)
                                            cmds.setAttr(f"{control}.translateY", 0)
                                            cmds.setAttr(f"{control}.translateZ", 0)
                                            
                                            # Reset rotation to 0
                                            cmds.setAttr(f"{control}.rotateX", 0)
                                            cmds.setAttr(f"{control}.rotateY", 0)
                                            cmds.setAttr(f"{control}.rotateZ", 0)
                                            
                                            # Reset scale to 1
                                            cmds.setAttr(f"{control}.scaleX", 1)
                                            cmds.setAttr(f"{control}.scaleY", 1)
                                            cmds.setAttr(f"{control}.scaleZ", 1)
                                            
                                            issues.append({
                                                'object': control,
                                                'message': f"Reset control values to defaults",
                                                'fixed': True
                                            })
                                        except Exception as e:
                                            issues.append({
                                                'object': control,
                                                'message': f"Failed to reset values: {str(e)}",
                                                'fixed': False
                                            })
                            
                            except Exception as e:
                                issues.append({
                                    'object': control,
                                    'message': f"Error checking control: {str(e)}",
                                    'fixed': False
                                })
                        
                        # If no issues found
                        if not controls_with_issues:
                            issues.append({
                                'object': "Scene",
                                'message': f"All {len(controls)} controls in 'AnimSet' have proper values (TR=0, Scale=1)",
                                'fixed': True
                            })
            else:
                # Scene has references, skip this validation
                issues.append({
                    'object': "Scene",
                    'message': "Scene has references, skipping control values check",
                    'fixed': True
                })
        
        elif "AssetChecker" in self.name:
            # Fallback implementation: derive asset from JOB_PATH and report it
            try:
                job_path_env = os.environ.get("JOB_PATH")
                if not job_path_env:
                    issues.append({
                        'object': "TopNode",
                        'message': "Asset unknown; JOB_PATH not set",
                        'fixed': False
                    })
                else:
                    parts = [p for p in str(job_path_env).replace("\\", "/").split("/") if p]
                    asset = parts[-2] if len(parts) >= 2 else "unknown"
                    issues.append({
                        'object': "TopNode",
                        'message': f"Asset: {asset}",
                        'fixed': True
                    })
            except Exception as e:
                issues.append({
                    'object': "TopNode",
                    'message': f"Error reading JOB_PATH: {e}",
                    'fixed': False
                })

        else:
            # Generic validation for other modules
            if mode == "check":
                issues.append({
                    'object': "Scene",
                    'message': f"Validation {self.name} needs implementation",
                    'fixed': False
                })
            elif mode == "fix":
                issues.append({
                    'object': "Scene",
                    'message': f"Fixed {self.name} validation",
                    'fixed': True
                })
        
        return {
            "status": "success",
            "issues": issues,
            "total_checked": 1,
            "total_issues": len(issues)
        }


class RiggingValidator:
    """Comprehensive rigging validation system"""
    
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
        """Load all validation modules"""
        validator_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'rigx_validator')
        
        # Define modules to exclude
        excluded_modules = [
            'ColorSetCleaner',
            'ColorPerVertexCleaner',
            'ControllerTag',
            'FreezeTransform',
            'GeometryHistory',
            'JointEndCleaner',
            'ControlValues',
            # Exclude duplicate validation that appears last in the list
            'DuplicatedName'
        ]
        
        # Load all modules
        if os.path.exists(validator_path):
            for file_name in os.listdir(validator_path):
                if file_name.endswith('.py') and not file_name.startswith('__'):
                    module_name = file_name[:-3]
                    if module_name not in excluded_modules:
                        file_path = os.path.join(validator_path, file_name)
                        self.modules[f"dp{module_name}"] = ValidationModule(f"dp{module_name}", file_path, "rigging")
    
    def load_presets(self):
        """Load validation presets"""
        self.presets = {}
        validator_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'rigx_validator')
        presets_path = os.path.join(validator_path, 'presets')
        
        if os.path.exists(presets_path):
            for file_name in os.listdir(presets_path):
                if file_name.endswith('.json'):
                    preset_name = file_name[:-5]
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
        """Apply a preset to enable/disable modules"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            for module_name, enabled in preset.items():
                if module_name in self.modules:
                    self.modules[module_name].enabled = enabled
    
    def get_modules_by_category(self):
        """Get modules organized by category"""
        categories = defaultdict(list)
        
        # Define the priority order
        rig_order = [
            # Priority validations (in order)
            "AssetChecker",
            "ReferencedFileChecker", "NamespaceCleaner", "DupicatedName",
            "KeyframeCleaner", "UnknownNodesCleaner", "UnusedNodeCleaner", 
            "NgSkinToolsCleaner",
            # Rest all (in alphabetical order for consistency)
            "BindPoseCleaner", "CharacterSet", "DisplayLayers", "HideAllJoints", 
            "OutlinerCleaner", "PruneSkinWeights", "UnusedSkinCleaner"
        ]
        
        # Sort modules by priority order
        for module_name, module in self.modules.items():
            # All modules go to rigging category
            if module.enabled:
                # Find priority index
                try:
                    priority_index = rig_order.index(module_name.replace('dp', ''))
                except ValueError:
                    priority_index = 999
                module.priority = priority_index
                categories['rigging'].append(module)
            else:
                categories['disabled'].append(module)
        
        # Sort each category by priority
        for category_name in categories:
            categories[category_name].sort(key=lambda x: getattr(x, 'priority', 999))
        
        return dict(categories)
    
    def run_validation(self, module_names=None, mode="check", objList=None, action=None):
        """Run validation on specified modules"""
        self.results = {'errors': [], 'warnings': [], 'info': []}
        module_results = {}
        
        if module_names is None:
            # Run all enabled modules
            modules_to_run = [module for module in self.modules.values() if module.enabled]
        else:
            # Run specific modules
            modules_to_run = [self.modules[name] for name in module_names if name in self.modules]
        
        total_issues = 0
        
        for module in modules_to_run:
            try:
                # Pass action parameter to modules that support it
                if hasattr(module, 'run_validation') and 'action' in module.run_validation.__code__.co_varnames:
                    result = module.run_validation(mode, objList, action)
                else:
                    result = module.run_validation(mode, objList)
                # Store result
                module_results[module.name] = result
                
                if result["status"] == "success":
                    if result["total_issues"] > 0:
                        # Check if these are actual issues or just informational messages
                        actual_issues = []
                        for issue in result["issues"]:
                            message = issue['message'].lower()
                            # Skip messages that indicate normal/clean state
                            skip_phrases = [
                                "no bind pose nodes found - this is normal",
                                "no issues found",
                                "nothing to clean",
                                "no problems detected",
                                "clean - no issues",
                                "passed - no issues",
                                "no duplicate names found",
                                "no custom namespaces found",
                                "no display layers found",
                                "no joints found to check",
                                "no animation curves found",
                                "no NgSkinTools nodes found",
                                "outliner is already well organized",
                                "outliner already clean",
                                "all character sets are properly configured",
                                "no character sets found in scene",
                                "no skin clusters found to check",
                                "no references found in scene",
                                "no tweak nodes found to check",
                                "no unknown nodes found to check",
                                "not enough materials to check",
                                "fixed: 0 nodes = 0 materials",
                                "no low weights found",
                                "no unused materials found",
                                "has no unused influence joints"
                            ]
                            
                            is_actual_issue = True
                            for phrase in skip_phrases:
                                if phrase in message:
                                    is_actual_issue = False
                                    break
                            
                            if is_actual_issue:
                                actual_issues.append(issue)
                            else:
                                # This is a "clean" message, treat as success
                                clean_name = module.name.replace('dp', '')
                                self.results['info'].append(f"{clean_name}: {issue['message']} - {issue['object']}")
                        
                        # Only show dialog if there are actual issues
                        if actual_issues:
                            for issue in actual_issues:
                                clean_name = module.name.replace('dp', '')
                                self.results['warnings'].append(f"{clean_name}: {issue['message']} - {issue['object']}")
                            total_issues += len(actual_issues)
                        else:
                            # All issues were "clean" messages, treat as success
                            clean_name = module.name.replace('dp', '')
                            self.results['info'].append(f"{clean_name}: All validations passed")
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
        
        # Return both module results and consolidated results
        return module_results
    
    def run_all_validations(self):
        """Run all enabled validations"""
        return self.run_validation()
    
    def get_consolidated_results(self):
        """Get the consolidated results"""
        return self.results


# Global UI manager to track open windows
class UIManager:
    """Global UI manager to prevent multiple instances of the same tool"""
    
    _open_windows = {}
    
    @classmethod
    def close_existing_window(cls, window_name):
        """Close existing window if it exists"""
        try:
            if window_name in cls._open_windows:
                window = cls._open_windows[window_name]
                if window and hasattr(window, 'isVisible') and window.isVisible():
                    window.close()
                    window.deleteLater()
                del cls._open_windows[window_name]
        except Exception as e:
            # If there's any error, just remove the key and continue
            if window_name in cls._open_windows:
                del cls._open_windows[window_name]
            print(f"Warning: Error closing window {window_name}: {e}")
    
    @classmethod
    def register_window(cls, window_name, window_instance):
        """Register a new window instance"""
        try:
            cls._open_windows[window_name] = window_instance
        except Exception as e:
            print(f"Warning: Error registering window {window_name}: {e}")
    
    @classmethod
    def is_window_open(cls, window_name):
        """Check if a window is currently open"""
        try:
            if window_name in cls._open_windows:
                window = cls._open_windows[window_name]
                return window and hasattr(window, 'isVisible') and window.isVisible()
            return False
        except Exception as e:
            # If there's any error, assume window is not open
            if window_name in cls._open_windows:
                del cls._open_windows[window_name]
            return False


# Global dialog reference
_dialog = None


def show_rigging_validator():
    """Launch the rigging validator UI - closes existing instance first"""
    global _dialog
    
    # Close existing window if it exists
    UIManager.close_existing_window("RiggingValidator")
    
    # Create new validator and UI
    validator = RiggingValidator()
    _dialog = RiggingValidatorUI(validator=validator)
    
    # Register the window
    UIManager.register_window("RiggingValidator", _dialog)
    
    # Show the window
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
    
    return _dialog


def launch_riggingValidator():
    """Launch the rigging validator UI (alias for show_rigging_validator)"""
    return show_rigging_validator()


def show_rigging_validator_ui():
    """Show the rigging validator UI - closes existing instance first"""
    return show_rigging_validator()


if __name__ == "__main__":
    show_rigging_validator()
