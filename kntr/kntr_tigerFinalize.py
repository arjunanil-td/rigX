'''
Using Advanced Skeleton 6.300

FINALIZE:
main.reload_kntr()
main.kntr_tigerFinalize()

PUBLISH:
main.coreFinalize("charTiger")

'''

import utils
import maya.cmds as cmds


def kntr_tigerFinalize():

    lowRes = "model:bodyProxy_GEOBase"
    hiRes = "model:body_IDcharSkin_GEO"

    # Attributes to set to 0
    attributes_to_zero = [
        "IKSplineNeck3_M.ikHybridVis",
        "IKSpine3_M.ikHybridVis",
        "FKScapula_L.visibility",
        "FKScapula_R.visibility",
        "PoleLegFront_R.follow",
        "PoleLegBack_L.follow",
        "PoleLegFront_L.follow",
        "PoleLegBack_R.follow",
        "IKSplineNeck3_M.followChest",
        "IKSplineNeck3_M.followMain",
        "IKSplineNeck3_M.followRoot"
    ]

    # Set attributes to 0
    for attr in attributes_to_zero:
        cmds.setAttr(attr, 0)

    # Attributes to lock
    attributes_to_lock = [
        "PoleLegFront_R.follow",
        "PoleLegBack_L.follow",
        "PoleLegFront_L.follow",
        "PoleLegBack_R.follow",
        "IKSplineNeck3_M.followMain",
        "IKSplineNeck3_M.followRoot",
        "IKSplineNeck3_M.followChest"
    ]

    # Lock attributes
    for attr in attributes_to_lock:
        cmds.setAttr(attr, lock=True, keyable=False, channelBox=False)

    # Loop for connecting and disconnecting attributes
    for side in ["_L", "_R"]:
        cmds.disconnectAttr("Group.worldMatrix[0]", "FingersMM" + side + ".matrixIn[1]")
        cmds.connectAttr("Fingers1" + side + ".worldMatrix[0]", "FingersMM" + side + ".matrixIn[1]")
        try:
            cmds.disconnectAttr("Group.worldMatrix[0]", "ToesMM" + side + ".matrixIn[1]")
        except:
            pass
        cmds.connectAttr("Toes1" + side + ".worldMatrix[0]", "ToesMM" + side + ".matrixIn[0]")


    #old scapula hide
    cmds.setAttr('FKScapula_L.visibility', 0)
    cmds.setAttr('FKScapula_R.visibility', 0)

    #scapulaRotation connect
    reverseNode_R = cmds.createNode('reverse', name='reverseNode_R')
    reverseNode_L = cmds.createNode('reverse', name='reverseNode_L')

    cmds.connectAttr('FKScapulaMain_R.rotateX', reverseNode_R + '.inputX', force=True)
    cmds.connectAttr(reverseNode_R + '.outputX', 'FKScapula_R.rotateZ', force=True)

    cmds.connectAttr('FKScapulaMain_L.rotateX', reverseNode_L + '.inputX', force=True)
    cmds.connectAttr(reverseNode_L + '.outputX', 'FKScapula_L.rotateZ', force=True)

    attributes = ["tx", "ry", "rz", "sx", "sy", "sz"]
    sides = ["R", "L"]

    for side in sides:
        for attr in attributes:
            node = f"FKScapulaMain_{side}.{attr}"
            cmds.setAttr(node, lock=True, keyable=False, channelBox=False)

    #scapulaFollowAttrinute
    cmds.addAttr('FKScapulaMain_L',ln='Follow',min=0,max=1,dv=1,k=1)
    cmds.connectAttr('FKScapulaMain_L.Follow', 'AimScapulaBM_L.envelope')

    cmds.addAttr('FKScapulaMain_R',ln='Follow',min=0,max=1,dv=1,k=1)
    cmds.connectAttr('FKScapulaMain_R.Follow', 'AimScapulaBM_R.envelope')

    #polevector matrix delete
    poleVec = cmds.ls("PoleOffsetLeg*BM_?")
    cmds.delete(poleVec)

    # Standard for all characters
    utils.rigx_displayMode.setup_model_visibility(lowRes, hiRes)

