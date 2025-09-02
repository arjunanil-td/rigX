# -*- coding: utf-8 -*-
"""
RigX UsdSkel Export UI — Dockable PySide2 panel for Maya 2024+

This tool wraps the usd_skel_export publisher (REST + ANIM) and adds:
- Simple, safe defaults for UsdSkel export
- Selection hygiene (skinned meshes + influences)
- One‑click REST publish (static: mesh+weights+skeleton+blendshapes targets)
- One‑click ANIM publish (SkelAnimation curves for joints and optional BS channels)
- Optional ANIM chunking + Value Clip manifest authoring
- Persistent settings via QSettings

Save to (suggested):
Q:/METAL/tools/pipeline/rigX/src/rigging_pipeline/tools/ui/rigx_usdskel_export_ui.py

Launch inside Maya:
    from rigging_pipeline.tools.ui.rigx_usdskel_export_ui import launch
    launch(dock=True)

Requires:
- Maya 2024+ (Python 3.10)
- mayaUsdPlugin loaded (auto-loads)
- The publisher module from earlier steps available at:
    rigging_pipeline.publish.usd_skel_export

If your path differs, adjust IMPORT_PATHS below.
"""
from __future__ import annotations
import os
import sys
from typing import List, Tuple

from maya import cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# PySide2 imports
from PySide2 import QtWidgets, QtCore

# --------------------------------------------------------------------------------------
# Import publisher (adjust these if your repo layout is different)
# --------------------------------------------------------------------------------------
PUBLISH_IMPORT = "rigging_pipeline.publish.usd_skel_export"

try:
    skelx = __import__(PUBLISH_IMPORT, fromlist=["*"])
except Exception as e:
    # Try to add a likely src path if running locally
    # Edit these hints if your environment uses different roots
    candidate_roots = [
        r"Q:/METAL/tools/pipeline/rigX/src",
        r"/mnt/q/METAL/tools/pipeline/rigX/src",
    ]
    for root in candidate_roots:
        if os.path.isdir(root) and root not in sys.path:
            sys.path.insert(0, root)
    try:
        skelx = __import__(PUBLISH_IMPORT, fromlist=["*"])
    except Exception as e2:
        raise ImportError(
            f"Failed to import publisher '{PUBLISH_IMPORT}'. Error: {e2}\n"
            f"Ensure usd_skel_export.py is available and PYTHONPATH includes your repo /src."
        )

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
ORG = "rigX"
APP = "UsdSkelExportUI"


def _qsettings() -> QtCore.QSettings:
    return QtCore.QSettings(ORG, APP)


def _playback_range() -> Tuple[int, int]:
    """Return (min, max) playback range as ints."""
    try:
        mn = int(cmds.playbackOptions(q=True, min=True))
        mx = int(cmds.playbackOptions(q=True, max=True))
        return mn, mx
    except Exception:
        return 1, 100


# --------------------------------------------------------------------------------------
# UI Widgets
# --------------------------------------------------------------------------------------
class PathField(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(str)

    def __init__(self, label: str, mode: str = "save", parent=None):
        super().__init__(parent)
        self._mode = mode  # "save" or "open"
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(label)
        self.edit = QtWidgets.QLineEdit()
        self.btn = QtWidgets.QPushButton("…")
        self.btn.setFixedWidth(28)
        lay.addWidget(self.label)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.btn)
        self.btn.clicked.connect(self._on_browse)
        self.edit.textChanged.connect(self.valueChanged)

    def setText(self, text: str):
        self.edit.setText(text)

    def text(self) -> str:
        return self.edit.text().strip()

    def _on_browse(self):
        start = self.text() or os.path.expanduser("~")
        if self._mode == "save":
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Select Output .usdc", start, "USD files (*.usdc *.usd *.usda)"
            )
            if path:
                self.setText(path)
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select File", start, "All files (*.*)"
            )
            if path:
                self.setText(path)


