import maya.cmds as mc
import maya.mel as mel

import maya.OpenMayaUI as mui
from PySide2 import QtCore, QtWidgets
from shiboken2 import wrapInstance

def getSelectedChannels():
    channelBox = mel.eval('global string $gChannelBoxName; $temp=$gChannelBoxName;')	#fetch maya's main channelbox
    attrs = cmds.channelBox(channelBox, q=True, sma=True)
    if not attrs:    return []
    return attrs

def mayaMainWin():
    pointer = mui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)

def createCtrlCrv(model):
    if model==1:
        return mc.curve( d=1, p=[(0, 0.599954, -1.33416e-006), 
                  (0, 0.553732, -0.229361),      (0, 0.424231, -0.424236),  (0, 0.229363, -0.553725),  (0, 0, -0.6), 
                  (0, -0.229363, -0.553725),     (0, -0.424231, -0.424236), (0, -0.553732, -0.229361), (0, -0.599954, -1.33416e-006), 
                  (0, -0.553732, 0.229364),      (0, -0.424231, 0.424231),  (0, -0.229363, 0.553732),  (0, 0, 0.599954), 
                  (0, 0.229363, 0.553732),       (0, 0.424231, 0.424231),   (0, 0.553732, 0.229364),   (0, 0.599954, -1.33416e-006), 
                  (0, -0.599954, -1.33416e-006), (0, -0.553732, 0.229364),  (0, -0.424231, 0.424231),  (0, -0.229363, 0.553732), 
                  (0, 0, 0.599954),              (0, 0, -0.6)], 
                k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22] )

    if model==2:
        return mc.curve( degree = 1,\
                knot = [0, 4.7999999999999998, 9.5999999999999996, 12.800000000000001, 17.600000000000001,\
                        22.399999999999999, 25.600000000000001, 30.399999999999999, 35.200000000000003,\
                        38.399999999999999, 43.200000000000003, 48, 51.200000000000003],\
                point = [(-0.64000000000000012, -2.5600000000000005, 0), (-0.64000000000000012, -0.64000000000000012, 0),\
                         (-2.5600000000000005, -0.64000000000000012, 0), (-2.5600000000000005, 0.64000000000000012, 0),\
                         (-0.64000000000000012, 0.64000000000000012, 0), (-0.64000000000000012, 2.5600000000000005, 0),\
                         (0.64000000000000012, 2.5600000000000005, 0),   (0.64000000000000012, 0.64000000000000012, 0),\
                         (2.5600000000000005, 0.64000000000000012, 0),   (2.5600000000000005, -0.64000000000000012, 0),\
                         (0.64000000000000012, -0.64000000000000012, 0), (0.64000000000000012, -2.5600000000000005, 0),\
                         (-0.64000000000000012, -2.5600000000000005, 0)] )
                         
    if model==3:
        return mc.curve( d=1, p=[(0.173648, 0.984808, 0),        (-0.173648, 0.984808, 0),             (-0.173648, 0.796726, -0.578856), 
                              (0.173648, 0.796726, -0.578856),   (0.173648, 0.304322, -0.936608),      (-0.173648, 0.304322, -0.936608), 
                              (-0.173648, -0.304323, -0.936608), (0.173648, -0.304323, -0.936608),     (0.173648, -0.796726, -0.578856), 
                              (-0.173648, -0.796726, -0.578856), (-0.173648, -0.984808, 5.86991e-008), (0.173648, -0.984808, 5.86991e-008), 
                              (0.173648, -0.796726, 0.578856),   (-0.173648, -0.796726, 0.578856),     (-0.173648, -0.304322, 0.936608), 
                              (0.173648, -0.304322, 0.936608),   (0.173648, 0.304322, 0.936608),       (-0.173648, 0.304322, 0.936608), 
                              (-0.173648, 0.796726, 0.578856),   (0.173648, 0.796726, 0.578856),       (0.173648, 0.984808, 0)], 
                         k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20] )
    
    if model==4:
        return mc.curve( d=1, p=[(0, 1, -1), (0, -1, -1), (0, -1, 1), (0, 1, 1), (0, 1, -1)], k=[0,1,2,3,4] )           

    if model==5:    #box
        return mc.curve( degree = 1,\
                knot = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],\
                point = [(-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5),(-0.5, -0.5, 0.5),\
                         (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),(0.5, 0.5, -0.5),\
                         (0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5)] )

    if model==6:    #sphere 
        return mc.curve( degree = 1,\
                knot = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,\
                        21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,\
                        39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52],\
                point = [(0, 1, 0), (0, 0.92388000000000003, 0.382683), (0, 0.70710700000000004, 0.70710700000000004), (0, 0.382683, 0.92388000000000003),\
                         (0, 0, 1), (0, -0.382683, 0.92388000000000003), (0, -0.70710700000000004, 0.70710700000000004), (0, -0.92388000000000003, 0.382683),\
                         (0, -1, 0), (0, -0.92388000000000003, -0.382683), (0, -0.70710700000000004, -0.70710700000000004), (0, -0.382683, -0.92388000000000003),\
                         (0, 0, -1), (0, 0.382683, -0.92388000000000003), (0, 0.70710700000000004, -0.70710700000000004), (0, 0.92388000000000003, -0.382683),\
                         (0, 1, 0), (0.382683, 0.92388000000000003, 0), (0.70710700000000004, 0.70710700000000004, 0), (0.92388000000000003, 0.382683, 0),\
                         (1, 0, 0), (0.92388000000000003, -0.382683, 0), (0.70710700000000004, -0.70710700000000004, 0), (0.382683, -0.92388000000000003, 0),\
                         (0, -1, 0), (-0.382683, -0.92388000000000003, 0), (-0.70710700000000004, -0.70710700000000004, 0), (-0.92388000000000003, -0.382683, 0),\
                         (-1, 0, 0), (-0.92388000000000003, 0.382683, 0), (-0.70710700000000004, 0.70710700000000004, 0), (-0.382683, 0.92388000000000003, 0),\
                         (0, 1, 0),(0, 0.92388000000000003, -0.382683), (0, 0.70710700000000004, -0.70710700000000004), (0, 0.382683, -0.92388000000000003),\
                         (0, 0, -1), (-0.382683, 0, -0.92388000000000003), (-0.70710700000000004, 0, -0.70710700000000004), (-0.92388000000000003, 0, -0.382683),\
                         (-1, 0, 0), (-0.92388000000000003, 0, 0.382683), (-0.70710700000000004, 0, 0.70710700000000004), (-0.382683, 0, 0.92388000000000003),\
                         (0, 0, 1), (0.382683, 0, 0.92388000000000003), (0.70710700000000004, 0, 0.70710700000000004), (0.92388000000000003, 0, 0.382683),\
                         (1, 0, 0), (0.92388000000000003, 0, -0.382683), (0.70710700000000004, 0, -0.70710700000000004), (0.382683, 0, -0.92388000000000003),\
                         (0, 0, -1)] )

