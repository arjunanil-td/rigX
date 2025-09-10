import maya.cmds as cmds

def fix_duplicates():
    """Find duplicate short names and rename with incremental suffix."""
    objs = cmds.ls(long=True)
    names = {}
    for o in objs:
        short = o.split('|')[-1]
        names.setdefault(short, []).append(o)
    for short, paths in names.items():
        if len(paths) > 1:
            for i, path in enumerate(paths, start=1):
                new_name = f"{short}_{i}"
                try: cmds.rename(path, new_name)
                except: cmds.warning(f"Dup fix failed: {path}")
    #self.populate_object_list()
    cmds.inViewMessage(statusMessage="Duplicates fixed",fade=True)

def fix_shape_names():
    """Ensure shape nodes follow transform name conventions."""
    transforms = cmds.ls(type='transform', long=True)
    for t in transforms:
        shapes = cmds.listRelatives(t, shapes=True, fullPath=True) or []
        for s in shapes:
            short_s = s.split('|')[-1]
            correct = t.split('|')[-1] + 'Shape'
            if short_s != correct:
                new = f"{correct}"
                try: cmds.rename(s, new)
                except: cmds.warning(f"Shape rename failed: {s}")
    cmds.inViewMessage(statusMessage="Shape names fixed",fade=True)

def apply_affix(items, affix, mode='prefix'):
    """Adds a prefix or suffix to a list of items."""
    for o in items:
        name = o.split('|')[-1]
        new = (affix + name) if mode == 'prefix' else (name + affix)
        try:
            cmds.rename(o, new)
        except:
            cmds.warning(f"Could not rename {o}")

def search_replace(items, search_text, replace_text):
    """Performs search and replace on the names of items."""
    if not search_text:
        cmds.warning("Enter search text.")
        return
    for o in items:
        name = o.split('|')[-1]
        new = name.replace(search_text, replace_text)
        try:
            cmds.rename(o, new)
        except:
            cmds.warning(f"Could not rename {o}")

def change_case(items, method):
    """Changes the case of item names."""
    for o in items:
        name = o.split('|')[-1]
        if method == 'lower':
            new = name.lower()
        elif method == 'upper':
            new = name.upper()
        elif method == 'title':
            new = name.title()
        elif method == 'camel':
            new = to_camel_case(name)
        else:
            new = name.capitalize()
        try:
            cmds.rename(o, new)
        except:
            cmds.warning(f"Could not rename {o}")

def to_camel_case(text):
    """Convert text to camelCase."""
    if not text:
        return text
    
    # Split on common separators and spaces
    import re
    words = re.split(r'[_\-\s]+', text)
    
    # Filter out empty strings
    words = [word for word in words if word]
    
    if not words:
        return text
    
    # First word lowercase, rest are title case
    camel_words = [words[0].lower()]
    for word in words[1:]:
        camel_words.append(word.capitalize())
    
    return ''.join(camel_words)
