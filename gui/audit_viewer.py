"""Audit log viewer dialog."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QLineEdit, QHeaderView, QFileDialog,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from datetime import datetime


class AuditViewerDialog(QDialog):
    """Dialog for viewing the audit log."""

    def __init__(self, parent=None, audit_logger=None, zones: list = None):
        super().__init__(parent)
        self.audit_logger = audit_logger
        self.zones = zones or []

        self.setWindowTitle("Audit Log")
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)
        self.setup_ui()
        self.load_entries()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("DNS Change Audit Log")
        header.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(header)

        # Filters
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Domain:"))
        self.domain_filter = QComboBox()
        self.domain_filter.addItem("All Domains")
        for zone in self.zones:
            self.domain_filter.addItem(zone.get("name", ""))
        self.domain_filter.currentTextChanged.connect(self.load_entries)
        filter_layout.addWidget(self.domain_filter)

        filter_layout.addWidget(QLabel("Action:"))
        self.action_filter = QComboBox()
        self.action_filter.addItems([
            "All Actions", "add", "edit", "delete", "batch", "backup", "restore"
        ])
        self.action_filter.currentTextChanged.connect(self.load_entries)
        filter_layout.addWidget(self.action_filter)

        filter_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_entries)
        filter_layout.addWidget(self.refresh_btn)

        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Action", "Domain", "Record Type", "Record Name", "Details"
        ])

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export Log")
        self.export_btn.clicked.connect(self.export_log)
        btn_layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def load_entries(self):
        """Load audit log entries."""
        if not self.audit_logger:
            return

        domain = self.domain_filter.currentText()
        if domain == "All Domains":
            domain = None

        action = self.action_filter.currentText()
        if action == "All Actions":
            action = None

        entries = self.audit_logger.get_entries(limit=500, domain=domain, action=action)
        self.populate_table(entries)

    def populate_table(self, entries: list):
        """Populate the table with entries."""
        self.table.setRowCount(0)

        for entry in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Timestamp
            timestamp = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            self.table.setItem(row, 0, QTableWidgetItem(timestamp))

            # Action
            action = entry.get("action", "")
            action_item = QTableWidgetItem(action)
            if action == "add":
                action_item.setForeground(Qt.GlobalColor.darkGreen)
            elif action == "delete":
                action_item.setForeground(Qt.GlobalColor.darkRed)
            elif action == "edit":
                action_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(row, 1, action_item)

            # Domain
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("domain", "")))

            # Record info
            record = entry.get("record", {})
            self.table.setItem(row, 3, QTableWidgetItem(record.get("type", "")))
            self.table.setItem(row, 4, QTableWidgetItem(record.get("name", "")))

            # Details
            details = []
            if record.get("content"):
                details.append(f"Content: {record['content'][:50]}...")
            if entry.get("claude_review"):
                review = entry["claude_review"]
                details.append(f"Claude: {review.get('assessment', 'N/A')}")
            self.table.setItem(row, 5, QTableWidgetItem(" | ".join(details)))

    def export_log(self):
        """Export the audit log to a file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Audit Log",
            f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )

        if not filepath:
            return

        domain = self.domain_filter.currentText()
        if domain == "All Domains":
            domain = None

        from pathlib import Path
        success, message = self.audit_logger.export_log(Path(filepath), domain)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", message)

    def clear_log(self):
        """Clear the audit log."""
        reply = QMessageBox.question(
            self, "Clear Audit Log",
            "Are you sure you want to clear the entire audit log?\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.audit_logger.clear_log()
            if success:
                self.load_entries()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Error", message)
