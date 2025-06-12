'''
# Run the UI
BlendshapeExtractorUI()

'''

import maya.cmds as cmds

class BlendshapeExtractorUI:
    def __init__(self):
        self.window = "blendshapeExtractorWin"
        self.build_ui()

    def build_ui(self):
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window)

        self.window = cmds.window(self.window, title="BlendShape Extractor", widthHeight=(460, 200), sizeable=False)
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=12)

        cmds.separator(height=12, style='in')

        self.blendshape_field = cmds.textFieldButtonGrp(
            label="BlendShape Node:",
            buttonLabel="Pick",
            columnAlign=[1, "right"],
            columnWidth3=(130, 260, 50),
            adjustableColumn=2,
            buttonCommand=self.get_selected_blendshape
        )

        self.geo_field = cmds.textFieldButtonGrp(
            label="Driven Geometry:",
            buttonLabel="Pick",
            columnAlign=[1, "right"],
            columnWidth3=(130, 260, 50),
            adjustableColumn=2,
            buttonCommand=self.get_selected_geo
        )

        cmds.separator(height=10, style='in')

        cmds.rowLayout(numberOfColumns=1, adjustableColumn=1, columnAlign=(1, 'center'))
        cmds.button(label="Extract All BlendShapes", height=45, width=300, command=self.extract_blendshapes)
        cmds.setParent('..')

        cmds.showWindow(self.window)

    def get_selected_blendshape(self, *args):
        sel = cmds.ls(selection=True, type="blendShape")
        if sel:
            cmds.textFieldButtonGrp(self.blendshape_field, edit=True, text=sel[0])
        else:
            cmds.warning("Please select a blendShape node.")

    def get_selected_geo(self, *args):
        sel = cmds.ls(selection=True, type="transform")
        if sel:
            cmds.textFieldButtonGrp(self.geo_field, edit=True, text=sel[0])
        else:
            cmds.warning("Please select a geometry.")

    def extract_blendshapes(self, *args):
        blendshape_node = cmds.textFieldButtonGrp(self.blendshape_field, query=True, text=True)
        driven_geo = cmds.textFieldButtonGrp(self.geo_field, query=True, text=True)

        if not cmds.objExists(blendshape_node):
            cmds.warning("Invalid blendShape node.")
            return
        if not cmds.objExists(driven_geo):
            cmds.warning("Invalid driven geometry.")
            return

        attrs = cmds.listAttr(f"{blendshape_node}.w", m=True)
        if not attrs:
            cmds.warning("No blendshape targets found.")
            return

        for attr in attrs:
            for other in attrs:
                cmds.setAttr(f"{blendshape_node}.{other}", 0)
            cmds.setAttr(f"{blendshape_node}.{attr}", 1)

            dup = cmds.duplicate(driven_geo, name=f"{attr}_shape")[0]
            cmds.makeIdentity(dup, apply=True, t=True, r=True, s=True, n=0)
            cmds.delete(dup, ch=True)

        for attr in attrs:
            cmds.setAttr(f"{blendshape_node}.{attr}", 0)

        cmds.confirmDialog(title="Done", message="All blendshapes were extracted.")

