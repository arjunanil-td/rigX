import os
from PySide2 import QtWidgets, QtCore, QtGui

class Banner(QtWidgets.QFrame):

    def __init__(self, title, icon_filename=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1b4332, stop:0.5 #2d6a4f, stop:1 #40916c);
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-size: 18pt;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#icon {
                padding-left: 15px;
                padding-top: 5px;
                background: transparent;
            }
            QLabel#title {
                padding-left: 10px;
            }
        """)

        banner_layout = QtWidgets.QHBoxLayout(self)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        banner_layout.setSpacing(10)

        if icon_filename:
            # Try multiple icon paths
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
            icon_paths = [
                # RigX project icons folder (config/icons at repo root)
                os.path.join(repo_root, "config", "icons", icon_filename),
                # RigX project icons folder (from io folder: io -> rigging_pipeline -> icons)
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", icon_filename),
                # RigX tools icons folder (from io folder: io -> rigging_pipeline -> tools -> icons)
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools", "icons", icon_filename),
                # Maya preferences icons folders (common versions)
                os.path.join(os.path.expanduser("~"), "Documents", "maya", "2024", "prefs", "icons", icon_filename),
                os.path.join(os.path.expanduser("~"), "Documents", "maya", "2023", "prefs", "icons", icon_filename),
                os.path.join(os.path.expanduser("~"), "Documents", "maya", "2022", "prefs", "icons", icon_filename),
            ]
            
            icon_found = False
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    icon_label = QtWidgets.QLabel()
                    icon_label.setObjectName("icon")
                    icon_pixmap = QtGui.QPixmap(icon_path).scaled(40, 40, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                    icon_label.setPixmap(icon_pixmap)
                    banner_layout.addWidget(icon_label)
                    icon_found = True
                    break
            
            if not icon_found:
                print(f"Warning: Icon '{icon_filename}' not found in any of these paths:")
                for path in icon_paths:
                    print(f"  - {path}")
                banner_layout.addSpacing(15)
        else:
            banner_layout.addSpacing(15)

        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("title")
        banner_layout.addWidget(title_label)

        banner_layout.addStretch() 