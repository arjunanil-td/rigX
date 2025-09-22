from __future__ import annotations

import os
import sys

# Maya imports
try:
    import maya.cmds as cmds
    import maya.OpenMayaUI as omui
    from shiboken2 import wrapInstance
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    print("Warning: Maya modules not available. This tool must be run within Maya.")

# Qt imports
from PySide2 import QtWidgets, QtCore, QtGui

# Pipeline imports
from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET
from rigging_pipeline.io.rigx_ui_banner import Banner
from rigging_pipeline.tools.modules_tail import TailModuleBuilder
from rigging_pipeline.tools.modules_curve_deformer import CurveDeformerModuleBuilder


def maya_main_window() -> QtWidgets.QWidget | None:
    """Return Maya's main window as a QtWidgets.QWidget for proper parenting.

    When Maya is not available (e.g., during tests), returns None so the UI
    still can be instantiated without a parent.
    """
    if not MAYA_AVAILABLE:
        return None
    try:
        ptr = omui.MQtUtil.mainWindow()
        if ptr is None:
            return None
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    except Exception:
        return None


class CollapsibleSection(QtWidgets.QWidget):
    """Simple collapsible section widget with a header and content area."""

    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None) -> None:
        super(CollapsibleSection, self).__init__(parent)
        # Style to match the reference exactly
        self._toggle = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        self._toggle.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self._toggle.setArrowType(QtCore.Qt.RightArrow)
        self._toggle.setFixedHeight(25)  # Reduce height of module headers
        self._toggle.setStyleSheet("""
            QToolButton {
                background-color: #4a4a4a;
                color: white;
                border: none;
                padding: 4px 12px;
                text-align: left;
                font-weight: normal;
                font-size: 12px;
            }
            QToolButton:hover {
                background-color: #5a5a5a;
            }
            QToolButton:checked {
                background-color: #5a5a5a;
            }
        """)
        self._toggle.toggled.connect(self._on_toggled)

        self._content = QtWidgets.QWidget()
        self._content.setVisible(False)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toggle)
        layout.addWidget(self._content)

    def setContentLayout(self, content_layout: QtWidgets.QLayout) -> None:
        self._content.setLayout(content_layout)

    def _on_toggled(self, checked: bool) -> None:
        self._toggle.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
        self._content.setVisible(checked)
        # Add some padding to content when visible
        if checked:
            self._content.setStyleSheet("background-color: #2a2a2a; padding: 8px;")
        else:
            self._content.setStyleSheet("")


