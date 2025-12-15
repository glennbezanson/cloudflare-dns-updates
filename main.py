#!/usr/bin/env python3
"""
Cloudflare DNS Manager with Claude AI Review

A GUI application for managing Cloudflare DNS records with:
- Secure encrypted credential storage
- Full DNS record management (A, AAAA, CNAME, MX, TXT, etc.)
- Claude AI integration for change review
- Audit logging
- Zone backup/restore
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui import MainWindow
from gui.styles import get_stylesheet


def main():
    """Main entry point."""
    # Enable High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Cloudflare DNS Manager")

    # Set application style
    app.setStyle("Fusion")

    # Apply application styling
    app.setStyleSheet(get_stylesheet())

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
