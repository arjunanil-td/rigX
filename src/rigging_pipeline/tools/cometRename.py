"""
CometRename - Python implementation
Based on the original cometRename.mel by Michael B. Comet

A comprehensive renaming utility for Maya with:
- Search & Replace functionality
- Prefix/Suffix addition  
- Sequential rename with numbering
- Proper hierarchy handling
"""

import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner


def maya_main_window():
    """Get Maya's main window"""
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class CometRenameUtils:
    """Utility functions for CometRename functionality"""
    
    @staticmethod
    def string_replace(text, search, replace):
        """
        Replace all occurrences of search string with replace string.
        Handles edge cases properly like the original MEL version.
        """
        if not search or not text:
            return text
        
        return text.replace(search, replace)
    
    @staticmethod
    def get_short_name(obj):
        """Get the short name from a full path (last part after |)"""
        if not obj:
            return ""
        
        parts = obj.split("|")
        return parts[-1] if parts else obj
    
    @staticmethod
    def do_rename(mode, **kwargs):
        """
        Main rename function
        
        Args:
            mode (int): 0=Search&Replace, 1=Prefix, 2=Suffix, 3=Rename&Number
            **kwargs: Various parameters for renaming
        """
        # Get selection mode
        selection_mode = kwargs.get('selection_mode', 'selected')
        
        # Get objects based on selection mode
        if selection_mode == 'selected':
            objs = cmds.ls(selection=True, long=True)
            if not objs:
                cmds.warning("No objects selected for renaming")
                return
        elif selection_mode == 'hierarchy':
            selected = cmds.ls(selection=True, long=True)
            if not selected:
                cmds.warning("No objects selected to get hierarchy from")
                return
            objs = []
            for sel in selected:
                descendants = cmds.listRelatives(sel, allDescendents=True, fullPath=True) or []
                objs.append(sel)  # Include the selected object itself
                objs.extend(descendants)
            # Remove duplicates while preserving order
            seen = set()
            objs = [x for x in objs if not (x in seen or seen.add(x))]
        elif selection_mode == 'all':
            objs = cmds.ls(transforms=True, long=True)
            if not objs:
                cmds.warning("No transform objects found in scene")
                return
        else:
            objs = cmds.ls(selection=True, long=True)
            if not objs:
                cmds.warning("No objects selected for renaming")
                return
        
        obj_count = len(objs)
        
        # Extract parameters
        search = kwargs.get('search', '')
        replace = kwargs.get('replace', '')
        prefix = kwargs.get('prefix', '')
        suffix = kwargs.get('suffix', '')
        rename_base = kwargs.get('rename', '')
        start_num = kwargs.get('start', 1)
        padding = kwargs.get('padding', 0)
        
        # Process each object
        for i, obj in enumerate(objs):
            short_name = CometRenameUtils.get_short_name(obj)
            new_short_name = ""
            
            if mode == 0:  # Search & Replace
                if not search:
                    cmds.warning("Can't search and replace, search field is blank!")
                    return
                new_short_name = CometRenameUtils.string_replace(short_name, search, replace)
                
            elif mode == 1:  # Add Prefix
                if not prefix:
                    cmds.warning("Can't add prefix, prefix field is blank!")
                    return
                new_short_name = prefix + short_name
                
            elif mode == 2:  # Add Suffix
                if not suffix:
                    cmds.warning("Can't add suffix, suffix field is blank!")
                    return
                new_short_name = short_name + suffix
                
            elif mode == 3:  # Rename & Number
                if not rename_base:
                    cmds.warning("Can't rename and number, rename field is blank!")
                    return
                
                # Calculate number with padding
                n = i + start_num
                pad_str = str(n).zfill(padding + len(str(n)))
                new_short_name = rename_base + pad_str
            
            # Perform the rename
            try:
                new_name = cmds.rename(obj, new_short_name)
                cmds.select(new_name, replace=True)
                new_long_names = cmds.ls(selection=True, long=True)
                new_long_name = new_long_names[0] if new_long_names else new_name
                
                # Update the objects list to handle hierarchy changes
                for j in range(obj_count):
                    tmp = objs[j] + "|"
                    tmp = tmp.replace(obj + "|", "|" + new_long_name + "|")
                    tmp = tmp.rstrip("|")
                    objs[j] = tmp
                    
            except Exception as e:
                cmds.warning(f"Failed to rename {short_name}: {str(e)}")
        
        # Reselect all renamed objects
        try:
            cmds.select(objs, replace=True)
        except:
            pass


