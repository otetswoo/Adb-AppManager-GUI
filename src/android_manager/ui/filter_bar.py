"""Filter bar widget for searching and filtering packages"""

from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QComboBox
)


class FilterBar(QWidget):
    """Search and filter controls"""
    
    filter_changed = pyqtSignal()  # Emits when any filter changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
        # Debounce timer for search input
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_changed.emit)
    
    def _setup_ui(self):
        """Setup UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search package...")
        self.search_input.textChanged.connect(
            lambda: self.search_timer.start(250)
        )
        layout.addWidget(self.search_input)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.currentIndexChanged.connect(
            self.filter_changed.emit
        )
        layout.addWidget(self.type_filter)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.currentIndexChanged.connect(
            self.filter_changed.emit
        )
        layout.addWidget(self.status_filter)
    
    def update_language(self, strings: dict):
        """Update UI language"""
        self.search_input.setPlaceholderText(
            strings.get("search_ph", "Search package...")
        )
        
        # Update type filter
        self.type_filter.blockSignals(True)
        self.type_filter.clear()
        self.type_filter.addItem(
            strings.get("type_all", "All types"), "all"
        )
        self.type_filter.addItem(
            strings.get("type_user", "User"), "User"
        )
        self.type_filter.addItem(
            strings.get("type_sys", "System"), "System"
        )
        self.type_filter.blockSignals(False)
        
        # Update status filter
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem(
            strings.get("status_all", "All statuses"), "all"
        )
        self.status_filter.addItem(
            strings.get("stat_en", "Enabled"), "Enabled"
        )
        self.status_filter.addItem(
            strings.get("stat_dis", "Disabled"), "Disabled"
        )
        self.status_filter.blockSignals(False)
    
    def get_search_text(self) -> str:
        """Get current search text"""
        return self.search_input.text().lower()
    
    def get_type_filter(self) -> str:
        """Get current type filter"""
        return self.type_filter.currentData()
    
    def get_status_filter(self) -> str:
        """Get current status filter"""
        return self.status_filter.currentData()
