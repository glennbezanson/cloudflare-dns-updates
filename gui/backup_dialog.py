"""Backup and restore dialog."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QGroupBox, QTextEdit, QHeaderView, QMessageBox,
    QAbstractItemView, QFileDialog, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from datetime import datetime
from functools import partial


class BackupDialog(QDialog):
    """Dialog for backup and restore operations."""

    def __init__(self, parent=None, zone_backup=None, cloudflare_client=None,
                 zone_id: str = "", zone_name: str = "", current_records: list = None):
        super().__init__(parent)
        self.zone_backup = zone_backup
        self.cf_client = cloudflare_client
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.current_records = current_records or []

        self.setWindowTitle(f"Backup & Restore - {zone_name}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setup_ui()
        self.load_backups()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Tabs
        self.tabs = QTabWidget()

        # Backup tab
        backup_tab = QWidget()
        backup_layout = QVBoxLayout(backup_tab)

        # Create backup section
        create_group = QGroupBox("Create New Backup")
        create_layout = QVBoxLayout(create_group)

        info_label = QLabel(
            f"Create a backup of all {len(self.current_records)} DNS records "
            f"for {self.zone_name}"
        )
        create_layout.addWidget(info_label)

        btn_row = QHBoxLayout()
        self.create_btn = QPushButton("Create Backup")
        self.create_btn.clicked.connect(self.create_backup)
        btn_row.addWidget(self.create_btn)

        self.export_bind_btn = QPushButton("Export as BIND Zone File")
        self.export_bind_btn.clicked.connect(self.export_bind)
        btn_row.addWidget(self.export_bind_btn)

        btn_row.addStretch()
        create_layout.addLayout(btn_row)

        backup_layout.addWidget(create_group)

        # Existing backups
        existing_group = QGroupBox("Existing Backups")
        existing_layout = QVBoxLayout(existing_group)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels([
            "Filename", "Created", "Records", "Actions"
        ])
        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        existing_layout.addWidget(self.backup_table)

        backup_layout.addWidget(existing_group)
        self.tabs.addTab(backup_tab, "Backup")

        # Restore tab
        restore_tab = QWidget()
        restore_layout = QVBoxLayout(restore_tab)

        restore_info = QLabel(
            "Select a backup from the Backup tab and click 'View' to see its contents, "
            "or 'Compare' to see differences with current records."
        )
        restore_info.setWordWrap(True)
        restore_layout.addWidget(restore_info)

        # Comparison view
        self.compare_text = QTextEdit()
        self.compare_text.setReadOnly(True)
        self.compare_text.setPlaceholderText(
            "Select a backup and click 'View' or 'Compare' to see details..."
        )
        restore_layout.addWidget(self.compare_text)

        self.tabs.addTab(restore_tab, "Compare/Restore")

        layout.addWidget(self.tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def load_backups(self):
        """Load existing backups for this domain."""
        if not self.zone_backup:
            return

        backups = self.zone_backup.list_backups(self.zone_name)
        self.backup_table.setRowCount(0)

        for backup in backups:
            row = self.backup_table.rowCount()
            self.backup_table.insertRow(row)

            filename = backup.get("filename", "")

            # Filename
            self.backup_table.setItem(row, 0, QTableWidgetItem(filename))

            # Created
            created = backup.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created)
                created = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
            self.backup_table.setItem(row, 1, QTableWidgetItem(created))

            # Record count
            self.backup_table.setItem(
                row, 2, QTableWidgetItem(str(backup.get("record_count", 0)))
            )

            # Action buttons - use partial to properly bind filename
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 0, 4, 0)

            view_btn = QPushButton("View")
            view_btn.setFixedWidth(60)
            view_btn.clicked.connect(partial(self.view_backup, filename))
            action_layout.addWidget(view_btn)

            compare_btn = QPushButton("Compare")
            compare_btn.setFixedWidth(70)
            compare_btn.clicked.connect(partial(self.compare_backup, filename))
            action_layout.addWidget(compare_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setFixedWidth(60)
            delete_btn.clicked.connect(partial(self.delete_backup, filename))
            action_layout.addWidget(delete_btn)

            self.backup_table.setCellWidget(row, 3, action_widget)

        self.backup_table.resizeColumnsToContents()

    def create_backup(self):
        """Create a new backup."""
        if not self.zone_backup:
            return

        success, message, filename = self.zone_backup.create_backup(
            self.zone_name,
            self.current_records,
            {"zone_id": self.zone_id}
        )

        if success:
            QMessageBox.information(self, "Success", f"Backup created: {filename}")
            self.load_backups()
        else:
            QMessageBox.warning(self, "Error", message)

    def export_bind(self):
        """Export as BIND zone file."""
        if not self.zone_backup:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export BIND Zone File",
            f"{self.zone_name}.zone",
            "Zone Files (*.zone);;All Files (*)"
        )

        if not filepath:
            return

        try:
            bind_content = self.zone_backup.export_to_bind(
                self.current_records, self.zone_name
            )
            with open(filepath, 'w') as f:
                f.write(bind_content)
            QMessageBox.information(self, "Success", f"Exported to: {filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def view_backup(self, filename: str):
        """View backup contents."""
        if not self.zone_backup:
            return

        success, message, data = self.zone_backup.load_backup(filename)

        if not success:
            QMessageBox.warning(self, "Error", message)
            return

        records = data.get("records", [])

        html = [f"<h3>Backup: {filename}</h3>"]
        html.append(f"<p>Created: {data.get('created_at', 'Unknown')}</p>")
        html.append(f"<p>Records: {len(records)}</p>")
        html.append("<hr>")

        for record in records:
            rtype = record.get("type", "")
            name = record.get("name", "")
            content = record.get("content", "")
            html.append(f"<p><b>{rtype}</b> {name} → {content}</p>")

        self.compare_text.setHtml("".join(html))
        # Switch to Compare/Restore tab to show results
        self.tabs.setCurrentIndex(1)

    def compare_backup(self, filename: str):
        """Compare backup with current records."""
        if not self.zone_backup:
            return

        success, message, data = self.zone_backup.load_backup(filename)

        if not success:
            QMessageBox.warning(self, "Error", message)
            return

        backup_records = data.get("records", [])
        comparison = self.zone_backup.compare_backup(backup_records, self.current_records)

        html = [f"<h3>Comparison: {filename} vs Current</h3>"]

        summary = comparison.get("summary", {})
        html.append(f"<p>Added since backup: {summary.get('added_count', 0)}</p>")
        html.append(f"<p>Removed since backup: {summary.get('removed_count', 0)}</p>")
        html.append(f"<p>Modified since backup: {summary.get('modified_count', 0)}</p>")
        html.append("<hr>")

        # Added records
        added = comparison.get("added", [])
        if added:
            html.append("<h4 style='color: green;'>+ Added Records</h4>")
            for record in added:
                html.append(
                    f"<p style='color: green;'>+ {record.get('type')} "
                    f"{record.get('name')} → {record.get('content')}</p>"
                )

        # Removed records
        removed = comparison.get("removed", [])
        if removed:
            html.append("<h4 style='color: red;'>- Removed Records</h4>")
            for record in removed:
                html.append(
                    f"<p style='color: red;'>- {record.get('type')} "
                    f"{record.get('name')} → {record.get('content')}</p>"
                )

        # Modified records
        modified = comparison.get("modified", [])
        if modified:
            html.append("<h4 style='color: orange;'>~ Modified Records</h4>")
            for mod in modified:
                current = mod.get("current", {})
                html.append(
                    f"<p style='color: orange;'>~ {current.get('type')} "
                    f"{current.get('name')} → {current.get('content')}</p>"
                )

        if not added and not removed and not modified:
            html.append("<p><i>No differences found</i></p>")

        self.compare_text.setHtml("".join(html))
        # Switch to Compare/Restore tab to show results
        self.tabs.setCurrentIndex(1)

    def delete_backup(self, filename: str):
        """Delete a backup."""
        reply = QMessageBox.question(
            self, "Delete Backup",
            f"Are you sure you want to delete backup:\n{filename}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.zone_backup.delete_backup(filename)
            if success:
                self.load_backups()
            else:
                QMessageBox.warning(self, "Error", message)
