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

def _show_simple_notification():
    """Show a simple floating notification that just says 'All loaded successfully!'"""
    try:
        # Use Maya's built-in inViewMessage which is guaranteed to be visible
        import maya.cmds as cmds
        
        # Show a prominent message in the center of the viewport
        cmds.inViewMessage(
            amg="✅ RigX: All Loaded Successfully!",
            pos="midCenter",
            fade=True,
            fadeInTime=0.3,
            fadeOutTime=1.0,
            holdTime=3.0,
            backColor=[0.1, 0.1, 0.1],  # Dark background
            textColor=[0.33, 0.85, 1.0],  # RigX blue color
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
    print(f"🚀 Starting RigX reload from: {__file__}")
    
    # Show dialog if available
    notification = _show_simple_notification()
    
    # ————— 1) Purge all existing rigging_pipeline modules —————
    try:
        to_delete = [name for name in sys.modules
                     if name == "rigging_pipeline" or name.startswith("rigging_pipeline.")]
        for name in to_delete:
            del sys.modules[name]
        print("🧹 Purged existing rigging_pipeline modules")
    except Exception as e:
        import traceback
        print(f"❌ Error purging modules: {str(e)}")
        print(f"📁 File: {__file__}")
        print("📋 Full traceback:")
        traceback.print_exc()

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
        if notification:
            # The new notification doesn't have a log_text, so we can't add a message here.
            # The new notification is a simple success message.
            pass

    # ————— 3) Reload the Model Toolkit UI (and any UI files) —————
    try:
        ui_mod = importlib.import_module("rigging_pipeline.tools.ui.rigx_model_toolkit_ui")
        importlib.reload(ui_mod)
        message = "✅ Model Toolkit Loaded"
        print(message)
        if notification:
            # The new notification doesn't have a log_text, so we can't add a message here.
            # The new notification is a simple success message.
            pass
    except Exception as e:
        import traceback
        message = f"❌ Could not reload model_toolkit_ui: {str(e)}"
        print(message)
        print(f"📁 File: {__file__}")
        print("📋 Full traceback:")
        traceback.print_exc()
        if notification:
            # The new notification doesn't have a log_text, so we can't add a message here.
            # The new notification is a simple success message.
            pass

    # If you have other UI modules you edit often, repeat the same:
    # e.g. reload rename_tool_ui, finalizer_ui, etc.
    # 
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
    
    # Update dialog status when done
    if notification:
        # The new notification doesn't have a status_label, so we can't update it here.
        # The new notification is a simple success message.
        pass