class CometRenameUI(QtWidgets.QDialog):
    """CometRename UI - Python/Qt version of the original MEL UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent or maya_main_window())
        
        self.setWindowTitle("CometRename - Python")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(320, 450)
        self.setStyleSheet(THEME_STYLESHEET)
        
        self.build_ui()
    
    def build_ui(self):
        """Build the user interface"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Add banner
        banner = Banner("CometRename", "rename.png")
        layout.addWidget(banner)
        
        # Search & Replace Section
        search_group = QtWidgets.QGroupBox("Search & Replace")
        search_group.setStyleSheet(self._get_group_style())
        search_layout = QtWidgets.QVBoxLayout(search_group)
        
        # Search field
        search_row = QtWidgets.QHBoxLayout()
        search_row.addWidget(QtWidgets.QLabel("Search:"))
        self.search_field = QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Text to find")
        search_row.addWidget(self.search_field)
        search_layout.addLayout(search_row)
        
        # Replace field
        replace_row = QtWidgets.QHBoxLayout()
        replace_row.addWidget(QtWidgets.QLabel("Replace:"))
        self.replace_field = QtWidgets.QLineEdit()
        self.replace_field.setPlaceholderText("Text to replace with")
        replace_row.addWidget(self.replace_field)
        search_layout.addLayout(replace_row)
        
        # Search & Replace button
        search_btn = QtWidgets.QPushButton("Search And Replace")
        search_btn.clicked.connect(lambda: self.do_rename(0))
        search_layout.addWidget(search_btn)
        
        layout.addWidget(search_group)
        
        # Prefix Section
        prefix_group = QtWidgets.QGroupBox("Add Prefix")
        prefix_group.setStyleSheet(self._get_group_style())
        prefix_layout = QtWidgets.QVBoxLayout(prefix_group)
        
        prefix_row = QtWidgets.QHBoxLayout()
        prefix_row.addWidget(QtWidgets.QLabel("Prefix:"))
        self.prefix_field = QtWidgets.QLineEdit()
        self.prefix_field.setPlaceholderText("Text to add before name")
        prefix_row.addWidget(self.prefix_field)
        prefix_layout.addLayout(prefix_row)
        
        prefix_btn = QtWidgets.QPushButton("Add Prefix")
        prefix_btn.clicked.connect(lambda: self.do_rename(1))
        prefix_layout.addWidget(prefix_btn)
        
        layout.addWidget(prefix_group)
        
        # Suffix Section
        suffix_group = QtWidgets.QGroupBox("Add Suffix")
        suffix_group.setStyleSheet(self._get_group_style())
        suffix_layout = QtWidgets.QVBoxLayout(suffix_group)
        
        suffix_row = QtWidgets.QHBoxLayout()
        suffix_row.addWidget(QtWidgets.QLabel("Suffix:"))
        self.suffix_field = QtWidgets.QLineEdit()
        self.suffix_field.setPlaceholderText("Text to add after name")
        suffix_row.addWidget(self.suffix_field)
        suffix_layout.addLayout(suffix_row)
        
        suffix_btn = QtWidgets.QPushButton("Add Suffix")
        suffix_btn.clicked.connect(lambda: self.do_rename(2))
        suffix_layout.addWidget(suffix_btn)
        
        layout.addWidget(suffix_group)
        
        # Rename & Number Section
        rename_group = QtWidgets.QGroupBox("Rename & Number")
        rename_group.setStyleSheet(self._get_group_style())
        rename_layout = QtWidgets.QVBoxLayout(rename_group)
        
        # Rename field
        rename_row = QtWidgets.QHBoxLayout()
        rename_row.addWidget(QtWidgets.QLabel("Rename:"))
        self.rename_field = QtWidgets.QLineEdit()
        self.rename_field.setPlaceholderText("Base name for objects")
        rename_row.addWidget(self.rename_field)
        rename_layout.addLayout(rename_row)
        
        # Number controls
        number_row = QtWidgets.QHBoxLayout()
        number_row.addWidget(QtWidgets.QLabel("Start #:"))
        self.start_spin = QtWidgets.QSpinBox()
        self.start_spin.setRange(0, 9999)
        self.start_spin.setValue(1)
        number_row.addWidget(self.start_spin)
        
        number_row.addWidget(QtWidgets.QLabel("Padding:"))
        self.padding_spin = QtWidgets.QSpinBox()
        self.padding_spin.setRange(0, 10)
        self.padding_spin.setValue(0)
        number_row.addWidget(self.padding_spin)
        rename_layout.addLayout(number_row)
        
        rename_btn = QtWidgets.QPushButton("Rename And Number")
        rename_btn.clicked.connect(lambda: self.do_rename(3))
        rename_layout.addWidget(rename_btn)
        
        layout.addWidget(rename_group)
        
        # Close button
        layout.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _get_group_style(self):
        """Get consistent group box styling"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #48bb78;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #4a5568;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 5px 0 5px;
            }
        """
    
    def do_rename(self, mode):
        """Execute rename operation"""
        kwargs = {
            'search': self.search_field.text(),
            'replace': self.replace_field.text(),
            'prefix': self.prefix_field.text(),
            'suffix': self.suffix_field.text(),
            'rename': self.rename_field.text(),
            'start': self.start_spin.value(),
            'padding': self.padding_spin.value()
        }
        
        CometRenameUtils.do_rename(mode, **kwargs)


