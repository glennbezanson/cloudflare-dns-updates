"""Review dialog for Claude AI integration."""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar,
    QGroupBox, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from gui.widgets.diff_viewer import DiffViewer
from gui.styles import (
    EDGE_BLUE, EDGE_GREEN, SUCCESS_GREEN, WARNING_YELLOW, ERROR_RED,
    DARK_TEAL, WHITE
)


class ReviewWorker(QThread):
    """Worker thread for Claude API calls."""

    finished = pyqtSignal(bool, str, dict)  # success, message, result

    def __init__(self, claude_client, domain, current_records, pending_changes):
        super().__init__()
        self.claude_client = claude_client
        self.domain = domain
        self.current_records = current_records
        self.pending_changes = pending_changes

    def run(self):
        success, message, result = self.claude_client.review_changes(
            self.domain,
            self.current_records,
            self.pending_changes
        )
        self.finished.emit(success, message, result)


class ReviewDialog(QDialog):
    """Dialog for reviewing DNS changes with Claude AI."""

    def __init__(self, parent=None, claude_client=None, domain: str = "",
                 current_records: list = None, pending_changes: list = None):
        super().__init__(parent)
        self.claude_client = claude_client
        self.domain = domain
        self.current_records = current_records or []
        self.pending_changes = pending_changes or []
        self.review_result = None
        self.approved = False

        self.setWindowTitle("Review Changes with Claude AI")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Reviewing changes for: {self.domain}")
        header.setProperty("heading", True)
        layout.addWidget(header)

        # Pending changes section
        changes_group = QGroupBox("Pending Changes")
        changes_layout = QVBoxLayout(changes_group)

        self.diff_viewer = DiffViewer()
        self.diff_viewer.set_changes(self.pending_changes, self.current_records)
        changes_layout.addWidget(self.diff_viewer)

        layout.addWidget(changes_group)

        # Claude review section
        review_group = QGroupBox("Claude AI Review")
        review_layout = QVBoxLayout(review_group)

        # Review button and progress
        review_row = QHBoxLayout()

        self.review_btn = QPushButton("Get AI Review")
        self.review_btn.clicked.connect(self.start_review)
        review_row.addWidget(self.review_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)  # Indeterminate
        review_row.addWidget(self.progress)

        review_row.addStretch()
        review_layout.addLayout(review_row)

        # Assessment badge
        self.assessment_label = QLabel("")
        self.assessment_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.assessment_label.setVisible(False)
        review_layout.addWidget(self.assessment_label)

        # Review content
        self.review_text = QTextEdit()
        self.review_text.setReadOnly(True)
        self.review_text.setFont(QFont("Segoe UI", 10))
        self.review_text.setPlaceholderText(
            "Click 'Get AI Review' to have Claude analyze your changes..."
        )
        review_layout.addWidget(self.review_text)

        layout.addWidget(review_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.approve_btn = QPushButton("Apply Changes")
        self.approve_btn.setEnabled(False)
        self.approve_btn.clicked.connect(self.approve_changes)
        btn_layout.addWidget(self.approve_btn)

        layout.addLayout(btn_layout)

    def start_review(self):
        """Start the Claude review process."""
        if not self.claude_client:
            self.review_text.setHtml(
                "<span style='color: red;'>Claude AI not configured. "
                "Please set up your Anthropic API key in Settings.</span>"
            )
            return

        self.review_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.review_text.setPlainText("Analyzing changes...")

        # Start worker thread
        self.worker = ReviewWorker(
            self.claude_client,
            self.domain,
            self.current_records,
            self.pending_changes
        )
        self.worker.finished.connect(self.on_review_complete)
        self.worker.start()

    def on_review_complete(self, success: bool, message: str, result: dict):
        """Handle review completion."""
        self.progress.setVisible(False)
        self.review_btn.setEnabled(True)

        if not success:
            self.review_text.setHtml(
                f"<span style='color: red;'>Review failed: {message}</span>"
            )
            return

        self.review_result = result
        self.display_review(result)

        # Enable approve button based on assessment
        assessment = result.get("assessment", "CAUTION")
        if assessment in ["SAFE", "CAUTION"]:
            self.approve_btn.setEnabled(True)

    def display_review(self, result: dict):
        """Display the review results."""
        assessment = result.get("assessment", "UNKNOWN")
        issues = result.get("issues", [])
        warnings = result.get("warnings", [])
        recommendations = result.get("recommendations", [])
        summary = result.get("summary", "")

        # Assessment badge
        self.assessment_label.setVisible(True)
        if assessment == "SAFE":
            self.assessment_label.setStyleSheet(
                f"background-color: {SUCCESS_GREEN}; color: {WHITE}; padding: 10px; "
                "font-size: 14px; font-weight: bold; border-radius: 5px;"
            )
            self.assessment_label.setText("SAFE - Changes look good!")
        elif assessment == "CAUTION":
            self.assessment_label.setStyleSheet(
                f"background-color: {WARNING_YELLOW}; color: {DARK_TEAL}; padding: 10px; "
                "font-size: 14px; font-weight: bold; border-radius: 5px;"
            )
            self.assessment_label.setText("CAUTION - Review warnings before proceeding")
        else:  # DANGER
            self.assessment_label.setStyleSheet(
                f"background-color: {ERROR_RED}; color: {WHITE}; padding: 10px; "
                "font-size: 14px; font-weight: bold; border-radius: 5px;"
            )
            self.assessment_label.setText("DANGER - Critical issues found!")

        # Build HTML content
        html = []

        # Summary
        html.append(f"<h3 style='color: {EDGE_BLUE};'>Summary</h3><p>{summary}</p>")

        # Issues
        if issues:
            html.append(f"<h3 style='color: {ERROR_RED};'>Issues</h3><ul>")
            for issue in issues:
                html.append(f"<li style='color: {ERROR_RED};'>{issue}</li>")
            html.append("</ul>")

        # Warnings
        if warnings:
            html.append(f"<h3 style='color: {WARNING_YELLOW};'>Warnings</h3><ul>")
            for warning in warnings:
                html.append(f"<li>{warning}</li>")
            html.append("</ul>")

        # Recommendations
        if recommendations:
            html.append(f"<h3 style='color: {EDGE_BLUE};'>Recommendations</h3><ul>")
            for rec in recommendations:
                html.append(f"<li>{rec}</li>")
            html.append("</ul>")

        self.review_text.setHtml("".join(html))

    def approve_changes(self):
        """Approve and apply changes."""
        self.approved = True
        self.accept()

    def get_result(self) -> tuple[bool, Optional[dict]]:
        """Get the dialog result. Returns (approved, review_result)."""
        return self.approved, self.review_result
