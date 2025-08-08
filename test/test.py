import hou, time, json

# ------------------------ Configuration ------------------------ #
LOG_PATH    = hou.expandString("$HIP/sim_param_changes.log")
WATCH_NODES = [
    "/obj/geo1/muscleproperties1",
    "/obj/geo1/muscleconstraintpropertiesvellum1",
    "/obj/TISSUE_PREP/tissueproperties_base1",
]

# --------------------- Initialize Log File -------------------- #
with open(LOG_PATH, "w") as f:
    f.write("# Parameter Change Log: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

# ------------------- Parameter Value Cache -------------------- #
# Cache structure: { node_path: { parm_name: last_logged_value } }
_parm_value_cache = {}

# ------------------- Callback Definition --------------------- #
def on_node_event(event_type, **kwargs):
    if event_type != hou.nodeEventType.ParmTupleChanged:
        return
    parm_tuple = kwargs.get("parm_tuple")  # Correct key is 'parm_tuple'
    if not parm_tuple:
        return
    node = parm_tuple[0].node() if parm_tuple else None
    node_path = node.path() if node else None
    if node_path not in _parm_value_cache:
        _parm_value_cache[node_path] = {}
    for parm in parm_tuple:
        try:
            new_value = parm.eval()
            parm_name = parm.name()
            last_value = _parm_value_cache[node_path].get(parm_name, None)
            if new_value == last_value:
                continue  # Skip duplicate log
            entry = {
                "time":      time.strftime("%Y-%m-%d %H:%M:%S"),
                "node":      node_path,
                "parm":      parm_name,
                "new_value": new_value,
            }
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps(entry) + "\n")
            print("Logged:", entry)
            _parm_value_cache[node_path][parm_name] = new_value
        except Exception as e:
            print(f"Error logging parm {parm.name()}: {e}")

# --------------------- Register Callbacks -------------------- #
# To avoid double-registration, keep track of registered nodes
_registered_nodes = set()
for path in WATCH_NODES:
    node = hou.node(path)
    if not node:
        print(f"⚠️ Cannot find node: {path}")
        continue
    if path in _registered_nodes:
        print(f"⚠️ Callback already registered for node: {path}")
        continue
    node.addEventCallback((hou.nodeEventType.ParmTupleChanged,), on_node_event)
    _registered_nodes.add(path)

print("✅ Parameter Change Logger enabled; logging to:", LOG_PATH)
