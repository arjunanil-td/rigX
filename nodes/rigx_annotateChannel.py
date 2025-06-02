import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.cmds as cmds

def maya_useNewAPI():
    pass

class LiveAttributeAnnotation(omui.MPxLocatorNode):
    TYPE_NAME = "liveAttributeAnnotation"
    TYPE_ID = om.MTypeId(0x0013FE50)  # Change this to a unique ID in your studio
    DRAW_CLASSIFICATION = "drawdb/geometry/liveAttributeAnnotation"
    DRAW_REGISTRANT_ID = "LiveAttributeAnnotationPlugin"

    attr_target_obj = None
    attr_target_name = None

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):
        pass

    def __init__(self):
        super(LiveAttributeAnnotation, self).__init__()

    def get_live_attribute_value(self):
        if not self.attr_target_obj or not self.attr_target_name:
            return None

        if not cmds.objExists(self.attr_target_obj):
            return None

        try:
            value = cmds.getAttr(f"{self.attr_target_obj}.{self.attr_target_name}")
            return value
        except:
            return None

    def draw(self, view, path, style, status):
        # Use Viewport 2.0 MUIDrawManager!
        draw_manager = omui.MUIDrawManager()
        draw_manager.beginDrawable()

        # Text
        attr_value = self.get_live_attribute_value()
        if attr_value is not None:
            text = f"{self.attr_target_name}: {attr_value:.3f}"
        else:
            text = "No Target"

        # Settings
        draw_manager.setFontSize(omui.MUIDrawManager.kSmallFont)
        draw_manager.setColor((1.0, 1.0, 0.0))  # Yellow
        draw_manager.text(om.MPoint(0, 0, 0), text, omui.MUIDrawManager.kCenter)

        draw_manager.endDrawable()

# Plugin setup
def initializePlugin(plugin):
    vendor = "chatgpt"
    version = "1.0.0"

    plugin_fn = om.MFnPlugin(plugin, vendor, version)

    try:
        plugin_fn.registerNode(
            LiveAttributeAnnotation.TYPE_NAME,
            LiveAttributeAnnotation.TYPE_ID,
            LiveAttributeAnnotation.creator,
            LiveAttributeAnnotation.initialize,
            omui.MPxLocatorNode.kLocatorNode,
            LiveAttributeAnnotation.DRAW_CLASSIFICATION
        )
    except Exception as e:
        om.MGlobal.displayError(f"Failed to register node: {e}")

def uninitializePlugin(plugin):
    plugin_fn = om.MFnPlugin(plugin)

    try:
        plugin_fn.deregisterNode(LiveAttributeAnnotation.TYPE_ID)
    except Exception as e:
        om.MGlobal.displayError(f"Failed to deregister node: {e}")
