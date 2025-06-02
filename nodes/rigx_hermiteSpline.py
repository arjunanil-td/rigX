import maya.api.OpenMaya as om

# Define the node class
class HermiteSplineNode(om.MPxNode):
    # Define node name and ID
    NODE_NAME = "hermiteSplineNode"
    NODE_ID = om.MTypeId(0x87002)  # Replace with your unique node ID

    # Attribute handles
    inputPoints = om.MObject()       # Input control points
    inputTangents = om.MObject()    # Input tangents
    tension = om.MObject()          # Tension attribute
    outputCurve = om.MObject()      # Output spline curve

    # Node initialization
    @staticmethod
    def initialize():
        # Create and add attributes
        nAttr = om.MFnNumericAttribute()

        # Input points array attribute
        HermiteSplineNode.inputPoints = nAttr.createPoint("inputPoints", "inPts")
        nAttr.array = True
        HermiteSplineNode.addAttribute(HermiteSplineNode.inputPoints)

        # Input tangents array attribute
        HermiteSplineNode.inputTangents = nAttr.createPoint("inputTangents", "inTng")
        nAttr.array = True
        HermiteSplineNode.addAttribute(HermiteSplineNode.inputTangents)

        # Tension attribute
        HermiteSplineNode.tension = nAttr.create("tension", "tens", om.MFnNumericData.kFloat, 0.0)
        nAttr.keyable = True
        HermiteSplineNode.addAttribute(HermiteSplineNode.tension)

        # Output curve attribute
        cAttr = om.MFnTypedAttribute()
        HermiteSplineNode.outputCurve = cAttr.create("outputCurve", "outCrv", om.MFnData.kNurbsCurve)
        HermiteSplineNode.addAttribute(HermiteSplineNode.outputCurve)


        # Set attribute dependencies
        HermiteSplineNode.attributeAffects(HermiteSplineNode.inputPoints, HermiteSplineNode.outputCurve)
        HermiteSplineNode.attributeAffects(HermiteSplineNode.inputTangents, HermiteSplineNode.outputCurve)
        HermiteSplineNode.attributeAffects(HermiteSplineNode.tension, HermiteSplineNode.outputCurve)

    # Compute function to handle outputs
    def compute(self, plug, dataBlock):
        if plug == HermiteSplineNode.outputCurve:
            # Create empty NURBS curve data object
            curveDataFn = om.MFnNurbsCurveData()
            curveDataObj = curveDataFn.create()

            # Define curve properties
            controlPoints = [om.MPoint(0, 0, 0), om.MPoint(5, 5, 0)]  # Example points
            knots = [0, 0, 1, 1]  # Example knots
            degree = 3  # Cubic curve
            form = om.MFnNurbsCurve.kOpen  # Open curve

            # Create NURBS curve
            curveFn = om.MFnNurbsCurve()
            curveFn.create(controlPoints, knots, degree, form, False, curveDataObj)  # False = not rational

            # Set output curve attribute
            outputCurveHandle = dataBlock.outputValue(self.outputCurve)
            outputCurveHandle.setMObject(curveDataObj)
            outputCurveHandle.setClean()

        else:
            return om.kUnknownParameter


    # Node creator method
    @staticmethod
    def creator():
        return HermiteSplineNode()


# Plugin registration
def maya_useNewAPI():
    """Indicate Maya API 2.0 is used."""
    pass


def initializePlugin(mobject):
    print("initializePlugin called")
    plugin = om.MFnPlugin(mobject)
    try:
        plugin.registerNode(
            HermiteSplineNode.NODE_NAME,  # Name of the node
            HermiteSplineNode.NODE_ID,    # Unique ID of the node
            HermiteSplineNode.creator,    # Creator function
            HermiteSplineNode.initialize, # Initialize function
            om.MPxNode.kDependNode        # Node type
        )
        om.MGlobal.displayInfo(f"Successfully registered node: {HermiteSplineNode.NODE_NAME}")
    except Exception as e:
        om.MGlobal.displayError(f"Failed to register node: {HermiteSplineNode.NODE_NAME}. Error: {e}")


def uninitializePlugin(mobject):
    print("uninitializePlugin called")
    plugin = om.MFnPlugin(mobject)
    try:
        plugin.deregisterNode(HermiteSplineNode.NODE_ID)
        om.MGlobal.displayInfo(f"Successfully deregistered node: {HermiteSplineNode.NODE_NAME}")
    except Exception as e:
        om.MGlobal.displayError(f"Failed to deregister node: {HermiteSplineNode.NODE_NAME}. Error: {e}")