class RigXModulesUI(QtWidgets.QDialog):
    """RigX Modules UI - container for module-based rigging tools.

    This dialog provides a consistent rigX-themed interface for managing
    and building rig modules.
    """

    WINDOW_TITLE = "RigX Modules"

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super(RigXModulesUI, self).__init__(parent or maya_main_window())
        self.setObjectName("RigXModulesUI")
        self.setStyleSheet(THEME_STYLESHEET)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(500, 600)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        
        # Set main dialog background to match the dark theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #2a2a2a;
            }}
            {THEME_STYLESHEET}
        """)
        
        self._tail_builder = None
        self._curve_def_builder = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add the centralized banner
        banner = Banner("RigX Modules", "rigX_icon_modules.png")
        layout.addWidget(banner)

        # Three collapsible sections at the top, horizontally stretched
        sections_container = QtWidgets.QVBoxLayout()
        sections_container.setContentsMargins(0, 0, 0, 0)
        sections_container.setSpacing(2) # Small gap between modules

        # Tail Module section
        tail_section = CollapsibleSection("Tail Module")
        tail_form = QtWidgets.QFormLayout()
        tail_form.setContentsMargins(10, 10, 10, 10)
        tail_form.setHorizontalSpacing(8)
        tail_form.setVerticalSpacing(6)
        tail_form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        tail_form.setFormAlignment(QtCore.Qt.AlignTop)
        tail_form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        joints_row = QtWidgets.QHBoxLayout()
        self.tail_joints_le = QtWidgets.QLineEdit()
        self.tail_joints_pick_btn = QtWidgets.QPushButton("Pick Joints")
        joints_row.addWidget(self.tail_joints_le)
        joints_row.addWidget(self.tail_joints_pick_btn)
        tail_form.addRow("Joints", joints_row)

        self.tail_name_le = QtWidgets.QLineEdit("Tail")
        tail_form.addRow("Rig Name", self.tail_name_le)

        self.tail_ctrls_sb = QtWidgets.QSpinBox(); self.tail_ctrls_sb.setRange(2, 100); self.tail_ctrls_sb.setValue(5)
        tail_form.addRow("No. Controls", self.tail_ctrls_sb)

        self.tail_dyn_cb = QtWidgets.QCheckBox("Enable Dynamics (nHair)"); self.tail_dyn_cb.setChecked(True)
        tail_form.addRow(self.tail_dyn_cb)

        dp_row = QtWidgets.QHBoxLayout()
        self.tail_dp_le = QtWidgets.QLineEdit(); self.tail_dp_add_btn = QtWidgets.QPushButton("Pick +"); self.tail_dp_clear_btn = QtWidgets.QPushButton("Clear")
        dp_row.addWidget(self.tail_dp_le); dp_row.addWidget(self.tail_dp_add_btn); dp_row.addWidget(self.tail_dp_clear_btn)
        tail_form.addRow("Dynamic Parent Targets", dp_row)

        self.tail_build_btn = QtWidgets.QPushButton("Build Tail")
        tail_form.addRow(self.tail_build_btn)

        tail_section.setContentLayout(tail_form)
        sections_container.addWidget(tail_section)

        # Module 1 section - Curve Deformer
        m1_section = CollapsibleSection("Module 1 - Curve Deformer")
        m1_form = QtWidgets.QFormLayout()
        m1_form.setContentsMargins(10, 10, 10, 10)
        m1_form.setHorizontalSpacing(8)
        m1_form.setVerticalSpacing(6)
        m1_form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        m1_form.setFormAlignment(QtCore.Qt.AlignTop)
        m1_form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        # Driver curve picker
        m1_curve_row = QtWidgets.QHBoxLayout()
        self.m1_curve_le = QtWidgets.QLineEdit()
        self.m1_curve_pick_btn = QtWidgets.QPushButton("Pick Curve")
        m1_curve_row.addWidget(self.m1_curve_le)
        m1_curve_row.addWidget(self.m1_curve_pick_btn)
        m1_form.addRow("Driver Curve", m1_curve_row)

        # Targets picker (multi)
        m1_tgt_row = QtWidgets.QHBoxLayout()
        self.m1_targets_le = QtWidgets.QLineEdit()
        self.m1_targets_add_btn = QtWidgets.QPushButton("Pick +")
        self.m1_targets_clear_btn = QtWidgets.QPushButton("Clear")
        m1_tgt_row.addWidget(self.m1_targets_le)
        m1_tgt_row.addWidget(self.m1_targets_add_btn)
        m1_tgt_row.addWidget(self.m1_targets_clear_btn)
        m1_form.addRow("Targets", m1_tgt_row)

        # Name
        self.m1_name_le = QtWidgets.QLineEdit("CurveDef")
        m1_form.addRow("Name", self.m1_name_le)

        # Dropoff distance
        self.m1_dropoff_dsb = QtWidgets.QDoubleSpinBox(); self.m1_dropoff_dsb.setRange(0.001, 100000.0); self.m1_dropoff_dsb.setDecimals(3); self.m1_dropoff_dsb.setValue(5.0)
        m1_form.addRow("Dropoff Distance", self.m1_dropoff_dsb)

        # Scale compensation
        self.m1_comp_cb = QtWidgets.QCheckBox("Compensate Scale"); self.m1_comp_cb.setChecked(True)
        m1_form.addRow(self.m1_comp_cb)

        # Scale reference (optional)
        m1_ref_row = QtWidgets.QHBoxLayout()
        self.m1_scale_ref_le = QtWidgets.QLineEdit()
        self.m1_scale_ref_pick_btn = QtWidgets.QPushButton("Pick")
        m1_ref_row.addWidget(self.m1_scale_ref_le)
        m1_ref_row.addWidget(self.m1_scale_ref_pick_btn)
        m1_form.addRow("Scale Reference", m1_ref_row)

        # Build button
        self.m1_build_btn = QtWidgets.QPushButton("Create Curve Deformer")
        m1_form.addRow(self.m1_build_btn)

        m1_section.setContentLayout(m1_form)
        sections_container.addWidget(m1_section)

        # Module 2 section
        m2_section = CollapsibleSection("Module 2")
        m2_form = QtWidgets.QFormLayout()
        m2_form.addRow(QtWidgets.QLabel("Coming soon"))
        m2_section.setContentLayout(m2_form)
        sections_container.addWidget(m2_section)

        # Add sections to main layout
        layout.addLayout(sections_container)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Footer with Close button at bottom right
        footer_layout = QtWidgets.QHBoxLayout()
        footer_layout.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        footer_layout.addWidget(close_btn)
        layout.addLayout(footer_layout)

        # Wire signals
        self.tail_joints_pick_btn.clicked.connect(self._on_pick_joints)
        self.tail_dp_add_btn.clicked.connect(self._on_add_dp_target)
        self.tail_dp_clear_btn.clicked.connect(self._on_clear_dp_targets)
        self.tail_build_btn.clicked.connect(self._on_build_tail)
        self.m1_curve_pick_btn.clicked.connect(self._on_m1_pick_curve)
        self.m1_targets_add_btn.clicked.connect(self._on_m1_add_targets)
        self.m1_targets_clear_btn.clicked.connect(self._on_m1_clear_targets)
        self.m1_scale_ref_pick_btn.clicked.connect(self._on_m1_pick_scale_ref)
        self.m1_build_btn.clicked.connect(self._on_m1_build)

    # ------------------------------ Handlers ------------------------------ #
    def _ensure_tail_builder(self) -> TailModuleBuilder:
        if self._tail_builder is None:
            self._tail_builder = TailModuleBuilder()
        return self._tail_builder

    def _ensure_curve_def_builder(self) -> CurveDeformerModuleBuilder:
        if self._curve_def_builder is None:
            self._curve_def_builder = CurveDeformerModuleBuilder()
        return self._curve_def_builder

    def _on_pick_joints(self) -> None:
        if not MAYA_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Warning", "Maya is not available.")
            return
        try:
            sel = cmds.ls(sl=True, type='joint') or []
            if not sel:
                QtWidgets.QMessageBox.information(self, "Pick Joints", "Select a joint chain in Maya.")
                return
            self.tail_joints_le.setText(",".join(sel))
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to read selection: {exc}")

    def _on_add_dp_target(self) -> None:
        if not MAYA_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Warning", "Maya is not available.")
            return
        try:
            sel = cmds.ls(sl=True) or []
            if not sel:
                QtWidgets.QMessageBox.information(self, "Dynamic Parents", "Select one or more parent targets.")
                return
            existing = [s.strip() for s in self.tail_dp_le.text().split(',') if s.strip()]
            for s in sel:
                if s not in existing:
                    existing.append(s)
            self.tail_dp_le.setText(",".join(existing))
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to append targets: {exc}")

    def _on_clear_dp_targets(self) -> None:
        self.tail_dp_le.setText("")

    def _on_build_tail(self) -> None:
        if not MAYA_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Warning", "Maya is not available.")
            return
        # TailModule is the only available module currently
        joints_txt = self.tail_joints_le.text().strip()
        name = self.tail_name_le.text().strip() or "Tail"
        num_controls = int(self.tail_ctrls_sb.value())
        use_dyn = bool(self.tail_dyn_cb.isChecked())
        targets = [t.strip() for t in self.tail_dp_le.text().split(',') if t.strip()]
        try:
            builder = self._ensure_tail_builder()
            if not joints_txt:
                QtWidgets.QMessageBox.information(self, "Joints Required", "Pick a joint chain to build the tail.")
                return
            joints = [j.strip() for j in joints_txt.split(',') if j.strip()]
            result = builder.build_tail_from_joints(joints=joints, rig_name=name, use_dynamics=use_dyn, dynamic_parent_targets=targets or None, num_controls=num_controls)
            QtWidgets.QMessageBox.information(self, "Tail Module", f"Tail built. Main control: {result.get('main_control')}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Build Failed", str(exc))

    # --------------------------- Module 1 Handlers -------------------------- #
    def _on_m1_pick_curve(self) -> None:
        if not MAYA_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Warning", "Maya is not available.")
            return
        try:
            sel = cmds.ls(sl=True) or []
            if not sel:
                QtWidgets.QMessageBox.information(self, "Pick Curve", "Select a NURBS curve transform in Maya.")
                return
            self.m1_curve_le.setText(sel[0])
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to read selection: {exc}")

    def _on_m1_add_targets(self) -> None:
        if not MAYA_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Warning", "Maya is not available.")
            return
        try:
            sel = cmds.ls(sl=True) or []
            if not sel:
                QtWidgets.QMessageBox.information(self, "Targets", "Select one or more deformable targets (mesh or NURBS surface transforms).")
                return
            existing = [s.strip() for s in self.m1_targets_le.text().split(',') if s.strip()]
            for s in sel:
                if s not in existing:
                    existing.append(s)
            self.m1_targets_le.setText(",".join(existing))
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to append targets: {exc}")

    def _on_m1_clear_targets(self) -> None:
        self.m1_targets_le.setText("")

    def _on_m1_pick_scale_ref(self) -> None:
        if not MAYA_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Warning", "Maya is not available.")
            return
        try:
            sel = cmds.ls(sl=True) or []
            if not sel:
                QtWidgets.QMessageBox.information(self, "Scale Reference", "Select a transform to use as scale reference (optional).")
                return
            self.m1_scale_ref_le.setText(sel[0])
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to read selection: {exc}")

    def _on_m1_build(self) -> None:
        if not MAYA_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Warning", "Maya is not available.")
            return
        curve = self.m1_curve_le.text().strip()
        targets = [t.strip() for t in self.m1_targets_le.text().split(',') if t.strip()]
        name = self.m1_name_le.text().strip() or "CurveDef"
        dropoff = float(self.m1_dropoff_dsb.value())
        compensate = bool(self.m1_comp_cb.isChecked())
        scale_ref = self.m1_scale_ref_le.text().strip() or None
        try:
            builder = self._ensure_curve_def_builder()
            result = builder.create_curve_deformer(
                driver_curve=curve,
                targets=targets,
                name=name,
                dropoff_distance=dropoff,
                compensate_scale=compensate,
                scale_reference=scale_ref,
            )
            QtWidgets.QMessageBox.information(self, "Curve Deformer", f"Created curve deformer successfully!\nWire Deformer: {result.get('wire')}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Create Failed", str(exc))


