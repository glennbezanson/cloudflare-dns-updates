"""Diff viewer widget for showing changes."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QFont


class DiffViewer(QWidget):
    """Widget for displaying before/after comparison of DNS changes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the diff viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("Pending Changes")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Diff content
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        self.diff_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.diff_text)

    def set_changes(self, pending_changes: list[dict], current_records: list[dict]):
        """
        Display pending changes with diff formatting.

        Args:
            pending_changes: List of pending change operations
            current_records: Current DNS records for context
        """
        self.diff_text.clear()

        if not pending_changes:
            self.diff_text.setHtml("<i>No pending changes</i>")
            return

        html_parts = []

        # Group changes by action
        adds = [c for c in pending_changes if c.get("action") == "add"]
        edits = [c for c in pending_changes if c.get("action") == "edit"]
        deletes = [c for c in pending_changes if c.get("action") == "delete"]

        # Additions
        if adds:
            html_parts.append("<h3 style='color: #22863a;'>+ Additions</h3>")
            for change in adds:
                record = change.get("record", {})
                html_parts.append(self._format_add(record))

        # Modifications
        if edits:
            html_parts.append("<h3 style='color: #b08800;'>~ Modifications</h3>")
            for change in edits:
                old_record = change.get("old_record", {})
                new_record = change.get("record", {})
                html_parts.append(self._format_edit(old_record, new_record))

        # Deletions
        if deletes:
            html_parts.append("<h3 style='color: #cb2431;'>- Deletions</h3>")
            for change in deletes:
                record = change.get("record", {})
                html_parts.append(self._format_delete(record))

        self.diff_text.setHtml("".join(html_parts))

    def _format_add(self, record: dict) -> str:
        """Format an addition."""
        rtype = record.get("type", "?")
        name = record.get("name", "?")
        content = record.get("content", "?")
        ttl = record.get("ttl", "Auto")
        if ttl == 1:
            ttl = "Auto"

        return f"""
        <div style='background-color: #e6ffed; padding: 8px; margin: 4px 0; border-left: 3px solid #22863a;'>
            <code>+ {rtype} {name}</code><br>
            <code style='color: #22863a;'>  Content: {self._escape_html(content)}</code><br>
            <code style='color: #666;'>  TTL: {ttl}</code>
        </div>
        """

    def _format_edit(self, old_record: dict, new_record: dict) -> str:
        """Format a modification."""
        rtype = new_record.get("type", "?")
        name = new_record.get("name", "?")

        old_content = old_record.get("content", "")
        new_content = new_record.get("content", "")
        old_ttl = old_record.get("ttl", 1)
        new_ttl = new_record.get("ttl", 1)

        if old_ttl == 1:
            old_ttl = "Auto"
        if new_ttl == 1:
            new_ttl = "Auto"

        parts = [f"""
        <div style='background-color: #fffbdd; padding: 8px; margin: 4px 0; border-left: 3px solid #b08800;'>
            <code>~ {rtype} {name}</code><br>
        """]

        if old_content != new_content:
            parts.append(f"<code style='color: #cb2431;'>  - Content: {self._escape_html(old_content)}</code><br>")
            parts.append(f"<code style='color: #22863a;'>  + Content: {self._escape_html(new_content)}</code><br>")

        if old_ttl != new_ttl:
            parts.append(f"<code style='color: #666;'>  TTL: {old_ttl} → {new_ttl}</code><br>")

        parts.append("</div>")
        return "".join(parts)

    def _format_delete(self, record: dict) -> str:
        """Format a deletion."""
        rtype = record.get("type", "?")
        name = record.get("name", "?")
        content = record.get("content", "?")

        return f"""
        <div style='background-color: #ffeef0; padding: 8px; margin: 4px 0; border-left: 3px solid #cb2431;'>
            <code>- {rtype} {name}</code><br>
            <code style='color: #cb2431;'>  Content: {self._escape_html(content)}</code>
        </div>
        """

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

    def clear(self):
        """Clear the diff view."""
        self.diff_text.clear()
