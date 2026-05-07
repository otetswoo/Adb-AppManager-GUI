"""Custom table widget for displaying packages"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
    QApplication,
)
from typing import List, Optional

from ..core.adb_controller import PackageInfo
from ..utils.themes import THEMES
from ..utils.i18n import STRINGS


class PackageTable(QTableWidget):
    """Table widget for displaying Android packages"""
    
    package_selected = pyqtSignal(str)  # Emits selected package name
    context_menu_requested = pyqtSignal(str)  # Emits package for context menu
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._packages: List[PackageInfo] = []
        self._theme = THEMES["dark"]
        self._strings = STRINGS["en"]
    
    def _setup_ui(self):
        """Initialize table UI"""
        self.setColumnCount(3)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Configure headers
        self.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.setHorizontalHeaderLabels(["Package", "Status", "Type"])
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect selection change
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def update_theme(self, theme_data: dict):
        """Update table theme"""
        self._theme = theme_data
        self._update_colors()
    
    def update_language(self, strings: dict):
        """Update table language"""
        self._strings = strings
        self.setHorizontalHeaderLabels(["Package", "Status", "Type"])
    
    def set_packages(self, packages: List[PackageInfo]):
        """Set packages to display"""
        self._packages = packages
        self._populate_table()
    
    def _populate_table(self):
        """Fill table with package data"""
        self.setRowCount(0)
        
        for package in self._packages:
            row = self.rowCount()
            self.insertRow(row)
            
            # Create items
            items = [
                QTableWidgetItem(package.package),
                QTableWidgetItem(self._get_status_text(package.status)),
                QTableWidgetItem(self._get_type_text(package.app_type)),
            ]
            
            # Set colors
            status_color = (
                self._theme["green"] 
                if package.status == "Enabled" 
                else self._theme["red"]
            )
            row_color = QColor(
                self._theme["row_disabled"] 
                if package.status == "Disabled" 
                else self._theme["row_enabled"]
            )
            
            for col, item in enumerate(items):
                item.setBackground(row_color)
                if col == 1:  # Status column
                    item.setForeground(QColor(status_color))
                self.setItem(row, col, item)
    
    def _get_status_text(self, status: str) -> str:
        """Get localized status text"""
        if status == "Enabled":
            return self._strings.get("stat_en", "Enabled")
        return self._strings.get("stat_dis", "Disabled")
    
    def _get_type_text(self, app_type: str) -> str:
        """Get localized type text"""
        if app_type == "System":
            return self._strings.get("type_sys", "System")
        return self._strings.get("type_user", "User")
    
    def get_selected_package(self) -> Optional[str]:
        """Get currently selected package name"""
        row = self.currentRow()
        if row >= 0:
            item = self.item(row, 0)
            if item:
                return item.text()
        return None
    
    def _on_selection_changed(self):
        """Handle selection change"""
        package = self.get_selected_package()
        if package:
            self.package_selected.emit(package)
    
    def _show_context_menu(self, pos):
        """Show context menu for package"""
        item = self.itemAt(pos)
        if not item:
            return
        
        menu = QMenu()
        copy_action = menu.addAction(
            self._strings.get("copy_pkg", "Copy package")
        )
        
        action = menu.exec_(self.viewport().mapToGlobal(pos))
        
        if action == copy_action:
            package = self.item(item.row(), 0).text()
            QApplication.clipboard().setText(package)
    
    def _update_colors(self):
        """Update table colors based on current theme"""
        self._populate_table()
