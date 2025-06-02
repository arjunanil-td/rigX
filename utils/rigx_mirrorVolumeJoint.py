import maya.cmds as mc
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui


def mirror_slide_and_follow(direction='LtoR'):
    """
    Mirror the 'slide' attribute between matching volume slider joints and
    the 'follow' attribute between matching partial joints.

    Args:
        direction (str): 'LtoR' to mirror from *Slider*_L → *Slider*_R (default),
                         'RtoL' to mirror from *Slider*_R → *Slider*_L.
    """
    if direction not in ('LtoR', 'RtoL'):
        mc.warning(f"Invalid mirror direction '{direction}'. Use 'LtoR' or 'RtoL'.")
        return
    src_suffix, tgt_suffix = ('_L','_R') if direction=='LtoR' else ('_R','_L')

    # Slide attributes
    slide_pattern = f"*Slider*{src_suffix}"
    joints = mc.ls(slide_pattern,type='joint') or []
    for src in joints:
        if mc.attributeQuery('slide',node=src,exists=True):
            tgt = src.replace(src_suffix,tgt_suffix)
            if mc.objExists(tgt) and mc.attributeQuery('slide',node=tgt,exists=True):
                val = mc.getAttr(f"{src}.slide")
                mc.setAttr(f"{tgt}.slide",val)

    # Follow attributes
    follow_pattern = f"*Partial*{src_suffix}"
    joints = mc.ls(follow_pattern,type='joint') or []
    for src in joints:
        if mc.attributeQuery('follow',node=src,exists=True):
            tgt = src.replace(src_suffix,tgt_suffix)
            if mc.objExists(tgt) and mc.attributeQuery('follow',node=tgt,exists=True):
                val = mc.getAttr(f"{src}.follow")
                mc.setAttr(f"{tgt}.follow",val)

    mc.inViewMessage(statusMessage='Mirror '+direction+' complete',fade=True)


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class MirrorVolumeUI(QtWidgets.QDialog):
    """UI for mirroring slide and follow attributes."""
    def __init__(self, parent=maya_main_window()):
        super(MirrorVolumeUI, self).__init__(parent)
        self.setWindowTitle('Mirror Volume Joints')
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(200,100)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.group = QtWidgets.QButtonGroup(self)
        ltoR = QtWidgets.QRadioButton('Left → Right')
        rtoL = QtWidgets.QRadioButton('Right → Left')
        ltoR.setChecked(True)
        self.group.addButton(ltoR,0)
        self.group.addButton(rtoL,1)
        layout.addWidget(ltoR)
        layout.addWidget(rtoL)
        btn = QtWidgets.QPushButton('Mirror')
        btn.clicked.connect(self._on_mirror)
        layout.addWidget(btn)

    def _on_mirror(self):
        direction = 'LtoR' if self.group.checkedId()==0 else 'RtoL'
        mirror_slide_and_follow(direction)
        self.close()


# Singleton
_dialog = None

def show_mirror_ui():
    global _dialog
    try:
        _dialog.close()
    except:
        pass
    _dialog = MirrorVolumeUI()
    _dialog.show()
