"""Device selection widget"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel
)
from typing import List


class DeviceSelector(QWidget):
    """Widget for selecting Android device"""
    
    device_changed = pyqtSignal(str)  # Emits selected device ID
    refresh_requested = pyqtSignal()  # Emits when refresh is requested
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Device label
        self.device_label = QLabel("Device:")
        layout.addWidget(self.device_label)
        
        # Device combo box
        self.device_combo = QComboBox()
        self.device_combo.currentTextChanged.connect(
            self._on_device_changed
        )
        layout.addWidget(self.device_combo)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(
            self.refresh_requested.emit
        )
        layout.addWidget(self.refresh_button)
        
        # Device info label
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        layout.addStretch()
    
    def update_devices(self, devices: List[str]):
        """Update device list"""
        current = self.device_combo.currentText()
        
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        self.device_combo.addItems(devices)
        
        # Restore selection if possible
        if current and current in devices:
            self.device_combo.setCurrentText(current)
        
        self.device_combo.blockSignals(False)
        
        # Update info label
        if not devices:
            self.info_label.setText("No devices connected")
        elif len(devices) == 1:
            self.info_label.setText("")
            self._on_device_changed(devices[0])
    
    def update_device_info(self, info: str):
        """Update device info display"""
        self.info_label.setText(info)
    
    def update_language(self, strings: dict):
        """Update UI language"""
        self.device_label.setText(strings.get("device_lbl", "Device:"))
        self.refresh_button.setText(strings.get("refresh_dev", "Refresh"))
        
        if not self.device_combo.count():
            self.info_label.setText(
                strings.get("no_devices", "No devices connected")
            )
    
    def get_selected_device(self) -> str:
        """Get currently selected device ID"""
        return self.device_combo.currentText()
    
    def _on_device_changed(self, device_id: str):
        """Handle device selection change"""
        if device_id:
            self.device_changed.emit(device_id)
