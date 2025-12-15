"""Zone selector panel."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class ZonePanel(QWidget):
    """Panel for selecting and managing zones/domains."""

    zone_selected = pyqtSignal(str, str)  # zone_id, zone_name

    def __init__(self, parent=None, cloudflare_client=None):
        super().__init__(parent)
        self.cf_client = cloudflare_client
        self.zones = []

        self.setup_ui()

    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("Zones")
        header.setProperty("heading", True)
        layout.addWidget(header)

        # Search/filter
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter zones...")
        self.search_edit.textChanged.connect(self.filter_zones)
        layout.addWidget(self.search_edit)

        # Zone list
        self.zone_list = QListWidget()
        self.zone_list.itemClicked.connect(self.on_zone_clicked)
        layout.addWidget(self.zone_list)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh Zones")
        self.refresh_btn.clicked.connect(self.load_zones)
        layout.addWidget(self.refresh_btn)

    def set_client(self, client):
        """Set the Cloudflare client."""
        self.cf_client = client

    def load_zones(self):
        """Load zones from Cloudflare."""
        if not self.cf_client:
            QMessageBox.warning(self, "Error", "Cloudflare not configured")
            return

        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Loading...")

        try:
            self.zones = self.cf_client.list_zones()
            self.populate_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load zones: {e}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("Refresh Zones")

    def populate_list(self, filter_text: str = ""):
        """Populate the zone list."""
        self.zone_list.clear()

        for zone in self.zones:
            name = zone.get("name", "")
            zone_id = zone.get("id", "")
            status = zone.get("status", "")

            # Apply filter
            if filter_text and filter_text.lower() not in name.lower():
                continue

            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, zone_id)

            # Style based on status
            if status == "active":
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "pending":
                item.setForeground(Qt.GlobalColor.darkYellow)

            # Add paused indicator
            if zone.get("paused"):
                item.setText(f"{name} (paused)")
                item.setForeground(Qt.GlobalColor.gray)

            self.zone_list.addItem(item)

    def filter_zones(self, text: str):
        """Filter zones by search text."""
        self.populate_list(text)

    def on_zone_clicked(self, item: QListWidgetItem):
        """Handle zone selection."""
        zone_id = item.data(Qt.ItemDataRole.UserRole)
        zone_name = item.text().replace(" (paused)", "")
        self.zone_selected.emit(zone_id, zone_name)

    def get_selected_zone(self) -> tuple[str, str]:
        """Get currently selected zone. Returns (zone_id, zone_name)."""
        item = self.zone_list.currentItem()
        if item:
            zone_id = item.data(Qt.ItemDataRole.UserRole)
            zone_name = item.text().replace(" (paused)", "")
            return zone_id, zone_name
        return "", ""
