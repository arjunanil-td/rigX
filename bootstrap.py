import sys
import importlib
import pkgutil
import sys

def reload_package(package, package_name=None):
    """
    Recursively reload all submodules in a given package.
    
    Args:
        package (module): The imported package module.
        package_name (str): Optional name to filter submodules (required in some nested reloads).
    """
    name = package_name or package.__name__

    print(f"\n🔁 Reloading package: {name}")

    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, prefix=f"{name}."):
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
                print(f"✅ Reloaded: {module_name}")
            except Exception as e:
                print(f"❌ Failed to reload {module_name}: {e}")
        else:
            __import__(module_name)
            print(f"📦 Imported: {module_name}")


repo_path = "Q:/references/rigging/Scripts/riggingBase"
if repo_path not in sys.path:
    sys.path.append(repo_path)

# Core modules
import main
import utils
import kntr
import file
import nodes


from bootstrap import reload_package  # or just define it inline

reload_package(utils)
reload_package(kntr)
reload_package(nodes)
importlib.reload(main)

print("✅ Bootstrap complete.")
