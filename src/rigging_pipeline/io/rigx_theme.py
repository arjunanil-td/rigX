# theme.py
THEME_STYLESHEET = r"""
    QDialog { background-color: #2d2d2d; color: #ffffff; }
    QGroupBox { border: 1px solid #555555; border-radius: 6px; margin-top: 10px; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
    QLabel, QRadioButton, QCheckBox { color: #dddddd; }
    QPushButton { background-color: #4a4a4a; color: #ffffff; border: none; padding: 6px; border-radius: 4px; }
    QPushButton:hover { background-color: #6a6a6a; }
    QPushButton:pressed { background-color: #3a3a3a; }
    QListWidget, QLineEdit, QSpinBox, QComboBox { background-color: #3a3a3a; color: #ffffff; border: 1px solid #555555; border-radius: 4px; }
    QScrollBar:vertical { background: #3a3a3a; width:12px; margin: 0; }
    QScrollBar::handle:vertical { background: #5a5a5a; min-height:20px; border-radius:4px; }
    QScrollBar::handle:vertical:hover { background: #7a7a7a; }
"""