# Global dialog reference
_comet_rename_dialog = None


def launch_comet_rename():
    """Launch the CometRename dialog"""
    global _comet_rename_dialog
    
    try:
        if _comet_rename_dialog is not None:
            _comet_rename_dialog.close()
            _comet_rename_dialog.deleteLater()
    except:
        pass
    
    _comet_rename_dialog = CometRenameUI()
    _comet_rename_dialog.show()
    return _comet_rename_dialog


# Quick access functions for utility tools integration
def comet_search_replace(search_text, replace_text, selection_mode='selected'):
    """Quick search and replace function"""
    CometRenameUtils.do_rename(0, search=search_text, replace=replace_text, selection_mode=selection_mode)


def comet_add_prefix(prefix_text, selection_mode='selected'):
    """Quick add prefix function"""
    CometRenameUtils.do_rename(1, prefix=prefix_text, selection_mode=selection_mode)


def comet_add_suffix(suffix_text, selection_mode='selected'):
    """Quick add suffix function"""
    CometRenameUtils.do_rename(2, suffix=suffix_text, selection_mode=selection_mode)


def comet_rename_number(base_name, start_num=1, padding=2, selection_mode='selected'):
    """Quick rename and number function"""
    CometRenameUtils.do_rename(3, rename=base_name, start=start_num, padding=padding, selection_mode=selection_mode)


def comet_change_case(case_type):
    """Quick change case function"""
    try:
        selected = cmds.ls(selection=True, long=True)
        if not selected:
            cmds.warning("Please select objects to rename")
            return
        
        from rigging_pipeline.utils.rig import utils_name
        utils_name.change_case(selected, case_type)
        print(f"Changed case to {case_type} for {len(selected)} objects")
        
    except Exception as e:
        cmds.error(f"Error changing case: {str(e)}")
