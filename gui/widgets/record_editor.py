"""Record editor dialog widget."""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QPushButton, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from config.settings import DNS_RECORD_TYPES, TTL_OPTIONS
from utils.validators import validate_record


class RecordEditorDialog(QDialog):
    """Dialog for adding/editing DNS records."""

    def __init__(self, parent=None, record: Optional[dict] = None, domain: str = ""):
        super().__init__(parent)
        self.record = record
        self.domain = domain
        self.result_record = None

        self.setWindowTitle("Edit Record" if record else "Add Record")
        self.setMinimumWidth(500)
        self.setup_ui()

        if record:
            self.populate_from_record(record)

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Record type
        self.type_combo = QComboBox()
        self.type_combo.addItems(DNS_RECORD_TYPES)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form.addRow("Type:", self.type_combo)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("@ for root, or subdomain name")
        name_layout = QHBoxLayout()
        name_layout.addWidget(self.name_edit)
        self.domain_label = QLabel(f".{self.domain}" if self.domain else "")
        name_layout.addWidget(self.domain_label)
        form.addRow("Name:", name_layout)

        # Content
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(80)
        self.content_edit.setPlaceholderText("Record value (IP address, hostname, or text)")
        form.addRow("Content:", self.content_edit)

        # TTL
        self.ttl_combo = QComboBox()
        for label in TTL_OPTIONS.keys():
            self.ttl_combo.addItem(label)
        form.addRow("TTL:", self.ttl_combo)

        # Priority (for MX/SRV)
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(0, 65535)
        self.priority_spin.setValue(10)
        self.priority_label = QLabel("Priority:")
        self.priority_row_widget = QHBoxLayout()
        self.priority_row_widget.addWidget(self.priority_spin)
        self.priority_row_widget.addStretch()
        form.addRow(self.priority_label, self.priority_row_widget)

        # Proxied (for A/AAAA/CNAME)
        self.proxied_check = QCheckBox("Proxy through Cloudflare (orange cloud)")
        self.proxied_label = QLabel("Proxy:")
        form.addRow(self.proxied_label, self.proxied_check)

        layout.addLayout(form)

        # Validation message
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red;")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_record)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        # Initial visibility
        self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, record_type: str):
        """Handle record type change."""
        # Show/hide priority for MX/SRV
        show_priority = record_type in ["MX", "SRV"]
        self.priority_spin.setVisible(show_priority)
        self.priority_label.setVisible(show_priority)

        # Show/hide proxied for A/AAAA/CNAME
        show_proxied = record_type in ["A", "AAAA", "CNAME"]
        self.proxied_check.setVisible(show_proxied)
        self.proxied_label.setVisible(show_proxied)

        # Update placeholder text
        placeholders = {
            "A": "IPv4 address (e.g., 192.168.1.1)",
            "AAAA": "IPv6 address (e.g., 2001:db8::1)",
            "CNAME": "Target hostname (e.g., example.com)",
            "MX": "Mail server hostname (e.g., mail.example.com)",
            "TXT": "Text content (e.g., v=spf1 include:example.com -all)",
            "NS": "Nameserver hostname",
            "SRV": "Target (e.g., 0 5 5269 xmpp-server.example.com)",
            "CAA": "CAA record (e.g., 0 issue letsencrypt.org)",
            "PTR": "Pointer hostname",
        }
        self.content_edit.setPlaceholderText(placeholders.get(record_type, "Record value"))

    def populate_from_record(self, record: dict):
        """Populate form from existing record."""
        # Type
        record_type = record.get("type", "A")
        idx = self.type_combo.findText(record_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        # Name - strip domain suffix
        name = record.get("name", "@")
        if self.domain and name.endswith(f".{self.domain}"):
            name = name[:-len(f".{self.domain}")]
        elif name == self.domain:
            name = "@"
        self.name_edit.setText(name)

        # Content
        self.content_edit.setPlainText(record.get("content", ""))

        # TTL
        ttl = record.get("ttl", 1)
        for i, (label, value) in enumerate(TTL_OPTIONS.items()):
            if value == ttl:
                self.ttl_combo.setCurrentIndex(i)
                break

        # Priority
        priority = record.get("priority")
        if priority is not None:
            self.priority_spin.setValue(priority)

        # Proxied
        self.proxied_check.setChecked(record.get("proxied", False))

    def validate(self) -> tuple[bool, list[str]]:
        """Validate current form values."""
        record_type = self.type_combo.currentText()
        name = self.name_edit.text().strip() or "@"
        content = self.content_edit.toPlainText().strip()
        ttl_label = self.ttl_combo.currentText()
        ttl = TTL_OPTIONS.get(ttl_label, 1)
        priority = self.priority_spin.value() if record_type in ["MX", "SRV"] else None

        return validate_record(record_type, name, content, ttl, priority)

    def save_record(self):
        """Validate and save the record."""
        is_valid, errors = self.validate()

        if not is_valid:
            self.validation_label.setText("\n".join(errors))
            return

        # Build result record
        record_type = self.type_combo.currentText()
        name = self.name_edit.text().strip() or "@"
        content = self.content_edit.toPlainText().strip()
        ttl_label = self.ttl_combo.currentText()
        ttl = TTL_OPTIONS.get(ttl_label, 1)

        self.result_record = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl,
        }

        if record_type in ["MX", "SRV"]:
            self.result_record["priority"] = self.priority_spin.value()

        if record_type in ["A", "AAAA", "CNAME"]:
            self.result_record["proxied"] = self.proxied_check.isChecked()

        # Preserve ID if editing
        if self.record and "id" in self.record:
            self.result_record["id"] = self.record["id"]

        # Show warnings but allow save
        warnings = [e for e in errors if e.startswith("Warning")]
        if warnings:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Warnings")
            msg.setText("The following warnings were detected:")
            msg.setDetailedText("\n".join(warnings))
            msg.setStandardButtons(
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )
            if msg.exec() != QMessageBox.StandardButton.Ok:
                return

        self.accept()

    def get_record(self) -> Optional[dict]:
        """Get the resulting record after dialog closes."""
        return self.result_record
