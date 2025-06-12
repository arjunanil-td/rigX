import os
import maya.cmds as cmds

def import_flat(file_path):
    """
    Import a Maya file with all of its namespaces stripped away.
    Any new namespaces created by the import will be merged into root.
    """
    if not os.path.isfile(file_path):
        cmds.error(f"File not found: {file_path}")

    # 1. Get namespaces before import
    before = set(cmds.namespaceInfo(listOnlyNamespaces=True))

    # 2. Import the file (this usually creates a namespace)
    cmds.file(
        file_path,
        i=True,
        namespace=":",               # root namespace
        mergeNamespacesOnClash=True,
        ignoreVersion=True
    )

    # 3. Get namespaces after import
    after = set(cmds.namespaceInfo(listOnlyNamespaces=True))

    # 4. The newly created ones are in (after - before)
    new_ns = after - before

    # 5. Merge & remove each new namespace
    for ns in new_ns:
        # skip Maya internal namespaces
        if ns in ("UI", "shared"): 
            continue
        try:
            cmds.namespace(
                removeNamespace=ns,
                mergeNamespaceWithRoot=True
            )
            print(f"➕ Merged namespace '{ns}' back into root")
        except Exception as e:
            print(f"⚠️ Could not remove namespace '{ns}': {e}")