def setTopHierarchy():
    rad = 5
    mc.group( em=1, n='CENTER' )
    mc.setAttr( 'CENTER.v', l=True, k=False, cb=False )            
    ctls = ['Ctrl_ROOT', 'Ctrl_LOCAL', 'Ctrl_PLACE']
    for cir in ctls:           
        mc.circle( n=cir, c=[0,0,0], nr=[0,1,0], sw=360, r=rad, d=3, ut=0, tol=0.01, s=8, ch=0 )
        if cir=='Ctrl_PLACE':    
            mc.addAttr( 'Ctrl_PLACE', ln="globalScale", at='double', dv=1, k=1 )
            mc.addAttr( 'Ctrl_PLACE', ln="geoVis", at='bool' )
            mc.setAttr( 'Ctrl_PLACE.geoVis', e=1, channelBox=True )
            mc.setAttr( 'Ctrl_PLACE.geoVis', 1 )
            for atr in ['sx', 'sy', 'sz']:    mc.connectAttr( 'Ctrl_PLACE.globalScale', 'Ctrl_ROOT.%s' %atr )
        if cir=='Ctrl_ROOT':
            tmp = mc.circle( n=cir, c=[0,0,0], nr=[0,1,0], sw=360, r=5.2, d=3, ut=0, tol=0.01, s=8, ch=0 )
            tmp = mc.listRelatives( tmp, s=1 )
            mc.parent( tmp, 'Ctrl_ROOT', r=1, s=1 )
            mc.delete('Ctrl_ROOT1')            
        for shp in mc.listRelatives( cir, s=1 ):
            mc.setAttr( "%s.overrideEnabled" %shp, 1 )
            mc.setAttr( "%s.overrideColor" %shp, 13 )            
        rad+=1
    mc.parent( 'CENTER', 'Ctrl_ROOT' )
    for i, cir in enumerate(ctls):
        for atr in ['sx', 'sy', 'sz', 'v']:    
            mc.setAttr( '%s.%s' %(cir,atr), l=True, k=False, cb=False )
        if cir!='Ctrl_PLACE':    
            mc.parent( cir, ctls[i+1] ) 
    
    for grp in ['RIG', 'Systems', 'AssetName']:
        mc.group( em=1, n=grp )    
        atrs = ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v']    
        if grp!='RIG':    atrs.pop()    
        for atr in atrs:    mc.setAttr( '%s.%s' %(grp,atr), l=True, k=False, cb=False )               
        if grp=='AssetName':    
            mc.addAttr( 'AssetName', ln="modelLock", at='bool' )
            mc.setAttr( 'AssetName.modelLock', e=1, channelBox=True )
            mc.parent( 'RIG', grp )
            mc.parent( 'Systems', 'RIG' )
            mc.parent( 'Ctrl_PLACE', 'RIG' )
    mc.cluster( ['Ctrl_LOCALShape', 'Ctrl_PLACEShape'], n='cls_scalePlaceLocal' )
    mc.parent( 'cls_scalePlaceLocalHandle', 'Systems' )
    atrs.append('v')
    for atr in atrs:           
        if atr in ['sx', 'sy', 'sz']:    mc.connectAttr( 'Ctrl_PLACE.globalScale', 'cls_scalePlaceLocalHandle.%s' %atr )
        if atr=='v':    mc.setAttr( 'cls_scalePlaceLocalHandle.%s' %atr, 0 )
        mc.setAttr( 'cls_scalePlaceLocalHandle.%s' %atr, l=True, k=False, cb=False )


