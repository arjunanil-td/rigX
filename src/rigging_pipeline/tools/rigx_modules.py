from __future__ import annotations

try:
    import maya.cmds as cmds  # type: ignore
    MAYA_AVAILABLE = True
except Exception:
    MAYA_AVAILABLE = False

from PySide2 import QtWidgets  # type: ignore

from .ui.rigx_modules_ui import RigXModulesUI


class UIManager:
    """Track and manage a single instance per window name inside Maya."""

    _open_windows: dict[str, QtWidgets.QWidget] = {}

    @classmethod
    def register_window(cls, window_name: str, window: QtWidgets.QWidget) -> None:
        cls._open_windows[window_name] = window

    @classmethod
    def close_existing_window(cls, window_name: str) -> None:
        if window_name in cls._open_windows:
            try:
                win = cls._open_windows[window_name]
                if win is not None:
                    win.close()
            except Exception:
                pass
            finally:
                del cls._open_windows[window_name]


class RigXModules:
    """Controller for the RigX Modules tool."""

    def __init__(self) -> None:
        self.ui: RigXModulesUI | None = None

    def show_ui(self) -> None:
        UIManager.close_existing_window("RigXModules")
        self.ui = RigXModulesUI()
        UIManager.register_window("RigXModules", self.ui)
        self.ui.show()
        self.ui.raise_()
        self.ui.activateWindow()


def launch_modules():
    """Launch the RigX Modules UI."""
    try:
        tool = RigXModules()
        tool.show_ui()
        print("✅ RigX Modules launched successfully!")
        return tool
    except Exception as exc:  # pragma: no cover - Maya UI runtime specific
        print(f"❌ Error launching RigX Modules: {exc}")
        return None


