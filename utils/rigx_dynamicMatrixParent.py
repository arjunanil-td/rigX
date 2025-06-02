import maya.cmds as mc


class MatrixDynParent(object):
    """A Maya UI Tool for setting up dynamic parent switching using Offset Parent Matrix."""
    
    def __init__(self):
        super(MatrixDynParent, self).__init__()
        
        self.wid = {}    
        if mc.window( 'dynParWin', ex=1 ):        mc.deleteUI( 'dynParWin' )
        if mc.windowPref( 'dynParWin', ex=1 ):    mc.windowPref( 'dynParWin', r=1 )

        self.wid['win']  = mc.window( 'dynParWin', t='Dynamic Matrix Parent', s=0 )
        self.wid['mLay'] = mc.columnLayout(adj=1)
        
        mc.rowLayout(nc=2)
        mc.text( 'Parent Objs', w=130)
        mc.text( 'EnumNames', w=100)
        mc.setParent('..')
        
        self.wid['rCLay'] = mc.columnLayout(adj=1)

        mc.button( 'Add Parent Field', p=self.wid['mLay'], c=lambda event:self.addField() )

        mc.separator( h=6, st='none', p=self.wid['mLay'] )
        mc.rowLayout( nc=3, p=self.wid['mLay'] )
        mc.text( 'Offset:', w=80)
        self.wid['obj_tf'] = mc.textField( w=120, h=24 )
        mc.button( '<<', w=35, c=lambda event:self.addParent('obj_tf', None) )

        mc.separator( h=6, st='none', p=self.wid['mLay'] )
        mc.rowLayout( nc=3, p=self.wid['mLay'] )
        mc.text( 'Control:', w=80)
        self.wid['ctl_tf'] = mc.textField( w=120, h=24 )
        mc.button( '<<', w=35, c=lambda event:self.addParent('ctl_tf', None) )        

        mc.separator( h=6, st='none', p=self.wid['mLay'] )
        mc.button( 'Set Dynamic Matrix Parent', h=24, p=self.wid['mLay'], c=lambda event:self.dynParent() )

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
        if sel:  
            mc.textField( self.wid[tfnm], e=True, tx=sel[0] )
            if tfen:
                mc.textField( self.wid[tfen], e=True, tx=sel[0] )


    def create_nested_groups(self, parent_transforms, control_name):
        # Validate inputs
        for parent in parent_transforms:
            if not mc.objExists(parent):
                raise ValueError(f"Parent transform '{parent}' does not exist.")
        if not mc.objExists(control_name):
            raise ValueError(f"Control '{control_name}' does not exist.")

        # Save the original parent of the control
        original_parent = mc.listRelatives(control_name, parent=True)
        top_level_group = None  
        first_group_name = None  

        # Create nested groups for each parent transform
        for parent in parent_transforms:
            # Create the first null group
            null_group1_name = f"{parent}_Tmp_{control_name}"
            null_group1 = mc.group(empty=True, name=null_group1_name)

            mc.matchTransform(null_group1, parent)

            if first_group_name is None:
                first_group_name = null_group1

            # Create the second null group nested inside the first null group
            null_group2_name = f"{parent}_Buf_{control_name}"
            null_group2 = mc.group(empty=True, name=null_group2_name, parent=null_group1)

            mc.matchTransform(null_group2, parent)

            if top_level_group:
                mc.parent(null_group1, top_level_group)

            top_level_group = null_group2

        mc.parent(control_name, top_level_group)
        
        # Re-parent the first group back to the original parent of the control
        if original_parent:
            mc.parent(first_group_name, original_parent[0])
        else:
            mc.parent(first_group_name, world=True)

        return top_level_group, first_group_name




    def setDynParent(self, obj, parents, control, attr_name="parentSwitch"):
        """
        Sets up dynamic parent switching using Offset Parent Matrix and a choice node.
        """
        if not mc.objExists(obj):
            mc.warning(f"Object {obj} does not exist.")
            return
        
        cnt = mc.columnLayout(self.wid['rCLay'], q=True, nch=True)
        enums = []
        for i in range(cnt):    
            enums.append(mc.textField(self.wid[f'enu{i+1}_tf'], q=True, tx=True))

        # Ensure the enum attribute exists on the control
        if not mc.attributeQuery(attr_name, node=control, exists=True):
            mc.addAttr(control, longName=attr_name, attributeType="enum",
                    enumName=":".join(enums), keyable=True)


        self.create_nested_groups(parents, obj)

        offset_parent = mc.listRelatives(control, parent=True)
        # Create utility nodes
        choice_node = mc.createNode("choice", name=f"choice_{obj}")
        pick_matrix = mc.createNode("pickMatrix", name=f"dm_{obj}")

        for i, p in enumerate(parents):
            if mc.objExists(p):
                buf_grp = (f"{p}_Buf_{obj}")
                mult_matrix = mc.createNode("multMatrix", name=f"mm_{p}")  
                mc.connectAttr(f"{buf_grp}.worldInverseMatrix[0]", f"{mult_matrix}.matrixIn[0]")
                mc.connectAttr(f"{p}.worldMatrix[0]", f"{mult_matrix}.matrixIn[1]")
                mc.connectAttr(f"{mult_matrix}.matrixSum", f"{choice_node}.input[{i}]")


        mc.connectAttr(f"{control}.{attr_name}", f"{choice_node}.selector")
        mc.connectAttr(f"{choice_node}.output", f"{pick_matrix}.inputMatrix")
        mc.connectAttr(f"{pick_matrix}.outputMatrix", f"{offset_parent[0]}.offsetParentMatrix")

        print(f"Dynamic parenting setup complete for {obj} using Offset Parent Matrix with a choice node.")


    def dynParent(self):
        cnt = mc.columnLayout(self.wid['rCLay'], q=True, nch=True)
        parents = []
        for i in range(cnt):    
            parents.append(mc.textField(self.wid[f'par{i+1}_tf'], q=True, tx=True))
        
        obj = mc.textField(self.wid['obj_tf'], q=True, tx=True)
        control = mc.textField(self.wid['ctl_tf'], q=True, tx=True)

        # Check if control has a parent
        nul = mc.listRelatives(obj, p=True, c=False)
        if not nul:
            mc.warning(f"Control {control} has no parent.")
            return

        # Check for existing input connections and remove them
        existing_connections = mc.listConnections(f"{obj}.offsetParentMatrix", source=True, destination=False, plugs=True)
        
        if existing_connections:
            for connection in existing_connections:
                mc.disconnectAttr(connection, f"{obj}.offsetParentMatrix")
                print(f"Disconnected existing connection: {connection} -> {obj}.offsetParentMatrix")

        self.setDynParent(obj, parents, control)


if __name__ == '__main__':
    MatrixDynParent()
