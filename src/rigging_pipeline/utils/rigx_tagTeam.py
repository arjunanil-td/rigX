

import maya.cmds as mc

__all__ = [
    "initialize_tags",
    "set_model_tag",
    "get_model_tag",
    "clear_model_tag",
    "find_tagged_nodes",
    "add_new_tag",
    "remove_tag_from_enum",
]

# Default tag list; modify as needed or pass your own list to initialize_tags()
DEFAULT_TAGS = ["proxy", "render", "fur", "collision", "guide"]


def initialize_tags(nodes=None, tag_list=None):
    """
    Ensure each node in `nodes` has an enum attribute "modelTag" with entries from tag_list.
    If nodes is None, operates on current selection.
    If tag_list is None, uses DEFAULT_TAGS.

    Any existing "modelTag" attrs will be overwritten with the new enum order.
    """
    if tag_list is None:
        tag_list = DEFAULT_TAGS[:]

    if nodes is None:
        nodes = mc.ls(selection=True, transforms=True)
        if not nodes:
            mc.warning("initialize_tags: no nodes selected and no nodes passed in.")
            return

    enum_str = ":".join(tag_list) + ":"
    for n in nodes:
        if not mc.objExists(n):
            mc.warning(f"initialize_tags: '{n}' does not exist; skipping.")
            continue

        # If attribute exists, remove it first to reset the enum list
        if mc.attributeQuery("modelTag", node=n, exists=True):
            try:
                mc.deleteAttr(f"{n}.modelTag")
            except Exception as e:
                mc.warning(f"initialize_tags: failed to delete existing modelTag on '{n}': {e}")

        # Add new enum attribute
        try:
            mc.addAttr(n,
                       longName="modelTag",
                       attributeType="enum",
                       enumName=enum_str,
                       keyable=True)
            # Set default to first entry (index 0)
            mc.setAttr(f"{n}.modelTag", 0)
        except Exception as e:
            mc.warning(f"initialize_tags: could not add modelTag to '{n}': {e}")


def set_model_tag(node, tag_name):
    """
    Sets the "modelTag" enum on `node` to `tag_name`.  Node must already have a modelTag attr.
    """
    if not mc.objExists(node):
        mc.error(f"set_model_tag: '{node}' does not exist.")
    if not mc.attributeQuery("modelTag", node=node, exists=True):
        mc.error(f"set_model_tag: '{node}' has no 'modelTag' attribute. Call initialize_tags() first.")

    enum_list = mc.attributeQuery("modelTag", node=node, listEnum=True)[0].split(":")[:-1]
    if tag_name not in enum_list:
        mc.error(f"set_model_tag: '{tag_name}' not in modelTag enum list on '{node}': {enum_list}")

    index = enum_list.index(tag_name)
    mc.setAttr(f"{node}.modelTag", index)


def get_model_tag(node):
    """
    Returns the current tag (string) on `node`.  If no attribute or invalid, returns None.
    """
    if not mc.objExists(node):
        mc.error(f"get_model_tag: '{node}' does not exist.")
    if not mc.attributeQuery("modelTag", node=node, exists=True):
        return None

    idx = mc.getAttr(f"{node}.modelTag")
    enum_list = mc.attributeQuery("modelTag", node=node, listEnum=True)[0].split(":")[:-1]
    if 0 <= idx < len(enum_list):
        return enum_list[idx]
    return None


def clear_model_tag(node):
    """
    Removes the 'modelTag' attribute entirely from `node`, if present.
    """
    if not mc.objExists(node):
        mc.error(f"clear_model_tag: '{node}' does not exist.")
    if mc.attributeQuery("modelTag", node=node, exists=True):
        try:
            mc.deleteAttr(f"{node}.modelTag")
        except Exception as e:
            mc.warning(f"clear_model_tag: could not remove modelTag from '{node}': {e}")


def find_tagged_nodes(tag_name=None):
    """
    Returns a list of all transform nodes that have a 'modelTag' attribute.
    If tag_name is provided, only returns those whose tag matches tag_name.
    """
    all_transforms = mc.ls(type="transform")
    tagged = []
    for n in all_transforms:
        if mc.attributeQuery("modelTag", node=n, exists=True):
            if tag_name:
                current = get_model_tag(n)
                if current == tag_name:
                    tagged.append(n)
            else:
                tagged.append(n)
    return tagged


def add_new_tag(node, new_tag):
    """
    Appends `new_tag` to the existing enum list on `node`.
    If `node` lacks modelTag, calls initialize_tags on [node] with DEFAULT_TAGS + [new_tag].
    """
    if not mc.objExists(node):
        mc.error(f"add_new_tag: '{node}' does not exist.")
    if mc.attributeQuery("modelTag", node=node, exists=True):
        enum_list = mc.attributeQuery("modelTag", node=node, listEnum=True)[0].split(":")[:-1]
        if new_tag in enum_list:
            mc.warning(f"add_new_tag: '{new_tag}' already exists on '{node}'.")
            return
        enum_list.append(new_tag)
        initialize_tags([node], enum_list)
    else:
        initialize_tags([node], DEFAULT_TAGS + [new_tag])


def remove_tag_from_enum(node, tag_to_remove):
    """
    Removes `tag_to_remove` from the enum list on `node`.
    If the tag is currently assigned on the node, resets to first entry.
    """
    if not mc.objExists(node):
        mc.error(f"remove_tag_from_enum: '{node}' does not exist.")
    if not mc.attributeQuery("modelTag", node=node, exists=True):
        mc.warning(f"remove_tag_from_enum: '{node}' has no modelTag attr.")
        return

    enum_list = mc.attributeQuery("modelTag", node=node, listEnum=True)[0].split(":")[:-1]
    if tag_to_remove not in enum_list:
        mc.warning(f"remove_tag_from_enum: '{tag_to_remove}' not found on '{node}'.")
        return

    enum_list.remove(tag_to_remove)
    if not enum_list:
        # no tags left → delete attribute
        clear_model_tag(node)
        mc.warning(f"remove_tag_from_enum: removed last tag on '{node}', modelTag deleted.")
    else:
        initialize_tags([node], enum_list)

