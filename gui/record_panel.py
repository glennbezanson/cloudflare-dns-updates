"""DNS record list panel."""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QComboBox, QHeaderView, QMessageBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from config.settings import DNS_RECORD_TYPES


class RecordPanel(QWidget):
    """Panel for displaying and managing DNS records."""

    record_selected = pyqtSignal(dict)  # Selected record
    add_requested = pyqtSignal()
    quick_add_requested = pyqtSignal()  # Paste request / natural language input
    edit_requested = pyqtSignal(dict)
    delete_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.records = []
        self.current_zone_id = ""
        self.current_zone_name = ""

        self.setup_ui()

    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with zone name
        self.header = QLabel("DNS Records")
        self.header.setProperty("heading", True)  # Edge Solutions heading style
        layout.addWidget(self.header)

        # Filter row
        filter_layout = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter records...")
        self.search_edit.textChanged.connect(self.filter_records)
        filter_layout.addWidget(self.search_edit)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.addItems(DNS_RECORD_TYPES)
        self.type_filter.currentTextChanged.connect(self.filter_records)
        filter_layout.addWidget(self.type_filter)

        layout.addLayout(filter_layout)

        # Record table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Type", "Name", "Content", "TTL", "Proxied", "ID"
        ])

        # Hide ID column (used for reference)
        self.table.setColumnHidden(5, True)

        # Configure table
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_double_click)

        layout.addWidget(self.table)

        # Action buttons
        btn_layout = QHBoxLayout()

        self.quick_add_btn = QPushButton("Paste Request")
        self.quick_add_btn.setObjectName("pasteRequestBtn")  # For accent styling
        self.quick_add_btn.setToolTip("Paste a ticket or request - Claude will parse it into DNS records")
        self.quick_add_btn.clicked.connect(lambda: self.quick_add_requested.emit())
        btn_layout.addWidget(self.quick_add_btn)

        self.add_btn = QPushButton("+ Add Record")
        self.add_btn.clicked.connect(lambda: self.add_requested.emit())
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(lambda: self.refresh_requested())
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)

    def refresh_requested(self):
        """Signal that refresh is requested - parent handles this."""
        pass  # Connected externally

    def set_zone(self, zone_id: str, zone_name: str):
        """Set the current zone."""
        self.current_zone_id = zone_id
        self.current_zone_name = zone_name
        self.header.setText(f"DNS Records for: {zone_name}")

    def set_records(self, records: list[dict]):
        """Set the records to display."""
        self.records = records
        self.populate_table()

    def populate_table(self, filter_text: str = "", type_filter: str = ""):
        """Populate the record table."""
        self.table.setRowCount(0)

        for record in self.records:
            record_type = record.get("type", "")
            name = record.get("name", "")
            content = record.get("content", "")
            ttl = record.get("ttl", 1)
            proxied = record.get("proxied", False)
            record_id = record.get("id", "")

            # Apply filters
            if filter_text:
                search_str = f"{name} {content}".lower()
                if filter_text.lower() not in search_str:
                    continue

            if type_filter and type_filter != "All Types":
                if record_type != type_filter:
                    continue

            # Add row
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(record_type))
            self.table.setItem(row, 1, QTableWidgetItem(name))

            # Truncate long content for display
            display_content = content[:100] + "..." if len(content) > 100 else content
            self.table.setItem(row, 2, QTableWidgetItem(display_content))

            ttl_display = "Auto" if ttl == 1 else str(ttl)
            self.table.setItem(row, 3, QTableWidgetItem(ttl_display))

            proxied_display = "Yes" if proxied else "No"
            proxied_item = QTableWidgetItem(proxied_display)
            if proxied:
                proxied_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(row, 4, proxied_item)

            self.table.setItem(row, 5, QTableWidgetItem(record_id))

    def filter_records(self):
        """Filter records based on search and type."""
        filter_text = self.search_edit.text()
        type_filter = self.type_filter.currentText()
        self.populate_table(filter_text, type_filter)

    def on_selection_changed(self):
        """Handle selection change."""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        if has_selection:
            record = self.get_selected_record()
            if record:
                self.record_selected.emit(record)

    def on_double_click(self, item):
        """Handle double-click to edit."""
        record = self.get_selected_record()
        if record:
            self.edit_requested.emit(record)

    def on_edit_clicked(self):
        """Handle edit button click."""
        record = self.get_selected_record()
        if record:
            self.edit_requested.emit(record)

    def on_delete_clicked(self):
        """Handle delete button click."""
        record = self.get_selected_record()
        if record:
            self.delete_requested.emit(record)

    def get_selected_record(self) -> Optional[dict]:
        """Get the currently selected record."""
        row = self.table.currentRow()
        if row < 0:
            return None

        record_id = self.table.item(row, 5).text()

        # Find the full record
        for record in self.records:
            if record.get("id") == record_id:
                return record

        return None

    def clear(self):
        """Clear the table."""
        self.records = []
        self.table.setRowCount(0)
        self.header.setText("DNS Records")
        self.current_zone_id = ""
        self.current_zone_name = ""
