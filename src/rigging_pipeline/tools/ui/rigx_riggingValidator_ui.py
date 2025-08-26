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
        super(RiggingValidatorUI, self).__init__(parent)
        
        self.setWindowTitle("RigX Rigging Validator")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        self.resize(500, 900)
        
        self.setStyleSheet(THEME_STYLESHEET)
        self.validator = validator
        self._updating_check_all = False  # Flag to prevent circular dependency
        
        # Initialize button dictionaries
        self.module_verify_buttons = {}
        self.module_fix_buttons = {}
        self.module_status_buttons = {}  # Store status buttons for each module
        self.module_status_labels = {}  # Store status labels for each module
        
        self.build_ui()
    
    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Add the centralized banner
        banner = Banner("RigX Rigging Validator", "../icons/rigX_validator.png")
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
        layout.addWidget(options_group)
        
        # ───── Main Splitter for Validations and Results ─────
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #666666;
            }
        """)
        
        # ───── Validations ─────
        validations_group = QtWidgets.QGroupBox("Validations")
        validations_layout = QtWidgets.QVBoxLayout(validations_group)
        
        if self.validator:
            self.build_validations_list(validations_layout)
        
        self.main_splitter.addWidget(validations_group)
        
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
                font-size: 12px;
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
                font-size: 12px;
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
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        
        button_layout.addWidget(self.btn_validate)
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
                color: white;
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
                background-color: #2b2b2b; 
                border: 1px solid #555555;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                min-height: 150px;
                color: white;
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
        
        # Sort modules by name for consistent ordering
        filtered_modules.sort(key=lambda x: x.name)
        
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
                description = self.get_validation_description(module_name)
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
                
                # Status button (tick/checkmark/X/warning)
                status_btn = QtWidgets.QPushButton("✓")
                status_btn.setFixedSize(25, 25)
                status_btn.setEnabled(False)  # Disabled by default, only shows status
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #808080; 
                        color: white; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #808080;
                        color: white;
                    }
                """)
                
                # Store buttons for later access
                self.module_verify_buttons[module.name] = verify_btn
                self.module_fix_buttons[module.name] = fix_btn
                self.module_status_buttons[module.name] = status_btn
                
                # Set initial button states based on checkbox state
                verify_btn.setEnabled(checkbox.isChecked())
                fix_btn.setEnabled(checkbox.isChecked())
                
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
        
        parent_layout.addWidget(scroll_area)
    
    def get_validation_description(self, module_name):
        """Get validation description for a module"""
        validation_descriptions = {
            # All validations (formerly Model + Rig) - Geometry, mesh, rigging and animation related
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
            "UnlockNormals": "It will unlock normals from the geometries.",
            "InvertedNormals": "It will verify inverted normals in the geometries.",
            "SoftenEdges": "It will verify soften edges in the geometries.",
            "OverrideCleaner": "It will verify if there are nodes with overrides and remove them.",
            
            # Additional validations (CheckOut) - Rigging and animation related
            "CycleChecker": "It will verify if there are cycle errors in the scene. It will only verify and report them as this theme is very complex to fix automatically.",
            "BrokenRivet": "Lists the follicles in the world origin, meaning those that are not correctly fixed, and tries to fix them.",
            "KeyframeCleaner": "It will delete the animated objects keyframes. It won't check drivenKeys, blendWeights or pairBlends.",
            "NgSkinToolsCleaner": "It will clean-up all ngSkinTools custom nodes forever.",
            "BrokenNetCleaner": "It will detect if there are some broken correction manager network to clean-up them.",
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
            "ControlsHierarchy": "Check if controls hierarchy match with a previous state exported, to prevent animation loss.",
            "DisplayLayers": "It will check that no display layers exist in the scene (except the default layer). If any display layers are found, it will report them and clear them to keep the scene clean.",
            "ResetPose": "It will reset the rig to its default pose.",
            "BindPoseCleaner": "It will verify if there are bindPose nodes in the scene. If so, it will delete them and create just a new one node for all skinned joints.",
            "RemapValueToSetRange": "It will verify if there are remapValue nodes that could be converted to setRange nodes without losing any behavior. It will optimize the calculation and get a faster rig.",
            "HideAllJoints": "It will hide joints in the scene.",
            "PassthroughAttributes": "It will verify if there are attributes with no necessary inbetween connections. If so, it will change (a -> b -> c) to (a -> c).",
            "ProxyCreator": "Creates proxy geometry for performance optimization during rigging.",
            "Cleanup": "It will check for rigXDeleteIt attributes and delete their nodes."
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
                self.module_fix_buttons[module.name].setEnabled(enabled)
    
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
        results = self.validator.run_validation(module_names=[module.name], mode="check", objList=None)
        
        # Update module status based on results
        if results and module.name in results:
            self.update_module_status_from_results(module.name, results[module.name])
        else:
            self.update_module_status(module.name, 'default')
        
        # Display results
        self.display_results(action_type="verify")
        
        # Module verification completed
        clean_name = module.name.replace('dp', '')
        consolidated_results = self.validator.get_consolidated_results()
        print(f"Verified {clean_name} - {len(consolidated_results['info'])} items found")
    
    def fix_single_module(self, module):
        """Fix issues for a single validation module"""
        if not self.validator or not module:
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
        
        # Display results
        self.display_results(action_type="validate")
        
        print("Validation completed")
    
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
        
        # Display results
        self.display_results(action_type="fix")
        
        print("Fix completed")
    
    def display_results(self, action_type="validate"):
        """Display validation results in the results area"""
        if not self.validator:
            return
            
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
        
        # If no errors, no warnings, and no relevant info, show success message
        if not has_errors and not has_warnings and not has_relevant_info:
            # Show success message for all modes
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
                    self.results_display.append(f"⚠️ {warning}")
                    
        elif action_type == "fix":
            # Show fix results - errors, filtered warnings, and relevant info
            if has_errors:
                for error in consolidated_results['errors']:
                    self.results_display.append(f"❌ {error}")
            
            if has_warnings:
                for warning in filtered_warnings:
                    self.results_display.append(f"⚠️ {warning}")
            
            # Show relevant info for successful fixes (excluding "No issues found")
            if has_relevant_info:
                for info in filtered_info:
                    self.results_display.append(f"✅ {info}")
            
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
                    self.results_display.append(f"⚠️ {warning}")
            
            # If no errors and no relevant warnings, show success message
            if not has_errors and not has_warnings:
                self.results_display.append("✅ All validations passed successfully!")
    

    def clear_results(self, clear_type="both"):
        """Clear results display"""
        if clear_type in ["both", "results"]:
            self.results_display.clear()
        
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
                        color: white; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #4CAF50;
                        color: white;
                    }
                """)
            elif status == 'fail':
                status_btn.setText("✗")
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #f44336; 
                        color: white; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #f44336;
                        color: white;
                    }
                """)
            elif status == 'warning':
                status_btn.setText("?")
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #ff9800; 
                        color: white; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #ff9800;
                        color: white;
                    }
                """)
            else:  # default
                status_btn.setText("✓")
                status_btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #808080; 
                        color: white; 
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:disabled {
                        background-color: #808080;
                        color: white;
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
        separator.setStyleSheet("QFrame { background-color: #555555; margin: 10px 0px; }")
        return separator
    
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
