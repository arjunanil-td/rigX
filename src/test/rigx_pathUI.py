# Houdini: create one USD Import SOP per .usd in a folder
# Run in Houdini's Python Source Editor (uses hou module)

import hou, os, glob

# ========== USER SETTINGS ==========
usd_folder     = r"Q:/METAL/projects/OSS/Production/Assets/charAhuja/rig/maya/mohanraj-s"   # <-- change to your folder
geo_node_name  = "usd_imports_geo"         # geometry container name under /obj
# ===================================

if not os.path.isdir(usd_folder):
    raise RuntimeError("usd_folder does not exist: %s" % usd_folder)

usd_files = sorted(glob.glob(os.path.join(usd_folder, "*.usd")))
if not usd_files:
    raise RuntimeError("No .usd files found in folder: %s" % usd_folder)

# helper: try to detect a USD Import SOP type name
def detect_usd_import_sop():
    cat = hou.sopNodeTypeCategory()
    # common candidates (may differ by build)
    candidates = ["usdimport", "usdimport_sop", "SdfImport", "SOP_USDImport", "usd_import", "usdimport::2.0"]
    for c in candidates:
        try:
            t = cat.nodeType(c)
            if t:
                return t.name()
        except Exception:
            pass
    # fallback: search any sop node type whose name contains 'usd'
    for t in cat.nodeTypes().values():
        if "usd" in t.name().lower():
            return t.name()
    return None

usd_sop_type = detect_usd_import_sop()
if usd_sop_type:
    print("Detected USD Import SOP type:", usd_sop_type)
else:
    print("Could not auto-detect a USD Import SOP type. Placeholders (null) will be created; swap to the correct node manually.")

# get /obj context
obj = hou.node("/obj")
if obj is None:
    raise RuntimeError("Couldn't find /obj context - run inside Houdini.")

# create or reuse geo container
geo = obj.node(geo_node_name)
if geo is None:
    geo = obj.createNode("geo", node_name=geo_node_name)
    # optional: remove default file/box nodes
    for c in geo.children():
        if c.type().name() in ("file", "file1", "box"):
            try:
                c.destroy()
            except Exception:
                pass
else:
    print("Re-using existing /obj/%s" % geo_node_name)

created = []
for i, usd_path in enumerate(usd_files):
    base = os.path.basename(usd_path)
    name = "usd_in_{:03d}_{}".format(i+1, os.path.splitext(base)[0])
    # try to create a USD import SOP
    node = None
    if usd_sop_type:
        try:
            node = geo.createNode(usd_sop_type, node_name=name)
            # set known parm names
            for parm_name in ("file", "filepath", "filename", "usdfile", "usd_path", "path"):
                p = node.parm(parm_name)
                if p is not None:
                    p.set(usd_path)
                    break
            # if no parm matched, try to set first string param
            else:
                for p in node.parms():
                    if p.parmTemplate().type() == hou.parmTemplateType.String:
                        try:
                            p.set(usd_path)
                            break
                        except Exception:
                            pass
        except Exception as e:
            print("Failed to create node '%s' of type '%s': %s" % (name, usd_sop_type, e))
            node = None

    # fallback: create a null node with a spare parm holding the path
    if node is None:
        node = geo.createNode("null", node_name=name + "_ph")
        # add spare string parm called usd_path if it doesn't exist
        try:
            if node.parm("usd_path") is None:
                node.addSpareParmTuple(hou.StringParmTemplate("usd_path", "USD Path", 1))
            node.parm("usd_path").set(usd_path)
        except Exception:
            pass

    created.append(node)

# Layout nodes
geo.layoutChildren()

print("Created %d nodes under %s:" % (len(created), geo.path()))
for n in created:
    print(" -", n.path())

print("/nDone. If placeholders were created, replace the nulls with the correct USD Import SOP and point to the 'usd_path' parm.")
