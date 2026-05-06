import sys
import os
import subprocess
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QColor

os.environ["QT_QPA_PLATFORM"] = "wayland"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


class AdbWorker(QThread):
    output = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.check_output(
                self.command, shell=True, text=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            result = e.output
        self.output.emit(result)


class AndroidAppManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Android App Manager")
        self.setGeometry(100, 100, 950, 650)
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: #ffffff; }
            QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget {
                color: #ffffff; background-color: #3c3f41;
                border: 1px solid #555555; padding: 5px; border-radius: 3px;
            }
            QPushButton:hover { background-color: #4c5052; }
            QTableWidget { gridline-color: #555555; }
            QHeaderView::section { background-color: #3c3f41; color: #ffffff; padding: 5px; border: 1px solid #555555; }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.all_apps = []
        self.workers = []
        self.temp_packages = []
        self.uad_info = {}

        self.load_uad_lists()
        self.setup_ui()
        self.refresh_devices()

    def load_uad_lists(self):
        try:
            with open("uad_lists.json", "r", encoding="utf-8") as f:
                for entry in json.load(f):
                    if "id" in entry:
                        self.uad_info[entry["id"]] = entry
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Ошибка загрузки uad_lists.json: {e}")

    def setup_ui(self):
        device_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        self.device_combo.currentIndexChanged.connect(self.on_device_selected)

        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.refresh_devices)

        device_layout.addWidget(QLabel("Select Device: "))
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.refresh_btn)
        device_layout.addStretch()
        self.main_layout.addLayout(device_layout)

        self.device_info_label = QLabel("Device Info: Not connected")
        self.main_layout.addWidget(self.device_info_label)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by package name...")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_apps)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        self.main_layout.addLayout(search_layout)

        self.app_table = QTableWidget()
        self.app_table.setColumnCount(4)
        self.app_table.setHorizontalHeaderLabels(["App Name", "Package Name", "Status", "Type"])
        self.app_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.app_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.app_table.setSelectionMode(QTableWidget.SingleSelection)
        self.main_layout.addWidget(self.app_table)
        self.app_table.itemSelectionChanged.connect(self.update_app_desc)

        self.app_desc_label = QLabel()
        self.app_desc_label.setWordWrap(True)
        self.app_desc_label.setMinimumHeight(80)
        self.app_desc_label.setStyleSheet("background-color: #232629; color: #ffffff; border: 1px solid #555555; padding: 8px; border-radius: 3px;")
        self.main_layout.addWidget(self.app_desc_label)
        self.clear_app_desc()

        action_layout = QHBoxLayout()
        self.install_apk_btn = QPushButton("Install APK")
        self.enable_btn = QPushButton("Enable")
        self.disable_btn = QPushButton("Disable")
        self.uninstall_btn = QPushButton("Uninstall")

        self.install_apk_btn.clicked.connect(self.install_apk)
        self.enable_btn.clicked.connect(lambda: self.change_app_state("enable"))
        self.disable_btn.clicked.connect(lambda: self.change_app_state("disable"))
        self.uninstall_btn.clicked.connect(self.uninstall_app)

        action_layout.addWidget(self.install_apk_btn)
        action_layout.addWidget(self.enable_btn)
        action_layout.addWidget(self.disable_btn)
        action_layout.addWidget(self.uninstall_btn)
        self.main_layout.addLayout(action_layout)

    def on_device_selected(self, index):
        if index == -1:
            return
        self.all_apps.clear()
        self.app_table.setRowCount(0)
        self.app_table.clearContents()
        self.clear_app_desc()
        self.load_device_info()
        self.load_all_apps()

    def clear_app_desc(self):
        self.app_desc_label.setText("<b>App Description:</b><br>Select an application to view details.")

    def update_app_desc(self):
        row = self.app_table.currentRow()
        if row == -1:
            self.clear_app_desc()
            return

        package = self.app_table.item(row, 1).text()
        info = self.uad_info.get(package)

        if not info:
            self.app_desc_label.setText(f"<b>App Description:</b><br>No information available for <code>{package}</code>.")
            return

        app_type = info.get("list", "Unknown")
        desc = info.get("description", "No description available.")
        removal = info.get("removal", "Recommended")

        colors = {"Recommended": "#4CAF50", "Advanced": "#FFA500", "Expert": "#F44336"}
        color = colors.get(removal, "#aaaaaa")
        removal_text = f"<span style='color:{color};font-weight:bold;'>{removal}</span>"

        html = f"<b>App Type:</b> {app_type}<br><b>Description:</b> {desc}<br><b>Removal:</b> {removal_text}"
        self.app_desc_label.setText(html)

    def run_adb_command(self, command, callback):
        worker = AdbWorker(command)
        worker.output.connect(callback)
        worker.finished.connect(lambda w=worker: self.workers.remove(w) if w in self.workers else None)
        self.workers.append(worker)
        worker.start()

    def refresh_devices(self):
        self.device_combo.clear()
        self.run_adb_command("adb devices", self._handle_devices)

    @pyqtSlot(str)
    def _handle_devices(self, output):
        devices = []
        for line in output.strip().splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])

        self.device_combo.addItems(devices)
        if devices:
            self.device_combo.setCurrentIndex(0)

    def load_device_info(self):
        device = self.device_combo.currentText()
        if device:
            self.run_adb_command(f"adb -s {device} shell getprop", self._handle_device_info)

    @pyqtSlot(str)
    def _handle_device_info(self, output):
        info = {}
        for line in output.splitlines():
            if "]:" in line:
                key, value = line.split("]:", 1)
                info[key.strip("[] ")] = value.strip("[] ")

        model = info.get("ro.product.model", "Unknown")
        version = info.get("ro.build.version.release", "Unknown")
        sdk = info.get("ro.build.version.sdk", "Unknown")
        self.device_info_label.setText(f"Model: {model} | Android: {version} | API: {sdk}")

    def load_all_apps(self):
        device = self.device_combo.currentText()
        if not device:
            return

        self.temp_packages = []
        self.run_adb_command(f"adb -s {device} shell pm list packages -f", self._handle_installed_packages)

    @pyqtSlot(str)
    def _handle_installed_packages(self, output):
        current_device = self.device_combo.currentText()
        if not current_device:
            return

        self.temp_packages = []
        for line in output.strip().splitlines():
            if "=" in line:
                try:
                    path, pkg = line.split("=", 1)
                    self.temp_packages.append((pkg, path))
                except ValueError:
                    continue

        self.run_adb_command(f"adb -s {current_device} shell pm list packages -d", self._handle_disabled_packages)

    @pyqtSlot(str)
    def _handle_disabled_packages(self, output):
        disabled = {line.split(":", 1)[1] for line in output.strip().splitlines() if line.startswith("package:")}
        self.all_apps = []

        for pkg, path in self.temp_packages:
            app_name = pkg.split(".")[-1]
            status = "Disabled" if pkg in disabled else "Enabled"
            app_type = "System" if any(p in path for p in ["/system/", "/product/", "/vendor/", "/system_ext/"]) else "User"
            self.all_apps.append((app_name, pkg, status, app_type))

        self.display_apps(self.all_apps)

    def display_apps(self, apps):
        self.app_table.setRowCount(0)
        for name, pkg, status, app_type in apps:
            row = self.app_table.rowCount()
            self.app_table.insertRow(row)
            self.app_table.setItem(row, 0, QTableWidgetItem(name))
            self.app_table.setItem(row, 1, QTableWidgetItem(pkg))
            self.app_table.setItem(row, 2, QTableWidgetItem(status))
            self.app_table.setItem(row, 3, QTableWidgetItem(app_type))

            color = QColor(244, 67, 54) if status == "Disabled" else QColor(76, 175, 80)
            for col in range(4):
                self.app_table.item(row, col).setBackground(color)

    def search_apps(self):
        query = self.search_input.text().lower().strip()
        if not query:
            self.display_apps(self.all_apps)
            return
        filtered = [app for app in self.all_apps if query in app[1].lower()]
        self.display_apps(filtered)

    def install_apk(self):
        device = self.device_combo.currentText()
        if not device:
            QMessageBox.warning(self, "Ошибка", "Не выбрано устройство")
            return

        filepath, _ = QFileDialog.getOpenFileName(self, "Выберите APK", "", "APK Files (*.apk)")
        if not filepath:
            return

        cmd = f'adb -s {device} install -r "{filepath}"'
        self.run_adb_command(cmd, self._handle_install_result)

    @pyqtSlot(str)
    def _handle_install_result(self, output):
        if "Success" in output:
            QMessageBox.information(self, "Установка", "Приложение успешно установлено")
            QTimer.singleShot(1000, self.load_all_apps)
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось установить приложение:\n{output}")

    def change_app_state(self, action):
        device = self.device_combo.currentText()
        row = self.app_table.currentRow()
        if not device:
            QMessageBox.warning(self, "Ошибка", "Не выбрано устройство")
            return
        if row == -1:
            QMessageBox.warning(self, "Ошибка", "Не выбрано приложение")
            return

        package = self.app_table.item(row, 1).text()
        if action == "disable":
            cmd = f"adb -s {device} shell pm disable-user {package}"
        else:
            cmd = f"adb -s {device} shell pm enable {package}"

        self.run_adb_command(cmd, lambda _: QTimer.singleShot(1000, self.load_all_apps))

    def uninstall_app(self):
        device = self.device_combo.currentText()
        row = self.app_table.currentRow()
        if not device or row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите устройство и приложение")
            return

        package = self.app_table.item(row, 1).text()
        app_type = self.app_table.item(row, 3).text()

        if app_type == "System":
            reply = QMessageBox.warning(self, "Внимание", "Удаление системных приложений может нарушить работу устройства. Продолжить?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.run_adb_command(f"adb -s {device} shell pm uninstall --user 0 {package}", lambda _: QTimer.singleShot(1000, self.load_all_apps))

    def closeEvent(self, event):
        for worker in self.workers:
            if worker.isRunning():
                worker.quit()
                worker.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AndroidAppManager()
    window.show()
    sys.exit(app.exec_())
