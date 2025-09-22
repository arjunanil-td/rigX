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
                from rigging_pipeline.version import get_version_string
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
        from rigging_pipeline.version import get_detailed_version, get_version_string
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
    
    # ————— 4) Your existing show-reload logic —————
    try:
        show_name = os.environ.get("RIGX_SHOW") or detect_show_from_workspace()
        if not show_name:
            message = "ℹ️ No RIGX_SHOW; skipping show reload"
            print(message)
            if notification:
                # The new notification doesn't have a log_text, so we can't add a message here.
                # The new notification is a simple success message.
                pass
            return

        # ————— 2) Determine show_name —————
        show_name = os.environ.get("RIGX_SHOW")
        if not show_name:
            show_name = detect_show_from_workspace()

        if not show_name:
            message = "ℹ️ Could not detect a show; skipping show reload."
            print(message)
            if notification:
                # The new notification doesn't have a log_text, so we can't add a message here.
                # The new notification is a simple success message.
                pass
            return

        # ————— 3) Find show_dir on disk —————
        # bootstrap.py lives in <repo_root>/src/rigging_pipeline/bootstrap.py
        base_dir = os.path.dirname(__file__)           # …/rigX/src/rigging_pipeline
        repo_root = os.path.abspath(os.path.join(base_dir, "..", ".."))  # …/rigX

        candidates = [
            os.path.join(repo_root, "shows", show_name),
            os.path.join(repo_root, "src", "shows", show_name),
        ]

        show_dir = None
        for cand in candidates:
            if os.path.isdir(cand):
                show_dir = cand
                break

        if not show_dir:
            message = (
                f"⚠️ Show folder not found in either:\n"
                f"   • {candidates[0]}\n"
                f"   • {candidates[1]}"
            )
            print(message)
            if notification:
                # The new notification doesn't have a log_text, so we can't add a message here.
                # The new notification is a simple success message.
                pass
            return

        # — Insert the PARENT of show_dir into sys.path (so Python can import `show_name`) —
        parent_of_show = os.path.dirname(show_dir)   # …/rigX/shows or …/rigX/src/shows
        if parent_of_show not in sys.path:
            sys.path.insert(0, parent_of_show)

        # — Now import + reload the show package —
        try:
            show_pkg = __import__(show_name)
            _reload_package(show_pkg)
            message = f"✅ Show '{show_name}' reloaded (from {show_dir})."
            print(message)
            if notification:
                # The new notification doesn't have a log_text, so we can't add a message here.
                # The new notification is a simple success message.
                pass
        except Exception as e:
            import traceback
            message = f"❌ Failed to reload show '{show_name}': {str(e)}"
            print(message)
            print(f"📁 File: {__file__}")
            print("📋 Full traceback:")
            traceback.print_exc()
            has_errors = True
            if notification:
                # The new notification doesn't have a log_text, so we can't add a message here.
                # The new notification is a simple success message.
                pass
                
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
