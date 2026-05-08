"""Main application window"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QFileDialog,
    QMessageBox, QDialog, QTextEdit, QComboBox,
    QApplication
)
import os
from typing import Optional

from ..core.adb_controller import AdbController, PackageInfo
from ..data.uad_loader import UADLoader
from ..utils.constants import *
from ..utils.themes import THEMES
from ..utils.i18n import STRINGS
from .package_table import PackageTable
from .device_selector import DeviceSelector
from .filter_bar import FilterBar


class MainWindow(QMainWindow):
    """Main window of Android App Manager"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize controllers
        self.adb = AdbController()
        self.uad_loader = UADLoader()
        
        # Application state
        self.current_theme = THEME_DARK
        self.current_lang = LANG_EN
        self.all_packages: list[PackageInfo] = []
        self.packages_buffer: dict = {}
        self.is_loading = False
        
        # Load UAD data
        self.uad_loader.load_lists()
        
        # Setup UI
        self._setup_ui()
        self._apply_theme()
        self._update_language()
        
        # Initial device scan
        self.refresh_devices()
    
    def _setup_ui(self):
        """Initialize all UI components"""
        self.setWindowTitle("Android App Manager")
        
        # Set application icon (use PNG for better compatibility)
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "icon-256.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "Adb-appmanager-icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "Adb-appmanager-icon.jpg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1100, 750)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        
        # Device selector
        self.device_selector = DeviceSelector()
        self.device_selector.device_changed.connect(self._on_device_changed)
        self.device_selector.refresh_requested.connect(self.refresh_devices)
        self.main_layout.addWidget(self.device_selector)
        
        # Language/Theme selectors
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["EN", "RU"])
        self.lang_combo.currentIndexChanged.connect(self._change_language)
        top_bar.addWidget(self.lang_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentIndexChanged.connect(self._change_theme)
        top_bar.addWidget(self.theme_combo)
        
        self.main_layout.addLayout(top_bar)
        
        # Filter bar
        self.filter_bar = FilterBar()
        self.filter_bar.filter_changed.connect(self._apply_filters)
        self.main_layout.addWidget(self.filter_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)
        
        # Package table
        self.package_table = PackageTable()
        self.package_table.package_selected.connect(self._show_package_info)
        self.main_layout.addWidget(self.package_table)
        
        # Package info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setMinimumHeight(90)
        self.info_label.setObjectName("infoArea")
        self.main_layout.addWidget(self.info_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh_apps)
        button_layout.addWidget(self.refresh_btn)
        
        self.install_btn = QPushButton()
        self.install_btn.clicked.connect(self._install_apk)
        button_layout.addWidget(self.install_btn)
        
        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self._export_apk)
        button_layout.addWidget(self.export_btn)
        
        self.batch_btn = QPushButton()
        self.batch_btn.clicked.connect(self._batch_disable)
        button_layout.addWidget(self.batch_btn)
        
        self.enable_btn = QPushButton()
        self.enable_btn.clicked.connect(lambda: self._change_state("enable"))
        button_layout.addWidget(self.enable_btn)
        
        self.disable_btn = QPushButton()
        self.disable_btn.clicked.connect(lambda: self._change_state("disable"))
        button_layout.addWidget(self.disable_btn)
        
        self.uninstall_btn = QPushButton()
        self.uninstall_btn.setObjectName("dangerBtn")
        self.uninstall_btn.clicked.connect(self._uninstall)
        button_layout.addWidget(self.uninstall_btn)
        
        self.action_buttons = [
            self.refresh_btn, self.install_btn, self.export_btn, self.batch_btn,
            self.enable_btn, self.disable_btn, self.uninstall_btn
        ]
        
        self.main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel()
        self.main_layout.addWidget(self.status_label)
    
    def _apply_theme(self):
        """Apply current theme to all widgets"""
        theme = THEMES[self.current_theme]
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}
            
            QTableWidget {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
                gridline-color: {theme['border']};
            }}
            
            QHeaderView::section {{
                background-color: {theme['surface2']};
                border: none;
                border-bottom: 1px solid {theme['border']};
                padding: 4px;
                color: {theme['accent']};
                font-weight: bold;
            }}
            
            QPushButton {{
                background-color: {theme['surface2']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 6px;
            }}
            
            QPushButton:hover {{
                border-color: {theme['accent']};
            }}
            
            QPushButton#dangerBtn {{
                color: {theme['red']};
                border-color: {theme['red']};
            }}
            
            QLineEdit, QComboBox {{
                background-color: {theme['surface2']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            
            QLabel#infoArea {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        
        # Update child widgets
        self.package_table.update_theme(theme)
    
    def _update_language(self):
        """Update all UI text for current language"""
        strings = STRINGS[self.current_lang]
        
        # Update window title
        self.setWindowTitle(strings["title"])
        
        # Update widgets
        self.device_selector.update_language(strings)
        self.filter_bar.update_language(strings)
        self.package_table.update_language(strings)
        
        # Update buttons
        self.refresh_btn.setText(strings["btn_refresh_apps"])
        self.install_btn.setText(strings["btn_install_apk"])
        self.export_btn.setText(strings["btn_export_apk"])
        self.batch_btn.setText(strings["btn_batch"])
        self.enable_btn.setText(strings["btn_enable"])
        self.disable_btn.setText(strings["btn_disable"])
        self.uninstall_btn.setText(strings["btn_uninstall"])
        
        # Update status
        self.status_label.setText(strings["ready"])
    
    def _change_language(self, index: int):
        """Handle language change"""
        self.current_lang = LANG_EN if index == 0 else LANG_RU
        self._update_language()
        self._apply_filters()
    
    def _change_theme(self, index: int):
        """Handle theme change"""
        self.current_theme = THEME_DARK if index == 0 else THEME_LIGHT
        self._apply_theme()
    
    def _set_loading(self, loading: bool):
        """Set loading state"""
        self.is_loading = loading
        self.progress_bar.setVisible(loading)
        self.progress_bar.setRange(0, 0 if loading else 1)
        
        for btn in self.action_buttons:
            btn.setEnabled(not loading)
    
    def refresh_devices(self):
        """Refresh connected devices list"""
        self._set_status(STRINGS[self.current_lang]["loading_pkgs"])
        self.adb.get_devices(self._handle_devices)
    
    def _handle_devices(self, output: str):
        """Handle device list response"""
        devices = []
        
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        
        self.device_selector.update_devices(devices)
        self._set_status(STRINGS[self.current_lang]["ready"])
    
    def _on_device_changed(self, device_id: str):
        """Handle device selection change"""
        if not device_id:  # Empty device ID means no device selected
            return
        self._load_device_info()
        self.load_packages()
    
    def _load_device_info(self):
        """Load device information"""
        device = self.device_selector.get_selected_device()
        if not device:
            return
        
        self.adb.get_device_properties(
            device, self._handle_device_info
        )
    
    def _handle_device_info(self, output: str):
        """Handle device info response"""
        props = {}
        
        for line in output.splitlines():
            if "]: [" not in line:
                continue
            try:
                key, value = line.split("]: [", 1)
                props[key[1:]] = value[:-1]
            except:
                continue
        
        model = props.get("ro.product.model", "Unknown")
        brand = props.get("ro.product.brand", "").capitalize()
        version = props.get("ro.build.version.release", "?")
        
        info = f"{brand} {model} | Android {version}".strip()
        self.device_selector.update_device_info(info)
    
    def load_packages(self):
        """Load all packages from device"""
        device = self.device_selector.get_selected_device()
        if not device:
            return
        
        self._set_loading(True)
        self._set_status(STRINGS[self.current_lang]["loading_pkgs"])
        self.adb.get_packages(device, callback=self._handle_packages)
    
    def _handle_packages(self, output: str):
        """Handle packages list response"""
        self.packages_buffer.clear()
        
        for line in output.splitlines():
            if not line.startswith("package:"):
                continue
            try:
                path, package = line[8:].rsplit("=", 1)
                self.packages_buffer[package.strip()] = {
                    "path": path,
                    "status": STATUS_ENABLED,
                }
            except:
                continue
        
        # Load disabled packages
        device = self.device_selector.get_selected_device()
        self.adb.get_disabled_packages(
            device, callback=self._handle_disabled_packages
        )
    
    def _handle_disabled_packages(self, output: str):
        """Handle disabled packages response"""
        for line in output.splitlines():
            package = line.replace("package:", "").strip()
            if package in self.packages_buffer:
                self.packages_buffer[package]["status"] = STATUS_DISABLED
        
        # Build package list
        self.all_packages.clear()
        
        for package, info in self.packages_buffer.items():
            app_type = (
                TYPE_SYSTEM
                if any(p in info["path"] for p in SYSTEM_PATHS)
                else TYPE_USER
            )
            
            self.all_packages.append(
                PackageInfo(
                    package=package,
                    status=info["status"],
                    app_type=app_type,
                    path=info["path"],
                )
            )
        
        self.all_packages.sort(key=lambda x: x.package)
        self._apply_filters()
        self._set_loading(False)
        
        self._set_status(
            STRINGS[self.current_lang]["loaded_count"].format(
                len(self.all_packages)
            )
        )
    
    def _apply_filters(self):
        """Apply search and filter criteria"""
        search = self.filter_bar.get_search_text()
        type_filter = self.filter_bar.get_type_filter()
        status_filter = self.filter_bar.get_status_filter()
        
        filtered = [
            pkg for pkg in self.all_packages
            if (not search or search in pkg.package.lower())
            and (type_filter == "all" or pkg.app_type == type_filter)
            and (status_filter == "all" or pkg.status == status_filter)
        ]
        
        self.package_table.set_packages(filtered)
    
    def _show_package_info(self, package: str):
        """Show detailed info for selected package"""
        app = next(
            (a for a in self.all_packages if a.package == package),
            None
        )
        if not app:
            return
        
        theme = THEMES[self.current_theme]
        strings = STRINGS[self.current_lang]
        
        status_text = (
            strings["stat_en"]
            if app.status == STATUS_ENABLED
            else strings["stat_dis"]
        )
        status_color = (
            theme["green"]
            if app.status == STATUS_ENABLED
            else theme["red"]
        )
        
        text = (
            f"<b>{package}</b> | "
            f"<span style='color:{status_color}'>{status_text}</span><br>"
        )
        
        # Add UAD info if available
        uad_info = self.uad_loader.get_app_info(package)
        if uad_info:
            text += (
                f"<p><b>List:</b> {uad_info.get('list', '?')} | "
                f"<b>Removal:</b> {uad_info.get('removal', '?')}</p>"
                f"<p style='color:{theme['text_dim']}'>"
                f"{uad_info.get('description', '')}</p>"
            )
        else:
            text += (
                f"<p style='color:{theme['text_dim']}'>"
                f"{strings['no_info']}</p>"
            )
        
        self.info_label.setText(text)
    
    def _change_state(self, action: str):
        """Enable/disable selected package"""
        device = self.device_selector.get_selected_device()
        package = self.package_table.get_selected_package()
        
        if not device or not package:
            return
        
        self.adb.change_package_state(
            device, action, package,
            callback=lambda output: self._handle_action_result(output, package),
            error_callback=lambda msg: self._handle_error(package, msg)
        )
    
    def _uninstall(self):
        """Uninstall selected package"""
        device = self.device_selector.get_selected_device()
        package = self.package_table.get_selected_package()
        
        if not device or not package:
            return
        
        # Warning for system apps
        app = next(
            (a for a in self.all_packages if a.package == package),
            None
        )
        if app and app.app_type == TYPE_SYSTEM:
            strings = STRINGS[self.current_lang]
            result = QMessageBox.warning(
                self, "Warning", strings["confirm_sys"],
                QMessageBox.Yes | QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return
        
        self.adb.uninstall_package(
            device, package,
            callback=lambda output: self._handle_action_result(output, package),
            error_callback=lambda msg: self._handle_error(package, msg)
        )
    
    def _install_apk(self):
        """Install APK file"""
        device = self.device_selector.get_selected_device()
        if not device:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select APK", "", "APK files (*.apk)"
        )
        if not file_path:
            return
        
        self._set_loading(True)
        
        def on_finish(output):
            self._set_loading(False)
            if "Success" in output:
                QMessageBox.information(
                    self, "Success",
                    STRINGS[self.current_lang]["install_ok"]
                )
            self.load_packages()
        
        self.adb.install_apk(device, file_path, callback=on_finish)
    
    def _export_apk(self):
        """Export APK file from device"""
        device = self.device_selector.get_selected_device()
        package = self.package_table.get_selected_package()
        
        if not device or not package:
            strings = STRINGS[self.current_lang]
            QMessageBox.warning(
                self, "Warning",
                strings["err_no_dev"] if not device else "Select a package to export"
            )
            return
        
        # Get default filename from package name
        default_filename = f"{package}.apk"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save APK", default_filename, "APK files (*.apk)"
        )
        if not file_path:
            return
        
        self._set_loading(True)
        
        def on_finish(output):
            self._set_loading(False)
            strings = STRINGS[self.current_lang]
            if "Success" in output or "pull" in output.lower() or os.path.exists(file_path):
                QMessageBox.information(
                    self, "Success",
                    strings["export_ok"].format(file_path)
                )
                self.load_packages()
            else:
                QMessageBox.critical(
                    self, "Error",
                    strings["export_err"].format(output)
                )
        
        def on_error(error_msg):
            self._set_loading(False)
            strings = STRINGS[self.current_lang]
            QMessageBox.critical(
                self, "Error",
                strings["export_err"].format(error_msg)
            )
        
        self.adb.export_apk(device, package, file_path, callback=on_finish, error_callback=on_error)
    
    def _batch_disable(self):
        """Open batch disable dialog"""
        device = self.device_selector.get_selected_device()
        if not device:
            return
        
        strings = STRINGS[self.current_lang]
        
        dialog = QDialog(self)
        dialog.setWindowTitle(strings["btn_batch"])
        dialog.resize(500, 450)
        
        layout = QVBoxLayout(dialog)
        editor = QTextEdit()
        layout.addWidget(editor)
        
        run_btn = QPushButton(strings["btn_disable"])
        layout.addWidget(run_btn)
        
        def run_batch():
            packages = [
                line.strip()
                for line in editor.toPlainText().splitlines()
                if line.strip()
            ]
            if not packages:
                return
            
            self._set_loading(True)
            
            # Disable packages sequentially
            for i, package in enumerate(packages):
                self.adb.change_package_state(
                    device, "disable", package,
                    callback=lambda out, p=package: None  # ignore individual results
                )
            
            dialog.accept()
            QTimer.singleShot(500, self.load_packages)
        
        run_btn.clicked.connect(run_batch)
        dialog.exec_()
    
    def _handle_action_result(self, output: str, package: str):
        """Handle result of enable/disable/uninstall"""
        strings = STRINGS[self.current_lang]
        
        if any(x in output for x in [
            "Security exception", "Permission denied", "not allowed"
        ]):
            QMessageBox.critical(
                self, "Error",
                strings["err_protected"].format(package)
            )
        elif "Error" in output or "Failure" in output:
            QMessageBox.warning(
                self, "Error",
                strings["err_cmd"].format(output)
            )
        
        QTimer.singleShot(400, self.load_packages)
    
    def _handle_error(self, package: str, error_msg: str):
        """Handle ADB command error"""
        strings = STRINGS[self.current_lang]
        QMessageBox.critical(
            self, "Error",
            strings["err_cmd"].format(error_msg)
        )
    
    def _set_status(self, text: str):
        """Update status bar text"""
        self.status_label.setText(text)
    
    def refresh_apps(self):
        """Refresh apps list"""
        self.load_packages()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.adb.cleanup()
        super().closeEvent(event)
