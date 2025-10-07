import os
import sys
import importlib
import pkgutil

from rigging_pipeline.utils.utils_job import detect_show_from_workspace

def _reload_package(package):
    """
    Reload a package and all its submodules.
    """
    for _, mod_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])

def _show_simple_notification(success=True):
    """Show a simple floating notification that says success or failure"""
    try:
        # Use Maya's built-in inViewMessage which is guaranteed to be visible
        import maya.cmds as cmds
        
        if success:
            # Try to get version info for the message
            try:
                import sys
                import os
                # Add rigX root to path to import version
                rigx_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if rigx_root not in sys.path:
                    sys.path.insert(0, rigx_root)
                from version import get_version_string
                version_info = get_version_string()
                message = f"✅ {version_info} - All Loaded Successfully!"
            except ImportError:
                message = "✅ RigX: All Loaded Successfully!"
            text_color = [0.33, 0.85, 1.0]  # RigX blue color
        else:
            # Show failure message
            message = "❌ RigX: Failed to Load Scripts"
            text_color = [1.0, 0.33, 0.33]  # Red color for errors
        
        # Show a prominent message in the center of the viewport
        cmds.inViewMessage(
            amg=message,
            pos="midCenter",
            fade=True,
            fadeInTime=0.3,
            fadeOutTime=1.0,
            holdTime=3.0,
            backColor=[0.1, 0.1, 0.1],  # Dark background
            textColor=text_color,
            fontSize="large"
        )
        
        return "maya_message"
        
    except Exception as e:
        import traceback
        print(f"❌ Error showing notification: {str(e)}")
        print(f"📁 File: {__file__}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return None

def reload_all():
    """
    1) Purge all rigging_pipeline modules from sys.modules.
    2) Re-import + reload core rigging_pipeline.
    3) Reload UI module so you see edits immediately.
    4) (Optional) reload your show package as before.
    """
    
    # Import and display version information
    try:
        import sys
        import os
        # Add rigX root to path to import version
        rigx_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if rigx_root not in sys.path:
            sys.path.insert(0, rigx_root)
        from version import get_detailed_version, get_version_string
        print(get_detailed_version())
    except ImportError:
        print("⚠️ Version information not available")
    
    # Track if any errors occurred
    has_errors = False
    
    # Show dialog if available
    notification = _show_simple_notification(success=True)
    
    # ————— 1) Purge all existing rigging_pipeline modules —————
    try:
        to_delete = [name for name in sys.modules
                     if name == "rigging_pipeline" or name.startswith("rigging_pipeline.")]
        for name in to_delete:
            del sys.modules[name]
    except Exception as e:
        import traceback
        print(f"❌ Error purging modules: {str(e)}")
        print(f"📁 File: {__file__}")
        print("📋 Full traceback:")
        traceback.print_exc()
        has_errors = True

    # ————— 2) Reload core pipeline —————
    try:
        import rigging_pipeline
        _reload_package(rigging_pipeline)
        message = "✅ Core pipeline Loaded"
        print(message)
        if notification:
            # The new notification doesn't have a log_text, so we can't add a message here.
            # The new notification is a simple success message.
            pass
    except Exception as e:
        import traceback
        message = f"❌ Failed to reload core pipeline: {str(e)}"
        print(message)
        print(f"📁 File: {__file__}")
        print("📋 Full traceback:")
        traceback.print_exc()
        has_errors = True
        if notification:
            # The new notification doesn't have a log_text, so we can't add a message here.
            # The new notification is a simple success message.
            pass

    # ————— 3) Reload UI files (if any) —————
    # Note: Model toolkit UI removed to avoid circular imports
    # If you have other UI modules you edit often, add them here:
    # e.g. reload rename_tool_ui, finalizer_ui, etc.
    
    # ————— 4) Auto-detect and reload ALL shows —————
    try:
        # bootstrap.py lives in <repo_root>/src/rigging_pipeline/bootstrap.py
        base_dir = os.path.dirname(__file__)           # …/rigX/src/rigging_pipeline
        repo_root = os.path.abspath(os.path.join(base_dir, "..", ".."))  # …/rigX

        # Look for shows directory
        shows_dir = os.path.join(repo_root, "src", "shows")
        if not os.path.exists(shows_dir):
            shows_dir = os.path.join(repo_root, "shows")
        
        if not os.path.exists(shows_dir):
            message = f"⚠️ Shows directory not found at {shows_dir}"
            print(message)
            return

        # Get all show folders
        all_folders = []
        for item in os.listdir(shows_dir):
            item_path = os.path.join(shows_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                all_folders.append(item)

        
        if not all_folders:
            message = f"ℹ️ No show folders found in {shows_dir}"
            print(message)
            return

        # Add shows directory to sys.path
        if shows_dir not in sys.path:
            sys.path.insert(0, shows_dir)

        # Load each show folder
        loaded_shows = []
        failed_shows = []
        
        for show_name in all_folders:
            try:
                # Try to import as package if it has __init__.py
                init_file = os.path.join(shows_dir, show_name, "__init__.py")
                if os.path.exists(init_file):
                    show_pkg = __import__(show_name)
                    _reload_package(show_pkg)
                    loaded_shows.append(show_name)
                else:
                    # Just acknowledge the folder exists
                    loaded_shows.append(show_name)
            except Exception as e:
                failed_shows.append((show_name, str(e)))
                has_errors = True

        # Then individual show messages
        for show_name in loaded_shows:
            print(f"✅ Show '{show_name}' loaded")
            
        if failed_shows:
            print(f"⚠️ Failed to load {len(failed_shows)} show(s): {', '.join([name for name, _ in failed_shows])}")
                
    except Exception as e:
        import traceback
        print(f"❌ Error in show reload logic: {str(e)}")
        print(f"📁 File: {__file__}")
        print("📋 Full traceback:")
        traceback.print_exc()
        has_errors = True
    
    # Show final notification based on success/failure
    if has_errors:
        # Show failure notification
        _show_simple_notification(success=False)
    
    # Update dialog status when done
    if notification:
        # The new notification doesn't have a status_label, so we can't update it here.
        # The new notification is a simple success message.
        pass
