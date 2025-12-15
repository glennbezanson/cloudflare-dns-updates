"""Settings dialog for API key configuration."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QTabWidget, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """Dialog for configuring API keys and settings."""

    def __init__(self, parent=None, credential_manager=None,
                 cloudflare_client=None, claude_client=None):
        super().__init__(parent)
        self.cred_manager = credential_manager
        self.cf_client = cloudflare_client
        self.claude_client = claude_client

        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setup_ui()
        self.load_current_values()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # API Keys tab
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        # Cloudflare section
        cf_group = QGroupBox("Cloudflare API")
        cf_layout = QFormLayout()

        self.cf_token_edit = QLineEdit()
        self.cf_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.cf_token_edit.setPlaceholderText("Enter Cloudflare API token")
        cf_layout.addRow("API Token:", self.cf_token_edit)

        self.cf_test_btn = QPushButton("Test Connection")
        self.cf_test_btn.clicked.connect(self.test_cloudflare)
        self.cf_status = QLabel("")
        cf_test_row = QHBoxLayout()
        cf_test_row.addWidget(self.cf_test_btn)
        cf_test_row.addWidget(self.cf_status)
        cf_test_row.addStretch()
        cf_layout.addRow("", cf_test_row)

        cf_group.setLayout(cf_layout)
        api_layout.addWidget(cf_group)

        # Anthropic section
        claude_group = QGroupBox("Claude AI (Anthropic)")
        claude_layout = QFormLayout()

        self.claude_key_edit = QLineEdit()
        self.claude_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.claude_key_edit.setPlaceholderText("Enter Anthropic API key")
        claude_layout.addRow("API Key:", self.claude_key_edit)

        self.claude_test_btn = QPushButton("Test Connection")
        self.claude_test_btn.clicked.connect(self.test_claude)
        self.claude_status = QLabel("")
        claude_test_row = QHBoxLayout()
        claude_test_row.addWidget(self.claude_test_btn)
        claude_test_row.addWidget(self.claude_status)
        claude_test_row.addStretch()
        claude_layout.addRow("", claude_test_row)

        claude_group.setLayout(claude_layout)
        api_layout.addWidget(claude_group)

        api_layout.addStretch()
        tabs.addTab(api_tab, "API Keys")

        # Security tab
        security_tab = QWidget()
        security_layout = QVBoxLayout(security_tab)

        pw_group = QGroupBox("Change Master Password")
        pw_layout = QFormLayout()

        self.old_pw_edit = QLineEdit()
        self.old_pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pw_layout.addRow("Current Password:", self.old_pw_edit)

        self.new_pw_edit = QLineEdit()
        self.new_pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pw_layout.addRow("New Password:", self.new_pw_edit)

        self.confirm_pw_edit = QLineEdit()
        self.confirm_pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pw_layout.addRow("Confirm Password:", self.confirm_pw_edit)

        self.change_pw_btn = QPushButton("Change Password")
        self.change_pw_btn.clicked.connect(self.change_password)
        pw_layout.addRow("", self.change_pw_btn)

        pw_group.setLayout(pw_layout)
        security_layout.addWidget(pw_group)
        security_layout.addStretch()

        tabs.addTab(security_tab, "Security")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def load_current_values(self):
        """Load current API keys (masked)."""
        if self.cred_manager and self.cred_manager.is_unlocked():
            cf_token = self.cred_manager.get_cloudflare_token()
            if cf_token:
                self.cf_token_edit.setText(cf_token)

            claude_key = self.cred_manager.get_anthropic_key()
            if claude_key:
                self.claude_key_edit.setText(claude_key)

    def test_cloudflare(self):
        """Test Cloudflare API connection."""
        token = self.cf_token_edit.text().strip()
        if not token:
            self.cf_status.setText("No token entered")
            self.cf_status.setStyleSheet("color: red;")
            return

        self.cf_test_btn.setEnabled(False)
        self.cf_status.setText("Testing...")
        self.cf_status.setStyleSheet("color: gray;")

        # Update client and test
        if self.cf_client:
            self.cf_client.set_token(token)
            success, message = self.cf_client.test_connection()

            if success:
                self.cf_status.setText("Connected!")
                self.cf_status.setStyleSheet("color: green;")
            else:
                self.cf_status.setText(f"Failed: {message[:50]}")
                self.cf_status.setStyleSheet("color: red;")

        self.cf_test_btn.setEnabled(True)

    def test_claude(self):
        """Test Claude API connection."""
        key = self.claude_key_edit.text().strip()
        if not key:
            self.claude_status.setText("No key entered")
            self.claude_status.setStyleSheet("color: red;")
            return

        self.claude_test_btn.setEnabled(False)
        self.claude_status.setText("Testing...")
        self.claude_status.setStyleSheet("color: gray;")

        # Update client and test
        if self.claude_client:
            self.claude_client.set_api_key(key)
            success, message = self.claude_client.test_connection()

            if success:
                self.claude_status.setText("Connected!")
                self.claude_status.setStyleSheet("color: green;")
            else:
                self.claude_status.setText(f"Failed: {message[:50]}")
                self.claude_status.setStyleSheet("color: red;")

        self.claude_test_btn.setEnabled(True)

    def change_password(self):
        """Change the master password."""
        old_pw = self.old_pw_edit.text()
        new_pw = self.new_pw_edit.text()
        confirm_pw = self.confirm_pw_edit.text()

        if not old_pw or not new_pw:
            QMessageBox.warning(self, "Error", "Please fill in all password fields")
            return

        if new_pw != confirm_pw:
            QMessageBox.warning(self, "Error", "New passwords do not match")
            return

        if len(new_pw) < 8:
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters")
            return

        if self.cred_manager:
            if self.cred_manager.change_master_password(old_pw, new_pw):
                QMessageBox.information(self, "Success", "Password changed successfully")
                self.old_pw_edit.clear()
                self.new_pw_edit.clear()
                self.confirm_pw_edit.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to change password. Check current password.")

    def save_settings(self):
        """Save API keys."""
        if not self.cred_manager or not self.cred_manager.is_unlocked():
            QMessageBox.warning(self, "Error", "Credentials not unlocked")
            return

        cf_token = self.cf_token_edit.text().strip()
        claude_key = self.claude_key_edit.text().strip()

        # Save Cloudflare token
        if cf_token:
            self.cred_manager.set_cloudflare_token(cf_token)
            if self.cf_client:
                self.cf_client.set_token(cf_token)

        # Save Claude key
        if claude_key:
            self.cred_manager.set_anthropic_key(claude_key)
            if self.claude_client:
                self.claude_client.set_api_key(claude_key)

        self.accept()
