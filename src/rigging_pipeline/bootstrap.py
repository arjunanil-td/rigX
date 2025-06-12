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

def reload_all():
    """
    1) Purge all rigging_pipeline modules from sys.modules.
    2) Re-import + reload core rigging_pipeline.
    3) Reload UI module so you see edits immediately.
    4) (Optional) reload your show package as before.
    """
    # ————— 1) Purge all existing rigging_pipeline modules —————
    to_delete = [name for name in sys.modules
                 if name == "rigging_pipeline" or name.startswith("rigging_pipeline.")]
    for name in to_delete:
        del sys.modules[name]

    # ————— 2) Reload core pipeline —————
    try:
        import rigging_pipeline
        _reload_package(rigging_pipeline)
        print("✅ Core pipeline Loaded")
    except Exception as e:
        print("⚠️ Failed to reload core pipeline:", e)

    # ————— 3) Reload the Model Toolkit UI (and any UI files) —————
    try:
        ui_mod = importlib.import_module("rigging_pipeline.tools.ui.rigx_model_toolkit_ui")
        importlib.reload(ui_mod)
        print("✅ Model Toolkit Loaded")
    except Exception as e:
        print("⚠️ Could not reload model_toolkit_ui:", e)

    # If you have other UI modules you edit often, repeat the same:
    # e.g. reload rename_tool_ui, finalizer_ui, etc.
    # 
    # ————— 4) Your existing show-reload logic —————
    show_name = os.environ.get("RIGX_SHOW") or detect_show_from_workspace()
    if not show_name:
        print("ℹ️ No RIGX_SHOW; skipping show reload")
        return

    # ————— 2) Determine show_name —————
    show_name = os.environ.get("RIGX_SHOW")
    if not show_name:
        show_name = detect_show_from_workspace()

    if not show_name:
        print("ℹ️ Could not detect a show; skipping show reload.")
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
        print(
            f"⚠️ Show folder not found in either:\n"
            f"   • {candidates[0]}\n"
            f"   • {candidates[1]}"
        )
        return

    # — Insert the PARENT of show_dir into sys.path (so Python can import `show_name`) —
    parent_of_show = os.path.dirname(show_dir)   # …/rigX/shows or …/rigX/src/shows
    if parent_of_show not in sys.path:
        sys.path.insert(0, parent_of_show)

    # — Now import + reload the show package —
    try:
        show_pkg = __import__(show_name)
        _reload_package(show_pkg)
        print(f"✅ Show '{show_name}' reloaded (from {show_dir}).")
    except Exception as e:
        print(f"⚠️ Failed to reload show '{show_name}': {e}")
