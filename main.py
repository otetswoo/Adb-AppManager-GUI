import sys
import os
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

PM_USER = "--user"
PM_USER_ID = "0"


THEMES = {
    "dark": {
        "bg": "#1e1e2e",
        "surface": "#2a2a3e",
        "surface2": "#313149",
        "border": "#44445a",
        "text": "#cdd6f4",
        "text_dim": "#6c7086",
        "accent": "#89b4fa",
        "green": "#a6e3a1",
        "red": "#f38ba8",
        "row_enabled": "#1e2d1e",
        "row_disabled": "#2d1e1e",
    },
    "light": {
        "bg": "#f0f0f0",
        "surface": "#ffffff",
        "surface2": "#e0e0e0",
        "border": "#cccccc",
        "text": "#1a1a1a",
        "text_dim": "#666666",
        "accent": "#1a73e8",
        "green": "#2e7d32",
        "red": "#d32f2f",
        "row_enabled": "#e8f5e9",
        "row_disabled": "#ffebee",
    },
}


STRINGS = {
    "ru": {
        "title": "Android App Manager",
        "device_lbl": "Устройство:",
        "refresh_dev": "Обновить",
        "no_devices": "Нет подключённых устройств",
        "search_ph": "Поиск пакета...",
        "type_all": "Все типы",
        "type_user": "Пользовательские",
        "type_sys": "Системные",
        "stat_en": "Включено",
        "stat_dis": "Отключено",
        "status_all": "Все статусы",
        "ready": "Готово",
        "loading_pkgs": "Загрузка приложений...",
        "loaded_count": "Загружено: {} приложений",
        "no_info": "Информация отсутствует",
        "select_app_hint": "Выберите приложение",
        "btn_refresh_apps": "Обновить список",
        "btn_install_apk": "Установить APK",
        "btn_batch": "Пакетное отключение",
        "btn_enable": "Включить",
        "btn_disable": "Выключить",
        "btn_uninstall": "Удалить",
        "copy_pkg": "Копировать пакет",
        "install_ok": "APK установлен",
        "confirm_sys": "Удаление системного приложения может повредить систему. Продолжить?",
        "err_no_dev": "Выберите устройство",
        "err_protected": "Пакет '{}' защищён системой",
        "err_cmd": "Ошибка выполнения:\n{}",
    },
    "en": {
        "title": "Android App Manager",
        "device_lbl": "Device:",
        "refresh_dev": "Refresh",
        "no_devices": "No devices connected",
        "search_ph": "Search package...",
        "type_all": "All types",
        "type_user": "User",
        "type_sys": "System",
        "stat_en": "Enabled",
        "stat_dis": "Disabled",
        "status_all": "All statuses",
        "ready": "Ready",
        "loading_pkgs": "Loading apps...",
        "loaded_count": "Loaded: {} apps",
        "no_info": "No info available",
        "select_app_hint": "Select app",
        "btn_refresh_apps": "Refresh list",
        "btn_install_apk": "Install APK",
        "btn_batch": "Batch disable",
        "btn_enable": "Enable",
        "btn_disable": "Disable",
        "btn_uninstall": "Uninstall",
        "copy_pkg": "Copy package",
        "install_ok": "APK installed",
        "confirm_sys": "Removing system apps may break device. Continue?",
        "err_no_dev": "Select device",
        "err_protected": "Package '{}' is protected",
        "err_cmd": "Command failed:\n{}",
    },
}


@dataclass
class AppInfo:
    package: str
    status: str
    app_type: str
    path: str


