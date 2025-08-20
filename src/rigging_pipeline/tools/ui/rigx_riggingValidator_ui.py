import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class RiggingValidatorUI(QtWidgets.QDialog):
    """UI for the rigging validation tool"""
    
    def __init__(self, parent=maya_main_window(), validator=None):
        super(RiggingValidatorUI, self).__init__(parent)
        
        self.setWindowTitle("RigX Rigging Validator")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(600, 900)
        
        self.setStyleSheet(THEME_STYLESHEET)
        self.validator = validator
        self._updating_check_all = False  # Flag to prevent circular dependency
        
        # Initialize button dictionaries
        self.module_verify_buttons = {}
        self.module_fix_buttons = {}
        
        self.build_ui()
    
    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Add the centralized banner
        banner = Banner("RigX Rigging Validator", "rigX_validator.png")
        layout.addWidget(banner)
        
        # ───── Validation Options ─────
        options_group = QtWidgets.QGroupBox("Validation Options")
        options_layout = QtWidgets.QVBoxLayout(options_group)
        
        # Add Check All checkbox
        self.checkbox_check_all = QtWidgets.QCheckBox("Check All")
        self.checkbox_check_all.clicked.connect(self.toggle_all_modules)
        self.checkbox_check_all.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #555555;
                background-color: #2b2b2b;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #4CAF50;
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #666666;
            }
        """)
        
        options_layout.addWidget(self.checkbox_check_all)
        
        # Create tab widget for different validation categories
        self.modules_tabs = QtWidgets.QTabWidget()
        self.modules_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
        """)
        
        if self.validator:
            self.build_module_tabs()
        
        options_layout.addWidget(self.modules_tabs)
        layout.addWidget(options_group)
        
        # ───── Action Buttons ─────
        button_layout = QtWidgets.QHBoxLayout()
        
        self.btn_validate = QtWidgets.QPushButton("Run Validation")
        self.btn_validate.clicked.connect(self.run_validation)
        self.btn_validate.setStyleSheet("""
            QPushButton { 
                background-color: #666666; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #444444;
            }
        """)
        
        self.btn_fix = QtWidgets.QPushButton("Fix Issues")
        self.btn_fix.clicked.connect(self.fix_issues)
        self.btn_fix.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.btn_clear = QtWidgets.QPushButton("Clear Results")
        self.btn_clear.clicked.connect(lambda: self.clear_results("both"))
        self.btn_clear.setStyleSheet("""
            QPushButton { 
                background-color: #666666; 
                color: white; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        
        button_layout.addWidget(self.btn_validate)
        button_layout.addWidget(self.btn_fix)
        button_layout.addWidget(self.btn_clear)
        layout.addLayout(button_layout)
        
        layout.addWidget(self._separator())
        
        # ───── Results Display ─────
        results_group = QtWidgets.QGroupBox("Validation Results")
        results_layout = QtWidgets.QHBoxLayout(results_group)
        
        # Info section (for verify/validation output)
        info_section = QtWidgets.QVBoxLayout()
        info_label = QtWidgets.QLabel("ℹ️ Info")
        info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
                background-color: #3a3a3a;
                border-radius: 4px;
            }
        """)
        info_section.addWidget(info_label)
        
        self.info_list = QtWidgets.QListWidget()
        self.info_list.setStyleSheet("""
            QListWidget { 
                background-color: #2b2b2b; 
                border: 1px solid #555555;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                min-height: 200px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #4a4a4a;
            }
        """)
        self.info_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.info_list.customContextMenuRequested.connect(self.show_info_context_menu)
        info_section.addWidget(self.info_list)
        
        # Vertical separator line
        separator_line = QtWidgets.QFrame()
        separator_line.setFrameShape(QtWidgets.QFrame.VLine)
        separator_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator_line.setStyleSheet("QFrame { background-color: #555555; }")
        
        # Results section (for fix output)
        results_section = QtWidgets.QVBoxLayout()
        results_label = QtWidgets.QLabel("📋 Results")
        results_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
                background-color: #3a3a3a;
                border-radius: 4px;
            }
        """)
        results_section.addWidget(results_label)
        
        self.results_list = QtWidgets.QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget { 
                background-color: #2b2b2b; 
                border: 1px solid #555555;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                min-height: 200px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background-color: #4a4a4a;
            }
        """)
        self.results_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_results_context_menu)
        results_section.addWidget(self.results_list)
        
        # Add sections to the main layout with separator
        results_layout.addLayout(info_section)
        results_layout.addWidget(separator_line)
        results_layout.addLayout(results_section)
        layout.addWidget(results_group)
    
    def build_module_tabs(self):
        """Build the module tabs based on available validation modules"""
        if not self.validator:
            return
        
        # Initialize the rig_modules_widgets dictionary for filtering
        self.rig_modules_widgets = {}
        
        # Add validation descriptions dictionary from English.json
        self.validation_descriptions = {
            # Model validations (CheckIn) - Geometry and mesh related
            "VaccineCleaner": "It will desinfect the vaccine virus.",
            "ImportReference": "It will check if there are referenced file to import them up.",
            "NamespaceCleaner": "Check if there are namespaces to clean them up. It won't delete namespace from rigXGuides.",
            "UnlockInitialShadingGroup": "It will unlock the InitialShadingGroup to avoid the blocking to just create a simple polyCube.",
            "ShowBPCleaner": "It will delete the ShowBP scriptNodes.",
            "DuplicatedName": "Check if there are any node with duplicated name and report them.",
            "ParentedGeometry": "It will verify if there are some parented geometries in the hierarchy.",
            "OneVertex": "It will verify if there are some non manifold vertex in the meshes. That means a vertex in the union of 2 shapes.",
            "TFaceCleaner": "It will verify if there are T faces in the meshes. That means if there's one edge connected to 3 or plus faces. It will fix them.",
            "LaminaFaceCleaner": "It will verify if there are some lamina faces in the meshes and cleanup them.",
            "NonManifoldCleaner": "It will verify if there are polygons with non-manifold issues and remove them.",
            "NonQuadFace": "It will find non quad polygon faces. These cannot be fixed automatically and require manual attention.",
            "BorderGap": "It will find borders or holes in the mesh. These cannot be fixed automatically, but you can try to use the fill hole Maya command to fix them.",
            "RemainingVertexCleaner": "It will verify if there are some remaining vertex in the meshes. It means have one vertex connected to only 2 non border edges.",
            "ColorPerVertexCleaner": "It will remove polyColorPerVertex nodes in the scene.",
            "UnlockNormals": "It will unlock normals from the geometries.",
            "InvertedNormals": "It will verify inverted normals in the geometries.",
            "SoftenEdges": "It will verify soften edges in the geometries.",
            "OverrideCleaner": "It will verify if there are nodes with overrides and remove them.",
            "UnlockAttributes": "It will verify and unlock attributes.",
            "FreezeTransform": "Check if all geometries have frozen transformations, translate, rotate values at zero and scale values at one, otherwise try to apply them.",
            "GeometryHistory": "It will clean-up the geometry deformer history.",
            
            # Rig validations (CheckOut) - Rigging and animation related
            "CycleChecker": "It will verify if there are cycle errors in the scene. It will only verify and report them as this theme is very complex to fix automatically.",
            "BrokenRivet": "Lists the follicles in the world origin, meaning those that are not correctly fixed, and tries to fix them.",
            "KeyframeCleaner": "It will delete the animated objects keyframes. It won't check drivenKeys, blendWeights or pairBlends.",
            "NgSkinToolsCleaner": "It will clean-up all ngSkinTools custom nodes forever.",
            "BrokenNetCleaner": "It will detect if there are some broken correction manager network to clean-up them.",
            "ColorSetCleaner": "It will clean-up all colorSet nodes when Shape Editor and sculpt tools is used.",
            "HideDataGrp": "It will hide the Data_Grp if it isn't hidden yet.",
                            
            "SideCalibration": "It will detect if there are some controllers with different side calibration and priorize the setup from the non defaultValue or use the left side as source if the two sides are configured.",
            "TargetCleaner": "Check if there are blendShape primary targets to clean them up. It will delete not connected or not deformed geometries.",
            "UnknownNodesCleaner": "It will clean-up the unknown nodes in the scene.",
            "UnusedNodeCleaner": "It will remove unnecessary rendering nodes.",
            "PruneSkinWeights": "It will verify if there are small skinning weights to prune.",
            "UnusedSkinCleaner": "It will remove unused skin influences.",
            "EnvelopeChecker": "It will check for envelope attributes lower than one.",
            "ScalableDeformerChecker": "It will verify if there are deformers with scalable connections in the scene. It will check and fix the scalable connections to deformers: skinCluster and deltaMush.",
            "WIPCleaner": "Check if there are any node inside of the WIP_Grp and delete them.",
            "ExitEditMode": "It will check if there are any corrective controller in the edit mode and it will back to normal state without save changes or settings.",
            "HideCorrectives": "It will lock and hide the corrective attribute on Option_Ctrl",
            "ControllerTag": "It will tag as controller all rigXControls.",
            "ControlsHierarchy": "Check if controls hierarchy match with a previous state exported, to prevent animation loss.",
            "DisplayLayers": "It will check that no display layers exist in the scene (except the default layer). If any display layers are found, it will report them and clear them to keep the scene clean.",
            "ResetPose": "It will reset the rig to its default pose.",
            "JointEndCleaner": "It will verify if there are unnecessary joints at the end of the chains. If so, it will delete them because they aren't useful to animation.",
            "BindPoseCleaner": "It will verify if there are bindPose nodes in the scene. If so, it will delete them and create just a new one node for all skinned joints.",
            "TweakNodeCleaner": "It will verify if there are some tweak nodes in the scene and cleanup them.",
            "RemapValueToSetRange": "It will verify if there are remapValue nodes that could be converted to setRange nodes without losing any behavior. It will optimize the calculation and get a faster rig.",
            "HideAllJoints": "It will hide joints in the scene.",
            "PassthroughAttributes": "It will verify if there are attributes with no necessary inbetween connections. If so, it will change (a -> b -> c) to (a -> c).",
            "ProxyCreator": "Creates proxy geometry for performance optimization during rigging.",
 
            "Cleanup": "It will check for rigXDeleteIt attributes and delete their nodes."
        }
        
        categories = self.validator.get_modules_by_category()
        
        for category_name, modules in categories.items():
            # Create scroll area for the category
            scroll_widget = QtWidgets.QWidget()
            scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
            
            # Add topic filter for Rig tab only
            if category_name == "Rig":
                # Define Rig topics and their associated modules
                self.rig_topics = {
                    "Scene & File Integrity": [
                        "UnknownNodesCleaner", "ImportReference", "DuplicatedName", 
                        "UnusedNodeCleaner"
                    ],
                                           "Rig Hierarchy & Structure": [
                           "FreezeTransform", "HideAllJoints", "UnusedSkinCleaner", 
                           "DisplayLayers"
                       ],
                    "Skinning & Deformation": [
                        "BindPoseCleaner", "NgSkinToolsCleaner", "PruneSkinWeights", 
                        "CycleChecker", "EnvelopeChecker"
                    ],
                    "Animation Data & Keying": [
                        "KeyframeCleaner", "ResetPose", "TargetCleaner"
                    ],
                    "Geometry & UVs": [
                        "ColorSetCleaner", "LaminaFaceCleaner", "NonManifoldCleaner", 
                        "NonQuadFace", "OneVertex", "TFaceCleaner"
                    ],
                    "Performance & Optimization": [
                        "ScalableDeformerChecker", "Cleanup", "WIPCleaner"
                    ],
                    "Final Presentation": [
                        "ControllerTag", "ControlsHierarchy", "SideCalibration", 
                        "ExitEditMode", "HideCorrectives", "HideDataGrp"
                    ],
                    "Extra (Optional, but Recommended)": [
                        "NamespaceCleaner", "BrokenRivet", "BrokenNetCleaner", 
                        "PassthroughAttributes", "ProxyCreator", "JointEndCleaner", 
                        "TweakNodeCleaner", "RemapValueToSetRange"
                    ]
                }
                
                # Create topic filter combo box
                topic_filter_label = QtWidgets.QLabel("Filter by Topic:")
                topic_filter_label.setStyleSheet("color: white; font-size: 11px; padding: 5px;")
                self.topic_filter_combo = QtWidgets.QComboBox()
                self.topic_filter_combo.addItem("All Topics")
                for topic in self.rig_topics.keys():
                    self.topic_filter_combo.addItem(topic)
                self.topic_filter_combo.currentTextChanged.connect(self.filter_rig_modules_by_topic)
                self.topic_filter_combo.setStyleSheet("""
                    QComboBox {
                        background-color: #3a3a3a;
                        color: white;
                        border: 1px solid #555555;
                        border-radius: 3px;
                        padding: 5px;
                        min-width: 200px;
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 20px;
                    }
                    QComboBox::down-arrow {
                        image: none;
                        border-left: 5px solid transparent;
                        border-right: 5px solid transparent;
                        border-top: 5px solid white;
                        margin-right: 5px;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #3a3a3a;
                        color: white;
                        border: 1px solid #555555;
                        selection-background-color: #555555;
                    }
                """)
                
                # Add topic filter to the top of the rig tab
                topic_filter_layout = QtWidgets.QHBoxLayout()
                topic_filter_layout.addWidget(topic_filter_label)
                topic_filter_layout.addWidget(self.topic_filter_combo)
                topic_filter_layout.addStretch()
                scroll_layout.addLayout(topic_filter_layout)
                
                # Add separator line
                separator = QtWidgets.QFrame()
                separator.setFrameShape(QtWidgets.QFrame.HLine)
                separator.setFrameShadow(QtWidgets.QFrame.Sunken)
                separator.setStyleSheet("background-color: #555555; margin: 10px 0px;")
                scroll_layout.addWidget(separator)
            
            # Add module checkboxes with individual verify/fix buttons
            for module in modules:
                # Create horizontal layout for each module
                module_layout = QtWidgets.QHBoxLayout()
                
                # Module checkbox
                checkbox = QtWidgets.QCheckBox(module.name.replace('dp', ''))
                checkbox.setChecked(module.enabled)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        color: white;
                        font-size: 11px;
                        padding: 5px;
                        min-width: 150px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                    QCheckBox::indicator:unchecked {
                        border: 2px solid #555555;
                        background-color: #2b2b2b;
                        border-radius: 3px;
                    }
                    QCheckBox::indicator:checked {
                        border: 2px solid #4CAF50;
                        background-color: #4CAF50;
                        border-radius: 3px;
                    }
                """)
                
                # Connect checkbox to module enabled state
                checkbox.toggled.connect(lambda checked, m=module: self.toggle_module(m, checked))
                
                # Get description for this module
                module_name = module.name.replace('dp', '')
                description = self.validation_descriptions.get(module_name, "No description available")
                checkbox.setToolTip(description)
                
                # Verify button for this module
                verify_btn = QtWidgets.QPushButton("Verify")
                verify_btn.setFixedSize(70, 25)
                verify_btn.clicked.connect(self.create_verify_connection(module))
                verify_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #666666; 
                        color: white; 
                        border: none;
                        border-radius: 3px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #555555;
                    }
                    QPushButton:pressed {
                        background-color: #444444;
                    }
                    QPushButton:disabled {
                        background-color: #3a3a3a;
                        color: #888888;
                        border: 1px solid #555555;
                    }
                """)
                
                # Fix button for this module
                fix_btn = QtWidgets.QPushButton("Fix")
                fix_btn.setFixedSize(70, 25)
                fix_btn.clicked.connect(self.create_fix_connection(module))
                fix_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #4CAF50; 
                        color: white; 
                        border: none;
                        border-radius: 3px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40;
                    }
                    QPushButton:disabled {
                        background-color: #2a3a2a;
                        color: #888888;
                        border: 1px solid #555555;
                    }
                """)
                
                # Store buttons for later access
                self.module_verify_buttons[module.name] = verify_btn
                self.module_fix_buttons[module.name] = fix_btn
                
                # Store module widgets for filtering (for Rig tab only)
                if category_name == "Rig":
                    module_name = module.name.replace('dp', '')
                    if module_name not in self.rig_modules_widgets:
                        self.rig_modules_widgets[module_name] = []
                    self.rig_modules_widgets[module_name].extend([checkbox, verify_btn, fix_btn])
                
                # Set initial button states based on checkbox state
                verify_btn.setEnabled(checkbox.isChecked())
                fix_btn.setEnabled(checkbox.isChecked())
                
                # Add widgets to module layout with proper spacing
                module_layout.addWidget(checkbox)
                module_layout.addSpacing(15)
                module_layout.addWidget(verify_btn)
                module_layout.addSpacing(5)
                module_layout.addWidget(fix_btn)
                module_layout.addStretch()
                
                # Add module layout to scroll layout
                scroll_layout.addLayout(module_layout)
            
            scroll_layout.addStretch()
            
            # Create scroll area
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
                QScrollBar:vertical {
                    background-color: #3a3a3a;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #555555;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #666666;
                }
            """)
            
            self.modules_tabs.addTab(scroll_area, category_name)
        
        # Set initial state of Check All checkbox
        self.update_check_all_state()
    
    def filter_rig_modules_by_topic(self, selected_topic):
        """Filter Rig validation modules based on selected topic"""
        if not hasattr(self, 'rig_modules_widgets'):
            return
            
        if selected_topic == "All Topics":
            # Show all modules
            for module_name, widgets in self.rig_modules_widgets.items():
                for widget in widgets:
                    widget.setVisible(True)
        else:
            # Show only modules for selected topic
            topic_modules = self.rig_topics.get(selected_topic, [])
            for module_name, widgets in self.rig_modules_widgets.items():
                should_show = module_name in topic_modules
                for widget in widgets:
                    widget.setVisible(should_show)
    
    def update_check_all_state(self):
        """Update the Check All checkbox state based on individual module states"""
        if not self.validator or self._updating_check_all:
            return
        
        # Check if all modules are enabled
        all_enabled = all(module.enabled for module in self.validator.modules.values())
        self._updating_check_all = True
        self.checkbox_check_all.setChecked(all_enabled)
        self._updating_check_all = False
    
    def toggle_module(self, module, enabled):
        """Toggle a validation module on/off"""
        if module:
            module.enabled = enabled
            # Update the Check All checkbox state
            self.update_check_all_state()
            
            # Enable/disable the verify and fix buttons for this module
            if module.name in self.module_verify_buttons:
                self.module_verify_buttons[module.name].setEnabled(enabled)
            if module.name in self.module_fix_buttons:
                self.module_fix_buttons[module.name].setEnabled(enabled)
    
    def toggle_all_modules(self, checked):
        """Toggle all module checkboxes"""
        if not self.validator or self._updating_check_all:
            return
        
        # Enable/disable all modules in the validator
        for module in self.validator.modules.values():
            module.enabled = checked
        
        # Update all checkboxes to match the checked state
        for i in range(self.modules_tabs.count()):
            scroll_area = self.modules_tabs.widget(i)
            if scroll_area and scroll_area.widget():
                scroll_widget = scroll_area.widget()
                for child in scroll_widget.children():
                    if isinstance(child, QtWidgets.QCheckBox):
                        child.setChecked(checked)
        
        # Update all button states
        for module_name in self.module_verify_buttons:
            self.module_verify_buttons[module_name].setEnabled(checked)
        for module_name in self.module_fix_buttons:
            self.module_fix_buttons[module_name].setEnabled(checked)
    
    def create_verify_connection(self, module):
        """Create a connection function for verify button"""
        def verify_connection():
            self.verify_single_module(module)
        return verify_connection
    
    def create_fix_connection(self, module):
        """Create a connection function for fix button"""
        def fix_connection():
            self.fix_single_module(module)
        return fix_connection
    
    def verify_single_module(self, module):
        """Verify a single validation module"""
        if not self.validator or not module:
            return
        
        # Run validation for this specific module
        self.validator.run_validation(module_names=[module.name], mode="check", objList=None)
        
        # Display results in Info tab (preserves Results tab content)
        self.display_results(action_type="verify")
        
        # Module verification completed
        clean_name = module.name.replace('dp', '')
        print(f"Verified {clean_name} - {len(self.validator.results['info'])} items found")
    
    def fix_single_module(self, module):
        """Fix issues for a single validation module"""
        if not self.validator or not module:
            return
        
        # Run validation in fix mode for this specific module
        self.validator.run_validation(module_names=[module.name], mode="fix", objList=None)
        
        # Display results in Results tab (preserves Info tab content)
        self.display_results(action_type="fix")
        
        # Module fixing completed
        clean_name = module.name.replace('dp', '')
        print(f"Fixed {clean_name} - {len(self.validator.results['info'])} items processed")
    
    def _separator(self):
        """Create a visual separator"""
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        return line
    
    def run_validation(self):
        """Run validation on enabled modules"""
        if not self.validator:
            return
            
        # Run validation
        self.validator.run_validation(mode="check", objList=None)
        
        # Display results in Info tab (preserves Results tab content)
        self.display_results(action_type="validation")
        
        # Validation completed
        print(f"Validation complete - {len(self.validator.results['info'])} items processed")
    
    def fix_issues(self):
        """Run validation in fix mode"""
        if not self.validator:
            return
            
        # Run validation in fix mode
        self.validator.run_validation(mode="fix", objList=None)
        
        # Display results in Results tab (preserves Info tab content)
        self.display_results(action_type="fix")
        
        # Fixing completed
        print(f"Fixing complete - {len(self.validator.results['info'])} items processed")
    
    def _create_colored_item(self, text, background_color, foreground_color):
        """Create a list item with specified background and foreground colors"""
        item = QtWidgets.QListWidgetItem(text)
        item.setBackground(background_color)
        item.setForeground(foreground_color)
        return item
    
    def display_results(self, action_type="verify"):
        """Display validation results in the UI based on action type"""
        if not self.validator:
            return
            
        if action_type in ["verify", "validation"]:
            # Clear only Info tab and display verify/validation results
            self.clear_results(tab="info")
            
            for error in self.validator.results['errors']:
                item = self._create_colored_item(
                    f"❌ {error}",
                    QtGui.QColor(255, 200, 200),  # Light red background
                    QtGui.QColor(255, 69, 0)       # Orange text
                )
                self.info_list.addItem(item)
            
            for warning in self.validator.results['warnings']:
                item = self._create_colored_item(
                    f"⚠️ {warning}",
                    QtGui.QColor(255, 220, 180),  # Light orange background
                    QtGui.QColor(255, 69, 0)       # Orange text
                )
                self.info_list.addItem(item)
            
            for info in self.validator.results['info']:
                item = self._create_colored_item(
                    f"ℹ️ {info}",
                    QtGui.QColor(255, 165, 0),    # Orange background
                    QtGui.QColor(255, 69, 0)       # Orange text
                )
                self.info_list.addItem(item)
                
        elif action_type in ["fix"]:
            # Clear only Results tab and display fix results
            self.clear_results(tab="results")
            
            for error in self.validator.results['errors']:
                item = self._create_colored_item(
                    f"❌ {error}",
                    QtGui.QColor(255, 200, 200),  # Light red background
                    QtGui.QColor(0, 128, 0)        # Green text
                )
                self.results_list.addItem(item)
            
            for warning in self.validator.results['warnings']:
                item = self._create_colored_item(
                    f"✅ {warning}",
                    QtGui.QColor(255, 220, 180),  # Light orange background
                    QtGui.QColor(0, 128, 0)        # Green text
                )
                self.results_list.addItem(item)
            
            for info in self.validator.results['info']:
                item = self._create_colored_item(
                    f"ℹ️ {info}",
                    QtGui.QColor(200, 255, 200),  # Light green background
                    QtGui.QColor(0, 128, 0)        # Green text
                )
                self.results_list.addItem(item)
    
    def update_summary(self):
        """Update the summary label with validation results"""
        if not self.validator:
            return
        
        total_info = len(self.validator.results['info'])
        
        if total_info == 0:
            self.summary_label.setText("✅ Validation complete - No issues found")
            self.summary_label.setStyleSheet("QLabel { font-weight: bold; padding: 10px; color: #4CAF50; }")
        else:
            self.summary_label.setText(f"ℹ️ Validation complete - {total_info} items processed")
            self.summary_label.setStyleSheet("QLabel { font-weight: bold; padding: 10px; color: #2196F3; }")
    
    def clear_results(self, tab="both"):
        """Clear the results display - specify which tab to clear"""
        if tab == "both" or tab == "info":
            self.info_list.clear()
        if tab == "both" or tab == "results":
            self.results_list.clear()
    
    def show_info_context_menu(self, position):
        """Show context menu for Info list"""
        self.show_context_menu(self.info_list, position, "Info")
    
    def show_results_context_menu(self, position):
        """Show context menu for Results list"""
        self.show_context_menu(self.results_list, position, "Results")
    
    def show_context_menu(self, list_widget, position, list_name):
        """Show context menu with copy options"""
        context_menu = QtWidgets.QMenu(self)
        
        # Copy selected item
        copy_selected_action = context_menu.addAction("Copy Selected")
        copy_selected_action.triggered.connect(lambda: self.copy_selected_items(list_widget))
        
        # Copy all items
        copy_all_action = context_menu.addAction(f"Copy All {list_name}")
        copy_all_action.triggered.connect(lambda: self.copy_all_items(list_widget))
        
        # Show context menu at cursor position
        context_menu.exec_(list_widget.mapToGlobal(position))
    
    def copy_selected_items(self, list_widget):
        """Copy selected items to clipboard"""
        selected_items = list_widget.selectedItems()
        if selected_items:
            text_to_copy = "\n".join([item.text() for item in selected_items])
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(text_to_copy)
            print(f"Copied {len(selected_items)} selected items to clipboard")
        else:
            print("No items selected to copy")
    
    def copy_all_items(self, list_widget):
        """Copy all items to clipboard"""
        all_items = [list_widget.item(i).text() for i in range(list_widget.count())]
        if all_items:
            text_to_copy = "\n".join(all_items)
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(text_to_copy)
            print(f"Copied {len(all_items)} items to clipboard")
        else:
            print("No items to copy")
    

    
    def closeEvent(self, event):
        """Handle window close event"""
        # Clear the global dialog reference when window is closed
        try:
            from rigging_pipeline.tools.rigx_riggingValidator import _dialog
            if _dialog == self:
                import rigging_pipeline.tools.rigx_riggingValidator
                rigging_pipeline.tools.rigx_riggingValidator._dialog = None
        except:
            pass
        event.accept()
