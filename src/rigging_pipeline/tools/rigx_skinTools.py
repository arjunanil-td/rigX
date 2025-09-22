import os
import sys

# Maya imports
try:
    import maya.cmds as cmds
    import maya.OpenMayaUI as omui
    from shiboken2 import wrapInstance
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    print("Warning: Maya modules not available. This tool must be run within Maya.")

# Qt imports
from PySide2 import QtWidgets, QtCore, QtGui

# Pipeline imports
from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.tools.ui.rigx_skinTools_ui import SkinWeightsToolUI


def maya_main_window():
    if not MAYA_AVAILABLE:
         return None
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


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


class RigXSkinTools:
    """Main class for RigX Skin Tools functionality"""
    
    def __init__(self):
         self.ui = None
         
    def show_ui(self):
         """Show the RigX Skin Tools UI - closes existing instance first"""
         # Close existing window if it exists
         UIManager.close_existing_window("RigXSkinTools")
         
         # Create new UI instance
         self.ui = SkinWeightsToolUI()
         
         # Register the window
         UIManager.register_window("RigXSkinTools", self.ui)
         
         # Show the window
         self.ui.show()
         self.ui.raise_()
         self.ui.activateWindow()
    
    # ==================== SKIN TOOLS ====================
    
    def run_save_weights_single(self):
        """Save weights for a single mesh"""
        try:
            selected = cmds.ls(selection=True, transforms=True)
            if not selected:
                cmds.warning("Please select a mesh to save weights for")
                return
            
            # Use the skin weights tool's save functionality
            if self.ui:
                self.ui._on_save_single()
            else:
                cmds.warning("Skin Tools UI not available")
        except Exception as e:
            cmds.error(f"Error saving weights: {str(e)}")
    
    def run_save_weights_multiple(self):
        """Save weights for multiple meshes"""
        try:
            selected = cmds.ls(selection=True, transforms=True)
            if not selected:
                cmds.warning("Please select meshes to save weights for")
                return
            
            # Use the skin weights tool's save functionality
            if self.ui:
                self.ui._on_save_multi()
            else:
                cmds.warning("Skin Tools UI not available")
        except Exception as e:
            cmds.error(f"Error saving weights: {str(e)}")
    
    def run_load_weights_single(self):
        """Load weights for a single mesh"""
        try:
            selected = cmds.ls(selection=True, transforms=True)
            if not selected:
                cmds.warning("Please select a mesh to load weights for")
                return
            
            # Use the skin weights tool's load functionality
            if self.ui:
                self.ui._on_load_single()
            else:
                cmds.warning("Skin Tools UI not available")
        except Exception as e:
            cmds.error(f"Error loading weights: {str(e)}")
    
    def run_load_weights_multiple(self):
        """Load weights for multiple meshes"""
        try:
            selected = cmds.ls(selection=True, transforms=True)
            if not selected:
                cmds.warning("Please select meshes to load weights for")
                return
            
            # Use the skin weights tool's load functionality
            if self.ui:
                self.ui._on_load_multi()
            else:
                cmds.warning("Skin Tools UI not available")
        except Exception as e:
            cmds.error(f"Error loading weights: {str(e)}")
    
    def run_copy_weights_one_to_many(self):
        """Copy weights from one mesh to many"""
        try:
            selected = cmds.ls(selection=True, transforms=True)
            if len(selected) < 2:
                cmds.warning("Please select source mesh first, then target meshes")
                return
            
            # Use the skin weights tool's copy functionality
            if self.ui:
                self.ui._on_copy_o2m()
            else:
                cmds.warning("Skin Tools UI not available")
        except Exception as e:
            cmds.error(f"Error copying weights: {str(e)}")
    
    def run_copy_weights_many_to_one(self):
        """Copy weights from many meshes to one"""
        try:
            selected = cmds.ls(selection=True, transforms=True)
            if len(selected) < 2:
                cmds.warning("Please select source meshes first, then target mesh")
                return
            
            # Use the skin weights tool's copy functionality
            if self.ui:
                self.ui._on_copy_m2o()
            else:
                cmds.warning("Skin Tools UI not available")
        except Exception as e:
            cmds.error(f"Error copying weights: {str(e)}")

    def run_rebind_skin(self):
        """Run skin rebind for selected objects"""
        try:
            run_rebind_skin()
            print("✅ Skin rebind completed!")
        except Exception as e:
            print(f"❌ Error in skin rebind: {str(e)}")


    def run_ng_skin(self):
        """Run NgSkinTools"""
        try:
            run_ng_skin()
            print("✅ NgSkinTools completed!")
        except Exception as e:
            print(f"❌ Error in NgSkinTools: {str(e)}")

def run_ng_skin():
    """Run NgSkinTools"""
    try:
        import ngSkinTools2; ngSkinTools2.open_ui()
        print("✅ NgSkinTools completed!")
    except Exception as e:
        print(f"❌ Error in NgSkinTools: {str(e)}")