class SplineRig:
    def __init__(self):        
        self.CJ  = 'CJ'
        self.SJ  = 'SJ'
        self.ctl = 'Ctrl'

    def createJoints( self, crv, split, rName ):         #(curve, joint spans, rig name)
        tloc = mc.spaceLocator()[0]
        mp = mc.pathAnimation( tloc, c=crv, fm=True, f=True, fa='x', ua='y', wut="vector", wu=[0,1,0] )
        mc.cutKey( mp, cl=True, at="u" )    
      
        self.jnt   = []
        self.split = split
        self.rName = rName.capitalize()
        self.noj   = split+1
        self.ikCrv = mc.rename( crv, 'crv_ik%s' %self.rName )
        
        self.jGrp  = mc.group(em=1, n='grp_jnt%s' %self.rName)
        if not mc.attributeQuery('rigName', node=self.ikCrv, exists=True):
            mc.addAttr( self.ikCrv, ln='rigName', dt='string' )
        mc.setAttr( '%s.rigName' %self.ikCrv, self.rName,  type='string' )
        if not mc.attributeQuery('joints', node=self.ikCrv, exists=True):
            mc.addAttr( self.ikCrv, ln='joints', at='message' )

        dLen = len( str(self.split+1) )
        for i in range( self.noj ):
            #pos = mc.pointOnCurve( self.ikCrv, pr=1.0/self.split*i, top=1 )
            mc.setAttr( '{0}.uValue'.format(mp), 1.0/self.split*i )            
            mc.select( self.jGrp )        
            self.jnt.append( mc.joint( n='%s_%s%s' %(self.CJ, self.rName, str(i+1).zfill(dLen)), p=mc.getAttr('{0}.worldPosition'.format(tloc))[0] ) )
            mc.delete( mc.tangentConstraint( self.ikCrv, self.jnt[-1], w=1, aim=[1,0,0], u=[0,1,0], wut="vector", wu=[0,1,0] )  )
            mc.makeIdentity( self.jnt[-1], apply=True, t=1, r=1, s=1, n=0 )
            
            mc.addAttr( self.jnt[-1], ln='ikCurve', at='message' )
            mc.connectAttr( '%s.joints' %self.ikCrv, '%s.ikCurve' %self.jnt[-1], f=1 )
        mc.delete( tloc, mp )
        return self.ikCrv
        
    
    def setSJ(self, ikCrv, par=None):               # ( ik curve, parent SJ)
        self.rName = mc.getAttr( '%s.rigName' %ikCrv )        
        objCrv     = mc.listConnections('%s.offsetCurve' %ikCrv)[0]
        self.jnt   = mc.listConnections('%s.joints' %ikCrv) or []
        self.jnt.sort()
        self.noj = len( self.jnt )
        obj, loc, npc = [], [], []       
        for i, jnt in enumerate(self.jnt):    #setting orientation
            if jnt==self.jnt[-1]:
                mc.delete( mc.orientConstraint( self.jnt[-2], self.jnt[-1], mo=0 ) )
                break                    
            obj.append( mc.group( em=1, n=jnt.replace( 'CJ_', 'obj_tmp' ) ) )
            loc.append( mc.spaceLocator( n=jnt.replace( 'CJ_', 'loc_tmp' ) )[0] )
            mc.delete( mc.pointConstraint( jnt, loc[-1], mo=0 ) )
            npc.append( mc.createNode( 'nearestPointOnCurve', n=jnt.replace('CJ_', 'npc_tmp') ) )
            mc.connectAttr( '%s.worldSpace[0]' %objCrv, '%s.inputCurve' %npc[-1] )
            mc.connectAttr( '%s.worldPosition[0]' %loc[-1], '%s.inPosition' %npc[-1] )
            mc.connectAttr( '%s.position' %npc[-1], '%s.translate' %obj[-1], f=1 )
            mc.delete( mc.aimConstraint( self.jnt[i+1], jnt, o=[0,0,0], w=1, aim=[1,0,0], u=[0,1,0], wut="object", wuo=obj[-1] ) )
         
        for i, jnt in enumerate(self.jnt):    #renaming ad parenting
            jnt = mc.rename( jnt, jnt.replace( self.CJ, self.SJ ) )
            self.jnt[i] = jnt
            if i==0:    continue
            mc.parent( jnt, self.jnt[i-1] )
    
        g = mc.listRelatives( self.jnt[0], p=1, c=0 )
        if par:    mc.parent( self.jnt[0], par )
        else:      mc.parent( self.jnt[0], w=1 )
        mc.makeIdentity( self.jnt[0], apply=True, t=1, r=1, s=1, n=0 )
        mc.delete( g, npc, loc, obj )

    def setOffsetCrv( self, crv, dist=0.5, tol=0.1 ):    #( ik curve, distance, tolerance)
        self.rName = mc.getAttr( '%s.rigName' %crv )
        ofc = mc.offsetCurve( crv, ch=0, rn=False, cb=2, st=True, cl=True, cr=0, d=dist, tol=tol, sd=5, ugn=False )[0]    #offset curve
        ofc = mc.rename( ofc, 'crv_obj%s' %self.rName )
        if not mc.attributeQuery('offsetCurve', node=crv, exists=True):
            mc.addAttr( crv, ln='offsetCurve', at='message' )
        if not mc.attributeQuery('ikCurve', node=ofc, exists=True):
            mc.addAttr( ofc, ln='ikCurve', at='message' )
        mc.connectAttr( '%s.offsetCurve' %crv, '%s.ikCurve' %ofc, f=1 )
        return mc.getAttr( '%s.spans' %ofc )         #offset curve Spans returns
            
    def offsetCurveTemplate( self, crv ):
        self.rName = mc.getAttr( '%s.rigName' %crv )
        mc.spaceLocator( n='offsetCurveTmp_loc' )
        mc.setAttr( "offsetCurveTmp_loc.localScale", 0.2, 0.2, 0.2 )
        mc.group( 'offsetCurveTmp_loc', n='offsetCurveTmp_nul' )
        mc.group( 'offsetCurveTmp_loc', n='offsetCurveTmpRot_nul' )
        mc.xform( 'offsetCurveTmp_nul', t=mc.pointPosition( '%s.cv[0]' %crv, w=1 ) )
        mc.delete( mc.tangentConstraint( crv, 'offsetCurveTmp_nul', w=1, aim=[1,0,0], u=[0,1,0], wut="vector", wu=[0,1,0] ) )
        mc.setAttr( 'offsetCurveTmp_loc.ty', 1 )
        mc.addAttr( 'offsetCurveTmp_loc', ln="angle", at='double', k=1, min=0, max=360, dv=0 )
        mc.createNode( 'multiplyDivide', n='offsetCurveTmp_mdn' )
        mc.setAttr( 'offsetCurveTmp_mdn.input2X', -1 )
        mc.connectAttr( 'offsetCurveTmp_loc.angle', 'offsetCurveTmp_mdn.input1X' )
        mc.connectAttr( 'offsetCurveTmp_mdn.outputX', 'offsetCurveTmpRot_nul.rx' )
        for ax in ['tx', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']:    mc.setAttr( "offsetCurveTmp_loc.%s" %ax, l=1, k=0, cb=0 )
        mc.select( 'offsetCurveTmp_loc' )
        
    def createOffsetCurve( self, crv ):        
        self.rName = mc.getAttr( '%s.rigName' %crv )
        # Fallback: if the temporary offset template locator doesn't exist, use simple offset
        if not mc.objExists('offsetCurveTmp_loc'):
            try:
                bb = mc.exactWorldBoundingBox(crv)
                max_dim = max(abs(bb[3]-bb[0]), abs(bb[4]-bb[1]), abs(bb[5]-bb[2]))
                dist = max(0.01, max_dim * 0.05)
            except Exception:
                dist = 0.5
            return self.setOffsetCurve(crv, dist=dist, tol=0.1)
        cir = mc.circle( c=[0,0,0], nr=[0,1,0], sw=360, r=mc.getAttr( 'offsetCurveTmp_loc.ty' ), d=3, ut=0, tol=0.0001, s=360, ch=1 )
        sur = mc.extrude( cir[0], crv, ch=1, rn=0, po=0, et=2, ucp=1, fpt=1, upn=1, ro=0, sc=1, rsp=1 )[0]
        cps = mc.createNode( 'closestPointOnSurface', n='offsetCurveTmp_cps' )
        mc.connectAttr( '%s.worldSpace[0]' %sur, '%s.inputSurface' %cps )
        mc.connectAttr( 'offsetCurveTmp_loc.worldPosition[0]', '%s.inPosition' %cps )        
        dc = mc.duplicateCurve( 'extrudedSurface1.u[%f]' %mc.getAttr( '%s.parameterU' %cps ), ch=0, rn=0, l=0 )[0]
        cvPos = []
        deg = mc.getAttr( '%s.degree' %crv )
        for i in range( mc.getAttr( '%s.spans' %crv ) + deg ):    cvPos.append( mc.pointPosition( '%s.cv[%s]' %(dc,i), w=1 ) )
        ofc = mc.curve( d=deg, p=cvPos ) 
        ofc = mc.rename( ofc, 'crv_obj%s' %self.rName )
        if not mc.attributeQuery('offsetCurve', node=crv, exists=True):
            mc.addAttr( crv, ln='offsetCurve', at='message' )
        if not mc.attributeQuery('ikCurve', node=ofc, exists=True):
            mc.addAttr( ofc, ln='ikCurve', at='message' )
        mc.connectAttr( '%s.offsetCurve' %crv, '%s.ikCurve' %ofc, f=1 )
        mc.delete( dc, cir, sur, 'offsetCurveTmp_nul' )
        return mc.getAttr( '%s.spans' %ofc )         #offset curve Spans returns

    def setSplineStretch( self, ikCrv, jntsIK ):            #stretch def
        self.rName = mc.getAttr( '%s.rigName' %ikCrv )
        if not mc.attributeQuery('globalScale', node=ikCrv, exists=True):
            mc.addAttr( ikCrv, ln='globalScale', at='double', dv=1 )
        if not mc.attributeQuery('stretch', node=ikCrv, exists=True):
            mc.addAttr( ikCrv, ln='stretch', at='double', min=0, max=1, dv=1 )
        
        cin = mc.createNode( 'curveInfo', n='cin_ikSplnStr%s' %self.rName )
        mc.connectAttr( '%s.worldSpace[0]' %ikCrv, '%s.inputCurve' %cin, f=1 )
        
        mdn = mc.createNode( 'multiplyDivide', n='mdn_ikSplnStr%s' %self.rName )
        mc.setAttr( '%s.operation' %mdn, 2 )
        mc.connectAttr( '%s.arcLength' %cin, '%s.input1X' %mdn, f=1 )
        
        mdl = mc.createNode( 'multDoubleLinear', n='mdl_cmpSca%s' %self.rName )
        mc.connectAttr( '%s.globalScale' %ikCrv, '%s.input1' %mdl, f=1 )
        mc.setAttr( '%s.input2' %mdl, mc.arclen( ikCrv ) )
        mc.connectAttr( '%s.output' %mdl, '%s.input2X' %mdn, f=1 )
        
        bta = mc.createNode( 'blendTwoAttr', n='bta_switchStr%s' %self.rName )
        mc.setAttr( '%s.input[0]' %bta, 1 )
        mc.connectAttr( '%s.outputX' %mdn, '%s.input[1]' %bta, f=1 )
        mc.connectAttr( '%s.stretch' %ikCrv, '%s.attributesBlender' %bta, f=1 )
        
        for i, ikJnt in enumerate(jntsIK):
            if ikJnt==jntsIK[0]:    continue
            mdl = mc.createNode( 'multDoubleLinear', n=ikJnt.replace( 'jnt_ik', 'mdl_ikJntTrans' ) )
            mc.setAttr( '%s.input2' %mdl, mc.getAttr( '%s.tx' %ikJnt ) )
            mc.connectAttr( '%s.output' %bta, '%s.input1' %mdl, f=1 )
            mc.connectAttr( '%s.output' %mdl, '%s.tx' %ikJnt, f=1 ) 

    def setSimpleRig(self, ikCrv):
        self.rName = mc.getAttr( '%s.rigName' %ikCrv )
        objCrv     = mc.listConnections('%s.offsetCurve' %ikCrv)[0]
        jnts       = {'SJ':mc.listConnections('%s.joints' %ikCrv) or []}
        jnts['SJ'].sort()
        self.noj   = len( jnts['SJ'] )
        ik = mc.ikHandle( sj=jnts['SJ'][0], ee=jnts['SJ'][-1], c=ikCrv, sol='ikSplineSolver', ccv=False, pcv=False, n='ik_{0}'.format(self.rName) )[0]

        npc = mc.createNode( 'nearestPointOnCurve')
        mc.connectAttr( '{0}.worldSpace[0]'.format(ikCrv), '{0}.inputCurve'.format(npc), f=True )    

        deg = mc.getAttr('{0}.degree'.format(ikCrv))
        cvs = mc.getAttr('{0}.spans'.format(ikCrv)) + deg                       #total curve cvs

        ctlLocs, pos, drv, ancs, cnt = [], [], [], {'ik':[], 'fk':[]}, 0
        cMvr, ctl = [], []
        dLen = len( str(cvs) )
        for i in range( cvs ):        #anchoring locators
            pos.append( mc.pointPosition( '{0}.cv[{1}]'.format(ikCrv, i), w=True ) )    #setting control locator
            ctlLocs.append( mc.spaceLocator( n ='loc_{0}{1}'.format(self.rName, str(i).zfill(dLen)) )[0] )
            mc.setAttr( '{0}.v'.format(ctlLocs[-1]), 0, l=1 )
            mc.setAttr( '{0}.localScale'.format(ctlLocs[-1]), 0.2, 0.2, 0.2 )
            mc.xform( ctlLocs[-1], ws=True, t=pos[-1] )
            mc.connectAttr('{0}.worldPosition[0]'.format(ctlLocs[-1]), '{0}.cv[{1}]'.format(ikCrv, i) )

            if i==1 or i==(cvs-2):  continue            
            mc.connectAttr( '{0}.worldPosition[0]'.format(ctlLocs[-1]), '{0}.inPosition'.format(npc), f=True )  #tmp 
            cMvr.append( mc.rename(createCtrlCrv(6), 'Ctrl_{0}Mvr{1}'.format(self.rName, i+1) ) )
            mc.setAttr( '{0}.s'.format(cMvr[-1]), 0.5, 0.5, 0.5 )
            mc.makeIdentity( cMvr[-1], apply=True, t=False, r=False, s=True, n=False )
            ctl.append( mc.rename(createCtrlCrv(5), 'Ctrl_{0}{1}'.format(self.rName, i+1) ) )
            g = mc.group( ctl[-1], n='nul_{0}{1}'.format(self.rName, i+1) )
            mc.parent(  cMvr[-1], ctl[-1] )
            mc.xform( g, ws=True, t=mc.getAttr( '{0}.result.position'.format(npc) )[0] )
            mc.delete( mc.tangentConstraint( ikCrv, g, w=1, aim=[1,0,0], u=[0,1,0], wut="objectrotation", wu=[0,1,0], wuo=jnts['SJ'][0] ) )
            mc.parent( ctlLocs[-1], cMvr[-1] )
            if i==0:    continue
            mc.parent( g, ctl[-2] )
        mc.parent( ctlLocs[1], cMvr[0] )
        mc.parent( ctlLocs[-2], cMvr[-2] )
        mc.delete( objCrv )

        for obj in cMvr:
            for atr in ['rx','ry','rz','sx','sy','sz','v']:     mc.setAttr( "{0}.{1}".format(obj,atr), l=True, k=False, cb=False  )
        for obj in ctl:
            for atr in ['sx','sy','sz','v']:     mc.setAttr( "{0}.{1}".format(obj,atr), l=True, k=False, cb=False  )

        mc.setAttr( '{0}.v'.format( mc.listRelatives( ctl[-1], s=True )[0] ), 0, l=True )   #hiding last ctl

        self.setSplineStretch( ikCrv, jnts['SJ'] )
        c = mc.rename(createCtrlCrv(2), 'Ctrl_{0}Switch'.format(self.rName) )
        mc.xform( c, ws=True, t=mc.xform( ctl[-1], q=True, ws=True, rp=True ), ro=mc.xform( ctl[-1], q=True, ws=True, ro=True ) )
        mc.setAttr( '{0}.s'.format(c), 0.2, 0.2, 0.2 )
        mc.makeIdentity( c, apply=True, t=False, r=False, s=True, n=False )
        mc.parent( c, cMvr[-1] )
        mc.xform( c, os=True, t=[1.5,0,0] )
        for atr in ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v']:     mc.setAttr( "{0}.{1}".format(c,atr), l=True, k=False, cb=False  )
        mc.addAttr( c, ln="stretch", at='double',  min=0, max=1, dv=0, k=True )
        mc.connectAttr( '{0}.stretch'.format(c), '{0}.stretch'.format(ikCrv) )

        #setting twist
        mc.setAttr( "{0}.dTwistControlEnable".format(ik), 1 )
        mc.setAttr( "{0}.dWorldUpType".format(ik), 4 )
        #mc.setAttr( "{0}.dWorldUpVectorY".format(ik), 0 )
        #mc.setAttr( "{0}.dWorldUpVectorZ".format(ik), 1 )
        #mc.setAttr( "{0}.dWorldUpVectorEndY".format(ik), 0 )
        #mc.setAttr( "{0}.dWorldUpVectorEndZ".format(ik), 1 )
        mc.connectAttr( '{0}.worldMatrix[0]'.format(cMvr[0]), '{0}.dWorldUpMatrix'.format(ik), f=True )
        mc.connectAttr( '{0}.worldMatrix[0]'.format(cMvr[-1]), '{0}.dWorldUpMatrixEnd'.format(ik), f=True )

        sys = mc.group( [ikCrv,ik], n='Sys_{0}'.format(self.rName) )
        if mc.objExists('Systems'):     mc.parent( sys, 'Systems' )
        for atr in ['tx','ty','tz','rx','ry','rz','sx','sy','sz']:     mc.setAttr( "{0}.{1}".format(sys,atr), l=True, k=False, cb=False )
        mc.setAttr( "{0}.v".format(sys), 0, l=True )
        if mc.objExists('CENTER'):      mc.parent( 'nul_{0}1'.format(self.rName), 'CENTER' )

        if mc.objExists( "Ctrl_ROOT.globalScale" ):     mc.connectAttr( "Ctrl_ROOT.globalScale", '{0}.globalScale'.format(ikCrv) )
        elif mc.objExists( 'RootPlace_MD.outputX' ):     mc.connectAttr( 'RootPlace_MD.outputX', '{0}.globalScale'.format(ikCrv) )   


    def setRig( self, ikCrv ):                #(ik curve, globalscale Attr )
        self.rName = mc.getAttr( '{0}.rigName'.format(ikCrv) )
        jnts       = {'SJ':mc.listConnections('{0}.joints'.format(ikCrv)) or []}
        # Fallback 1: search by naming convention if no connections present
        if not jnts['SJ']:
            try:
                jnts['SJ'] = mc.ls('SJ_{0}*'.format(self.rName), type='joint') or []
            except Exception:
                jnts['SJ'] = []
        # Fallback 2: search in the expected group created by Tail builder
        if not jnts['SJ']:
            try:
                grp = 'grp_jnt{0}'.format(self.rName)
                if mc.objExists(grp):
                    roots = mc.listRelatives(grp, c=True, type='joint') or []
                    if roots:
                        chain = [roots[0]]
                        cur = roots[0]
                        while True:
                            kids = mc.listRelatives(cur, c=True, type='joint') or []
                            if not kids:
                                break
                            cur = kids[0]
                            chain.append(cur)
                        jnts['SJ'] = chain
            except Exception:
                pass
        jnts['SJ'].sort()
        self.noj   = len( jnts['SJ'] )
        try:       objCrv = mc.listConnections('{0}.offsetCurve'.format(ikCrv))[0]
        except:    objCrv = mc.rename( mc.offsetCurve( ikCrv, ch=0, rn=0, cb=2, st=1, cl=1, cr=0, d=1, tol=0.1, sd=5, ugn=0 )[0], 'crv_obj{0}'.format(self.rName) )    #offset curve

        jnts.update( CJ=[], ik=[], aim=[] )
        xtrCtl, fkCtl, nulXtr = [], [], []    
        for pre in ['CJ', 'ik', 'aim']:
            if pre=='CJ':    jntName = '%s_' %pre
            else:           jntName = 'jnt_%s' %pre            
            if not jnts['SJ']:
                raise RuntimeError('SplineRig.setRig: No SJ joints found to duplicate')
            tmp = mc.duplicate( jnts['SJ'], rc=1 )
            
            for i, jnt in enumerate(jnts['SJ']):
                jnts[pre].append( mc.rename( tmp[i], jnt.replace('SJ_', jntName) )  )                                  
                if pre=='aim':    mc.parent( jnts[pre][-1], jnts['ik'][i] )
                if pre=='CJ':
                    xtrCtl.append( mc.rename( createCtrlCrv(1), jnt.replace('SJ_', '%s_xtr' %self.ctl) ) )
                    nulXtr.append( mc.group( xtrCtl[-1], n=jnt.replace('SJ_', 'nul_xtr') ) )
                    mc.delete( mc.parentConstraint( jnt, nulXtr[-1] ) )
                    mc.parent( jnts['CJ'][i], xtrCtl[-1] )
                    mc.setAttr( '%s.visibility' %jnts['CJ'][i], 0, l=1 )
                    if i==0:    continue
                    mc.parent( nulXtr[-1], xtrCtl[i-1] )         
        ik = mc.ikHandle( sj=jnts['ik'][0], ee=jnts['ik'][-1], c=ikCrv, sol='ikSplineSolver', ccv=False, pcv=False, n='ik_%s' %self.rName )[0]

        for i, nul in enumerate( nulXtr ):                        #custom parent constrain of xtrCtrl to aim joints
            if nul==nulXtr[0]:    continue             
            con = mc.createNode( 'parentConstraint', n='%s_parentConstraint1' %nul )
            mc.parent( con, nul )
            mc.connectAttr( '%s.worldMatrix[0]' %jnts['aim'][i], '%s.target[0].targetParentMatrix' %con, f=1 )
            mc.connectAttr( '%s.constraintRotate' %con, '%s.rotate' %nul, f=1 )
            mc.connectAttr( '%s.constraintTranslate' %con, '%s.translate' %nul, f=1 )
            mc.connectAttr( '%s.worldInverseMatrix[0]' %jnts['aim'][i-1], '%s.constraintParentInverseMatrix' %con, f=1 )             
        mc.parentConstraint( jnts['aim'][0], nulXtr[0] )
        
        pntLoc, upObj = [], []
        for i, ikJnt in enumerate( jnts['ik'] ):
            if ikJnt==jnts['ik'][-1]:    continue                                                    #aim constrain                                                
            pntLoc.append( mc.spaceLocator( n=ikJnt.replace( 'jnt_ik', 'loc_pnt' ) )[0] )            #position capture locator
            mc.setAttr( '%s.v' %pntLoc[-1], 0, l=1 )
            mc.parent( pntLoc[-1], ikJnt )
            mc.setAttr( '%s.t' %pntLoc[-1], 0, 0, 0 )
            mc.setAttr( '%s.r' %pntLoc[-1], 0, 0, 0 )
            mc.setAttr( '%s.localScale' %pntLoc[-1], 0.2, 0.2, 0.2 ) 
            
            upObj.append( mc.group( em=1, n=ikJnt.replace( 'jnt_ik', 'obj_aim' ) ) )                 #up object
            npc = mc.createNode( 'nearestPointOnCurve', n=ikJnt.replace( 'jnt_ik', 'npc_pnt' ) )    
            poc = mc.createNode( 'pointOnCurveInfo', n=ikJnt.replace( 'jnt_ik', 'poc_pnt' ) )               

            #objCrv = mc.listConnections('crv_ikName.offsetCurve')[0] 
            mc.connectAttr( '%s.worldSpace[0]' %ikCrv, '%s.inputCurve' %npc )
            mc.connectAttr( '%s.worldPosition[0]' %pntLoc[-1], '%s.inPosition' %npc )
            mc.connectAttr( '%s.worldSpace[0]' %objCrv, '%s.inputCurve' %poc )
            mc.connectAttr( '%s.parameter' %npc, '%s.parameter' %poc )
            mc.connectAttr( '%s.position' %poc, '%s.translate' %upObj[-1], f=1 )
            mc.aimConstraint( jnts['ik'][i+1], jnts['aim'][i], mo=1, w=1, aim=[1,0,0], u=[0,1,0], wut="object", wuo=upObj[-1] )
        gObj = mc.group( em=1, n='grp_objs%s' %self.rName )
        mc.parent( upObj, gObj )
        
        sw = mc.rename( createCtrlCrv(2), '%s_main%s' %(self.ctl, self.rName) )     #fkik switch ctl
        mc.parent( sw, xtrCtl[-1] )
        mc.setAttr( '%s.t' %sw, 4, 0, 0 )
        mc.setAttr( '%s.r' %sw, 0, 0, 0 )
        mc.setAttr( '%s.s' %sw, 0.2, 0.2, 0.2 )
        mc.makeIdentity( sw, apply=True, t=1, r=1, s=1, n=0 )
        mc.addAttr( sw, ln='IKFK', at='double', min=0, max=1, dv=1, k=1 )        #ikfk switch
        rev = mc.createNode( 'reverse', n='rev_ikfk%s' %self.rName )
        mc.connectAttr( '%s.IKFK' %sw, '%s.inputX' %rev, f=1 ) 
        #setting ikfk
        

        deg = mc.getAttr('%s.degree' %ikCrv)
        cvs = mc.getAttr('%s.spans' %ikCrv) + deg                       #total curve cvs

        ctlLocs, pos, drv, ancs, cnt = {'ik':[], 'obj':[]}, {'ik':[], 'obj':[]}, [], {'ik':[], 'fk':[]}, 0
        dLen = len( str(cvs) )
        for i in range( cvs ):        #anchoring locators
            for item in ['ik', 'obj']:
                pos[item].append( mc.pointPosition( 'crv_{0}{1}.cv[{2}]'.format(item, self.rName, i), w=True ) )    #setting control locator
                ctlLocs[item].append( mc.spaceLocator( n ='loc_{0}{1}{2}'.format(item, self.rName, str(i).zfill(dLen)) )[0] )
                mc.setAttr( '%s.v' %ctlLocs[item][-1], 0, l=1 )
                mc.setAttr( '%s.localScale' %ctlLocs[item][-1], 0.2, 0.2, 0.2 )
                mc.xform( ctlLocs[item][-1], ws=True, t=pos[item][-1] )
                mc.connectAttr('%s.worldPosition[0]' %ctlLocs[item][-1], 'crv_%s%s.cv[%d]' %(item, self.rName, i) )
                #setting ikfk anchoring

        for i, ctlLoc in enumerate(ctlLocs['ik']):
            if ctlLoc==ctlLocs['ik'][1] or ctlLoc==ctlLocs['ik'][-2]:    continue        
            drv.append( mc.group( em=1, n='nul_drv%s%s' %(self.rName, str(cnt).zfill(dLen)) ) )
            mc.move( pos['ik'][i][0], pos['ik'][i][1], pos['ik'][i][2], drv[-1] )
            mc.delete( mc.tangentConstraint( ikCrv, drv[-1], w=1, aim=[1,0,0], u=[0,1,0], wut="object", wuo=ctlLocs['obj'][i] ) ) 
            for ele in ['fk','ik']:    ancs[ele].append( mc.duplicate( drv[-1], n=drv[-1].replace('drv', ele) )[0] )
            pCon = mc.parentConstraint( ancs['fk'][-1], ancs['ik'][-1], drv[-1], mo=0 )[0]
            for src, pAtr in zip( ['%s.IKFK' %sw, '%s.outputX' %rev], mc.parentConstraint( pCon, q=1, wal=1 ) ):    mc.connectAttr( src, '%s.%s' %(pCon, pAtr) )
            parLocs = [ ctlLoc, ctlLocs['obj'][i] ]
            if ctlLoc==ctlLocs['ik'][0]:     parLocs = parLocs + [ ctlLocs['ik'][1],  ctlLocs['obj'][1] ]
            if ctlLoc==ctlLocs['ik'][-1]:    parLocs = parLocs + [ ctlLocs['ik'][-2], ctlLocs['obj'][-2] ]
            mc.parent( parLocs, drv[-1] )   

        gFkCtl, tmpLoc, tmpObjs = [], [], {'ik':[], 'obj':[]}
        tmpNpc = mc.createNode( 'nearestPointOnCurve', n='npc_tmp' )
        for i, nulDrv in enumerate(drv):
            tmpLoc.append( mc.spaceLocator( n='loc_tmp%d' %i )[0] )
            if i==0:    mc.delete( mc.parentConstraint( ctlLocs['ik'][0], tmpLoc[-1], mo=0 ) )
            else:       mc.delete( mc.parentConstraint( ctlLocs['ik'][i], ctlLocs['ik'][i+1], tmpLoc[-1], mo=0 ) )
            mc.connectAttr( '%s.worldPosition[0]' %tmpLoc[-1], '%s.inPosition' %tmpNpc, f=1 )
            for pls, crv in zip( ['ik', 'obj'], [ikCrv, objCrv] ):
                tmpObjs[pls].append( mc.group( em=1, n=tmpLoc[-1].replace('loc', pls ) ) ) 
                mc.connectAttr( '%s.position' %tmpNpc, '%s.translate' %tmpObjs[pls][-1], f=1 )
                mc.connectAttr( '%s.worldSpace[0]' %crv, '%s.inputCurve' %tmpNpc, f=1 )                                
                mc.disconnectAttr( '%s.position' %tmpNpc, '%s.translate' %tmpObjs[pls][-1] )

            fkCtl.append( mc.rename( createCtrlCrv(3), nulDrv.replace('nul_drv', '%s_fk' %self.ctl) ) )
            gFkCtl.append( mc.group( fkCtl[-1], n=fkCtl[-1].replace( '%s_fk' %self.ctl, 'nul_fkCtl' ) ) )                
            mc.delete( mc.pointConstraint( tmpObjs['ik'][-1], gFkCtl[-1], mo=0 ) )
            mc.delete( mc.tangentConstraint( ikCrv, gFkCtl[-1], w=1, aim=[1,0,0], u=[0,1,0], wut="object", wuo=tmpObjs['obj'][-1] ) )
            mc.parent( ancs['fk'][i], fkCtl[-1] )    #parenting fk nul
            try:       mc.parent( gFkCtl[-1], fkCtl[i-1] )
            except:    pass            
        mc.delete( tmpLoc, tmpObjs['ik'], tmpObjs['obj'] )                                
        for cj, sj in zip( jnts['CJ'], jnts['SJ'] ):    mc.parentConstraint( cj, sj, mo=1 )     #parenting sj to cj
           
        self.setSplineStretch( ikCrv, jnts['ik'] )                                              #stretch Rig
        mc.addAttr( sw, ln='stretch', at='double', min=0, max=1, dv=1, k=1 )
        mc.connectAttr( '%s.stretch' %sw, '%s.stretch' %ikCrv, f=1 )
        #if gSca:    mc.connectAttr( gSca, '%s.globalScale' %ikCrv, f=1 )
        if mc.objExists( "Ctrl_ROOT.globalScale" ):     mc.connectAttr( "Ctrl_ROOT.globalScale", '{0}.globalScale'.format(ikCrv) )
        elif mc.objExists( "Ctrl_PLACE.globalScale" ):     mc.connectAttr( "Ctrl_PLACE.globalScale", '{0}.globalScale'.format(ikCrv) )
        elif mc.objExists( 'RootPlace_MD.outputX' ):     mc.connectAttr( 'RootPlace_MD.outputX', '{0}.globalScale'.format(ikCrv) )         

        tg  = mc.group( em=1, n='grp_ctls%s' %self.rName )                                      #grouping - working, system
        mc.parent( ancs['ik'], gFkCtl[0], drv, nulXtr[0], tg )
        sys = mc.group( em=1, n='Sys_%s' %self.rName )
        for ax in ['tx','ty','tz','rx','ry','rz','sx','sy','sz']:    mc.setAttr( '%s.%s' %(sys, ax), l=1, k=0, cb=0 )
        mc.setAttr( '%s.visibility' %sys, 0, l=1 )
        mc.parent( ik, ikCrv, objCrv, gObj, sys )

        mc.addAttr( sw, ln="additionalControls", at='bool', k=1 )                                #xtrControls visibility setup
        mc.setAttr( '%s.additionalControls' %sw, e=1, channelBox=1 )
        for xc in xtrCtl:                        
            for attr in ['sx', 'sy', 'sz', 'v']:    mc.setAttr( "%s.%s" %(xc,attr), l=1, k=0, cb=0 )
            xc = mc.listRelatives( xc, s=1 )[0]
            mc.connectAttr( '%s.additionalControls' %sw, '%s.v' %xc )
            
        mc.connectAttr( '%s.IKFK' %sw, '%s.v' %fkCtl[0], f=1 )                                  #FKctl visibility 
        for fkC in fkCtl:                                                                        #cleaning fkControls
            for attr in ['sx', 'sy', 'sz', 'v']:    mc.setAttr( "%s.%s" %(fkC,attr), l=1, k=0, cb=0 )                   

        self.ancsIK = ancs['ik']
        return sys, tg, jnts['ik'], jnts['SJ'], sw, xtrCtl, fkCtl, ancs['ik']                        
        #returns sys group, control top group, ik joints, SJ joints, main control(switch), [additional controls], [fk controls], [ik anchor points]


    def setIkControls(self, ikCrv, surf, pnts, gSca=None):    #(ik curve, attach surface, ik hooks, globalScale attr)
        print(pnts)  # Updated to use parentheses
        self.rName = mc.getAttr('%s.rigName' % ikCrv)
        cps = mc.createNode('closestPointOnSurface')
        loc = mc.spaceLocator()[0]
        mc.connectAttr('%s.worldSpace[0]' % surf, '%s.inputSurface' % cps)
        mc.connectAttr('%s.worldPosition[0]' % loc, '%s.inPosition' % cps)
        atc, ikCtl = [], []
        for i, pnt in enumerate(pnts):
            ikCtl.append(mc.rename(createCtrlCrv(4), '%s_ik%s%d' % (self.ctl, self.rName, i)))
            nul = mc.group(em=1, n='nul_ikCtl%s%d' % (self.rName, i))
            mc.parent(ikCtl[-1], nul)
            mc.parent(nul, 'grp_ctls%s' % self.rName)
            mc.delete(mc.parentConstraint(pnt, nul, mo=0))
            mc.parent(pnt, ikCtl[-1])
            
            mc.delete(mc.pointConstraint(pnt, loc, mo=0, w=1))
            psi = mc.createNode('pointOnSurfaceInfo', n='psi_ikAtc%s%d' % (self.rName, i))
            mc.connectAttr('%s.worldSpace[0]' % surf, '%s.inputSurface' % psi)
            mc.setAttr('%s.parameterU' % psi, mc.getAttr('%s.parameterU' % cps))
            mc.setAttr('%s.parameterV' % psi, mc.getAttr('%s.parameterV' % cps))

            atc.append(mc.group(em=1, n='atc_ikSrf%s%d' % (self.rName, i)))
            aim = mc.createNode('aimConstraint', n='%s_aimConstraint1' % atc[-1])
            mc.parent(aim, atc[-1])
            mc.connectAttr('%s.position' % psi, '%s.translate' % atc[-1])
            mc.connectAttr('%s.normalizedNormal' % psi, '%s.worldUpVector' % aim)
            mc.connectAttr('%s.normalizedTangentU' % psi, '%s.target[0].targetTranslate' % aim)
            mc.connectAttr('%s.constraintRotate' % aim, '%s.rotate' % atc[-1])
            if gSca:
                if mc.objExists(gSca):
                    for ax in ['x', 'y', 'z']:
                        mc.connectAttr(gSca, '%s.s%s' % (atc[-1], ax))
            mc.parentConstraint(atc[-1], nul, mo=1)
        mc.parent(atc, mc.parent(mc.group(em=1, n='grp_ikSrfAtc%s' % self.rName), 'Sys_%s' % self.rName))
        mc.delete(loc, cps)

        nm = mc.getAttr('%s.rigName' % ikCrv)
        for i, c in enumerate(ikCtl):  # attr locking
            mc.connectAttr('rev_ikfk%s.outputX' % nm, '%s.v' % c)
            if i == 0:
                axis = ['tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'v']
            elif i == len(ikCtl) - 1:
                axis = ['sx', 'sy', 'sz', 'v']
            else:
                axis = ['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
            for ax in axis:
                mc.setAttr('%s.%s' % (c, ax), lock=True, keyable=False, channelBox=False)
        return ikCtl


class SplineRigUI(QtWidgets.QDialog):
    """docstring for SplineRigUI"""
    
    sRig = SplineRig()

    def __init__(self, parent=mayaMainWin() ):
        super().__init__(parent)
        
    def createUI(self):

        win_name = 'spline_win'
        if mc.window('spline_win', ex=True):    mc.deleteUI('spline_win', wnd=True)     

        self.setWindowTitle('Spline Rig')
        self.setObjectName(win_name)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setMaximumSize(280, 435)
        self.setMinimumSize(280, 435)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.create_controls()
        self.create_layout()
        self.create_slots()

        self.show()

    def create_separator(self):

        sprtr = QtWidgets.QFrame()
        sprtr.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Plain)
        #sprtr.setFixedHeight(1)
        sprtr.setLineWidth(2)
        return sprtr

    def create_controls(self):
        
        self.rigType_lbl = QtWidgets.QLabel('Rig type:')
        self.simple_rdb = QtWidgets.QRadioButton('Simple')
        self.advanced_rdb = QtWidgets.QRadioButton('Advanced')
        self.advanced_rdb.setChecked(True)

        self.topCtls_btn = QtWidgets.QPushButton('Create Top Controls')

        self.curve_lbl = QtWidgets.QLabel('Curve:')
        self.curve_ldt = QtWidgets.QTextEdit('Curve')
        self.curve_ldt.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.curve_btn = QtWidgets.QPushButton('<<')

        self.rignm_lbl = QtWidgets.QLabel('Rig Name:')
        self.rignm_ldt = QtWidgets.QTextEdit('Name')
        self.rignm_ldt.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.span_lbl = QtWidgets.QLabel('No of Spans(Bones):')
        self.span_sbx = QtWidgets.QSpinBox()
        self.span_sbx.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.span_sbx.setValue(1)

        self.jnts_btn = QtWidgets.QPushButton('Create Joints')

        self.cmnt_lbl = QtWidgets.QLabel('Re-pose Joints if necessary')

        self.offcurtmp_btn = QtWidgets.QPushButton('Offset Curve Tmp')
        self.offcurve_btn = QtWidgets.QPushButton('Offset Curve')

        self.parto_lbl = QtWidgets.QLabel('SJ Parent To:')
        self.parto_ldt = QtWidgets.QTextEdit('None')
        self.parto_ldt.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.parto_btn = QtWidgets.QPushButton('<<')

        self.sj_btn = QtWidgets.QPushButton('Set SJ')
        self.rig_btn = QtWidgets.QPushButton('Set Rig')
        self.rig_btn.setStyleSheet('background-color: blue')

        self.surf_lbl = QtWidgets.QLabel('IK Attach Surface:')
        self.surf_ldt = QtWidgets.QTextEdit()
        self.surf_ldt.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.surf_btn = QtWidgets.QPushButton('<<')

        self.ik_btn = QtWidgets.QPushButton('Set IK Controls')


    def create_layout(self):

        rigType_hlay = QtWidgets.QHBoxLayout()
        rigType_hlay.addWidget(self.rigType_lbl)
        rigType_hlay.addWidget(self.simple_rdb)
        rigType_hlay.addWidget(self.advanced_rdb)

        curve_hlay = QtWidgets.QHBoxLayout()
        curve_hlay.addWidget(self.curve_lbl)
        curve_hlay.addWidget(self.curve_ldt)
        curve_hlay.addWidget(self.curve_btn)

        rignm_hlay = QtWidgets.QHBoxLayout()
        rignm_hlay.addWidget(self.rignm_lbl)
        rignm_hlay.addWidget(self.rignm_ldt)

        span_hlay = QtWidgets.QHBoxLayout()
        span_hlay.addWidget(self.span_lbl)
        span_hlay.addWidget(self.span_sbx)

        offcrv_hlay = QtWidgets.QHBoxLayout()
        offcrv_hlay.addWidget(self.offcurtmp_btn)
        offcrv_hlay.addWidget(self.offcurve_btn)

        parto_hlay = QtWidgets.QHBoxLayout()
        parto_hlay.addWidget(self.parto_lbl)
        parto_hlay.addWidget(self.parto_ldt)
        parto_hlay.addWidget(self.parto_btn)

        surf_hlay = QtWidgets.QHBoxLayout()
        surf_hlay.addWidget(self.surf_lbl)
        surf_hlay.addWidget(self.surf_ldt)
        surf_hlay.addWidget(self.surf_btn)

        #Main V layout
        main_lay = QtWidgets.QVBoxLayout()
        main_lay.setContentsMargins(2,2,2,2)
        self.setLayout(main_lay)
        
        main_lay.addLayout(rigType_hlay)
        
        main_lay.addWidget( self.create_separator() )
        main_lay.addWidget(self.topCtls_btn)
        main_lay.addWidget( self.create_separator() )

        main_lay.addLayout(curve_hlay)
        main_lay.addLayout(rignm_hlay)
        main_lay.addLayout(span_hlay)

        main_lay.addWidget(self.jnts_btn)

        main_lay.addWidget(self.cmnt_lbl)
        main_lay.addWidget( self.create_separator() )

        main_lay.addLayout(offcrv_hlay)
        main_lay.addLayout(parto_hlay)

        main_lay.addWidget(self.sj_btn)

        main_lay.addWidget(self.rig_btn)
        main_lay.addWidget( self.create_separator() )

        main_lay.addLayout(surf_hlay)

        main_lay.addWidget(self.ik_btn)

        #self.setLayout(main_lay)
        
    def create_slots(self):

        self.simple_rdb.toggled.connect( lambda:self.ikuiState(self.simple_rdb) )
        self.advanced_rdb.toggled.connect( lambda:self.ikuiState(self.advanced_rdb) )

        self.topCtls_btn.clicked.connect(self.topctlbtnpress)

        self.curve_btn.clicked.connect(self.getCurve)

        self.jnts_btn.clicked.connect(self.createJoints)

        self.offcurtmp_btn.clicked.connect(self.setOffsetCurveTemplate)

        self.offcurve_btn.clicked.connect(self.setOffsetCurve)

        self.parto_btn.clicked.connect(self.getSjParent)

        self.sj_btn.clicked.connect(self.setSkinJoints)

        self.rig_btn.clicked.connect(self.doRig)


        self.surf_btn.clicked.connect(self.getSurface)
        self.ik_btn.clicked.connect(self.ikControls)
    
    def ikuiState(self, rb):
        if rb.text() == 'Simple':
            self.ik_btn.setDisabled(True)
            self.surf_lbl.setDisabled(True)
            self.surf_ldt.setDisabled(True)
            self.surf_btn.setDisabled(True)

        if rb.text() == 'Advanced':
            self.ik_btn.setEnabled(True)
            self.surf_lbl.setEnabled(True)
            self.surf_ldt.setEnabled(True)
            self.surf_btn.setEnabled(True)

    def getCurve(self):
        crv = mc.selected()[0]
        if crv.hasAttr('rigName'):
            self.rignm_ldt.setText( crv.rigName.get() )
        if crv.hasAttr('joints'):
            self.span_sbx.setValue( len( crv.joints.listConnections() )-1 )
        if crv.hasAttr('offsetCurve'):
            spn = crv.offsetCurve.get().spans.get()
        else:
            spn = 0
        self.curve_ldt.setText(crv.name() )
   
    def topctlbtnpress(self):
        #splineTestUI.tt.topctlbtn()
        setTopHierarchy()

    def createJoints(self):
        rName = self.rignm_ldt.toPlainText()
        crv   = self.curve_ldt.toPlainText()
        split = self.span_sbx.value()
        self.curve_ldt.setText( SplineRigUI.sRig.createJoints( crv, split, rName) )

    def setOffsetCurveTemplate(self):
        crv   = self.curve_ldt.toPlainText()
        SplineRigUI.sRig.offsetCurveTemplate( crv)

    def setOffsetCurve(self):
        crv   = self.curve_ldt.toPlainText()
        SplineRigUI.sRig.createOffsetCurve( crv)

    def getSjParent(self):
        self.parto_ldt.setText( mc.selected()[0].name() )

    def setSkinJoints(self):
        crv = self.curve_ldt.toPlainText()
        par = self.parto_ldt.toPlainText()
        if not par or par=='None':    
            par=None
        SplineRigUI.sRig.setSJ( crv, par)

    def doRig(self):
        crv = self.curve_ldt.toPlainText()
        if self.simple_rdb.isChecked():
            SplineRigUI.sRig.setSimpleRig( crv)
        elif self.advanced_rdb.isChecked():
            SplineRigUI.sRig.setRig( crv)

    def getSurface(self):
        self.surf_ldt.setText( mc.selected()[0].name() )

    def ikControls(self):
        SplineRigUI.sRig.setIkControls( self.curve_ldt.toPlainText(), self.surf_ldt.toPlainText(), 
                                        SplineRigUI.sRig.ancsIK, 'Ctrl_PLACE.globalScale' )


        

#######################
if __name__ == '__main__':
    ui = SplineRigUI()
    
    ui.createUI()
    #ui.show()