"""Application styles for PyQt6."""

# Application Theme Colors
PRIMARY_BLUE = "#486D87"    # Primary - headers, nav, primary buttons
ACCENT_GREEN = "#C6D219"    # Accent - success states, CTAs
DARK_TEAL = "#4C5351"       # Primary text
OLIVE_GRAY = "#7B7D72"      # Secondary text, borders
COOL_GRAY = "#F2F3F4"       # Backgrounds
WHITE = "#FFFFFF"

# Status Colors
SUCCESS_GREEN = "#28a745"   # Green for success
WARNING_YELLOW = "#E6A817"  # Warning states
ERROR_RED = "#C44536"       # Error states

# Derived Colors
PRIMARY_BLUE_LIGHT = "#5a7f99"  # Hover state for primary
PRIMARY_BLUE_DARK = "#3a5a70"   # Pressed state for primary
ACCENT_GREEN_DARK = "#a8b515"   # Hover state for accent


def get_stylesheet() -> str:
    """Return the complete application stylesheet."""
    return f"""
    /* ===== Global Styles ===== */
    QMainWindow, QDialog {{
        background-color: {COOL_GRAY};
        color: {DARK_TEAL};
    }}

    QWidget {{
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 8pt;
        color: {DARK_TEAL};
    }}

    /* ===== Menu Bar ===== */
    QMenuBar {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
        padding: 3px;
        spacing: 2px;
        font-size: 8pt;
    }}

    QMenuBar::item {{
        background-color: transparent;
        padding: 4px 10px;
        border-radius: 3px;
        color: {WHITE};
    }}

    QMenuBar::item:selected {{
        background-color: {PRIMARY_BLUE_LIGHT};
    }}

    QMenuBar::item:pressed {{
        background-color: {PRIMARY_BLUE_DARK};
    }}

    QMenu {{
        background-color: {WHITE};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 3px;
        padding: 3px;
    }}

    QMenu::item {{
        padding: 6px 20px;
        border-radius: 3px;
        color: {DARK_TEAL};
    }}

    QMenu::item:selected {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
    }}

    /* ===== Toolbar ===== */
    QToolBar {{
        background-color: {WHITE};
        border-bottom: 1px solid {OLIVE_GRAY};
        spacing: 6px;
        padding: 3px 6px;
    }}

    QToolBar::separator {{
        background-color: {OLIVE_GRAY};
        width: 1px;
        margin: 3px 6px;
    }}

    QToolButton {{
        background-color: transparent;
        border: none;
        border-radius: 3px;
        padding: 4px 10px;
        color: {DARK_TEAL};
    }}

    QToolButton:hover {{
        background-color: {COOL_GRAY};
    }}

    QToolButton:pressed {{
        background-color: {OLIVE_GRAY};
    }}

    /* ===== Buttons ===== */
    QPushButton {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
        border: none;
        border-radius: 3px;
        padding: 6px 12px;
        font-weight: bold;
        min-width: 60px;
    }}

    QPushButton:hover {{
        background-color: {PRIMARY_BLUE_LIGHT};
    }}

    QPushButton:pressed {{
        background-color: {PRIMARY_BLUE_DARK};
    }}

    QPushButton:disabled {{
        background-color: {OLIVE_GRAY};
        color: {COOL_GRAY};
    }}

    /* Small inline buttons (for table cells) */
    QTableWidget QPushButton {{
        background-color: {COOL_GRAY};
        color: {DARK_TEAL};
        border: 1px solid {OLIVE_GRAY};
        padding: 3px 8px;
        min-width: 40px;
        font-weight: normal;
    }}

    QTableWidget QPushButton:hover {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
        border-color: {PRIMARY_BLUE};
    }}

    /* Accent/Success Button */
    QPushButton[accent="true"], QPushButton#pasteRequestBtn {{
        background-color: {ACCENT_GREEN};
        color: {DARK_TEAL};
    }}

    QPushButton[accent="true"]:hover, QPushButton#pasteRequestBtn:hover {{
        background-color: {ACCENT_GREEN_DARK};
    }}

    /* Danger Button */
    QPushButton[danger="true"] {{
        background-color: {ERROR_RED};
        color: {WHITE};
    }}

    QPushButton[danger="true"]:hover {{
        background-color: #b33d2f;
    }}

    /* Secondary Button (outline style) */
    QPushButton[secondary="true"] {{
        background-color: transparent;
        color: {PRIMARY_BLUE};
        border: 1px solid {PRIMARY_BLUE};
    }}

    QPushButton[secondary="true"]:hover {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
    }}

    /* ===== Tables ===== */
    QTableWidget, QTableView {{
        background-color: {WHITE};
        alternate-background-color: {COOL_GRAY};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 3px;
        gridline-color: {OLIVE_GRAY};
        selection-background-color: {PRIMARY_BLUE};
        selection-color: {WHITE};
    }}

    QTableWidget::item, QTableView::item {{
        padding: 6px;
        color: {DARK_TEAL};
    }}

    QHeaderView::section {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
        padding: 6px;
        border: none;
        font-weight: bold;
    }}

    QHeaderView::section:hover {{
        background-color: {PRIMARY_BLUE_LIGHT};
    }}

    /* ===== Input Fields ===== */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
        background-color: {WHITE};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 3px;
        padding: 6px;
        color: {DARK_TEAL};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QSpinBox:focus, QComboBox:focus {{
        border: 2px solid {PRIMARY_BLUE};
    }}

    QLineEdit:disabled, QTextEdit:disabled {{
        background-color: {COOL_GRAY};
        color: {OLIVE_GRAY};
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 6px;
    }}

    QComboBox::down-arrow {{
        width: 10px;
        height: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {WHITE};
        border: 1px solid {OLIVE_GRAY};
        selection-background-color: {PRIMARY_BLUE};
        selection-color: {WHITE};
    }}

    /* ===== Group Boxes ===== */
    QGroupBox {{
        background-color: {WHITE};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 6px;
        color: {PRIMARY_BLUE};
        background-color: {WHITE};
    }}

    /* ===== Frames ===== */
    QFrame[frameShape="4"], QFrame[frameShape="5"] {{
        background-color: {WHITE};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 3px;
    }}

    /* ===== List Widget ===== */
    QListWidget {{
        background-color: {WHITE};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 3px;
        padding: 3px;
    }}

    QListWidget::item {{
        padding: 6px;
        border-radius: 3px;
        color: {DARK_TEAL};
    }}

    QListWidget::item:selected {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
    }}

    QListWidget::item:hover {{
        background-color: {COOL_GRAY};
    }}

    /* ===== Tab Widget ===== */
    QTabWidget::pane {{
        background-color: {WHITE};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 3px;
        padding: 6px;
    }}

    QTabBar::tab {{
        background-color: {COOL_GRAY};
        border: 1px solid {OLIVE_GRAY};
        border-bottom: none;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
        padding: 6px 12px;
        margin-right: 2px;
        color: {DARK_TEAL};
    }}

    QTabBar::tab:selected {{
        background-color: {WHITE};
        border-bottom-color: {WHITE};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {PRIMARY_BLUE_LIGHT};
        color: {WHITE};
    }}

    /* ===== Splitter ===== */
    QSplitter::handle {{
        background-color: {OLIVE_GRAY};
        width: 2px;
    }}

    QSplitter::handle:hover {{
        background-color: {PRIMARY_BLUE};
    }}

    /* ===== Progress Bar ===== */
    QProgressBar {{
        background-color: {COOL_GRAY};
        border: 1px solid {OLIVE_GRAY};
        border-radius: 3px;
        text-align: center;
        height: 16px;
    }}

    QProgressBar::chunk {{
        background-color: {ACCENT_GREEN};
        border-radius: 2px;
    }}

    /* ===== Scroll Bar ===== */
    QScrollBar:vertical {{
        background-color: {COOL_GRAY};
        width: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {OLIVE_GRAY};
        border-radius: 4px;
        min-height: 24px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {PRIMARY_BLUE};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: {COOL_GRAY};
        height: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {OLIVE_GRAY};
        border-radius: 4px;
        min-width: 24px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {PRIMARY_BLUE};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ===== Status Bar ===== */
    QStatusBar {{
        background-color: {WHITE};
        border-top: 1px solid {OLIVE_GRAY};
        color: {DARK_TEAL};
        padding: 3px;
    }}

    /* ===== Labels ===== */
    QLabel {{
        color: {DARK_TEAL};
    }}

    QLabel[heading="true"] {{
        font-size: 12pt;
        font-weight: bold;
        color: {PRIMARY_BLUE};
    }}

    QLabel[subheading="true"] {{
        font-size: 9pt;
        color: {OLIVE_GRAY};
    }}

    /* ===== Check Box ===== */
    QCheckBox {{
        spacing: 6px;
        color: {DARK_TEAL};
    }}

    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 2px solid {OLIVE_GRAY};
        border-radius: 3px;
        background-color: {WHITE};
    }}

    QCheckBox::indicator:checked {{
        background-color: {PRIMARY_BLUE};
        border-color: {PRIMARY_BLUE};
    }}

    QCheckBox::indicator:hover {{
        border-color: {PRIMARY_BLUE};
    }}

    /* ===== Radio Button ===== */
    QRadioButton {{
        spacing: 6px;
        color: {DARK_TEAL};
    }}

    QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border: 2px solid {OLIVE_GRAY};
        border-radius: 7px;
        background-color: {WHITE};
    }}

    QRadioButton::indicator:checked {{
        background-color: {PRIMARY_BLUE};
        border-color: {PRIMARY_BLUE};
    }}

    QRadioButton::indicator:hover {{
        border-color: {PRIMARY_BLUE};
    }}

    /* ===== Message Box ===== */
    QMessageBox {{
        background-color: {WHITE};
    }}

    QMessageBox QLabel {{
        color: {DARK_TEAL};
    }}

    QMessageBox QPushButton {{
        min-width: 70px;
    }}

    /* ===== Tooltips ===== */
    QToolTip {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
        border: none;
        padding: 6px;
        border-radius: 3px;
    }}

    /* ===== Input Dialog ===== */
    QInputDialog {{
        background-color: {WHITE};
    }}

    QInputDialog QLabel {{
        color: {DARK_TEAL};
    }}

    QInputDialog QLineEdit {{
        color: {DARK_TEAL};
    }}

    /* ===== Spin Box ===== */
    QSpinBox {{
        color: {DARK_TEAL};
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {COOL_GRAY};
        border: none;
        width: 16px;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {PRIMARY_BLUE_LIGHT};
    }}
    """


def get_validation_styles() -> dict:
    """Return styles for validation status indicators."""
    return {
        "success": f"background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; border: 1px solid {SUCCESS_GREEN};",
        "warning": f"background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; border: 1px solid {WARNING_YELLOW};",
        "error": f"background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; border: 1px solid {ERROR_RED};",
        "info": f"background-color: #e3f2fd; color: {PRIMARY_BLUE}; padding: 10px; border-radius: 5px; border: 1px solid {PRIMARY_BLUE};"
    }