def run_rebind_skin():
    """Execute skin rebind for selected objects using MEL script"""
    try:
        import maya.mel as mel
        # Get selected objects
        selected_objects = cmds.ls(selection=True)
        if not selected_objects:
            cmds.warning("Please select objects to rebind skin for")
            return
        
        # Ensure MEL procs are defined before calling
        setup_rebind_mel_functions()
        
        # Execute MEL script for rebinding
        mel_script = (
            "string $object[] = `ls -sl`;\n"
            "for ($temp in $object) { rig_skinRebind($temp); }"
        )
        
        # Execute the MEL script
        mel.eval(mel_script)
        
        # Show success message
        cmds.inViewMessage(
            amg="✅ Skin rebind completed successfully!",
            pos="midCenter",
            fade=True,
            fadeInTime=0.3,
            fadeOutTime=1.0,
            holdTime=2.0,
            backColor=[0.1, 0.1, 0.1],
            textColor=[0.33, 0.85, 1.0],
            fontSize="large"
        )
        
    except Exception as e:
        cmds.error(f"Error in skin rebind: {str(e)}")


def setup_rebind_mel_functions():
    """Setup the MEL functions required for skin rebinding"""
    try:
        import maya.mel as mel
        # Define the MEL functions
        mel_functions = """
        global proc string rig_skinGetCluster(string $object)
        {
            string $toke[];
            string $history[];

            string $shape = `rig_getShape $object`;
            if($shape=="") $shape = `match "^[^.]*" $object`;
            $history = `listHistory -pdo 1 -lf 1 $shape`;
            $history = `ls -type "skinCluster" $history`;

            return $history[0];
        }

        global proc string[] rig_skinGetInfluences(string $object)
        {
            if(`objExists $object`)
            {
                string $skinCluster;
                if(`nodeType $object`=="skinCluster") $skinCluster = $object;
                else    $skinCluster = rig_skinGetCluster($object);
               
                if(`objExists $skinCluster`)
                {
                    string $infs[] = `listConnections -s 1 ($skinCluster + ".matrix")`;
                    return $infs;
                }
            }
            return {};
        }

        global proc rig_skinRebind(string $object)
        {
            string $skinCluster = "";
            if(`nodeType $object` == "skinCluster")
                $skinCluster = $object;
            else
                $skinCluster = rig_skinGetCluster($object);
           
            string $influences[] = rig_skinGetInfluences($skinCluster);
            for($inf in $influences)
            {
                string $bindPoses[] = rig_skinGetBindPose($inf);
                if(size($bindPoses) > 0)
                    delete $bindPoses;
            }
            if(`objExists $skinCluster`)
            {
                skinCluster -e -ubk $skinCluster;
                string $deformedGeo[] = `skinCluster -q -g $skinCluster`;
                skinCluster -tsb $influences $deformedGeo[0];
            }
        }

        global proc string[] rig_skinGetBindPose(string $object)
        {
            if(`objExists ($object+".bindPose")`)
                return `listConnections -d 1 -s 0 ($object+".bindPose")`;
            return {};
        }

        global proc string[] rig_getShapes(string $object)
        {
            if(!`objExists $object`)
            {
                warning ("+rig_shape(): rig_getShapes: " + $object + " does not exist.");
                return {};
            }
           
            $object = rig_nameLong($object);
            $object = `match "^[^\.]*" $object`;
           
            if(`nodeType $object` == "objectSet") return {};
           
            string $shapes[] = `listRelatives -s -f $object`;
            string $transform[];
            string $object_long[];
            string $shapes_check[];
            string $shape_check;
           
            string $shapes_confirmed[];
           
            if(size($shapes)==0)
            {
                if(`nodeType $object` == "transform") return {};
               
                $transform = `listRelatives -p -f $object`;
               
                if(size($transform)==0) return {};
               
                $shapes_check  = `listRelatives -s -f $transform`;
                string $shape_check;
                for($shape_check in $shapes_check)
                {
                    if($shape_check==$object) $shapes_confirmed =  $shapes_check;
                }
            }
            else
             $shapes_confirmed = $shapes;   
            
            string $shapes_confirmed_filtered[];
           
             string $shape_test;
             for($shape_test in $shapes_confirmed)
             {
                 if(`attributeQuery -ex -n $shape_test "intermediateObject"`)
                {
                    if(`getAttr ($shape_test + ".intermediateObject")`==1) continue;
                }
                $shapes_confirmed_filtered[size($shapes_confirmed_filtered)] = $shape_test;
             }
             return $shapes_confirmed_filtered;
        }

        global proc string rig_nameLong(string $name)
        {
            string $long[] = `ls -l $name`;
            return $long[0];
        }

        global proc string rig_getShape(string $object)
        {
            string $shapes[] = rig_getShapes($object);
            return $shapes[0];
        }
        """
        
        # Execute the MEL functions
        mel.eval(mel_functions)
        print("✅ MEL functions for skin rebind loaded successfully!")
        
    except Exception as e:
        print(f"❌ Error setting up MEL functions: {str(e)}")


def launch_skinTools():
    """Launch the RigX Skin Tools"""
    try:
        # Setup MEL functions for rebind functionality
        setup_rebind_mel_functions()
        
        skin_tools = RigXSkinTools()
        skin_tools.show_ui()
        print("✅ RigX Skin Tools launched successfully!")
        return skin_tools
    except Exception as e:
        print(f"❌ Error launching RigX Skin Tools: {str(e)}")
        return None


def main():
    """Main function to run the RigX Skin Tools"""
    return launch_skinTools()


if __name__ == "__main__":
    main()
