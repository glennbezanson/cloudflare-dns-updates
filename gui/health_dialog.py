"""DNS Health Assessment dialog."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGroupBox, QScrollArea,
    QWidget, QFrame, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from gui.styles import (
    EDGE_BLUE, EDGE_GREEN, SUCCESS_GREEN, WARNING_YELLOW, ERROR_RED,
    DARK_TEAL, WHITE, COOL_GRAY
)


class HealthCheckWorker(QThread):
    """Worker thread for health check API call."""
    finished = pyqtSignal(bool, str, dict)  # success, message, result

    def __init__(self, claude_client, domain, records):
        super().__init__()
        self.claude_client = claude_client
        self.domain = domain
        self.records = records

    def run(self):
        success, message, result = self.claude_client.health_check(
            self.domain, self.records
        )
        self.finished.emit(success, message, result)


class GenerateFixesWorker(QThread):
    """Worker thread for generating fixes."""
    finished = pyqtSignal(bool, str, dict)  # success, message, result

    def __init__(self, claude_client, domain, records, health_report):
        super().__init__()
        self.claude_client = claude_client
        self.domain = domain
        self.records = records
        self.health_report = health_report

    def run(self):
        success, message, result = self.claude_client.generate_fixes(
            self.domain, self.records, self.health_report
        )
        self.finished.emit(success, message, result)


class HealthDialog(QDialog):
    """Dialog for DNS health assessment."""

    # Signal to send fixes back to main window
    fixes_requested = pyqtSignal(list)  # list of record operations

    def __init__(self, parent=None, claude_client=None, domain: str = "",
                 records: list = None):
        super().__init__(parent)
        self.claude_client = claude_client
        self.domain = domain
        self.records = records or []
        self.health_result = None
        self.fixes_result = None
        self.selected_fixes = []

        self.setWindowTitle(f"DNS Health Assessment - {domain}")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)

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
        header_layout = QHBoxLayout()
        header = QLabel(f"DNS Health Assessment: {self.domain}")
        header.setProperty("heading", True)
        header_layout.addWidget(header)
        header_layout.addStretch()

        self.run_btn = QPushButton("Run Health Check")
        self.run_btn.setObjectName("pasteRequestBtn")  # Accent styling
        self.run_btn.clicked.connect(self.run_health_check)
        header_layout.addWidget(self.run_btn)

        layout.addLayout(header_layout)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        # Status
        self.status_label = QLabel(f"Click 'Run Health Check' to analyze {len(self.records)} DNS records")
        self.status_label.setProperty("subheading", True)
        layout.addWidget(self.status_label)

        # Overall score card
        self.score_card = QFrame()
        self.score_card.setFrameStyle(QFrame.Shape.StyledPanel)
        self.score_card.setVisible(False)
        score_layout = QHBoxLayout(self.score_card)

        self.score_label = QLabel("--")
        self.score_label.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setMinimumWidth(80)
        score_layout.addWidget(self.score_label)

        score_info = QVBoxLayout()
        self.status_text = QLabel("Status")
        self.status_text.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        score_info.addWidget(self.status_text)

        self.summary_text = QLabel("Summary will appear here...")
        self.summary_text.setWordWrap(True)
        score_info.addWidget(self.summary_text)

        score_layout.addLayout(score_info, 1)
        layout.addWidget(self.score_card)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Category tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        categories_label = QLabel("Categories")
        categories_label.setProperty("heading", True)
        left_layout.addWidget(categories_label)

        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setIndentation(20)
        self.category_tree.itemClicked.connect(self.on_category_selected)
        left_layout.addWidget(self.category_tree)

        splitter.addWidget(left_widget)

        # Right: Details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("Details")
        details_label.setProperty("heading", True)
        right_layout.addWidget(details_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select a category to view details...")
        right_layout.addWidget(self.details_text)

        splitter.addWidget(right_widget)
        splitter.setSizes([300, 600])

        layout.addWidget(splitter, 1)

        # Critical issues section
        self.critical_group = QGroupBox("Critical Issues")
        self.critical_group.setVisible(False)
        critical_layout = QVBoxLayout(self.critical_group)
        self.critical_list = QLabel("")
        self.critical_list.setWordWrap(True)
        self.critical_list.setStyleSheet(
            f"background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px;"
        )
        critical_layout.addWidget(self.critical_list)
        layout.addWidget(self.critical_group)

        # Recommendations section
        self.recs_group = QGroupBox("Recommendations")
        self.recs_group.setVisible(False)
        recs_layout = QVBoxLayout(self.recs_group)
        self.recs_list = QLabel("")
        self.recs_list.setWordWrap(True)
        self.recs_list.setStyleSheet(
            f"background-color: #e3f2fd; color: {EDGE_BLUE}; padding: 10px; border-radius: 5px;"
        )
        recs_layout.addWidget(self.recs_list)
        layout.addWidget(self.recs_group)

        # Fixes section (hidden until generated)
        self.fixes_group = QGroupBox("Recommended Fixes")
        self.fixes_group.setVisible(False)
        fixes_layout = QVBoxLayout(self.fixes_group)

        # Fixes table
        self.fixes_table = QTableWidget()
        self.fixes_table.setColumnCount(6)
        self.fixes_table.setHorizontalHeaderLabels([
            "Apply", "Action", "Type", "Name", "Content", "Reason"
        ])
        self.fixes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fixes_table.setAlternatingRowColors(True)
        self.fixes_table.horizontalHeader().setStretchLastSection(True)
        self.fixes_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.fixes_table.setColumnWidth(0, 40)
        self.fixes_table.setColumnWidth(1, 60)
        self.fixes_table.setColumnWidth(2, 60)
        self.fixes_table.setColumnWidth(3, 120)
        self.fixes_table.setColumnWidth(5, 200)
        fixes_layout.addWidget(self.fixes_table)

        # Select all and manual fixes info
        fixes_bottom = QHBoxLayout()
        self.select_all_fixes = QCheckBox("Select All")
        self.select_all_fixes.setChecked(True)
        self.select_all_fixes.stateChanged.connect(self.toggle_all_fixes)
        fixes_bottom.addWidget(self.select_all_fixes)
        fixes_bottom.addStretch()
        fixes_layout.addLayout(fixes_bottom)

        # Manual fixes notice
        self.manual_fixes_label = QLabel("")
        self.manual_fixes_label.setWordWrap(True)
        self.manual_fixes_label.setVisible(False)
        self.manual_fixes_label.setStyleSheet(
            f"background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px;"
        )
        fixes_layout.addWidget(self.manual_fixes_label)

        layout.addWidget(self.fixes_group)

        # Buttons
        btn_layout = QHBoxLayout()

        self.implement_btn = QPushButton("Implement Best Practices")
        self.implement_btn.setObjectName("pasteRequestBtn")  # Accent styling
        self.implement_btn.setVisible(False)
        self.implement_btn.clicked.connect(self.generate_fixes)
        btn_layout.addWidget(self.implement_btn)

        btn_layout.addStretch()

        self.apply_fixes_btn = QPushButton("Add Selected Fixes to Pending")
        self.apply_fixes_btn.setObjectName("pasteRequestBtn")
        self.apply_fixes_btn.setVisible(False)
        self.apply_fixes_btn.clicked.connect(self.apply_selected_fixes)
        btn_layout.addWidget(self.apply_fixes_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def run_health_check(self):
        """Run the health check."""
        if not self.claude_client:
            self.status_label.setText("Error: Claude AI not configured")
            self.status_label.setStyleSheet(f"color: {ERROR_RED};")
            return

        if not self.records:
            self.status_label.setText("Error: No DNS records to analyze")
            self.status_label.setStyleSheet(f"color: {ERROR_RED};")
            return

        self.run_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setText("Analyzing DNS configuration...")
        self.status_label.setStyleSheet("")

        # Clear previous results
        self.score_card.setVisible(False)
        self.category_tree.clear()
        self.details_text.clear()
        self.critical_group.setVisible(False)
        self.recs_group.setVisible(False)

        # Start worker
        self.worker = HealthCheckWorker(self.claude_client, self.domain, self.records)
        self.worker.finished.connect(self.on_health_check_complete)
        self.worker.start()

    def on_health_check_complete(self, success: bool, message: str, result: dict):
        """Handle health check completion."""
        self.progress.setVisible(False)
        self.run_btn.setEnabled(True)

        if not success:
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet(f"color: {ERROR_RED};")
            return

        self.health_result = result
        self.display_results(result)

    def display_results(self, result: dict):
        """Display the health check results."""
        # Overall score
        score = result.get("overall_score", "?")
        status = result.get("overall_status", "Unknown")
        summary = result.get("summary", "")

        self.score_card.setVisible(True)
        self.score_label.setText(score)

        # Color based on score
        score_colors = {
            "A": (SUCCESS_GREEN, WHITE),
            "B": ("#8BC34A", DARK_TEAL),
            "C": (WARNING_YELLOW, DARK_TEAL),
            "D": ("#FF9800", WHITE),
            "F": (ERROR_RED, WHITE)
        }
        bg, fg = score_colors.get(score, (COOL_GRAY, DARK_TEAL))
        self.score_label.setStyleSheet(
            f"background-color: {bg}; color: {fg}; padding: 15px; border-radius: 10px;"
        )

        self.status_text.setText(status)
        self.summary_text.setText(summary)
        self.status_label.setText("Health check completed")
        self.status_label.setStyleSheet(f"color: {SUCCESS_GREEN}; font-weight: bold;")

        # Populate category tree
        self.category_tree.clear()
        categories = result.get("categories", [])

        for category in categories:
            cat_name = category.get("name", "Unknown")
            cat_score = category.get("score", "?")
            cat_status = category.get("status", "unknown")

            # Category item
            cat_item = QTreeWidgetItem([f"{cat_name} [{cat_score}]"])
            cat_item.setData(0, Qt.ItemDataRole.UserRole, category)

            # Color based on status
            if cat_status == "pass":
                cat_item.setForeground(0, QColor(SUCCESS_GREEN))
            elif cat_status == "warning":
                cat_item.setForeground(0, QColor(WARNING_YELLOW))
            elif cat_status == "fail":
                cat_item.setForeground(0, QColor(ERROR_RED))

            # Add findings as children
            for finding in category.get("findings", []):
                check = finding.get("check", "Unknown")
                f_status = finding.get("status", "unknown")

                status_icon = {
                    "pass": "✓",
                    "warning": "⚠",
                    "fail": "✗",
                    "missing": "○"
                }.get(f_status, "?")

                finding_item = QTreeWidgetItem([f"{status_icon} {check}"])
                finding_item.setData(0, Qt.ItemDataRole.UserRole, finding)

                if f_status == "pass":
                    finding_item.setForeground(0, QColor(SUCCESS_GREEN))
                elif f_status == "warning":
                    finding_item.setForeground(0, QColor(WARNING_YELLOW))
                elif f_status in ("fail", "missing"):
                    finding_item.setForeground(0, QColor(ERROR_RED))

                cat_item.addChild(finding_item)

            self.category_tree.addTopLevelItem(cat_item)

        self.category_tree.expandAll()

        # Critical issues
        critical = result.get("critical_issues", [])
        if critical:
            self.critical_group.setVisible(True)
            self.critical_list.setText("• " + "\n• ".join(critical))

        # Recommendations
        recs = result.get("recommendations", [])
        if recs:
            self.recs_group.setVisible(True)
            numbered = [f"{i+1}. {r}" for i, r in enumerate(recs)]
            self.recs_list.setText("\n".join(numbered))

        # Show implement button if there are issues to fix
        score = result.get("overall_score", "A")
        if score not in ("A",):  # Show if not perfect
            self.implement_btn.setVisible(True)

    def on_category_selected(self, item: QTreeWidgetItem, column: int):
        """Handle category/finding selection."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        html = []

        # Check if it's a category or finding
        if "findings" in data:
            # Category
            html.append(f"<h2 style='color: {EDGE_BLUE};'>{data.get('name', 'Category')}</h2>")
            html.append(f"<p><b>Score:</b> {data.get('score', '?')}</p>")
            html.append(f"<p><b>Status:</b> {data.get('status', 'unknown')}</p>")
            html.append("<hr>")

            for finding in data.get("findings", []):
                status = finding.get("status", "unknown")
                color = {
                    "pass": SUCCESS_GREEN,
                    "warning": WARNING_YELLOW,
                    "fail": ERROR_RED,
                    "missing": ERROR_RED
                }.get(status, DARK_TEAL)

                html.append(f"<h3 style='color: {color};'>{finding.get('check', 'Check')}</h3>")
                html.append(f"<p><b>Status:</b> {status.upper()}</p>")

                if finding.get("current"):
                    html.append(f"<p><b>Current:</b> <code>{finding.get('current')}</code></p>")

                html.append(f"<p>{finding.get('message', '')}</p>")

                if finding.get("recommendation"):
                    html.append(
                        f"<p style='background-color: #e3f2fd; padding: 8px; border-radius: 4px;'>"
                        f"<b>Recommendation:</b> {finding.get('recommendation')}</p>"
                    )
                html.append("<br>")
        else:
            # Individual finding
            status = data.get("status", "unknown")
            color = {
                "pass": SUCCESS_GREEN,
                "warning": WARNING_YELLOW,
                "fail": ERROR_RED,
                "missing": ERROR_RED
            }.get(status, DARK_TEAL)

            html.append(f"<h2 style='color: {color};'>{data.get('check', 'Check')}</h2>")
            html.append(f"<p><b>Status:</b> {status.upper()}</p>")

            if data.get("current"):
                html.append(f"<p><b>Current Value:</b></p>")
                html.append(f"<pre style='background-color: {COOL_GRAY}; padding: 10px; "
                           f"border-radius: 4px; overflow-x: auto;'>{data.get('current')}</pre>")

            html.append(f"<p><b>Analysis:</b></p>")
            html.append(f"<p>{data.get('message', 'No details available.')}</p>")

            if data.get("recommendation"):
                html.append(f"<hr>")
                html.append(
                    f"<div style='background-color: #e3f2fd; padding: 12px; border-radius: 6px; "
                    f"border-left: 4px solid {EDGE_BLUE};'>"
                    f"<b>💡 Recommendation:</b><br>{data.get('recommendation')}</div>"
                )

        self.details_text.setHtml("".join(html))

    def generate_fixes(self):
        """Generate fixes based on health assessment."""
        if not self.health_result:
            return

        self.implement_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setText("Generating recommended fixes...")
        self.status_label.setStyleSheet("")

        # Start worker
        self.fix_worker = GenerateFixesWorker(
            self.claude_client, self.domain, self.records, self.health_result
        )
        self.fix_worker.finished.connect(self.on_fixes_generated)
        self.fix_worker.start()

    def on_fixes_generated(self, success: bool, message: str, result: dict):
        """Handle fix generation completion."""
        self.progress.setVisible(False)
        self.implement_btn.setEnabled(True)

        if not success:
            self.status_label.setText(f"Error generating fixes: {message}")
            self.status_label.setStyleSheet(f"color: {ERROR_RED};")
            return

        self.fixes_result = result
        self.display_fixes(result)

    def display_fixes(self, result: dict):
        """Display the generated fixes."""
        fixes = result.get("fixes", [])
        cannot_fix = result.get("cannot_auto_fix", [])
        summary = result.get("summary", "")

        self.status_label.setText(f"Generated {len(fixes)} fixes - {summary}")
        self.status_label.setStyleSheet(f"color: {SUCCESS_GREEN}; font-weight: bold;")

        # Populate fixes table
        self.fixes_table.setRowCount(0)
        self.fix_checkboxes = []

        for fix in fixes:
            row = self.fixes_table.rowCount()
            self.fixes_table.insertRow(row)

            # Checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            self.fix_checkboxes.append(cb)
            self.fixes_table.setCellWidget(row, 0, cb)

            # Action
            action = fix.get("action", "add").upper()
            action_item = QTableWidgetItem(action)
            if action == "ADD":
                action_item.setForeground(QColor(SUCCESS_GREEN))
            elif action == "EDIT":
                action_item.setForeground(QColor(WARNING_YELLOW))
            elif action == "DELETE":
                action_item.setForeground(QColor(ERROR_RED))
            self.fixes_table.setItem(row, 1, action_item)

            # Type
            self.fixes_table.setItem(row, 2, QTableWidgetItem(fix.get("type", "")))

            # Name
            self.fixes_table.setItem(row, 3, QTableWidgetItem(fix.get("name", "@")))

            # Content
            content = fix.get("content", "")
            content_item = QTableWidgetItem(content[:80] + "..." if len(content) > 80 else content)
            content_item.setToolTip(content)
            self.fixes_table.setItem(row, 4, content_item)

            # Reason
            reason = fix.get("reason", "")
            reason_item = QTableWidgetItem(reason)
            reason_item.setToolTip(reason)
            self.fixes_table.setItem(row, 5, reason_item)

        self.fixes_table.resizeRowsToContents()

        # Show manual fixes if any
        if cannot_fix:
            manual_text = "<b>Manual Action Required:</b><br>"
            for item in cannot_fix:
                manual_text += f"• <b>{item.get('issue', '')}</b>: {item.get('manual_action', '')}<br>"
            self.manual_fixes_label.setText(manual_text)
            self.manual_fixes_label.setVisible(True)

        # Show fixes section and apply button
        if fixes:
            self.fixes_group.setVisible(True)
            self.apply_fixes_btn.setVisible(True)
            self.implement_btn.setVisible(False)  # Hide implement button once fixes shown

    def toggle_all_fixes(self, state):
        """Toggle all fix checkboxes."""
        checked = state == Qt.CheckState.Checked.value
        for cb in self.fix_checkboxes:
            cb.setChecked(checked)

    def apply_selected_fixes(self):
        """Apply selected fixes to pending changes."""
        if not self.fixes_result:
            return

        fixes = self.fixes_result.get("fixes", [])
        self.selected_fixes = []

        for i, cb in enumerate(self.fix_checkboxes):
            if cb.isChecked() and i < len(fixes):
                fix = fixes[i]
                self.selected_fixes.append({
                    "action": fix.get("action", "add"),
                    "record": {
                        "type": fix.get("type", "TXT"),
                        "name": fix.get("name", "@"),
                        "content": fix.get("content", ""),
                        "ttl": fix.get("ttl", 1),
                        "priority": fix.get("priority"),
                        "proxied": False,
                    }
                })

        if self.selected_fixes:
            self.fixes_requested.emit(self.selected_fixes)
            QMessageBox.information(
                self, "Fixes Added",
                f"Added {len(self.selected_fixes)} fixes to pending changes.\n\n"
                "Review them in the main window and click 'Apply Changes' when ready."
            )
            self.accept()
        else:
            QMessageBox.warning(self, "No Fixes Selected", "Please select at least one fix to apply.")