class LabeledSpin(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(int)

    def __init__(self, label: str, v: int, vmin: int, vmax: int, parent=None):
        super().__init__(parent)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.label = QtWidgets.QLabel(label)
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(vmin, vmax)
        self.spin.setValue(v)
        lay.addWidget(self.label)
        lay.addWidget(self.spin)
        self.spin.valueChanged.connect(self.valueChanged)

    def value(self) -> int:
        return int(self.spin.value())

    def setValue(self, v: int):
        self.spin.setValue(v)


class ExportOptionsWidget(QtWidgets.QGroupBox):
    """Common options that apply to both REST and ANIM exports."""

    def __init__(self, title: str = "Common Options", parent=None):
        super().__init__(title, parent)
        form = QtWidgets.QFormLayout(self)
        form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Mesh scheme
        self.meshScheme = QtWidgets.QComboBox()
        self.meshScheme.addItems(["catmullClark", "none"])  # you can extend

        # Skels/Skins export mode
        self.skelsMode = QtWidgets.QComboBox()
        self.skelsMode.addItems(["auto", "all", "none"])
        self.skinsMode = QtWidgets.QComboBox()
        self.skinsMode.addItems(["auto", "all", "none"])

        # Shading material handling
        self.shadingMode = QtWidgets.QComboBox()
        self.shadingMode.addItems(["useRegistry", "none", "displayColor"])  # common modes

        self.materialsScope = QtWidgets.QLineEdit("materials")
        self.stripNamespaces = QtWidgets.QCheckBox("Strip Namespaces")
        self.stripNamespaces.setChecked(True)
        self.mergeXformShape = QtWidgets.QCheckBox("Merge Transform & Shape")
        self.mergeXformShape.setChecked(True)
        self.exportDisplayColor = QtWidgets.QCheckBox("Export Display Color")
        self.exportDisplayColor.setChecked(True)

        form.addRow("Default Mesh Scheme:", self.meshScheme)
        form.addRow("Export Skeletons:", self.skelsMode)
        form.addRow("Export Skins:", self.skinsMode)
        form.addRow("Shading Mode:", self.shadingMode)
        form.addRow("Materials Scope:", self.materialsScope)
        form.addRow("Scene Hygiene:", self.stripNamespaces)
        form.addRow("Merge Xform/Shape:", self.mergeXformShape)
        form.addRow("Display Color:", self.exportDisplayColor)

    # Extract as kwargs for exporter
    def to_kwargs(self) -> dict:
        return dict(
            default_mesh_scheme=self.meshScheme.currentText(),
            export_skels=self.skelsMode.currentText(),
            export_skins=self.skinsMode.currentText(),
            shading_mode=self.shadingMode.currentText(),
            materials_scope_name=self.materialsScope.text().strip() or "materials",
            strip_namespaces=self.stripNamespaces.isChecked(),
            merge_transform_and_shape=self.mergeXformShape.isChecked(),
            export_display_color=self.exportDisplayColor.isChecked(),
        )


class RestTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)
        self.outPath = PathField("Output:")
        self.exportBlendshapes = QtWidgets.QCheckBox("Export BlendShapes")
        self.exportBlendshapes.setChecked(True)

        self.common = ExportOptionsWidget("Common Options")

        self.btn = QtWidgets.QPushButton("Export REST (UsdSkel)")
        self.btn.setMinimumHeight(32)

        v.addWidget(self.outPath)
        v.addWidget(self.exportBlendshapes)
        v.addWidget(self.common)
        v.addStretch(1)
        v.addWidget(self.btn)


class AnimTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)
        self.outPath = PathField("Output:")

        mn, mx = _playback_range()
        row = QtWidgets.QHBoxLayout()
        self.startSpin = LabeledSpin("Start:", mn, -100000, 100000)
        self.endSpin = LabeledSpin("End:", mx, -100000, 100000)
        self.samplesSpin = LabeledSpin("Samples/Frame:", 1, 1, 8)
        row.addWidget(self.startSpin)
        row.addWidget(self.endSpin)
        row.addWidget(self.samplesSpin)

        self.includeBlend = QtWidgets.QCheckBox("Include BlendShape Channel Animation")
        self.includeBlend.setChecked(True)
        self.eulerFilter = QtWidgets.QCheckBox("Euler Filter Rotations")
        self.eulerFilter.setChecked(True)

        # Chunking + clips
        self.chunkBox = QtWidgets.QGroupBox("Chunked Export + Value Clips (optional)")
        form = QtWidgets.QFormLayout(self.chunkBox)
        self.enableChunk = QtWidgets.QCheckBox("Enable Chunked Export")
        self.chunkSizeSpin = QtWidgets.QSpinBox()
        self.chunkSizeSpin.setRange(5, 100000)
        self.chunkSizeSpin.setValue(200)
        self.clipsDir = PathField("Clips Dir:", mode="save")
        self.clipsDir.label.setText("Clips Dir:")
        self.clipsDir.btn.setText("📁")
        self.manifestPath = PathField("Manifest .usda:", mode="save")
        self.skelRootEdit = QtWidgets.QLineEdit("/charTiger")
        form.addRow(self.enableChunk)
        form.addRow("Chunk Size (frames):", self.chunkSizeSpin)
        form.addRow(self.clipsDir)
        form.addRow("Skel Root Path:", self.skelRootEdit)
        form.addRow(self.manifestPath)

        self.common = ExportOptionsWidget("Common Options")

        btnRow = QtWidgets.QHBoxLayout()
        self.btnExport = QtWidgets.QPushButton("Export ANIM (UsdSkelAnimation)")
        self.btnExport.setMinimumHeight(32)
        self.btnExportClips = QtWidgets.QPushButton("Export ANIM as Clips + Build Manifest")
        self.btnExportClips.setMinimumHeight(32)
        btnRow.addWidget(self.btnExport)
        btnRow.addWidget(self.btnExportClips)

        v.addWidget(self.outPath)
        v.addLayout(row)
        v.addWidget(self.includeBlend)
        v.addWidget(self.eulerFilter)
        v.addWidget(self.chunkBox)
        v.addWidget(self.common)
        v.addStretch(1)
        v.addLayout(btnRow)


