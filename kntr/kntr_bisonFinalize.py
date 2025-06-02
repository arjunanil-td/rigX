'''
Using Advanced Skeleton 6.300

FINALIZE:
main.reload_kntr()
main.kntr_bisonFinalize()

PUBLISH:
main.coreFinalize("charBison")

'''

import utils
import maya.cmds as cmds


def kntr_bisonFinalize():

    lowRes = "model:bodyLow_IDcharSkin_GEO"
    hiRes = "model:body_IDcharSkin_GEO"

    # Attributes to set to 0
    attributes_to_zero = [
        "IKSplineNeck3_M.ikHybridVis",
        "IKSpline4_M.ikHybridVis",
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

    #old scapula hide
    cmds.setAttr('FKScapula_RShape.visibility', 0)
    cmds.setAttr('FKScapula_LShape.visibility', 0)


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


    # Standard for all characters
    utils.rigx_displayMode.setup_model_visibility(lowRes, hiRes)


    # Utility functions as provided
    def as_makeScSolverIkh(sel, ikhName):
        scsolverIkh = cmds.ikHandle(sol='ikSCsolver', sj=sel[0], ee=sel[1], n=ikhName)
        eEfIkNm = scsolverIkh[0].replace('Handle', 'Effector')
        cmds.rename(scsolverIkh[1], eEfIkNm)
        return scsolverIkh[0], eEfIkNm
    
    def as_makeCtlOnJnt(sel, prefxNam):
        for ech in sel:
            Ctrl = cmds.circle(c=(0, 0, 0), nr=(0, 1, 0), r=0.2, s=8, ch=0, n=(prefxNam + ech))[0]
            cmds.setAttr(f'{Ctrl}Shape.overrideEnabled', 1)
            cmds.setAttr(f'{Ctrl}Shape.overrideColor', 13)
            
            Grp = cmds.group(em=True, n=(prefxNam + 'Extra' + ech))
            ofGrp = cmds.group(em=True, n=(prefxNam + 'Offset' + ech))
            parGrp = cmds.group(em=True, n=(prefxNam + 'ExtraOffset' + ech))
            
            cmds.parent(Ctrl, Grp)
            cmds.parent(Grp, ofGrp)
            cmds.parent(ofGrp, parGrp)
            
            cmds.delete(cmds.parentConstraint(ech, parGrp, w=1))
            
        return parGrp, ofGrp, Grp, Ctrl
    
    # Main logic
    sides = ['L', 'R']
    
    for side in sides:
        # FINGERS
        ik_handle_name = f'IKfinger1Handle{side}'
        extra_offset_grp = f'IKExtraOffsetFingers3_{side}'
        
        if cmds.objExists(ik_handle_name):
            cmds.delete(ik_handle_name)
        if cmds.objExists(extra_offset_grp):
            cmds.delete(extra_offset_grp)
    
        # Recreate control and its group
        parGrp, ofGrp, grp, ctrl = as_makeCtlOnJnt([f'Fingers3_{side}'], 'IK')
    
        # Create IK handle and parent it
        fingerIk = as_makeScSolverIkh(
            [f'IKXFingers3_{side}', f'IKXFingers4_{side}'],
            ik_handle_name
        )
        cmds.setAttr(f'{fingerIk[0]}.v', 0)
        cmds.parent(fingerIk[0], f'IKFingers3_{side}')
        cmds.parent(parGrp, f'IKFingers1_{side}')
    
        # TOES
        toe_ik_handle = f'IKtoe1Handle{side}'
        toe_extra_grp = f'IKExtraOffsetToes2_{side}'
    
        if cmds.objExists(toe_ik_handle):
            cmds.delete(toe_ik_handle)
        if cmds.objExists(toe_extra_grp):
            cmds.delete(toe_extra_grp)
    
        parGrp, ofGrp, grp, ctrl = as_makeCtlOnJnt([f'Toes2_{side}'], 'IK')
    
        toeIk = as_makeScSolverIkh(
            [f'IKXToes2_{side}', f'IKXToes4_{side}'],
            toe_ik_handle
        )
        cmds.setAttr(f'{toeIk[0]}.v', 0)
        cmds.parent(toeIk[0], f'IKToes2_{side}')
        cmds.parent(parGrp, f'IKToes1_{side}')




    # Utility functions as provided
    def as_makeScSolverIkh(sel, ikhName):
        scsolverIkh = cmds.ikHandle(sol='ikSCsolver', sj=sel[0], ee=sel[1], n=ikhName)
        eEfIkNm = scsolverIkh[0].replace('Handle', 'Effector')
        cmds.rename(scsolverIkh[1], eEfIkNm)
        return scsolverIkh[0], eEfIkNm

    def as_makeCtlOnJnt(sel, prefxNam):
        for ech in sel:
            Ctrl = cmds.circle(c=(0, 0, 0), nr=(0, 1, 0), r=0.2, s=8, ch=0, n=(prefxNam + ech))[0]
            cmds.setAttr(f'{Ctrl}Shape.overrideEnabled', 1)
            cmds.setAttr(f'{Ctrl}Shape.overrideColor', 13)
            
            Grp = cmds.group(em=True, n=(prefxNam + 'Extra' + ech))
            ofGrp = cmds.group(em=True, n=(prefxNam + 'Offset' + ech))
            parGrp = cmds.group(em=True, n=(prefxNam + 'ExtraOffset' + ech))
            
            cmds.parent(Ctrl, Grp)
            cmds.parent(Grp, ofGrp)
            cmds.parent(ofGrp, parGrp)
            
            cmds.delete(cmds.parentConstraint(ech, parGrp, w=1))
            
        return parGrp, ofGrp, Grp, Ctrl

    # Main logic
    sides = ['L', 'R']

    for side in sides:
        # FINGERS
        ik_handle_name = f'IKfinger1Handle{side}'
        extra_offset_grp = f'IKExtraOffsetFingers3_{side}'
        
        if cmds.objExists(ik_handle_name):
            cmds.delete(ik_handle_name)
        if cmds.objExists(extra_offset_grp):
            cmds.delete(extra_offset_grp)

        # Recreate control and its group
        parGrp, ofGrp, grp, ctrl = as_makeCtlOnJnt([f'Fingers3_{side}'], 'IK')

        # Create IK handle and parent it
        fingerIk = as_makeScSolverIkh(
            [f'IKXFingers3_{side}', f'IKXFingers4_{side}'],
            ik_handle_name
        )
        cmds.setAttr(f'{fingerIk[0]}.v', 0)
        cmds.parent(fingerIk[0], f'IKFingers3_{side}')
        cmds.parent(parGrp, f'IKFingers1_{side}')

        # TOES
        toe_ik_handle = f'IKtoe1Handle{side}'
        toe_extra_grp = f'IKExtraOffsetToes2_{side}'

        if cmds.objExists(toe_ik_handle):
            cmds.delete(toe_ik_handle)
        if cmds.objExists(toe_extra_grp):
            cmds.delete(toe_extra_grp)

        parGrp, ofGrp, grp, ctrl = as_makeCtlOnJnt([f'Toes2_{side}'], 'IK')

        toeIk = as_makeScSolverIkh(
            [f'IKXToes2_{side}', f'IKXToes4_{side}'],
            toe_ik_handle
        )
        cmds.setAttr(f'{toeIk[0]}.v', 0)
        cmds.parent(toeIk[0], f'IKToes2_{side}')
        cmds.parent(parGrp, f'IKToes1_{side}')