class AdbWorker(QThread):
    finished_output = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.run(
                self.command,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = (result.stdout or "") + (result.stderr or "")
            self.finished_output.emit(output.strip())

        except Exception as e:
            self.finished_output.emit(f"ERROR: {e}")


class AdbClient:
    @staticmethod
    def run(*args):
        return ["adb", *args]


class AndroidAppManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.lang = "ru"
        self.theme_mode = "dark"

        self.all_apps = []
        self.workers = []
        self.uad_info = {}
        self.packages_buffer = {}

        self.search_timer = QTimer(parent=self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_filters)

        self.load_uad_lists()
        self.setup_ui()
        self.apply_theme()
        self.retranslate_ui()

        self.refresh_devices()

    def setup_ui(self):
        self.setWindowTitle("Android App Manager")
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "src", "android_manager", "ui", "Adb-appmanager-icon.jpg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)

        self.main_layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()

        self.lbl_dev = QLabel()

        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_selected)

        self.btn_refresh_dev = QPushButton()
        self.btn_refresh_dev.clicked.connect(self.refresh_devices)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["RU", "EN"])
        self.lang_combo.currentIndexChanged.connect(self.change_language)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)

        self.device_info_label = QLabel()

        top_bar.addWidget(self.lbl_dev)
        top_bar.addWidget(self.device_combo)
        top_bar.addWidget(self.btn_refresh_dev)
        top_bar.addSpacing(15)
        top_bar.addWidget(self.lang_combo)
        top_bar.addWidget(self.theme_combo)
        top_bar.addStretch()
        top_bar.addWidget(self.device_info_label)

        self.main_layout.addLayout(top_bar)

        filters = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(
            lambda: self.search_timer.start(250)
        )

        self.filter_type = QComboBox()
        self.filter_type.currentIndexChanged.connect(self.apply_filters)

        self.filter_status = QComboBox()
        self.filter_status.currentIndexChanged.connect(self.apply_filters)

        filters.addWidget(self.search_input)
        filters.addWidget(self.filter_type)
        filters.addWidget(self.filter_status)

        self.main_layout.addLayout(filters)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.main_layout.addWidget(self.progress_bar)

        self.app_table = QTableWidget()
        self.app_table.setColumnCount(3)
        self.app_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.app_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.app_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )

        self.app_table.itemSelectionChanged.connect(
            self.update_app_desc
        )

        self.app_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.app_table.customContextMenuRequested.connect(
            self.show_context_menu
        )

        self.main_layout.addWidget(self.app_table)

        self.app_desc_label = QLabel()
        self.app_desc_label.setWordWrap(True)
        self.app_desc_label.setMinimumHeight(90)
        self.app_desc_label.setObjectName("descArea")

        self.main_layout.addWidget(self.app_desc_label)

        buttons = QHBoxLayout()

        self.btn_refresh_apps = QPushButton()
        self.btn_install_apk = QPushButton()
        self.btn_batch = QPushButton()
        self.btn_enable = QPushButton()
        self.btn_disable = QPushButton()
        self.btn_uninstall = QPushButton()

        self.btn_uninstall.setObjectName("dangerBtn")

        self.btn_refresh_apps.clicked.connect(self.refresh_apps)
        self.btn_install_apk.clicked.connect(self.install_apk)
        self.btn_batch.clicked.connect(self.open_batch_dialog)

        self.btn_enable.clicked.connect(
            lambda: self.change_app_state("enable")
        )

        self.btn_disable.clicked.connect(
            lambda: self.change_app_state("disable")
        )

        self.btn_uninstall.clicked.connect(self.uninstall_app)

        self.action_buttons = [
            self.btn_refresh_apps,
            self.btn_install_apk,
            self.btn_batch,
            self.btn_enable,
            self.btn_disable,
            self.btn_uninstall,
        ]

        for button in self.action_buttons:
            buttons.addWidget(button)

        self.main_layout.addLayout(buttons)

        self.status_label = QLabel()

        self.main_layout.addWidget(self.status_label)

    def apply_theme(self):
        c = THEMES[self.theme_mode]

        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {c['bg']};
                color: {c['text']};
            }}

            QTableWidget {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                gridline-color: {c['border']};
            }}

            QHeaderView::section {{
                background-color: {c['surface2']};
                border: none;
                border-bottom: 1px solid {c['border']};
                padding: 4px;
                color: {c['accent']};
                font-weight: bold;
            }}

            QPushButton {{
                background-color: {c['surface2']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 6px;
            }}

            QPushButton:hover {{
                border-color: {c['accent']};
            }}

            QPushButton#dangerBtn {{
                color: {c['red']};
                border-color: {c['red']};
            }}

            QLineEdit, QComboBox {{
                background-color: {c['surface2']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 4px;
            }}

            QLabel#descArea {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 10px;
            }}
            """
        )

        self.apply_filters()

    def retranslate_ui(self):
        t = STRINGS[self.lang]

        self.lbl_dev.setText(t["device_lbl"])
        self.btn_refresh_dev.setText(t["refresh_dev"])

        self.search_input.setPlaceholderText(t["search_ph"])

        self.app_table.setHorizontalHeaderLabels(
            ["Package", "Status", "Type"]
        )

        self.filter_type.clear()
        self.filter_type.addItem(t["type_all"], "all")
        self.filter_type.addItem(t["type_user"], "User")
        self.filter_type.addItem(t["type_sys"], "System")

        self.filter_status.clear()
        self.filter_status.addItem(t["status_all"], "all")
        self.filter_status.addItem(t["stat_en"], "Enabled")
        self.filter_status.addItem(t["stat_dis"], "Disabled")

        self.btn_refresh_apps.setText(t["btn_refresh_apps"])
        self.btn_install_apk.setText(t["btn_install_apk"])
        self.btn_batch.setText(t["btn_batch"])
        self.btn_enable.setText(t["btn_enable"])
        self.btn_disable.setText(t["btn_disable"])
        self.btn_uninstall.setText(t["btn_uninstall"])

        self.set_status(t["ready"])

    def change_theme(self, index):
        self.theme_mode = "dark" if index == 0 else "light"
        self.apply_theme()

    def change_language(self, index):
        self.lang = "ru" if index == 0 else "en"
        self.retranslate_ui()
        self.apply_filters()

    def refresh_devices(self):
        self.run_adb_command(
            AdbClient.run("devices"),
            self.handle_devices,
        )

    def handle_devices(self, output):
        devices = []

        for line in output.splitlines()[1:]:
            parts = line.split()

            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])

        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        self.device_combo.addItems(devices)
        self.device_combo.blockSignals(False)

        if devices:
            self.on_device_selected(0)
        else:
            self.device_info_label.setText(
                STRINGS[self.lang]["no_devices"]
            )

    def on_device_selected(self, index):
        if index < 0:
            return

        if not self.device_combo.currentText():
            return

        self.load_device_info()
        self.load_all_apps()

    def load_device_info(self):
        device = self.device_combo.currentText()

        self.run_adb_command(
            AdbClient.run(
                "-s",
                device,
                "shell",
                "getprop",
            ),
            self.handle_device_info,
        )

    def handle_device_info(self, output):
        props = {}

        for line in output.splitlines():
            if "]: [" not in line:
                continue

            try:
                key, value = line.split("]: [", 1)

                key = key[1:]
                value = value[:-1]

                props[key] = value

            except Exception:
                continue

        model = props.get("ro.product.model", "Unknown")
        brand = props.get("ro.product.brand", "").capitalize()
        version = props.get("ro.build.version.release", "?")

        text = f"{brand} {model} | Android {version}".strip()

        self.device_info_label.setText(text)

    def load_all_apps(self):
        device = self.device_combo.currentText()

        if not device:
            return

        self.set_loading(True)

        self.run_adb_command(
            AdbClient.run(
                "-s",
                device,
                "shell",
                "pm",
                "list",
                "packages",
                "-f",
                PM_USER,
                PM_USER_ID,
            ),
            self.handle_packages,
        )

    def handle_packages(self, output):
        self.packages_buffer.clear()

        for line in output.splitlines():
            if not line.startswith("package:"):
                continue

            try:
                path, package = line[8:].rsplit("=", 1)

                self.packages_buffer[package.strip()] = {
                    "path": path,
                    "status": "Enabled",
                }

            except Exception:
                continue

        self.run_adb_command(
            AdbClient.run(
                "-s",
                self.device_combo.currentText(),
                "shell",
                "pm",
                "list",
                "packages",
                "-d",
                PM_USER,
                PM_USER_ID,
            ),
            self.handle_disabled_packages,
        )

    def handle_disabled_packages(self, output):
        for line in output.splitlines():
            package = line.replace("package:", "").strip()

            if package in self.packages_buffer:
                self.packages_buffer[package]["status"] = "Disabled"

        self.all_apps.clear()

        system_paths = (
            "/system/",
            "/vendor/",
            "/product/",
            "/apex/",
        )

        for package, info in self.packages_buffer.items():
            app_type = (
                "System"
                if any(p in info["path"] for p in system_paths)
                else "User"
            )

            self.all_apps.append(
                AppInfo(
                    package=package,
                    status=info["status"],
                    app_type=app_type,
                    path=info["path"],
                )
            )

        self.all_apps.sort(key=lambda x: x.package)

        self.apply_filters()

        self.set_loading(False)

        self.set_status(
            STRINGS[self.lang]["loaded_count"].format(
                len(self.all_apps)
            )
        )

    def apply_filters(self):
        query = self.search_input.text().lower()

        type_filter = self.filter_type.currentData()
        status_filter = self.filter_status.currentData()

        colors = THEMES[self.theme_mode]
        t = STRINGS[self.lang]

        filtered = []

        for app in self.all_apps:
            if query and query not in app.package.lower():
                continue

            if type_filter != "all" and app.app_type != type_filter:
                continue

            if status_filter != "all" and app.status != status_filter:
                continue

            filtered.append(app)

        self.app_table.setRowCount(0)

        for app in filtered:
            row = self.app_table.rowCount()
            self.app_table.insertRow(row)

            status_text = (
                t["stat_en"]
                if app.status == "Enabled"
                else t["stat_dis"]
            )

            type_text = (
                t["type_sys"]
                if app.app_type == "System"
                else t["type_user"]
            )

            items = [
                QTableWidgetItem(app.package),
                QTableWidgetItem(status_text),
                QTableWidgetItem(type_text),
            ]

            row_color = QColor(
                colors["row_disabled"]
                if app.status == "Disabled"
                else colors["row_enabled"]
            )

            for item in items:
                item.setBackground(row_color)

            items[1].setForeground(
                QColor(
                    colors["green"]
                    if app.status == "Enabled"
                    else colors["red"]
                )
            )

            for col, item in enumerate(items):
                self.app_table.setItem(row, col, item)

    def update_app_desc(self):
        row = self.app_table.currentRow()

        if row == -1:
            return

        package = self.app_table.item(row, 0).text()

        app = next(
            (a for a in self.all_apps if a.package == package),
            None,
        )

        if not app:
            return

        info = self.uad_info.get(package)

        colors = THEMES[self.theme_mode]
        t = STRINGS[self.lang]

        status_text = (
            t["stat_en"]
            if app.status == "Enabled"
            else t["stat_dis"]
        )

        status_color = (
            colors["green"]
            if app.status == "Enabled"
            else colors["red"]
        )

        text = (
            f"<b>{package}</b> | "
            f"<span style='color:{status_color}'>{status_text}</span><br>"
        )

        if info:
            text += (
                f"<p><b>List:</b> {info.get('list', '?')} | "
                f"<b>Removal:</b> {info.get('removal', '?')}</p>"
            )

            text += (
                f"<p style='color:{colors['text_dim']}'>"
                f"{info.get('description', '')}</p>"
            )
        else:
            text += (
                f"<p style='color:{colors['text_dim']}'>"
                f"{t['no_info']}</p>"
            )

        self.app_desc_label.setText(text)

    def change_app_state(self, action):
        device = self.device_combo.currentText()
        row = self.app_table.currentRow()

        if not device or row == -1:
            return

        package = self.app_table.item(row, 0).text()

        pm_action = (
            "disable-user"
            if action == "disable"
            else "enable"
        )

        self.run_adb_command(
            AdbClient.run(
                "-s",
                device,
                "shell",
                "pm",
                pm_action,
                PM_USER,
                PM_USER_ID,
                package,
            ),
            lambda output: self.handle_state_result(output, package),
        )

    def handle_state_result(self, output, package):
        if any(
            x in output
            for x in [
                "Security exception",
                "Permission denied",
                "not allowed",
            ]
        ):
            QMessageBox.critical(
                self,
                "Error",
                STRINGS[self.lang]["err_protected"].format(
                    package
                ),
            )

        elif "Error" in output or "Failure" in output:
            QMessageBox.warning(
                self,
                "Error",
                STRINGS[self.lang]["err_cmd"].format(output),
            )

        QTimer.singleShot(400, self.load_all_apps)

    def uninstall_app(self):
        device = self.device_combo.currentText()
        row = self.app_table.currentRow()

        if not device or row == -1:
            return

        package = self.app_table.item(row, 0).text()
        app_type = self.app_table.item(row, 2).text()

        if app_type == STRINGS[self.lang]["type_sys"]:
            result = QMessageBox.warning(
                self,
                "Warning",
                STRINGS[self.lang]["confirm_sys"],
                QMessageBox.Yes | QMessageBox.No,
            )

            if result == QMessageBox.No:
                return

        self.run_adb_command(
            AdbClient.run(
                "-s",
                device,
                "shell",
                "pm",
                "uninstall",
                PM_USER,
                PM_USER_ID,
                package,
            ),
            lambda output: self.handle_state_result(
                output,
                package,
            ),
        )

    def install_apk(self):
        device = self.device_combo.currentText()

        if not device:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "APK",
            "",
            "*.apk",
        )

        if not path:
            return

        self.set_loading(True)

        self.run_adb_command(
            AdbClient.run(
                "-s",
                device,
                "install",
                "-r",
                path,
            ),
            self.finish_install,
        )

    def finish_install(self, output):
        self.set_loading(False)

        if "Success" in output:
            QMessageBox.information(
                self,
                "OK",
                STRINGS[self.lang]["install_ok"],
            )

        self.load_all_apps()

    def open_batch_dialog(self):
        device = self.device_combo.currentText()

        if not device:
            return

        t = STRINGS[self.lang]
        c = THEMES[self.theme_mode]

        dialog = QDialog(self)
        dialog.setWindowTitle(t["btn_batch"])
        dialog.resize(500, 450)

        dialog.setStyleSheet(
            f"""
            background-color: {c['bg']};
            color: {c['text']};
            """
        )

        layout = QVBoxLayout(dialog)

        editor = QTextEdit()

        layout.addWidget(editor)

        run_button = QPushButton(t["btn_disable"])

        layout.addWidget(run_button)

        def run_batch():
            packages = [
                line.strip()
                for line in editor.toPlainText().splitlines()
                if line.strip()
            ]

            if not packages:
                return

            self.set_loading(True)

            for package in packages:
                try:
                    subprocess.run(
                        AdbClient.run(
                            "-s",
                            device,
                            "shell",
                            "pm",
                            "disable-user",
                            PM_USER,
                            PM_USER_ID,
                            package,
                        ),
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )

                except Exception as e:
                    print(e)

            dialog.accept()

            QTimer.singleShot(500, self.load_all_apps)

        run_button.clicked.connect(run_batch)

        dialog.exec_()

    def show_context_menu(self, pos):
        item = self.app_table.itemAt(pos)

        if not item:
            return

        menu = QMenu()

        copy_action = menu.addAction(
            STRINGS[self.lang]["copy_pkg"]
        )

        action = menu.exec_(
            self.app_table.viewport().mapToGlobal(pos)
        )

        if action == copy_action:
            package = self.app_table.item(
                item.row(),
                0,
            ).text()

            QApplication.clipboard().setText(package)

    def load_uad_lists(self):
        path = Path("uad_lists.json")

        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            for entry in data:
                package = entry.get("id")

                if package:
                    self.uad_info[package] = entry

        except Exception as e:
            print(f"uad_lists.json error: {e}")

    def set_status(self, text):
        self.status_label.setText(text)

    def set_loading(self, loading):
        self.progress_bar.setVisible(loading)

        self.progress_bar.setRange(
            0,
            0 if loading else 1,
        )

        for button in self.action_buttons:
            button.setEnabled(not loading)

    def refresh_apps(self):
        self.load_all_apps()

    def run_adb_command(self, command, callback):
        worker = AdbWorker(command)

        worker.finished_output.connect(callback)

        worker.finished.connect(
            lambda: self.workers.remove(worker)
            if worker in self.workers
            else None
        )

        self.workers.append(worker)

        worker.start()

    def closeEvent(self, event):
        for worker in self.workers:
            if worker.isRunning():
                worker.quit()
                worker.wait()

        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    window = AndroidAppManager()
    window.show()

    sys.exit(app.exec_())