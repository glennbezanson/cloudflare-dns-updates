"""Main application window."""
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QMessageBox,
    QInputDialog, QLineEdit, QStatusBar, QMenuBar,
    QMenu, QToolBar, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from config.settings import APP_NAME, APP_VERSION, CONFIG_FILE
from core import (
    CredentialManager, CloudflareClient, ClaudeClient,
    AuditLogger, ZoneBackup
)
from gui.zone_panel import ZonePanel
from gui.record_panel import RecordPanel
from gui.settings_dialog import SettingsDialog
from gui.review_dialog import ReviewDialog
from gui.audit_viewer import AuditViewerDialog
from gui.backup_dialog import BackupDialog
from gui.health_dialog import HealthDialog
from gui.widgets.record_editor import RecordEditorDialog
from gui.widgets.diff_viewer import DiffViewer
from gui.natural_input_dialog import NaturalInputDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Initialize core services
        self.cred_manager = CredentialManager(CONFIG_FILE)
        self.cf_client = CloudflareClient()
        self.claude_client = ClaudeClient()
        self.audit_logger = AuditLogger()
        self.zone_backup = ZoneBackup()

        # State
        self.current_zone_id = ""
        self.current_zone_name = ""
        self.current_records = []
        self.pending_changes = []

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 700)

        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()

        # Check if first run or unlock
        self.check_credentials()

    def setup_ui(self):
        """Set up the main UI."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Zone selector
        self.zone_panel = ZonePanel(cloudflare_client=self.cf_client)
        self.zone_panel.zone_selected.connect(self.on_zone_selected)
        self.zone_panel.setMaximumWidth(250)
        splitter.addWidget(self.zone_panel)

        # Right side container
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Record panel
        self.record_panel = RecordPanel()
        self.record_panel.add_requested.connect(self.add_record)
        self.record_panel.quick_add_requested.connect(self.quick_add_records)
        self.record_panel.edit_requested.connect(self.edit_record)
        self.record_panel.delete_requested.connect(self.delete_record)
        self.record_panel.refresh_requested = self.refresh_records
        right_layout.addWidget(self.record_panel)

        # Pending changes section
        pending_frame = QFrame()
        pending_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        pending_layout = QVBoxLayout(pending_frame)

        pending_header = QHBoxLayout()
        self.pending_label = QLabel("Pending Changes: 0")
        self.pending_label.setProperty("heading", True)
        pending_header.addWidget(self.pending_label)
        pending_header.addStretch()

        self.clear_pending_btn = QPushButton("Clear All")
        self.clear_pending_btn.clicked.connect(self.clear_pending_changes)
        self.clear_pending_btn.setEnabled(False)
        pending_header.addWidget(self.clear_pending_btn)

        pending_layout.addLayout(pending_header)

        # Diff viewer for pending changes
        self.diff_viewer = DiffViewer()
        self.diff_viewer.setMaximumHeight(150)
        pending_layout.addWidget(self.diff_viewer)

        # Action buttons
        action_row = QHBoxLayout()

        self.review_btn = QPushButton("Review with Claude AI")
        self.review_btn.clicked.connect(self.review_with_claude)
        self.review_btn.setEnabled(False)
        action_row.addWidget(self.review_btn)

        action_row.addStretch()

        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self.apply_changes)
        self.apply_btn.setEnabled(False)
        action_row.addWidget(self.apply_btn)

        pending_layout.addLayout(action_row)
        right_layout.addWidget(pending_frame)

        splitter.addWidget(right_container)
        splitter.setSizes([200, 1000])

        layout.addWidget(splitter)

    def setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        lock_action = QAction("Lock", self)
        lock_action.triggered.connect(self.lock_credentials)
        file_menu.addAction(lock_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Zone menu
        zone_menu = menubar.addMenu("Zone")

        refresh_zones_action = QAction("Refresh Zones", self)
        refresh_zones_action.triggered.connect(self.zone_panel.load_zones)
        zone_menu.addAction(refresh_zones_action)

        zone_menu.addSeparator()

        health_action = QAction("Health Assessment", self)
        health_action.triggered.connect(self.show_health_dialog)
        zone_menu.addAction(health_action)

        backup_action = QAction("Backup/Restore", self)
        backup_action.triggered.connect(self.show_backup_dialog)
        zone_menu.addAction(backup_action)

        # View menu
        view_menu = menubar.addMenu("View")

        audit_action = QAction("Audit Log", self)
        audit_action.triggered.connect(self.show_audit_log)
        view_menu.addAction(audit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_records)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        quick_add_action = QAction("Paste Request", self)
        quick_add_action.triggered.connect(self.quick_add_records)
        toolbar.addAction(quick_add_action)

        add_action = QAction("Add Record", self)
        add_action.triggered.connect(self.add_record)
        toolbar.addAction(add_action)

        toolbar.addSeparator()

        health_action = QAction("Health Check", self)
        health_action.triggered.connect(self.show_health_dialog)
        toolbar.addAction(health_action)

        backup_action = QAction("Backup", self)
        backup_action.triggered.connect(self.show_backup_dialog)
        toolbar.addAction(backup_action)

        audit_action = QAction("Audit Log", self)
        audit_action.triggered.connect(self.show_audit_log)
        toolbar.addAction(audit_action)

    def setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def check_credentials(self):
        """Check credentials and prompt for unlock/setup."""
        if self.cred_manager.is_configured():
            # Prompt for unlock
            password, ok = QInputDialog.getText(
                self, "Unlock",
                "Enter master password:",
                QLineEdit.EchoMode.Password
            )

            if ok and password:
                if self.cred_manager.unlock(password):
                    self.load_credentials()
                    self.statusbar.showMessage("Unlocked - Loading zones...")
                    self.zone_panel.load_zones()
                else:
                    QMessageBox.warning(self, "Error", "Invalid password")
                    self.check_credentials()
            else:
                self.statusbar.showMessage("Locked - Enter password to unlock")
        else:
            # First time setup
            self.first_time_setup()

    def first_time_setup(self):
        """First time setup wizard."""
        QMessageBox.information(
            self, "Welcome",
            f"Welcome to {APP_NAME}!\n\n"
            "Let's set up your master password to securely store API keys."
        )

        password, ok = QInputDialog.getText(
            self, "Create Master Password",
            "Create a master password (min 8 characters):",
            QLineEdit.EchoMode.Password
        )

        if not ok or len(password) < 8:
            QMessageBox.warning(
                self, "Error",
                "Password must be at least 8 characters"
            )
            self.first_time_setup()
            return

        confirm, ok = QInputDialog.getText(
            self, "Confirm Password",
            "Confirm your master password:",
            QLineEdit.EchoMode.Password
        )

        if not ok or password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            self.first_time_setup()
            return

        if self.cred_manager.create_new(password):
            QMessageBox.information(
                self, "Success",
                "Master password created!\n\n"
                "Now let's configure your API keys."
            )
            self.show_settings()
        else:
            QMessageBox.warning(self, "Error", "Failed to create credentials")

    def load_credentials(self):
        """Load API credentials into clients."""
        cf_token = self.cred_manager.get_cloudflare_token()
        if cf_token:
            self.cf_client.set_token(cf_token)

        claude_key = self.cred_manager.get_anthropic_key()
        if claude_key:
            self.claude_client.set_api_key(claude_key)

    def lock_credentials(self):
        """Lock credentials and clear sensitive data."""
        self.cred_manager.lock()
        self.cf_client.set_token("")
        self.claude_client.set_api_key("")
        self.record_panel.clear()
        self.pending_changes = []
        self.update_pending_ui()
        self.statusbar.showMessage("Locked")
        self.check_credentials()

    def on_zone_selected(self, zone_id: str, zone_name: str):
        """Handle zone selection."""
        self.current_zone_id = zone_id
        self.current_zone_name = zone_name
        self.pending_changes = []
        self.update_pending_ui()
        self.refresh_records()

    def refresh_records(self):
        """Refresh DNS records for current zone."""
        if not self.current_zone_id:
            return

        self.statusbar.showMessage("Loading records...")
        self.current_records = self.cf_client.list_dns_records(self.current_zone_id)
        self.record_panel.set_zone(self.current_zone_id, self.current_zone_name)
        self.record_panel.set_records(self.current_records)
        self.statusbar.showMessage(f"Loaded {len(self.current_records)} records")

    def add_record(self):
        """Add a new DNS record."""
        if not self.current_zone_id:
            QMessageBox.warning(self, "Error", "Please select a zone first")
            return

        dialog = RecordEditorDialog(self, domain=self.current_zone_name)
        if dialog.exec():
            record = dialog.get_record()
            if record:
                self.pending_changes.append({
                    "action": "add",
                    "record": record
                })
                self.update_pending_ui()

    def quick_add_records(self):
        """Open natural language input dialog to paste requests."""
        if not self.current_zone_id:
            QMessageBox.warning(self, "Error", "Please select a zone first")
            return

        dialog = NaturalInputDialog(
            self,
            claude_client=self.claude_client,
            domain=self.current_zone_name
        )
        if dialog.exec():
            new_changes = dialog.get_records()
            if new_changes:
                self.pending_changes.extend(new_changes)
                self.update_pending_ui()
                self.statusbar.showMessage(f"Added {len(new_changes)} records to pending changes")

    def edit_record(self, record: dict):
        """Edit an existing DNS record."""
        dialog = RecordEditorDialog(self, record=record, domain=self.current_zone_name)
        if dialog.exec():
            new_record = dialog.get_record()
            if new_record:
                self.pending_changes.append({
                    "action": "edit",
                    "record": new_record,
                    "old_record": record
                })
                self.update_pending_ui()

    def delete_record(self, record: dict):
        """Delete a DNS record."""
        reply = QMessageBox.question(
            self, "Delete Record",
            f"Are you sure you want to delete this record?\n\n"
            f"Type: {record.get('type')}\n"
            f"Name: {record.get('name')}\n"
            f"Content: {record.get('content')[:50]}...",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.pending_changes.append({
                "action": "delete",
                "record": record
            })
            self.update_pending_ui()

    def update_pending_ui(self):
        """Update the pending changes UI."""
        count = len(self.pending_changes)
        self.pending_label.setText(f"Pending Changes: {count}")

        has_changes = count > 0
        self.clear_pending_btn.setEnabled(has_changes)
        self.review_btn.setEnabled(has_changes)
        self.apply_btn.setEnabled(has_changes)

        self.diff_viewer.set_changes(self.pending_changes, self.current_records)

    def clear_pending_changes(self):
        """Clear all pending changes."""
        self.pending_changes = []
        self.update_pending_ui()

    def review_with_claude(self):
        """Open Claude review dialog."""
        dialog = ReviewDialog(
            self,
            claude_client=self.claude_client,
            domain=self.current_zone_name,
            current_records=self.current_records,
            pending_changes=self.pending_changes
        )

        if dialog.exec():
            approved, review_result = dialog.get_result()
            if approved:
                self.apply_changes(review_result)

    def apply_changes(self, review_result: Optional[dict] = None):
        """Apply pending changes to Cloudflare."""
        if not self.pending_changes:
            return

        reply = QMessageBox.question(
            self, "Apply Changes",
            f"Apply {len(self.pending_changes)} changes to {self.current_zone_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        success_count = 0
        error_count = 0

        for change in self.pending_changes:
            action = change.get("action")
            record = change.get("record", {})

            try:
                if action == "add":
                    success, msg, _ = self.cf_client.create_dns_record(
                        self.current_zone_id,
                        record.get("type"),
                        record.get("name"),
                        record.get("content"),
                        record.get("ttl", 1),
                        record.get("proxied", False),
                        record.get("priority")
                    )
                elif action == "edit":
                    success, msg = self.cf_client.update_dns_record(
                        self.current_zone_id,
                        record.get("id"),
                        record.get("type"),
                        record.get("name"),
                        record.get("content"),
                        record.get("ttl", 1),
                        record.get("proxied", False),
                        record.get("priority")
                    )
                elif action == "delete":
                    success, msg = self.cf_client.delete_dns_record(
                        self.current_zone_id,
                        record.get("id")
                    )
                else:
                    continue

                if success:
                    success_count += 1
                    # Log to audit
                    self.audit_logger.log(
                        action,
                        self.current_zone_name,
                        record.get("type", ""),
                        record.get("name", ""),
                        record.get("content", ""),
                        claude_review=review_result
                    )
                else:
                    error_count += 1

            except Exception as e:
                error_count += 1

        # Clear pending and refresh
        self.pending_changes = []
        self.update_pending_ui()
        self.refresh_records()

        # Show result
        if error_count == 0:
            QMessageBox.information(
                self, "Success",
                f"Successfully applied {success_count} changes"
            )
        else:
            QMessageBox.warning(
                self, "Partial Success",
                f"Applied {success_count} changes, {error_count} failed"
            )

    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(
            self,
            credential_manager=self.cred_manager,
            cloudflare_client=self.cf_client,
            claude_client=self.claude_client
        )
        if dialog.exec():
            self.load_credentials()
            self.zone_panel.load_zones()

    def show_health_dialog(self):
        """Show DNS health assessment dialog."""
        if not self.current_zone_id:
            QMessageBox.warning(self, "Error", "Please select a zone first")
            return

        dialog = HealthDialog(
            self,
            claude_client=self.claude_client,
            domain=self.current_zone_name,
            records=self.current_records
        )
        dialog.fixes_requested.connect(self.on_fixes_requested)
        dialog.exec()

    def on_fixes_requested(self, fixes: list):
        """Handle fixes from health dialog."""
        self.pending_changes.extend(fixes)
        self.update_pending_ui()
        self.statusbar.showMessage(f"Added {len(fixes)} fixes to pending changes")

    def show_backup_dialog(self):
        """Show backup/restore dialog."""
        if not self.current_zone_id:
            QMessageBox.warning(self, "Error", "Please select a zone first")
            return

        dialog = BackupDialog(
            self,
            zone_backup=self.zone_backup,
            cloudflare_client=self.cf_client,
            zone_id=self.current_zone_id,
            zone_name=self.current_zone_name,
            current_records=self.current_records
        )
        dialog.exec()

    def show_audit_log(self):
        """Show audit log viewer."""
        zones = self.cf_client.list_zones() if self.cred_manager.is_unlocked() else []
        dialog = AuditViewerDialog(self, audit_logger=self.audit_logger, zones=zones)
        dialog.exec()

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Manage Cloudflare DNS records with AI-powered review.\n\n"
            "Features:\n"
            "- Secure encrypted credential storage\n"
            "- Full DNS record management\n"
            "- Claude AI change review\n"
            "- Audit logging\n"
            "- Zone backup/restore"
        )