# --------------------------------------------------------------------------------------
# Main Dockable Widget
# --------------------------------------------------------------------------------------
class RigXUsdSkelExportUI(MayaQWidgetDockableMixin, QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rigxUsdSkelExportUI")
        self.setWindowTitle("RigX — UsdSkel Export")
        self.resize(720, 540)

        self.tabs = QtWidgets.QTabWidget()
        self.restTab = RestTab()
        self.animTab = AnimTab()
        self.tabs.addTab(self.restTab, "REST (rig)")
        self.tabs.addTab(self.animTab, "ANIM (shot)")

        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.tabs)

        self._wire_signals()
        self._restore_settings()

    # --------------------- Settings ---------------------
    def _restore_settings(self):
        s = _qsettings()
        self.tabs.setCurrentIndex(s.value("tabs/index", 0, int))

        # REST
        self.restTab.outPath.setText(s.value("rest/out", "", str))
        self.restTab.exportBlendshapes.setChecked(s.value("rest/exportBS", True, bool))
        self._apply_common_from_settings(self.restTab.common, prefix="common/")

        # ANIM
        self.animTab.outPath.setText(s.value("anim/out", "", str))
        # start/end default to playback range when empty
        mn, mx = _playback_range()
        self.animTab.startSpin.setValue(s.value("anim/start", mn, int))
        self.animTab.endSpin.setValue(s.value("anim/end", mx, int))
        self.animTab.samplesSpin.setValue(s.value("anim/samples", 1, int))
        self.animTab.includeBlend.setChecked(s.value("anim/includeBS", True, bool))
        self.animTab.eulerFilter.setChecked(s.value("anim/eulerFilter", True, bool))
        self.animTab.enableChunk.setChecked(s.value("anim/chunk/enabled", False, bool))
        self.animTab.chunkSizeSpin.setValue(s.value("anim/chunk/size", 200, int))
        self.animTab.clipsDir.setText(s.value("anim/chunk/dir", "", str))
        self.animTab.skelRootEdit.setText(s.value("anim/chunk/skelRoot", "/charTiger", str))
        self.animTab.manifestPath.setText(s.value("anim/chunk/manifest", "", str))
        self._apply_common_from_settings(self.animTab.common, prefix="common/")

    def _apply_common_from_settings(self, common: ExportOptionsWidget, prefix: str):
        s = _qsettings()
        # mesh scheme
        ms = s.value(prefix + "meshScheme", "catmullClark", str)
        i = common.meshScheme.findText(ms)
        common.meshScheme.setCurrentIndex(max(i, 0))
        # skels/skins
        sm = s.value(prefix + "skelsMode", "auto", str)
        i = common.skelsMode.findText(sm)
        common.skelsMode.setCurrentIndex(max(i, 0))
        dm = s.value(prefix + "skinsMode", "auto", str)
        i = common.skinsMode.findText(dm)
        common.skinsMode.setCurrentIndex(max(i, 0))
        # shading
        sh = s.value(prefix + "shadingMode", "useRegistry", str)
        i = common.shadingMode.findText(sh)
        common.shadingMode.setCurrentIndex(max(i, 0))
        common.materialsScope.setText(s.value(prefix + "materialsScope", "materials", str))
        common.stripNamespaces.setChecked(s.value(prefix + "stripNS", True, bool))
        common.mergeXformShape.setChecked(s.value(prefix + "merge", True, bool))
        common.exportDisplayColor.setChecked(s.value(prefix + "dispColor", True, bool))

    def _save_settings(self):
        s = _qsettings()
        s.setValue("tabs/index", self.tabs.currentIndex())

        # REST
        s.setValue("rest/out", self.restTab.outPath.text())
        s.setValue("rest/exportBS", self.restTab.exportBlendshapes.isChecked())

        # ANIM
        s.setValue("anim/out", self.animTab.outPath.text())
        s.setValue("anim/start", self.animTab.startSpin.value())
        s.setValue("anim/end", self.animTab.endSpin.value())
        s.setValue("anim/samples", self.animTab.samplesSpin.value())
        s.setValue("anim/includeBS", self.animTab.includeBlend.isChecked())
        s.setValue("anim/eulerFilter", self.animTab.eulerFilter.isChecked())
        s.setValue("anim/chunk/enabled", self.animTab.enableChunk.isChecked())
        s.setValue("anim/chunk/size", self.animTab.chunkSizeSpin.value())
        s.setValue("anim/chunk/dir", self.animTab.clipsDir.text())
        s.setValue("anim/chunk/skelRoot", self.animTab.skelRootEdit.text())
        s.setValue("anim/chunk/manifest", self.animTab.manifestPath.text())

        # Common (shared keyspace)
        c = self.restTab.common
        s.setValue("common/meshScheme", c.meshScheme.currentText())
        s.setValue("common/skelsMode", c.skelsMode.currentText())
        s.setValue("common/skinsMode", c.skinsMode.currentText())
        s.setValue("common/shadingMode", c.shadingMode.currentText())
        s.setValue("common/materialsScope", c.materialsScope.text())
        s.setValue("common/stripNS", c.stripNamespaces.isChecked())
        s.setValue("common/merge", c.mergeXformShape.isChecked())
        s.setValue("common/dispColor", c.exportDisplayColor.isChecked())

    # --------------------- Wiring ---------------------
    def _wire_signals(self):
        self.restTab.btn.clicked.connect(self._do_export_rest)
        self.animTab.btnExport.clicked.connect(self._do_export_anim_single)
        self.animTab.btnExportClips.clicked.connect(self._do_export_anim_clips)

    # --------------------- Export Actions ---------------------
    def _gather_common_kwargs(self, common: ExportOptionsWidget) -> dict:
        return common.to_kwargs()

    def _ensure_selection(self):
        sel = cmds.ls(sl=True)
        if not sel:
            raise RuntimeError("Nothing selected. Select your character root(s) and try again.")

    def _do_export_rest(self):
        try:
            self._ensure_selection()
            out_path = self.restTab.outPath.text()
            if not out_path:
                raise RuntimeError("Please set an output path for REST export.")
            kw = self._gather_common_kwargs(self.restTab.common)
            kw.update(dict(export_blendshapes=self.restTab.exportBlendshapes.isChecked()))
            skelx.export_rest(out_path, **kw)
            QtWidgets.QMessageBox.information(self, "UsdSkel REST", f"Exported to:\n{out_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "REST Export Failed", str(e))
        finally:
            self._save_settings()

    def _do_export_anim_single(self):
        try:
            self._ensure_selection()
            out_path = self.animTab.outPath.text()
            if not out_path:
                raise RuntimeError("Please set an output path for ANIM export.")
            start = self.animTab.startSpin.value()
            end = self.animTab.endSpin.value()
            if start > end:
                raise RuntimeError("Start frame must be <= End frame.")
            kw = self._gather_common_kwargs(self.animTab.common)
            kw.update(dict(
                start=start,
                end=end,
                samples_per_frame=self.animTab.samplesSpin.value(),
                include_blendshapes=self.animTab.includeBlend.isChecked(),
                euler_filter=self.animTab.eulerFilter.isChecked(),
            ))
            skelx.export_anim(out_path, **kw)
            QtWidgets.QMessageBox.information(self, "UsdSkel ANIM", f"Exported to:\n{out_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "ANIM Export Failed", str(e))
        finally:
            self._save_settings()

    def _do_export_anim_clips(self):
        try:
            self._ensure_selection()
            if not self.animTab.enableChunk.isChecked():
                raise RuntimeError("Enable Chunked Export in the section above or use 'Export ANIM'.")

            start = self.animTab.startSpin.value()
            end = self.animTab.endSpin.value()
            if start > end:
                raise RuntimeError("Start frame must be <= End frame.")
            chunk = int(self.animTab.chunkSizeSpin.value())
            clips_dir = self.animTab.clipsDir.text().strip()
            if not clips_dir:
                raise RuntimeError("Please set a Clips Dir for chunked export.")
            os.makedirs(clips_dir, exist_ok=True)

            # Base filename seed from the single-file output field
            base = os.path.splitext(os.path.basename(self.animTab.outPath.text().strip() or "anim.usdc"))[0]
            if not base:
                base = "anim"

            # Export each chunk using the publisher
            kw_common = self._gather_common_kwargs(self.animTab.common)
            kw_common.update(dict(
                samples_per_frame=self.animTab.samplesSpin.value(),
                include_blendshapes=self.animTab.includeBlend.isChecked(),
                euler_filter=self.animTab.eulerFilter.isChecked(),
            ))

            ranges: List[Tuple[int, int]] = []
            clip_paths: List[str] = []

            s = start
            while s <= end:
                e = min(s + chunk - 1, end)
                clip_name = f"{base}_{s:04d}_{e:04d}.usdc"
                clip_path = os.path.join(clips_dir, clip_name)
                skelx.export_anim(
                    clip_path,
                    start=s,
                    end=e,
                    **kw_common
                )
                ranges.append((s, e))
                clip_paths.append(clip_name)  # relative within the manifest folder
                s = e + 1

            # Build manifest next to clips_dir unless user provided a custom path
            manifest_path = self.animTab.manifestPath.text().strip()
            if not manifest_path:
                manifest_path = os.path.join(clips_dir, f"{base}_manifest.usda")

            # Use POSIX-style relative paths inside the manifest
            rel_assets = [os.path.basename(p).replace("\\", "/") for p in clip_paths]
            skel_root = self.animTab.skelRootEdit.text().strip() or "/SkelRoot"
            skelx.build_value_clip_manifest_usda(
                manifest_path,
                skel_root_path=skel_root,
                clip_asset_paths=rel_assets,
                clip_ranges=ranges,
            )

            QtWidgets.QMessageBox.information(
                self,
                "UsdSkel Clips",
                f"Exported {len(ranges)} clips to:\n{clips_dir}\n\nManifest:\n{manifest_path}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Chunked Export Failed", str(e))
        finally:
            self._save_settings()

    # --------------------- Dock/close ---------------------
    def dockCloseEventTriggered(self):  # Maya calls this on close of workspaceControl
        self._save_settings()


# --------------------------------------------------------------------------------------
# Launcher helpers
# --------------------------------------------------------------------------------------
def launch(dock: bool = True):
    """Create and (optionally) dock the UI in Maya."""
    if dock:
        # Unique UI name for workspaceControl
        ui = RigXUsdSkelExportUI()
        ui.show(dockable=True, area='right', floating=False)
        return ui
    else:
        ui = RigXUsdSkelExportUI()
        ui.show()
        return ui
