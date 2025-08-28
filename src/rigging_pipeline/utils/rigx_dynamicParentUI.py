import maya.cmds as mc

class SetParentRig(object):
    """docstring for RibbonRig"""
    def __init__(self):
        super().__init__()
        
        self.wid = {}    
        if mc.window( 'dynParWin', ex=1 ):        mc.deleteUI( 'dynParWin' )
        if mc.windowPref( 'dynParWin', ex=1 ):    mc.windowPref( 'dynParWin', r=1 )

        self.wid['win']  = mc.window( 'dynParWin', t='Dynamic Parent', s=0 )
        self.wid['mLay'] = mc.columnLayout(adj=1)
        
        mc.rowLayout(nc=2)
        mc.text( 'Parent Objs', w=130)
        mc.text( 'EnumNames', w=100)
        mc.setParent('..')
        
        self.wid['rCLay'] = mc.columnLayout(adj=1)

        mc.button( 'Add Parent Field', p=self.wid['mLay'], c=lambda event:self.addField() )

        mc.separator( h=6, st='none', p=self.wid['mLay'] )
        mc.rowLayout( nc=3, p=self.wid['mLay'] )
        mc.text( 'Object:', w=80)
        self.wid['obj_tf'] = mc.textField( w=120, h=24 )
        mc.button( '<<', w=35, c=lambda event:self.addParent('obj_tf', None) )

        mc.separator( h=6, st='none', p=self.wid['mLay'] )
        mc.rowLayout( nc=3, p=self.wid['mLay'] )
        mc.text( 'Control:', w=80)
        self.wid['ctl_tf'] = mc.textField( w=120, h=24 )
        mc.button( '<<', w=35, c=lambda event:self.addParent('ctl_tf', None) )        

        mc.separator( h=6, st='none', p=self.wid['mLay'] )
        mc.button( 'Set Dynamic Parent', h=24,p=self.wid['mLay'], c=lambda event:self.dynParent() )

        self.addField()
        self.addField()
        
        mc.showWindow('dynParWin')

    def addField(self):
        i = mc.columnLayout( self.wid['rCLay'], q=True, nch=True )
        tfnm = 'par{0}_tf'.format(i+1)
        tfen = 'enu{0}_tf'.format(i+1)

        mc.rowLayout( nc=3, p=self.wid['rCLay'] )
        self.wid[tfnm] = mc.textField( w=100, h=24 )
        mc.button( '<<', w=30, c=lambda event:self.addParent(tfnm, tfen) )
        self.wid[tfen] = mc.textField( w=100, h=24) 

    def addParent(self, tfnm, tfen):
        sel = mc.ls(sl=True)
        mc.textField( self.wid[tfnm], e=True, tx=sel[0] )
        if tfen:    mc.textField( self.wid[tfen], e=True, tx=sel[0] )

    def dynParent(self):
        cnt = mc.columnLayout( self.wid['rCLay'], q=True, nch=True ) 
        par = []
        for i in range(cnt):    par.append( mc.textField( self.wid['par{0}_tf'.format(i+1)], q=True, tx=True ) )
        #self.obj = mc.textField( self.wid['obj_tf'], q=True, tx=True )
        ctl = mc.textField( self.wid['ctl_tf'], q=True, tx=True )

        nul = mc.listRelatives(ctl, p=True, c=False)[0]
        #g = mc.group( em=True, n='g{0}'.format(self.obj) )        
        #mc.xform( g, ws=True, t=mc.xform(self.obj, q=True, ws=True, rp=True), ro=mc.xform(self.obj, q=True, ws=True, ro=True) )
        #mc.parent(self.obj, g)

        pCon = mc.parentConstraint( par, nul, mo=True )[0]

        #enm = []
        #for i in range(cnt):    enm.append( mc.textField( self.wid['enu{0}_tf'.format(i+1)], q=True, tx=True ) )
        enm = [ mc.textField( self.wid['enu{0}_tf'.format(i+1)], q=True, tx=True )    for i in range(cnt) ]
        enm = [ obj.replace('Ctrl_', '')   if 'Ctrl_' in obj   else obj      for obj in enm ]
        ctl = mc.textField( self.wid['ctl_tf'], q=True, tx=True )

        mc.addAttr( ctl, ln="mNodeId",  dt="string" )
        mc.setAttr( '{}.mNodeId'.format(ctl), ctl, type="string" )

        #mc.addAttr( ctl, ln="parentSwitch", at="enum", en=':'.join(enm)+':' ) 
        mc.addAttr( ctl, ln="parentTo",     at="enum", en=':'.join(enm)+':', k=True ) 
        #mc.addAttr( ctl, ln="switchNetwork", at="message" ) 

        #nwk = mc.createNode('network', n='nwk_{0}'.format(ctl))
        #mc.addAttr( nwk, ln="switchNetwork", at="message" ) 
        #mc.connectAttr( '{0}.switchNetwork'.format(nwk), '{0}.switchNetwork'.format(ctl) )

        cAtr = mc.parentConstraint( pCon, q=True, wal=True )
        tgts = mc.parentConstraint( pCon, q=True, tl=True ) 
        for i in range(cnt):    
            con = mc.createNode( 'condition', n='{0}Par{1}'.format(ctl.replace( 'Ctrl_', 'con_'), tgts[i].replace( 'Ctrl_', '') ) )
            mc.setAttr( "{0}.secondTerm".format(con), i )
            mc.setAttr( "{0}.colorIfTrue".format(con), 1,1,1 )
            mc.setAttr( "{0}.colorIfFalse".format(con), 0,0,0 )
            mc.connectAttr( '{0}.parentTo'.format(ctl), "{0}.firstTerm".format(con), f=True )
            mc.connectAttr( '{0}.outColorR'.format(con), '{0}.{1}'.format(pCon,cAtr[i]), f=True )

        mc.select(ctl)




if __name__ == '__main__':
    SetParentRig()