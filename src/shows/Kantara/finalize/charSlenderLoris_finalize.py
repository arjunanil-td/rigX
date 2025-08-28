'''
Using Advanced Skeleton 6.300

PUBLISH:
main.coreFinalize("charslenderLoris")

'''

import utils
import maya.cmds as cmds


def finalize(asset_name=None):

    lowRes = "model1:body_IDcharSkin_GEOBase"
    hiRes = "model1:body_IDcharSkin_GEO"

    # Attributes to set to 0
    attributes_to_zero = [
        "IKSplineNeck3_M.ikHybridVis",
        "IKSpine3_M.ikHybridVis",
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


    #scapulaFollowAttrinute
    cmds.addAttr('FKScapula_L',ln='Follow',min=0,max=1,dv=1,k=1)
    cmds.connectAttr('FKScapula_L.Follow', 'AimScapulaBM_L.envelope')

    cmds.addAttr('FKScapula_R',ln='Follow',min=0,max=1,dv=1,k=1)
    cmds.connectAttr('FKScapula_R.Follow', 'AimScapulaBM_R.envelope')

    #polevector matrix delete
    poleVec = cmds.ls("PoleOffsetLeg*BM_?")
    cmds.delete(poleVec)

    # Standard for all characters
    utils.rigx_displayMode.setup_model_visibility(lowRes, hiRes)

