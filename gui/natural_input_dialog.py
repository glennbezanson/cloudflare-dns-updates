"""Natural language input dialog for DNS requests."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QProgressBar, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QAbstractItemView, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from gui.styles import get_validation_styles, EDGE_BLUE, EDGE_GREEN, SUCCESS_GREEN


class ParseAndValidateWorker(QThread):
    """Worker thread for Claude API calls - parse then validate."""
    progress_update = pyqtSignal(str)  # status message
    finished = pyqtSignal(bool, str, list, dict)  # success, message, records, validation

    def __init__(self, claude_client, user_input, domain):
        super().__init__()
        self.claude_client = claude_client
        self.user_input = user_input
        self.domain = domain

    def run(self):
        # Step 1: Parse natural language
        self.progress_update.emit("Step 1/2: Parsing request...")
        success, message, records = self.claude_client.parse_natural_language(
            self.user_input, self.domain
        )

        if not success:
            self.finished.emit(False, message, [], {})
            return

        if not records:
            self.finished.emit(False, "No DNS records found in the text", [], {})
            return

        # Step 2: Validate against best practices
        self.progress_update.emit("Step 2/2: Validating against best practices...")
        val_success, val_message, validation = self.claude_client.validate_records(
            records, self.domain
        )

        if not val_success:
            # Still return parsed records even if validation fails
            self.finished.emit(True, f"Parsed but validation failed: {val_message}", records, {})
            return

        self.finished.emit(True, "Parsed and validated", records, validation)


class NaturalInputDialog(QDialog):
    """Dialog for entering natural language DNS requests."""

    def __init__(self, parent=None, claude_client=None, domain: str = ""):
        super().__init__(parent)
        self.claude_client = claude_client
        self.domain = domain
        self.parsed_records = []
        self.validated_records = []
        self.validation_result = {}
        self.selected_records = []

        self.setWindowTitle("Quick Add - Paste Request")
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)

        # Allow resize and maximize
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Quick Add DNS Records to: {self.domain}")
        header.setProperty("heading", True)
        layout.addWidget(header)

        # Input section
        input_group = QGroupBox("Paste Request or Ticket")
        input_layout = QVBoxLayout(input_group)

        help_text = QLabel(
            "Paste a ticket, email, or any text describing DNS records to add. "
            "Claude will parse it, validate against best practices, and show corrections."
        )
        help_text.setWordWrap(True)
        help_text.setProperty("subheading", True)
        input_layout.addWidget(help_text)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Example:\n\n"
            "Can someone help John on ticket 1077. He needs these TXT records added:\n\n"
            "apple-domain-verification=Pjl0nznIinJKyKF1\n"
            "google-site-verification=7uHnDNu8t-aeAGAMX5L9k6mD9K6_ZfbumR7V73AUoIM\n"
            "v=spf1 include:spf.protection.outlook.com -all"
        )
        self.input_text.setFont(QFont("Consolas", 10))
        self.input_text.setMinimumHeight(120)
        input_layout.addWidget(self.input_text)

        # Parse button row
        parse_row = QHBoxLayout()

        self.parse_btn = QPushButton("Parse & Validate with Claude AI")
        self.parse_btn.setObjectName("pasteRequestBtn")  # Accent styling
        self.parse_btn.clicked.connect(self.parse_input)
        parse_row.addWidget(self.parse_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)
        parse_row.addWidget(self.progress)

        parse_row.addStretch()
        input_layout.addLayout(parse_row)

        layout.addWidget(input_group)

        # Status/Progress label
        self.status_label = QLabel("Enter text above and click 'Parse & Validate with Claude AI'")
        self.status_label.setProperty("subheading", True)
        layout.addWidget(self.status_label)

        # Validation summary
        self.validation_summary = QLabel("")
        self.validation_summary.setWordWrap(True)
        self.validation_summary.setVisible(False)
        layout.addWidget(self.validation_summary)

        # Results section
        results_group = QGroupBox("Validated Records")
        results_layout = QVBoxLayout(results_group)

        # Results table - now with more columns for validation info
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Add", "Type", "Name", "Content (Corrected)", "Issues/Fixes", "Status"
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.results_table.setColumnWidth(0, 40)
        self.results_table.setColumnWidth(1, 60)
        self.results_table.setColumnWidth(2, 100)
        self.results_table.setColumnWidth(4, 200)
        self.results_table.setColumnWidth(5, 80)
        results_layout.addWidget(self.results_table)

        # Select all checkbox
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.setChecked(True)
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        results_layout.addWidget(self.select_all_cb)

        layout.addWidget(results_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.add_btn = QPushButton("Add Selected Records")
        self.add_btn.setEnabled(False)
        self.add_btn.setObjectName("pasteRequestBtn")  # Accent styling
        self.add_btn.clicked.connect(self.add_records)
        btn_layout.addWidget(self.add_btn)

        layout.addLayout(btn_layout)

    def parse_input(self):
        """Parse and validate the input text with Claude."""
        text = self.input_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Error", "Please enter some text to parse")
            return

        if not self.claude_client:
            QMessageBox.warning(
                self, "Error",
                "Claude AI not configured. Please set up your Anthropic API key in Settings."
            )
            return

        self.parse_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setText("Starting...")
        self.status_label.setStyleSheet("color: #666;")
        self.validation_summary.setVisible(False)

        # Start worker
        self.worker = ParseAndValidateWorker(self.claude_client, text, self.domain)
        self.worker.progress_update.connect(self.on_progress_update)
        self.worker.finished.connect(self.on_parse_complete)
        self.worker.start()

    def on_progress_update(self, message: str):
        """Handle progress updates."""
        self.status_label.setText(message)

    def on_parse_complete(self, success: bool, message: str, records: list, validation: dict):
        """Handle parse and validation completion."""
        self.progress.setVisible(False)
        self.parse_btn.setEnabled(True)

        if not success:
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet("color: red;")
            return

        self.parsed_records = records
        self.validation_result = validation

        # Show validation summary
        if validation:
            summary = validation.get("summary", "")
            is_valid = validation.get("valid", True)
            styles = get_validation_styles()

            if is_valid:
                self.validation_summary.setStyleSheet(styles["success"])
                self.validation_summary.setText(f"✓ Validation Passed: {summary}")
            else:
                self.validation_summary.setStyleSheet(styles["warning"])
                self.validation_summary.setText(f"⚠ Issues Found & Corrected: {summary}")

            self.validation_summary.setVisible(True)

        # Populate with validated/corrected records
        self.populate_results(validation)

        if records:
            self.status_label.setText(f"Found {len(records)} record(s) - reviewed and ready")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.add_btn.setEnabled(True)
        else:
            self.status_label.setText("No DNS records found in the text")
            self.status_label.setStyleSheet("color: orange;")

    def populate_results(self, validation: dict):
        """Populate the results table with validated records."""
        self.results_table.setRowCount(0)
        self.checkboxes = []
        self.validated_records = []

        corrected_records = validation.get("corrected_records", [])

        # If no validation result, fall back to parsed records
        if not corrected_records:
            for record in self.parsed_records:
                corrected_records.append({
                    "original": record,
                    "corrected": record,
                    "issues": [],
                    "fixes_applied": [],
                    "warnings": []
                })

        for item in corrected_records:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            original = item.get("original", {})
            corrected = item.get("corrected", original)
            issues = item.get("issues", [])
            fixes = item.get("fixes_applied", [])
            warnings = item.get("warnings", [])

            # Store the corrected record
            self.validated_records.append(corrected)

            # Checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            self.checkboxes.append(cb)
            self.results_table.setCellWidget(row, 0, cb)

            # Type
            rtype = corrected.get("type", "TXT")
            type_item = QTableWidgetItem(rtype)
            self.results_table.setItem(row, 1, type_item)

            # Name
            name = corrected.get("name", "@")
            self.results_table.setItem(row, 2, QTableWidgetItem(name))

            # Content (corrected)
            content = corrected.get("content", "")
            content_item = QTableWidgetItem(content)

            # Color based on whether changes were made
            if fixes:
                content_item.setBackground(QColor("#d4edda"))  # Light green - fixed
                content_item.setToolTip(f"Original: {original.get('content', '')}")
            elif issues:
                content_item.setBackground(QColor("#fff3cd"))  # Light yellow - has issues

            self.results_table.setItem(row, 3, content_item)

            # Issues/Fixes column
            notes = []
            for fix in fixes:
                notes.append(f"✓ {fix}")
            for issue in issues:
                notes.append(f"⚠ {issue}")
            for warning in warnings:
                notes.append(f"ℹ {warning}")

            notes_text = "\n".join(notes) if notes else "✓ Valid"
            notes_item = QTableWidgetItem(notes_text)
            if fixes:
                notes_item.setForeground(QColor("#155724"))  # Dark green
            elif issues:
                notes_item.setForeground(QColor("#856404"))  # Dark yellow/brown
            self.results_table.setItem(row, 4, notes_item)

            # Status column
            if fixes:
                status = "Fixed"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(QColor("#d4edda"))
                status_item.setForeground(QColor("#155724"))
            elif issues or warnings:
                status = "Warning"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(QColor("#fff3cd"))
                status_item.setForeground(QColor("#856404"))
            else:
                status = "Valid"
                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor("#155724"))

            self.results_table.setItem(row, 5, status_item)

        # Resize rows to fit content
        self.results_table.resizeRowsToContents()

    def toggle_select_all(self, state):
        """Toggle all checkboxes."""
        checked = state == Qt.CheckState.Checked.value
        for cb in self.checkboxes:
            cb.setChecked(checked)

    def add_records(self):
        """Add selected records to pending changes."""
        self.selected_records = []

        for i, cb in enumerate(self.checkboxes):
            if cb.isChecked() and i < len(self.validated_records):
                record = self.validated_records[i]

                self.selected_records.append({
                    "action": "add",
                    "record": {
                        "type": record.get("type", "TXT"),
                        "name": record.get("name", "@"),
                        "content": record.get("content", ""),
                        "ttl": record.get("ttl", 1),
                        "priority": record.get("priority"),
                        "proxied": record.get("proxied", False),
                    }
                })

        if self.selected_records:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "No records selected")

    def get_records(self) -> list:
        """Get the selected records to add."""
        return self.selected_records
