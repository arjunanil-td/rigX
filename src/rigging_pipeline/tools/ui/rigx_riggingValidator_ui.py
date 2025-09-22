import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner


def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class RiggingValidatorUI(QtWidgets.QWidget):
    """UI for the rigging validation tool"""
    
    def __init__(self, parent=maya_main_window(), validator=None):
        super().__init__(parent)
        
        self.setWindowTitle("RigX Rigging Validator")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        self.resize(500, 900)
        
        # Set darker background similar to Skin Tool Kit
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                color: #e0e0e0;
            }
            QGroupBox {
                background-color: #2A2A2A ;
                border: 1px solid #404040;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #e0e0e0;
                font-weight: bold;
            }
            QCheckBox {
                color: #e0e0e0;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #404040;
                background-color: #2A2A2A ;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #4CAF50;
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #66bb6a;
            }
            QPushButton {
                background-color: #404040;
                color: #e0e0e0;
                border: none;
                padding: 6px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #2A2A2A ;
            }
            QTextEdit {
                background-color: #2A2A2A ;
                border: 1px solid #404040;
                color: #e0e0e0;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                background-color: #2A2A2A ;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
            QSplitter::handle {
                background-color: #404040;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #505050;
            }
        """)
        
        self.validator = validator
        self._updating_check_all = False  # Flag to prevent circular dependency
        self._did_verify = False  # Track whether any verify has been run
        
        # Initialize button dictionaries
        self.module_verify_buttons = {}
        self.module_fix_buttons = {}
        self.module_status_buttons = {}  # Store status buttons for each module
        self.module_status_labels = {}  # Store status labels for each module
        self.module_verified = {}  # Track if a module has been verified at least once
        
        self.build_ui()
    
    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Add the centralized banner
        banner = Banner("RigX Rigging Validator", "../icons/rigX_icon_validator.png")
        layout.addWidget(banner)
        
        # ───── Main Splitter for Validations and Results ─────
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2A2A2A ;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #666666;
            }
        """)
        
        # ───── Validations ─────
        validations_group = QtWidgets.QGroupBox("Validations")
        validations_layout = QtWidgets.QVBoxLayout(validations_group)
        
        # Add Check All checkbox directly under validations
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
                border: 2px solid #2A2A2A ;
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
        
        validations_layout.addWidget(self.checkbox_check_all)
        
        if self.validator:
            self.build_validations_list(validations_layout)
        
        self.main_splitter.addWidget(validations_group)
        
        # ───── Action Buttons ─────
        button_layout = QtWidgets.QHBoxLayout()
        
        self.btn_validate = QtWidgets.QPushButton("Run Validation")
        self.btn_validate.clicked.connect(self.run_validation)
        self.btn_validate.setStyleSheet("""
            QPushButton { 
                background-color: #404040; 
                color: #e0e0e0; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #2A2A2A ;
            }
        """)
        
        self.btn_fix = QtWidgets.QPushButton("Fix Issues")
        self.btn_fix.clicked.connect(self.fix_issues)
        self.btn_fix.setEnabled(False)  # Disabled by default
        self.btn_fix.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: #e0e0e0; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #66bb6a;
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
            QPushButton:disabled {
                background-color: #2A2A2A ;
                color: #a0a0a0;
                border: 1px solid #404040;
            }
        """)
        
        self.btn_clear = QtWidgets.QPushButton("Clear Results")
        self.btn_clear.clicked.connect(lambda: self.clear_results("both"))
        self.btn_clear.setStyleSheet("""
            QPushButton { 
                background-color: #404040; 
                color: #e0e0e0; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        
        self.btn_interactive = QtWidgets.QPushButton("Feedback Validation")
        self.btn_interactive.clicked.connect(self.run_interactive_validation)
        self.btn_interactive.setStyleSheet("""
            QPushButton { 
                background-color: #2196F3; 
                color: #e0e0e0; 
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1976d2;
            }
        """)
        
        button_layout.addWidget(self.btn_validate)
        button_layout.addWidget(self.btn_interactive)
        button_layout.addWidget(self.btn_fix)
        button_layout.addWidget(self.btn_clear)
        
        # Add buttons to validations group
        validations_layout.addLayout(button_layout)
        
        # ───── Validation Results ─────
        results_group = QtWidgets.QGroupBox("Validation Results")
        results_layout = QtWidgets.QVBoxLayout(results_group)
        
        # Results header with folder icon
        results_header = QtWidgets.QHBoxLayout()
        results_label = QtWidgets.QLabel("📁 Results")
        results_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_layout.addLayout(results_header)
        
        # Results display area
        self.results_display = QtWidgets.QTextEdit()
        self.results_display.setStyleSheet("""
            QTextEdit { 
                background-color: #2A2A2A ; 
                border: 1px solid #404040;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                min-height: 150px;
                color: #e0e0e0;
            }
        """)
        self.results_display.setReadOnly(True)
        results_layout.addWidget(self.results_display)
        
        self.main_splitter.addWidget(results_group)
        
        # Set initial splitter sizes (70% for validations, 30% for results)
        self.main_splitter.setSizes([700, 300])
        
        layout.addWidget(self.main_splitter)
        
        # Set initial state of Check All checkbox
        if self.validator:
            self.update_check_all_state()
            self.reset_all_module_statuses()
    
    def build_validations_list(self, parent_layout):
        """Build the validations list with individual items"""
        if not self.validator:
            return
        
        # Get all modules in a single list (no tabs)
        all_modules = []
        categories = self.validator.get_modules_by_category()
        for category_name, modules in categories.items():
            all_modules.extend(modules)
        
        # Filter out specific modules that should not be displayed
        excluded_modules = [
            'dpColorSetCleaner',
            'dpColorPerVertexCleaner',
            'dpControllerTag', 
            'dpFreezeTransform',
            'dpGeometryHistory',
            'dpJointEndCleaner',
            'dpTweakNodeCleaner'
        ]
        
        # Also check for partial matches and different case variations
        excluded_patterns = [
            'colorset', 'colorpervertex', 'controller', 'freeze', 'geometry'
        ]
        
        # Remove excluded modules
        filtered_modules = []
        for module in all_modules:
            should_exclude = False
            
            # Check exact name match
            if module.name in excluded_modules:
                should_exclude = True
            
            # Check partial pattern match (case insensitive)
            module_lower = module.name.lower()
            for pattern in excluded_patterns:
                if pattern in module_lower:
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_modules.append(module)
        
        # Debug: Print what was filtered out
        filtered_out = [module.name for module in all_modules if module.name not in [m.name for m in filtered_modules]]
        if filtered_out:
            print(f"Filtered out validation modules: {filtered_out}")
        
        print(f"Total modules: {len(all_modules)}, Filtered modules: {len(filtered_modules)}")
        
        # Sort modules by priority order (same as in validator)
        priority_order = [
            # Priority validations (in order)
            "AssetChecker",
            "ReferencedFileChecker", "NamespaceCleaner", "DupicatedName",
            "KeyframeCleaner", "UnknownNodesCleaner", "UnusedNodeCleaner", 
            "NgSkinToolsCleaner",
            # Rest all (in alphabetical order for consistency)
            "BindPoseCleaner", "CharacterSet", "ColorSetCleaner", "ControllerTag", 
            "DisplayLayers", "FreezeTransform", "GeometryHistory", "HideAllJoints", 
            "JointEndCleaner", "OutlinerCleaner", "PruneSkinWeights", 
            "TweakNodeCleaner", "UnusedSkinCleaner"
        ]
        
        def get_priority_index(module):
            module_name = module.name.replace('dp', '')
            try:
                return priority_order.index(module_name)
            except ValueError:
                return 999  # Put unknown modules at the end
        
        # Sort modules by priority order
        filtered_modules.sort(key=get_priority_index)
        
        # Create scroll area for all validations
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        
        # Add each validation module
        for module in filtered_modules:
                # Create horizontal layout for each module
                module_layout = QtWidgets.QHBoxLayout()
                
                # Module checkbox
                checkbox = QtWidgets.QCheckBox(module.name.replace('dp', ''))
                checkbox.setChecked(module.enabled)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        color: #e0e0e0;
                        font-size: 11px;
                        padding: 5px;
                        min-width: 150px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                    QCheckBox::indicator:unchecked {
                        border: 2px solid #404040;
                        background-color: #2A2A2A ;
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
                description = self.get_validation_description(module_name)
                checkbox.setToolTip(description)
                
                # Verify button for this module
                verify_btn = QtWidgets.QPushButton("Verify")
                verify_btn.setFixedSize(70, 25)
                verify_btn.clicked.connect(self.create_verify_connection(module))
                verify_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #404040; 
                        color: #e0e0e0; 
                        border: none;
                        border-radius: 3px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #505050;
                    }
                    QPushButton:pressed {
                        background-color: #2A2A2A ;
                    }
                    QPushButton:disabled {
                        background-color: #2A2A2A ;
                        color: #a0a0a0;
                        border: 1px solid #404040;
                    }
                """)
                
                # Fix button for this module
                fix_btn = QtWidgets.QPushButton("Fix")
                fix_btn.setFixedSize(70, 25)
                fix_btn.clicked.connect(self.create_fix_connection(module))
                fix_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #4CAF50; 
                        color: #e0e0e0; 
                        border: none;
                        border-radius: 3px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #66bb6a;
                    }
                    QPushButton:pressed {
                        background-color: #388e3c;
                    }
                    QPushButton:disabled {
                        background-color: #2A2A2A ;
                        color: #a0a0a0;
                        border: 1px solid #404040;
                    }
                """)
                
                # Status button (tick/checkmark/X/warning)
                status_btn = QtWidgets.QPushButton("✓")
                status_btn.setFixedSize(25, 25)
                status_btn.setEnabled(False)  # Disabled by default, only shows status
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #505050; 
                        color: #e0e0e0; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #505050;
                        color: #e0e0e0;
                    }
                """)
                
                # Store buttons for later access
                self.module_verify_buttons[module.name] = verify_btn
                self.module_fix_buttons[module.name] = fix_btn
                self.module_status_buttons[module.name] = status_btn
                # Initialize verified state
                self.module_verified[module.name] = False
                
                # Set initial button states
                verify_btn.setEnabled(checkbox.isChecked())
                # Fix is disabled until this module is verified
                fix_btn.setEnabled(False)
                
                # Add widgets to module layout with proper spacing
                module_layout.addWidget(checkbox)
                module_layout.addSpacing(15)
                module_layout.addWidget(verify_btn)
                module_layout.addSpacing(5)
                module_layout.addWidget(fix_btn)
                module_layout.addSpacing(5)
                module_layout.addWidget(status_btn)
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
                    background-color: #2A2A2A ;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #404040;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #505050;
                }
            """)
        
        parent_layout.addWidget(scroll_area)
    
    def get_validation_description(self, module_name):
        """Get validation description for a module"""
        validation_descriptions = {
            # All validations (formerly Model + Rig) - Geometry, mesh, rigging and animation related
            "ImportReference": "It will check if there are referenced file to import them up.",
            "NamespaceCleaner": "Check if there are namespaces to clean them up. It won't delete namespace from rigXGuides.",
            "DupicatedName": "Check if there are nodes with duplicate short names and report them.",
            "UnlockInitialShadingGroup": "It will unlock the InitialShadingGroup to avoid the blocking to just create a simple polyCube.",
            "ShowBPCleaner": "It will delete the ShowBP scriptNodes.",
            
            "ParentedGeometry": "It will verify if there are some parented geometries in the hierarchy.",
            "OneVertex": "It will verify if there are some non manifold vertex in the meshes. That means a vertex in the union of 2 shapes.",
            "TFaceCleaner": "It will verify if there are T faces in the meshes. That means if there's one edge connected to 3 or plus faces. It will fix them.",
            "LaminaFaceCleaner": "It will verify if there are some lamina faces in the meshes and cleanup them.",
            "NonManifoldCleaner": "It will verify if there are polygons with non-manifold issues and remove them.",
            "NonQuadFace": "It will find non quad polygon faces. These cannot be fixed automatically and require manual attention.",
            "BorderGap": "It will find borders or holes in the mesh. These cannot be fixed automatically, but you can try to use the fill hole Maya command to fix them.",
            "RemainingVertexCleaner": "It will verify if there are some remaining vertex in the meshes. It means have one vertex connected to only 2 non border edges.",
            "UnlockNormals": "It will unlock normals from the geometries.",
            "InvertedNormals": "It will verify inverted normals in the geometries.",
            "SoftenEdges": "It will verify soften edges in the geometries.",
            "OverrideCleaner": "It will verify if there are nodes with overrides and remove them.",
            
            # Additional validations (CheckOut) - Rigging and animation related
            "CycleChecker": "It will verify if there are cycle errors in the scene. It will only verify and report them as this theme is very complex to fix automatically.",
            "KeyframeCleaner": "It will delete the animated objects keyframes. It won't check drivenKeys, blendWeights or pairBlends.",
            "NgSkinToolsCleaner": "It will clean-up all ngSkinTools custom nodes forever.",
            "BrokenNetCleaner": "It will detect if there are some broken correction manager network to clean-up them.",
            "HideDataGrp": "It will hide the Data_Grp if it isn't hidden yet.",
            "SideCalibration": "It will detect if there are some controllers with different side calibration and priorize the setup from the non defaultValue or use the left side as source if the two sides are configured.",
            "TargetCleaner": "Check if there are blendShape primary targets to clean them up. It will delete not connected or not deformed geometries.",
            "UnknownNodesCleaner": "It will clean-up the unknown nodes in the scene.",
            "UnusedNodeCleaner": "It will remove unnecessary rendering nodes and unused animation curves.",
            "PruneSkinWeights": "It will verify if there are small skinning weights to prune.",
            "UnusedSkinCleaner": "It will remove unused skin influences.",
            "EnvelopeChecker": "It will check for envelope attributes lower than one.",
            "ScalableDeformerChecker": "It will verify if there are deformers with scalable connections in the scene. It will check and fix the scalable connections to deformers: skinCluster and deltaMush.",
            "WIPCleaner": "Check if there are any node inside of the WIP_Grp and delete them.",
            "ExitEditMode": "It will check if there are any corrective controller in the edit mode and it will back to normal state without save changes or settings.",
            "HideCorrectives": "It will lock and hide the corrective attribute on Option_Ctrl",
            "ControlsHierarchy": "Check if controls hierarchy match with a previous state exported, to prevent animation loss.",
            "DisplayLayers": "It will check that no display layers exist in the scene (except the default layer). If any display layers are found, it will report them and clear them to keep the scene clean.",
            "ResetPose": "It will reset the rig to its default pose.",
            "BindPoseCleaner": "It will verify if there are bindPose nodes in the scene. If so, it will delete them and create just a new one node for all skinned joints.",
            "RemapValueToSetRange": "It will verify if there are remapValue nodes that could be converted to setRange nodes without losing any behavior. It will optimize the calculation and get a faster rig.",
            "HideAllJoints": "It will hide joints in the scene.",
            "PassthroughAttributes": "It will verify if there are attributes with no necessary inbetween connections. If so, it will change (a -> b -> c) to (a -> c).",
            "ProxyCreator": "Creates proxy geometry for performance optimization during rigging.",
            "Cleanup": "It will check for rigXDeleteIt attributes and delete their nodes.",
            "CharacterSet": "Validates and manages character sets for proper rigging workflow. Ensures character sets have proper naming, controls, and joint hierarchies.",
            "ControlValues": "Check animation set controls for proper TR values (0) and Scale values (1). Ensures all controls are in their default state.",
            "AssetChecker": "Asset Checker: derive asset from JOB_PATH, verify/rename top node to match.",
        }
        
        return validation_descriptions.get(module_name, "No description available")
    
    def show_help(self, module_name, description):
        """Show help information for a validation module"""
        QtWidgets.QMessageBox.information(
            self, 
            f"Help - {module_name}", 
            description,
            QtWidgets.QMessageBox.Ok
        )
    
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
                # Only enable Fix if module is enabled AND has been verified
                can_fix = enabled and self.module_verified.get(module.name, False)
                self.module_fix_buttons[module.name].setEnabled(can_fix)
    
    def toggle_all_modules(self, checked):
        """Toggle all module checkboxes"""
        if not self.validator or self._updating_check_all:
            return
        
        # Enable/disable all modules in the validator
        for module in self.validator.modules.values():
            module.enabled = checked
        
        # Update all checkboxes to match the checked state
        for child in self.findChildren(QtWidgets.QCheckBox):
            if child != self.checkbox_check_all:
                        child.setChecked(checked)
        
        # Update all button states
        for module_name in self.module_verify_buttons:
            self.module_verify_buttons[module_name].setEnabled(checked)
        for module_name in self.module_fix_buttons:
            can_fix = checked and self.module_verified.get(module_name, False)
            self.module_fix_buttons[module_name].setEnabled(can_fix)
    
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
        results = self.validator.run_validation(module_names=[module.name], mode="check", objList=None)
        
        # Update module status based on results
        if results and module.name in results:
            self.update_module_status_from_results(module.name, results[module.name])
        else:
            self.update_module_status(module.name, 'default')
        
        # Display results
        self.display_results(action_type="verify")
        
        # Mark this module as verified and enable its Fix button
        self.module_verified[module.name] = True
        if module.name in self.module_fix_buttons:
            self.module_fix_buttons[module.name].setEnabled(True)
        # Keep global Fix Issues button behavior unchanged
        self._did_verify = True
        self.btn_fix.setEnabled(True)
        
        # Module verification completed
        clean_name = module.name.replace('dp', '')
        consolidated_results = self.validator.get_consolidated_results()
        print(f"Verified {clean_name} - {len(consolidated_results['info'])} items found")
    
    def fix_single_module(self, module):
        """Fix issues for a single validation module"""
        if not self.validator or not module:
            return
        
        # Duplicate Name validation: only show manual-fix dialog if actual duplicates exist
        clean_name = module.name.replace('dp', '')
        if "DuplicatedName" in clean_name or "DupicatedName" in clean_name:
            check_results = self.validator.run_validation(module_names=[module.name], mode="check", objList=None)
            has_actual_duplicates = False
            if check_results and module.name in check_results:
                result = check_results[module.name]
                for issue in result.get('issues', []):
                    msg = issue.get('message', '').lower()
                    if any(phrase in msg for phrase in [
                        "no duplicate names found",
                        "passed - no issues",
                        "no issues found",
                        "clean - no issues",
                        "nothing to clean"
                    ]):
                        continue
                    has_actual_duplicates = True
                    break
            if not has_actual_duplicates:
                # Nothing to fix; mark as pass and inform user
                self.update_module_status(module.name, 'pass')
                self.results_display.append(f"✅ {clean_name}: No duplicate names found")
                return
            # Actual duplicates exist; prompt manual fix and skip auto-fix
            QtWidgets.QMessageBox.information(
                self,
                "Manual Fix Required",
                "Duplicate short names cannot be auto-fixed.\nPlease rename manually so each has a unique short name."
            )
            self.update_module_status(module.name, 'warning')
            self.results_display.append(f"ℹ️ {clean_name}: Manual fix required for duplicate short names")
            return

        # Run validation in fix mode for this specific module
        results = self.validator.run_validation(module_names=[module.name], mode="fix", objList=None)
        
        # Update module status based on fix results
        if results and module.name in results:
            self.update_module_status_from_results(module.name, results[module.name])
        else:
            self.update_module_status(module.name, 'default')
        
        # Display results
        self.display_results(action_type="fix")
        
        # Module fix completed
        clean_name = module.name.replace('dp', '')
        consolidated_results = self.validator.get_consolidated_results()
        print(f"Fixed {clean_name} - {len(consolidated_results['info'])} items processed")
    
    def run_validation(self):
        """Run validation on all enabled modules"""
        if not self.validator:
            return
            
        # Clear previous results
        self.results_display.clear()
            
        # Run validation
        results = self.validator.run_all_validations()
        
        # Update all module statuses based on results
        if results:
            for module_name in results:
                if module_name in self.module_status_buttons:
                    self.update_module_status_from_results(module_name, results[module_name])
                    # Mark modules that were part of this run as verified so their Fix buttons can be enabled
                    self.module_verified[module_name] = True
                    if module_name in self.module_fix_buttons:
                        self.module_fix_buttons[module_name].setEnabled(True)
        
        # Display results
        self.display_results(action_type="validate")
        
        # Enable global Fix Issues after a full validation run
        self._did_verify = True
        self.btn_fix.setEnabled(True)
        
        print("Validation completed")
    
    def run_interactive_validation(self):
        """Run interactive validation - step by step with user interaction"""
        if not self.validator:
            return
            
        # Clear previous results
        self.results_display.clear()
        
        # Get enabled modules in priority order
        enabled_modules = []
        categories = self.validator.get_modules_by_category()
        for category_name, modules in categories.items():
            for module in modules:
                if module.enabled:
                    enabled_modules.append(module)
        
        # Sort by priority order (same as in build_validations_list)
        priority_order = [
            "AssetChecker", "ReferencedFileChecker", "NamespaceCleaner", "DupicatedName", 
            "KeyframeCleaner", "UnknownNodesCleaner", "UnusedNodeCleaner", 
            "NgSkinToolsCleaner", "BindPoseCleaner", "CharacterSet", 
            "DisplayLayers", "HideAllJoints", "OutlinerCleaner", 
            "PruneSkinWeights", "UnusedSkinCleaner"
        ]
        
        def get_priority_index(module):
            module_name = module.name.replace('dp', '')
            try:
                return priority_order.index(module_name)
            except ValueError:
                return 999
        
        enabled_modules.sort(key=get_priority_index)
        
        # Run validations one by one
        for module in enabled_modules:
            clean_name = module.name.replace('dp', '')
            
            # Run validation for this module
            results = self.validator.run_validation(module_names=[module.name], mode="check")
            # Mark this module as verified and enable Fix
            self.module_verified[module.name] = True
            if module.name in self.module_fix_buttons:
                self.module_fix_buttons[module.name].setEnabled(True)
            
            if results and module.name in results:
                result = results[module.name]
                
                # Update module status
                self.update_module_status_from_results(module.name, result)
                
                # Check if there are issues
                if result.get('total_issues', 0) > 0:
                    # Check if these are actual issues or just informational "clean" messages
                    actual_issues = []
                    for issue in result.get('issues', []):
                        message = issue.get('message', '').lower()
                        # Skip messages that indicate normal/clean state
                        skip_phrases = [
                            "no duplicate names found",
                            "no custom namespaces found",
                            "no bind pose nodes found",
                            "no display layers found",
                            "no joints found to check",
                            "no animation curves found",
                            "no NgSkinTools nodes found",
                            "No NgSkinTools nodes found",
                            "no ngskintools nodes found",
                            "outliner is already well organized",
                            "outliner already clean",
                            "outliner is clean: only",
                            "all character sets are properly configured",
                            "no character sets found in scene",
                            "no skin clusters found to check",
                            "no references found in scene",
                            "no tweak nodes found to check",
                            "no unknown nodes found to check",
                            "not enough materials to check",
                            "fixed: 0 nodes = 0 materials",
                            "no low weights found",
                            "no unused materials found",
                            "has no unused influence joints",
                            "no issues found",
                            "nothing to clean",
                            "no problems detected",
                            "clean - no issues",
                            "passed - no issues",
                            "no action needed",
                            "already clean",
                            "is already well organized",
                            "already well organized",
                            "no action required",
                            "nothing to fix",
                            "no fixes needed",
                            "no cleanup needed",
                            "no cleanup required",
                            "no changes needed",
                            "no changes required",
                            "all validations passed",
                            "validation passed",
                            "passed successfully",
                            "successfully passed",
                            "no errors found",
                            "no warnings found",
                            "no problems found",
                            "no issues detected",
                            "no problems detected",
                            "no errors detected",
                            "no warnings detected"
                        ]
                        
                        is_actual_issue = True
                        for phrase in skip_phrases:
                            if phrase.lower() in message:
                                is_actual_issue = False
                                break
                        
                        if is_actual_issue:
                            actual_issues.append(issue)
                    
                    # Only show dialog if there are actual issues
                    if actual_issues:
                        # Check for specific FaceControlSet missing message first
                        face_control_set_issue = None
                        for issue in actual_issues:
                            if "missing 'facecontrolset'" in issue.get('message', '').lower():
                                face_control_set_issue = issue
                                break
                        
                        if face_control_set_issue:
                            # Directly show FaceControlSet dialog
                            dialog_result = cmds.confirmDialog(
                                title=f"FaceControlSet Missing - {clean_name}",
                                message=f"The validation '{clean_name}' found that 'FaceControlSet' is missing.\n\nWould you like to create it or skip for now?",
                                button=["Create FaceControlSet", "Skip for Now", "Stop Validation"],
                                defaultButton="Create FaceControlSet",
                                cancelButton="Stop Validation",
                                dismissString="Stop Validation"
                            )
                            
                            if dialog_result == "Create FaceControlSet":
                                # Run fix mode to create FaceControlSet
                                fix_results = self.validator.run_validation(module_names=[module.name], mode="fix")
                                if fix_results and module.name in fix_results:
                                    self.update_module_status_from_results(module.name, fix_results[module.name])
                                self.results_display.append(f"✅ {clean_name}: Created FaceControlSet")
                            elif dialog_result == "Skip for Now":
                                self.results_display.append(f"⚠️ {clean_name}: Skipped FaceControlSet creation")
                            elif dialog_result == "Stop Validation":
                                self.results_display.append(f"🛑 Validation stopped by user at {clean_name}")
                                break
                        else:
                            # There are actual issues - show dialog for user action
                            issues_text = ""
                            for issue in actual_issues:
                                issues_text += f"• {issue.get('message', 'Unknown issue')} - {issue.get('object', 'Unknown object')}\n"
                            
                            # Show dialog with options based on module type
                            if "ReferencedFileChecker" in module.name:
                                dialog_result = cmds.confirmDialog(
                                    title=f"Reference Files Found - {clean_name}",
                                    message=f"The validation '{clean_name}' found {len(actual_issues)} reference(s):\n\n{issues_text}\nWhat would you like to do?",
                                    button=["Import References", "Remove References", "Skip for Now", "Stop Validation"],
                                    defaultButton="Import References",
                                    cancelButton="Stop Validation",
                                    dismissString="Stop Validation"
                                )
                                
                                if dialog_result == "Import References":
                                    # Run fix mode to import references
                                    fix_results = self.validator.run_validation(module_names=[module.name], mode="fix", action="import")
                                    if fix_results and module.name in fix_results:
                                        self.update_module_status_from_results(module.name, fix_results[module.name])
                                    self.results_display.append(f"✅ {clean_name}: Imported references")
                                elif dialog_result == "Remove References":
                                    # Run fix mode to remove references
                                    fix_results = self.validator.run_validation(module_names=[module.name], mode="fix", action="remove")
                                    if fix_results and module.name in fix_results:
                                        self.update_module_status_from_results(module.name, fix_results[module.name])
                                    self.results_display.append(f"✅ {clean_name}: Removed references")
                                elif dialog_result == "Skip for Now":
                                    self.results_display.append(f"⚠️ {clean_name}: Skipped by user")
                                elif dialog_result == "Stop Validation":
                                    self.results_display.append(f"🛑 Validation stopped by user at {clean_name}")
                                    break
                            else:
                                # Generic dialog for other modules
                                dialog_result = cmds.confirmDialog(
                                    title=f"Validation Issues Found - {clean_name}",
                                    message=f"The validation '{clean_name}' found {len(actual_issues)} issue(s):\n\n{issues_text}\nWhat would you like to do?",
                                    button=["Fix Issues", "Skip for Now", "Stop Validation"],
                                    defaultButton="Fix Issues",
                                    cancelButton="Stop Validation",
                                    dismissString="Stop Validation"
                                )
                                
                                if dialog_result == "Fix Issues":
                                    # For duplicate name validation, show manual fix prompt and skip auto-fix
                                    if "DuplicatedName" in clean_name or "DupicatedName" in clean_name:
                                        QtWidgets.QMessageBox.information(
                                            self,
                                            "Manual Fix Required",
                                            "Duplicate short names cannot be auto-fixed.\nPlease rename manually so each has a unique short name."
                                        )
                                        self.update_module_status(module.name, 'warning')
                                        self.results_display.append(f"ℹ️ {clean_name}: Manual fix required for duplicate short names")
                                    else:
                                        # Run fix mode
                                        fix_results = self.validator.run_validation(module_names=[module.name], mode="fix")
                                        if fix_results and module.name in fix_results:
                                            self.update_module_status_from_results(module.name, fix_results[module.name])
                                        self.results_display.append(f"✅ {clean_name}: Issues fixed")
                                elif dialog_result == "Skip for Now":
                                    self.results_display.append(f"⚠️ {clean_name}: Skipped by user")
                                elif dialog_result == "Stop Validation":
                                    self.results_display.append(f"🛑 Validation stopped by user at {clean_name}")
                                    break
                    else:
                        # All issues were "clean" messages - continue silently
                        self.results_display.append(f"✅ {clean_name}: Passed")
                else:
                    # No issues - continue silently
                    self.results_display.append(f"✅ {clean_name}: Passed")
        
        # Do not enable Fix Issues here; only enable after a Verify action
        
        print("Interactive validation completed")
    
    def fix_issues(self):
        """Fix issues for all enabled modules"""
        if not self.validator:
            return
            
        # Clear previous results
        self.results_display.clear()
        
        # Run fix for all enabled modules
        results = self.validator.run_validation(mode="fix")
        
        # Update all module statuses based on fix results
        if results:
            for module_name in results:
                if module_name in self.module_status_buttons:
                    self.update_module_status_from_results(module_name, results[module_name])
        
        # Re-run validation in check mode to get updated status after fixing
        print("Re-running validation to check if issues were resolved...")
        check_results = self.validator.run_validation(mode="check")
        
        # Update module statuses based on the new check results
        if check_results:
            for module_name in check_results:
                if module_name in self.module_status_buttons:
                    self.update_module_status_from_results(module_name, check_results[module_name])
        
        # Display the current state after fixing (using check results)
        self.display_results(action_type="fix", use_check_results=True)
        
        print("Fix completed")
    
    def display_results(self, action_type="validate", use_check_results=False):
        """Display validation results in the results area
        
        Args:
            action_type (str): Type of action - "validate", "verify", or "fix"
            use_check_results (bool): If True, use check results instead of fix results for display
        """
        if not self.validator:
            return
            
        # If we're in fix mode and want to show current state, get check results
        if action_type == "fix" and use_check_results:
            # Temporarily run check to get current state
            self.validator.run_validation(mode="check")
            
        consolidated_results = self.validator.get_consolidated_results()
            
        # Clear previous results
        self.results_display.clear()
        
        # Check if there are any issues to report
        has_errors = bool(consolidated_results.get('errors', []))
        
        # Filter out warnings that indicate "no issues found" or "nothing to clean"
        filtered_warnings = []
        if consolidated_results.get('warnings'):
            for warning in consolidated_results['warnings']:
                # Skip warnings that indicate no issues or nothing to clean
                skip_phrases = [
                    "No namespaces to clean",
                    "No display layers to clear", 
                    "Outliner organized: 0 nodes moved",
                    "No issues found",
                    "Nothing to clean",
                    "No problems detected",
                    "Clean - no issues",
                    "Passed - no issues",
                    "No duplicate names found",
                    "No custom namespaces found",
                    "No bind pose nodes found",
                    "No display layers found",
                    "No joints found to check",
                    "No animation curves found",
                    "No NgSkinTools nodes found",
                    "Outliner is already well organized",
                    "Outliner already clean",
                    "All character sets are properly configured",
                    "No character sets found in scene",
                    "No skin clusters found to check",
                    "No references found in scene",
                    "No tweak nodes found to check",
                    "No unknown nodes found to check",
                    "Not enough materials to check",
                    "Fixed: 0 nodes = 0 materials"
                ]
                
                should_skip = False
                for phrase in skip_phrases:
                    if phrase.lower() in warning.lower():
                        should_skip = True
                        break
                
                if not should_skip:
                    filtered_warnings.append(warning)
        
        has_warnings = bool(filtered_warnings)
        
        # Filter out "No issues found" messages from info
        filtered_info = []
        if consolidated_results.get('info'):
            for info in consolidated_results['info']:
                # Skip "No issues found" messages
                if not info.endswith(": No issues found") and not info.endswith("No issues found"):
                    filtered_info.append(info)
        
        has_relevant_info = bool(filtered_info)
        
        # Check if any validation module has already simplified the output to just "All validations passed"
        simplified_success = False
        
        # Check info section
        if consolidated_results.get('info'):
            for info in consolidated_results['info']:
                if info == "All validations passed":
                    simplified_success = True
                    break
        
        # Check warnings section
        if not simplified_success and consolidated_results.get('warnings'):
            for warning in consolidated_results['warnings']:
                if warning == "All validations passed":
                    simplified_success = True
                    break
        
        # Check errors section
        if not simplified_success and consolidated_results.get('errors'):
            for error in consolidated_results['errors']:
                if error == "All validations passed":
                    simplified_success = True
                    break
        
        # If simplified success message is found, show it directly
        if simplified_success:
            self.results_display.append("✅ All validations passed successfully!")
            return
        
        # Check if there are any failed validations (X marks) by looking at module statuses
        has_failed_validations = False
        for module_name in self.module_status_buttons:
            status_btn = self.module_status_buttons[module_name]
            if status_btn.text() == "✗":  # X mark indicates failed validation
                has_failed_validations = True
                break
        
        # If no errors, no warnings, no relevant info, and no failed validations, show success message
        if not has_errors and not has_warnings and not has_relevant_info and not has_failed_validations:
            self.results_display.append("✅ All validations passed successfully!")
            return
        
        # Additional check: If we're in fix mode and all modules passed (no errors, only "clean" messages), show simplified success
        if action_type == "fix" and not has_errors and not has_failed_validations:
            # Check if all warnings are just "clean" messages (no issues found, already clean, etc.)
            all_clean_messages = True
            if consolidated_results.get('warnings'):
                clean_indicators = [
                    "no action needed", "already clean", "no issues found", "no problems detected",
                    "clean - no issues", "passed - no issues", "no duplicate names found",
                    "no custom namespaces found", "no bind pose nodes found", "no display layers found",
                    "no joints found to check", "no animation curves found", "no NgSkinTools nodes found",
                    "outliner is already well organized", "outliner already clean",
                    "all character sets are properly configured", "no character sets found in scene",
                    "no skin clusters found to check", "no references found in scene",
                    "no tweak nodes found to check", "no unknown nodes found to check",
                    "not enough materials to check", "fixed: 0 nodes = 0 materials",
                    "no low weights found", "no unused materials found", "has no unused influence joints"
                ]
                
                for warning in consolidated_results['warnings']:
                    warning_lower = warning.lower()
                    is_clean = any(indicator in warning_lower for indicator in clean_indicators)
                    if not is_clean:
                        all_clean_messages = False
                        break
            
            if all_clean_messages:
                self.results_display.append("✅ All validations passed successfully!")
                return
        
        # Check if all individual validations passed (all have "All validations passed" messages)
        passed_count = 0
        total_validations = 0
        
        # Count how many validations have "All validations passed" messages
        if consolidated_results.get('info'):
            for info in consolidated_results['info']:
                if "All validations passed" in info:
                    passed_count += 1
                total_validations += 1
        
        if consolidated_results.get('warnings'):
            for warning in consolidated_results['warnings']:
                if "All validations passed" in warning:
                    passed_count += 1
                total_validations += 1
        
        # Debug: Print what we found
        print(f"Debug - passed_count: {passed_count}, total_validations: {total_validations}")
        print(f"Debug - has_errors: {has_errors}, has_warnings: {has_warnings}, has_failed_validations: {has_failed_validations}")
        
        # If all validations passed and there are no errors, show consolidated success
        if passed_count > 0 and total_validations > 0 and passed_count == total_validations and not has_errors and not has_failed_validations:
            self.results_display.append("✅ All validations passed successfully!")
            return
        
        # Additional check: If we have multiple "All validations passed" messages and no errors/warnings, consolidate
        if passed_count >= 2 and not has_errors and not has_warnings and not has_failed_validations:
            self.results_display.append("✅ All validations passed successfully!")
            return
        
        # Final check: If we have any "All validations passed" messages and no errors/warnings/failed validations, consolidate
        if passed_count >= 1 and not has_errors and not has_warnings and not has_failed_validations:
            self.results_display.append("✅ All validations passed successfully!")
            return
        
        # Display results based on action type
        if action_type == "verify":
            # Show verification results - only errors and filtered warnings
            if has_errors:
                for error in consolidated_results['errors']:
                    self.results_display.append(f"❌ {error}")
            
            if has_warnings:
                for warning in filtered_warnings:
                    # Check if this warning message indicates success
                    if "All validations passed" in warning:
                        self.results_display.append(f"✅ {warning}")
                    else:
                        self.results_display.append(f"⚠️ {warning}")
                    
        elif action_type == "fix":
            if use_check_results:
                # Show current state after fixing (what's actually resolved vs. what remains)
                if has_errors:
                    for error in consolidated_results['errors']:
                        self.results_display.append(f"❌ {error}")
                
                if has_warnings:
                    for warning in filtered_warnings:
                        # Check if this warning message indicates success
                        if "All validations passed" in warning:
                            self.results_display.append(f"✅ {warning}")
                        else:
                            self.results_display.append(f"⚠️ {warning}")
                
                # If no errors and no warnings, show success message
                if not has_errors and not has_warnings:
                    self.results_display.append("✅ All validations passed successfully!")
            else:
                # Show fix operation results
                if has_errors:
                    for error in consolidated_results['errors']:
                        self.results_display.append(f"❌ {error}")
                
                # Process warnings and info to show appropriate emojis
                if has_warnings:
                    for warning in filtered_warnings:
                        # Check if this warning message indicates a successful fix or success
                        if any(phrase in warning.lower() for phrase in ["created", "fixed", "removed", "cleaned", "parented", "imported", "structure has been fixed", "is now valid"]) or "All validations passed" in warning:
                            self.results_display.append(f"✅ {warning}")
                        else:
                            self.results_display.append(f"⚠️ {warning}")
                
                # Show successful fixes with green ticks
                if has_relevant_info:
                    for info in filtered_info:
                        # Check if this info message indicates a successful fix
                        if any(phrase in info.lower() for phrase in ["created", "fixed", "removed", "cleaned", "parented", "imported"]):
                            self.results_display.append(f"✅ {info}")
                        else:
                            self.results_display.append(f"ℹ️ {info}")
                
                # If no errors and no relevant warnings, show success message
                if not has_errors and not has_warnings:
                    self.results_display.append("✅ All validations passed successfully!")
        else:
            # Show all results - only errors and filtered warnings
            if has_errors:
                for error in consolidated_results['errors']:
                    self.results_display.append(f"❌ {error}")
            
            if has_warnings:
                for warning in filtered_warnings:
                    # Check if this warning message indicates success
                    if "All validations passed" in warning:
                        self.results_display.append(f"✅ {warning}")
                    else:
                        self.results_display.append(f"⚠️ {warning}")
            
            # If no errors and no relevant warnings, show success message
            if not has_errors and not has_warnings:
                self.results_display.append("✅ All validations passed successfully!")
    

    def clear_results(self, clear_type="both"):
        """Clear results display"""
        if clear_type in ["both", "results"]:
            self.results_display.clear()
            # Disable the Fix Issues button when results are cleared
            self.btn_fix.setEnabled(False)
            self._did_verify = False
            # Reset per-module verified state and disable all Fix buttons
            for module_name in self.module_verified.keys():
                self.module_verified[module_name] = False
            for module_name, fix_btn in self.module_fix_buttons.items():
                fix_btn.setEnabled(False)
        
        if clear_type in ["both", "info"]:
            # Clear info list if it exists
            pass
    
    def update_module_status(self, module_name, status):
        """Update the status button for a specific module
        
        Args:
            module_name (str): Name of the module
            status (str): Status to display - 'pass', 'fail', 'warning', or 'default'
        """
        if module_name in self.module_status_buttons:
            status_btn = self.module_status_buttons[module_name]
            
            if status == 'pass':
                status_btn.setText("✓")
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #4CAF50; 
                        color: #e0e0e0; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #4CAF50;
                        color: #e0e0e0;
                    }
                """)
            elif status == 'fail':
                status_btn.setText("✗")
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #f44336; 
                        color: #e0e0e0; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #f44336;
                        color: #e0e0e0;
                    }
                """)
            elif status == 'warning':
                status_btn.setText("?")
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #ff9800; 
                        color: #e0e0e0; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #ff9800;
                        color: #e0e0e0;
                    }
                """)
            else:  # default
                status_btn.setText("✓")
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #505050; 
                        color: #e0e0e0; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #505050;
                        color: #e0e0e0;
                    }
                """)
    
    def update_module_status_from_results(self, module_name, results):
        """Update module status based on validation results
        
        Args:
            module_name (str): Name of the module
            results (dict): Results from validation
        """
        if not results or 'status' not in results:
            self.update_module_status(module_name, 'default')
            return
        
        # Check if there are any issues
        total_issues = results.get('total_issues', 0)
        
        if total_issues == 0:
            self.update_module_status(module_name, 'pass')
        else:
            # Check if all issues were fixed
            fixed_issues = 0
            if 'issues' in results:
                for issue in results['issues']:
                    if issue.get('fixed', False):
                        fixed_issues += 1
            
            if fixed_issues == total_issues:
                self.update_module_status(module_name, 'pass')
            elif fixed_issues > 0:
                # Some issues were fixed, some remain - this is a warning state
                self.update_module_status(module_name, 'warning')
            else:
                # No issues were fixed
                self.update_module_status(module_name, 'fail')

    def reset_all_module_statuses(self):
        """Reset all module statuses to default (grey)"""
        for module_name in self.module_status_buttons:
            self.update_module_status(module_name, 'default')
    
    def _separator(self):
        """Create a separator line"""
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setStyleSheet("QFrame { background-color: #2A2A2A ; margin: 10px 0px; }")
        return separator
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Clear the global dialog reference when window is closed
        try:
            # Use a safer approach to clear the dialog reference
            import sys
            if 'rigging_pipeline.tools.rigx_riggingValidator' in sys.modules:
                validator_module = sys.modules['rigging_pipeline.tools.rigx_riggingValidator']
                if hasattr(validator_module, '_dialog') and validator_module._dialog == self:
                    validator_module._dialog = None
            
            # Remove from UIManager if it exists
            from rigging_pipeline.tools.rigx_riggingValidator import UIManager
            if "RiggingValidator" in UIManager._open_windows:
                del UIManager._open_windows["RiggingValidator"]
        except Exception as e:
            # If there's any error, just continue
            pass
        event.accept()
