import maya.cmds as cmds

# Create a new set
def create_set(name="set1"):
    if not cmds.objExists(name):
        cmds.sets(name=name)
        print(f"Created set: {name}")
    else:
        print(f"Set '{name}' already exists.")

# Add selected objects to the last selected set
def rig_sets_add_selected():
    sel = cmds.ls(selection=True)
    if len(sel) < 2:
        cmds.error("Select objects and then the set (at least two selections required).")
        return

    set_node = sel[-1]
    add_items = sel[:-1]

    if cmds.nodeType(set_node) != "objectSet":
        cmds.error("The last selected item must be a set!")
        return

    cmds.sets(add_items, add=set_node)
    print(f"Added {add_items} to set '{set_node}'.")

# Remove selected objects from the last selected set
def rig_sets_remove_selected():
    sel = cmds.ls(selection=True)
    if len(sel) < 2:
        cmds.error("Select objects and then the set (at least two selections required).")
        return

    set_node = sel[-1]
    remove_items = sel[:-1]

    if cmds.nodeType(set_node) != "objectSet":
        cmds.error("The last selected item must be a set!")
        return

    cmds.sets(remove_items, remove=set_node)
    print(f"Removed {remove_items} from set '{set_node}'.")



# create_set("mySet")
# rig_sets_add_selected()
# rig_sets_remove_selected()