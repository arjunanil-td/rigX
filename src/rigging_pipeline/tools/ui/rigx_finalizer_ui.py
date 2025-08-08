import os
import sys
import importlib
import pkgutil

from rigging_pipeline.utils.utils_job import detect_show_from_workspace
from rigging_pipeline.io.rigx_theme import THEME_STYLESHEET

from PySide2 import QtWidgets, QtCore
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance


def maya_main_window():
    """
    Returns Maya's main window as a QtWidgets.QWidget.
    """
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def discover_finalizers():
    """
    Return a tuple of two dicts:

      (  { module_name: finalize_func, ... },
         { display_name: finalize_func, ... }  )

    - module_name    e.g. "charA_finalize"
    - display_name   e.g. "charA" (module_name without "_finalize")
    """
    show_name = os.environ.get("RIGX_SHOW") or detect_show_from_workspace()
    if not show_name:
        raise RuntimeError("No show detected; cannot discover finalizers.")

    import rigging_pipeline
    rig_pkg_dir = os.path.dirname(rigging_pipeline.__file__)

    repo_root = os.path.abspath(os.path.join(rig_pkg_dir, "..", ".."))

    finalize_dir = os.path.join(repo_root, "shows", show_name, "finalize")
    if not os.path.isdir(finalize_dir):
        raise RuntimeError(f"No finalize folder found at:\n  {finalize_dir}")

    parent_of_shows = os.path.join(repo_root, "shows")
    if parent_of_shows not in sys.path:
        sys.path.insert(0, parent_of_shows)

    by_module = {}
    by_display = {}
    pkg_name = f"{show_name}.finalize"
    for finder, module_name, ispkg in pkgutil.iter_modules([finalize_dir]):
        full_mod = f"{pkg_name}.{module_name}"
        try:
            mod = importlib.import_module(full_mod)
        except ImportError as e:
            print(f"⚠️ Could not import {full_mod}: {e}")
            continue

        if hasattr(mod, "finalize"):
            func = mod.finalize
            by_module[module_name] = func

            if module_name.lower().endswith("_finalize"):
                display = module_name[: -len("_finalize")]
            else:
                display = module_name
            by_display[display] = func

    return by_module, by_display


class FinalizerWindow(QtWidgets.QDialog):
    """
    A dockable Maya dialog that lists show-specific finalize scripts (by asset name),
    allows typing an optional asset_name, and runs the chosen finalize().
    """

    WINDOW_TITLE = "Rig Finalizer"

    def __init__(self, parent=None):
        super(FinalizerWindow, self).__init__(parent or maya_main_window())

        app = QtWidgets.QApplication.instance()
        app.setStyleSheet(THEME_STYLESHEET)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(350)

        try:
            self.by_module, self.by_display = discover_finalizers()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            self.close()
            return

        self._build_ui()
        self._populate_list()

    def _build_ui(self):
        """
        Construct the dialog layout:
         - QLabel
         - QListWidget (showing only the display_name keys)
         - QLineEdit for an optional asset name
         - “Finalize” + “Close” buttons in an HBox
        """
        layout = QtWidgets.QVBoxLayout(self)

        lbl = QtWidgets.QLabel("Select an asset to finalize:")
        layout.addWidget(lbl)

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)

        lbl2 = QtWidgets.QLabel("Asset name (optional):")
        layout.addWidget(lbl2)

        self.asset_line = QtWidgets.QLineEdit()
        layout.addWidget(self.asset_line)

        btn_layout = QtWidgets.QHBoxLayout()
        self.finalize_btn = QtWidgets.QPushButton("Finalize")
        self.finalize_btn.clicked.connect(self._on_finalize)
        btn_layout.addWidget(self.finalize_btn)

        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _populate_list(self):
        """
        Fill the QListWidget with display names (e.g. "charA", "charB", etc.).
        """
        for display_name in sorted(self.by_display.keys()):
            item = QtWidgets.QListWidgetItem(display_name)
            self.list_widget.addItem(item)

    def _on_finalize(self):
        """
        Called when “Finalize” is pressed. Retrieves the selected display_name,
        looks up the corresponding function, then runs it with the optional text.
        """
        selected = self.list_widget.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "No selection", "Please select an asset to finalize.")
            return

        display_key = selected[0].text()
        func = self.by_display.get(display_key)
        if not func:
            QtWidgets.QMessageBox.critical(self, "Error", f"Cannot find finalizer for '{display_key}'.")
            return

        asset_name = self.asset_line.text().strip() or None

        try:
            func(asset_name)
            QtWidgets.QMessageBox.information(self, "Success", f"Ran finalizer for: {display_key}")
        except Exception as e:
            # Print traceback to Script Editor and show a message box
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, "Finalize Failed", str(e))


def show_finalizer_window():
    """
    Create (or raise) the FinalizerWindow in Maya. Bind this to a shelf button.
    This version forces the window to be shown, raised, and activated.
    """
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, FinalizerWindow):
            w.show()
            w.raise_()
            w.activateWindow()
            return w

    win = FinalizerWindow()
    win.setParent(maya_main_window(), QtCore.Qt.Window)
    win.setWindowFlags(QtCore.Qt.Window)
    win.show()
    win.raise_()
    win.activateWindow()

    QtWidgets.QApplication.processEvents()
    return win
