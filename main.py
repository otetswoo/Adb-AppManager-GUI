import sys
import os
import subprocess
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QColor

os.environ["QT_QPA_PLATFORM"] = "wayland"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

PM_USER = "--user 0"

# ── Цвета темы ────────────────────────────────────────────────────────────────
CLR_BG           = "#1e1e2e"
CLR_SURFACE      = "#2a2a3e"
CLR_SURFACE2     = "#313149"
CLR_BORDER       = "#44445a"
CLR_TEXT         = "#cdd6f4"
CLR_TEXT_DIM     = "#6c7086"
CLR_ACCENT       = "#89b4fa"
CLR_GREEN        = "#a6e3a1"
CLR_RED          = "#f38ba8"
CLR_YELLOW       = "#f9e2af"
CLR_ROW_ENABLED  = "#1e2d1e"
CLR_ROW_DISABLED = "#2d1e1e"


# ── ADB worker ────────────────────────────────────────────────────────────────

class AdbWorker(QThread):
    output = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            result = subprocess.run(
                self.command, shell=True, capture_output=True,
                text=True, timeout=30,
            )
            out = result.stdout
            if result.returncode != 0 and not result.stdout:
                out = result.stderr
        except subprocess.TimeoutExpired:
            out = "ERROR: timeout"
        except Exception as e:
            out = f"ERROR: {e}"
        self.output.emit(out)


# ── Главное окно ──────────────────────────────────────────────────────────────

class AndroidAppManager(QMainWindow):

    COL_PKG    = 0
    COL_STATUS = 1
    COL_TYPE   = 2

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Android App Manager")
        self.setGeometry(100, 100, 1000, 680)
        self._apply_stylesheet()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(10, 10, 10, 8)

        self.all_apps:      list[tuple] = []
        self.workers:       list        = []
        self._packages_buf: dict        = {}
        self.uad_info:      dict        = {}

        self.load_uad_lists()
        self.setup_ui()
        self.refresh_devices()

    # ── Стиль ─────────────────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {CLR_BG};
                color: {CLR_TEXT};
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 13px;
            }}
            QLabel {{
                background: transparent;
                border: none;
                padding: 0;
            }}
            QPushButton {{
                background-color: {CLR_SURFACE2};
                color: {CLR_TEXT};
                border: 1px solid {CLR_BORDER};
                padding: 5px 12px;
                border-radius: 5px;
                min-height: 26px;
            }}
            QPushButton:hover   {{ background-color: #3a3a5a; border-color: {CLR_ACCENT}; }}
            QPushButton:pressed {{ background-color: #252540; }}
            QPushButton:disabled {{
                background-color: {CLR_SURFACE};
                color: {CLR_TEXT_DIM};
                border-color: {CLR_BORDER};
            }}
            QPushButton#dangerBtn {{
                border-color: {CLR_RED};
                color: {CLR_RED};
            }}
            QPushButton#dangerBtn:hover {{ background-color: #3a1e1e; }}

            QComboBox {{
                background-color: {CLR_SURFACE2};
                color: {CLR_TEXT};
                border: 1px solid {CLR_BORDER};
                padding: 4px 8px;
                border-radius: 5px;
                min-height: 26px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background-color: {CLR_SURFACE2};
                color: {CLR_TEXT};
                selection-background-color: {CLR_ACCENT};
                selection-color: {CLR_BG};
            }}

            QLineEdit {{
                background-color: {CLR_SURFACE2};
                color: {CLR_TEXT};
                border: 1px solid {CLR_BORDER};
                padding: 4px 8px;
                border-radius: 5px;
                min-height: 26px;
            }}
            QLineEdit:focus {{ border-color: {CLR_ACCENT}; }}

            QTableWidget {{
                background-color: {CLR_SURFACE};
                color: {CLR_TEXT};
                gridline-color: {CLR_BORDER};
                border: 1px solid {CLR_BORDER};
                border-radius: 5px;
                selection-background-color: #3a3a6a;
                selection-color: {CLR_TEXT};
                outline: none;
            }}
            QTableWidget::item {{ padding: 3px 6px; }}
            QHeaderView::section {{
                background-color: {CLR_SURFACE2};
                color: {CLR_ACCENT};
                font-weight: bold;
                padding: 5px 6px;
                border: none;
                border-right: 1px solid {CLR_BORDER};
                border-bottom: 1px solid {CLR_BORDER};
            }}
            QHeaderView::section:hover {{ background-color: #3a3a5a; }}

            QProgressBar {{
                background-color: {CLR_SURFACE2};
                border: 1px solid {CLR_BORDER};
                border-radius: 3px;
                height: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {CLR_ACCENT};
                border-radius: 3px;
            }}

            QScrollBar:vertical {{
                background: {CLR_SURFACE};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {CLR_BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {CLR_ACCENT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

    # ── UAD ───────────────────────────────────────────────────────────────────

    def load_uad_lists(self):
        try:
            with open("uad_lists.json", "r", encoding="utf-8") as f:
                for entry in json.load(f):
                    if "id" in entry:
                        self.uad_info[entry["id"]] = entry
        except Exception:
            pass

    # ── UI ────────────────────────────────────────────────────────────────────

    def setup_ui(self):
        # ── Строка устройства ────────────────────────────────────────────────
        dev_row = QHBoxLayout()

        lbl_dev = QLabel("Устройство:")
        lbl_dev.setStyleSheet(f"color: {CLR_TEXT_DIM};")

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(220)
        self.device_combo.currentIndexChanged.connect(self.on_device_selected)

        self.refresh_devices_btn = QPushButton("⟳  Refresh")
        self.refresh_devices_btn.clicked.connect(self.refresh_devices)

        self.device_info_label = QLabel("Нет подключённых устройств")
        self.device_info_label.setStyleSheet(f"color: {CLR_TEXT_DIM}; font-size: 12px;")

        dev_row.addWidget(lbl_dev)
        dev_row.addWidget(self.device_combo)
        dev_row.addWidget(self.refresh_devices_btn)
        dev_row.addSpacing(16)
        dev_row.addWidget(self.device_info_label)
        dev_row.addStretch()
        self.main_layout.addLayout(dev_row)

        # ── Строка поиска и фильтров ─────────────────────────────────────────
        filter_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Поиск по имени пакета…")
        self.search_input.textChanged.connect(self._apply_filters)
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.clear_search_btn = QPushButton("✕")
        self.clear_search_btn.setFixedWidth(30)
        self.clear_search_btn.setToolTip("Сбросить фильтры")
        self.clear_search_btn.clicked.connect(self._clear_filters)

        lbl_type = QLabel("Тип:")
        lbl_type.setStyleSheet(f"color: {CLR_TEXT_DIM};")
        self.filter_type = QComboBox()
        self.filter_type.setMinimumWidth(100)
        self.filter_type.addItems(["Все", "User", "System"])
        self.filter_type.currentIndexChanged.connect(self._apply_filters)

        lbl_status = QLabel("Статус:")
        lbl_status.setStyleSheet(f"color: {CLR_TEXT_DIM};")
        self.filter_status = QComboBox()
        self.filter_status.setMinimumWidth(110)
        self.filter_status.addItems(["Все", "Enabled", "Disabled"])
        self.filter_status.currentIndexChanged.connect(self._apply_filters)

        filter_row.addWidget(self.search_input)
        filter_row.addWidget(self.clear_search_btn)
        filter_row.addSpacing(8)
        filter_row.addWidget(lbl_type)
        filter_row.addWidget(self.filter_type)
        filter_row.addSpacing(8)
        filter_row.addWidget(lbl_status)
        filter_row.addWidget(self.filter_status)
        self.main_layout.addLayout(filter_row)

        # ── Прогресс-бар ─────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        # ── Таблица ───────────────────────────────────────────────────────────
        self.app_table = QTableWidget()
        self.app_table.setColumnCount(3)
        self.app_table.setHorizontalHeaderLabels(["Package Name", "Статус", "Тип"])

        hdr = self.app_table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_PKG,    QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_STATUS, QHeaderView.Fixed)
        hdr.setSectionResizeMode(self.COL_TYPE,   QHeaderView.Fixed)
        self.app_table.setColumnWidth(self.COL_STATUS, 90)
        self.app_table.setColumnWidth(self.COL_TYPE,   80)

        self.app_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.app_table.setSelectionMode(QTableWidget.SingleSelection)
        self.app_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.app_table.verticalHeader().setVisible(False)
        self.app_table.setSortingEnabled(True)
        self.app_table.horizontalHeader().setSortIndicatorShown(True)
        self.app_table.sortByColumn(self.COL_PKG, Qt.AscendingOrder)
        self.app_table.itemSelectionChanged.connect(self.update_app_desc)
        self.main_layout.addWidget(self.app_table)

        # ── Описание ──────────────────────────────────────────────────────────
        self.app_desc_label = QLabel()
        self.app_desc_label.setWordWrap(True)
        self.app_desc_label.setMinimumHeight(72)
        self.app_desc_label.setMaximumHeight(100)
        self.app_desc_label.setStyleSheet(f"""
            background-color: {CLR_SURFACE};
            color: {CLR_TEXT};
            border: 1px solid {CLR_BORDER};
            padding: 8px 10px;
            border-radius: 5px;
        """)
        self.main_layout.addWidget(self.app_desc_label)
        self.clear_app_desc()

        # ── Кнопки действий ───────────────────────────────────────────────────
        action_row = QHBoxLayout()

        self.refresh_apps_btn = QPushButton("⟳  Обновить список")
        self.install_apk_btn  = QPushButton("⬆  Установить APK")
        self.enable_btn       = QPushButton("✓  Enable")
        self.disable_btn      = QPushButton("⊘  Disable")
        self.uninstall_btn    = QPushButton("🗑  Uninstall")
        self.uninstall_btn.setObjectName("dangerBtn")

        self.refresh_apps_btn.clicked.connect(self.refresh_apps)
        self.install_apk_btn.clicked.connect(self.install_apk)
        self.enable_btn.clicked.connect(lambda: self.change_app_state("enable"))
        self.disable_btn.clicked.connect(lambda: self.change_app_state("disable"))
        self.uninstall_btn.clicked.connect(self.uninstall_app)

        self._action_buttons = [
            self.refresh_apps_btn, self.install_apk_btn,
            self.enable_btn, self.disable_btn, self.uninstall_btn,
        ]
        for btn in self._action_buttons:
            action_row.addWidget(btn)

        self.main_layout.addLayout(action_row)

        # ── Статусная строка ──────────────────────────────────────────────────
        self.status_label = QLabel("Готово")
        self.status_label.setStyleSheet(f"color: {CLR_TEXT_DIM}; font-size: 12px;")
        self.main_layout.addWidget(self.status_label)

    def set_status(self, text: str):
        self.status_label.setText(text)

    def set_loading(self, loading: bool):
        self.progress_bar.setVisible(loading)
        for btn in self._action_buttons:
            btn.setEnabled(not loading)

    # ── Device ────────────────────────────────────────────────────────────────

    def on_device_selected(self, index):
        if index < 0:
            return
        self.clear_app_desc()
        self.load_device_info()
        self.load_all_apps()

    def refresh_devices(self):
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        self.device_combo.blockSignals(False)
        self.run_adb_command("adb devices", self._handle_devices)

    @pyqtSlot(str)
    def _handle_devices(self, output):
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
            self.device_combo.setCurrentIndex(0)
            self.on_device_selected(0)
        else:
            self.device_info_label.setText("Нет подключённых устройств")

    def load_device_info(self):
        device = self.device_combo.currentText()
        if device:
            self.run_adb_command(
                f"adb -s {device} shell getprop",
                self._handle_device_info
            )

    @pyqtSlot(str)
    def _handle_device_info(self, output):
        info = {}
        for line in output.splitlines():
            if "]:" in line:
                key, _, value = line.partition("]:")
                info[key.strip("[] ")] = value.strip("[] ")
        model   = info.get("ro.product.model", "Unknown")
        version = info.get("ro.build.version.release", "Unknown")
        sdk     = info.get("ro.build.version.sdk", "Unknown")
        self.device_info_label.setText(
            f"{model}  |  Android {version}  |  API {sdk}"
        )

    # ── Загрузка приложений ───────────────────────────────────────────────────

    def refresh_apps(self):
        if not self.device_combo.currentText():
            QMessageBox.warning(self, "Ошибка", "Не выбрано устройство")
            return
        self.load_all_apps()

    def load_all_apps(self):
        device = self.device_combo.currentText()
        if not device:
            return
        self._packages_buf = {}
        self.all_apps      = []
        self.app_table.setRowCount(0)
        self.set_loading(True)
        self.set_status("Загружаю список пакетов…")

        self.run_adb_command(
            f"adb -s {device} shell pm list packages -f {PM_USER}",
            self._handle_installed_packages
        )

    @pyqtSlot(str)
    def _handle_installed_packages(self, output):
        if output.startswith("ERROR") or "SecurityException" in output:
            self.set_status(f"Ошибка: {output[:150]}")
            self.set_loading(False)
            return

        for line in output.splitlines():
            line = line.strip()
            if not line.startswith("package:"):
                continue
            body = line[len("package:"):]
            if "=" not in body:
                continue
            path, pkg = body.rsplit("=", 1)
            pkg  = pkg.strip()
            path = path.strip()
            if pkg:
                self._packages_buf[pkg] = {
                    "path":   path,
                    "status": "Enabled",
                }

        device = self.device_combo.currentText()
        if not device:
            self.set_loading(False)
            return

        self.run_adb_command(
            f"adb -s {device} shell pm list packages -d {PM_USER}",
            self._handle_disabled_packages
        )

    @pyqtSlot(str)
    def _handle_disabled_packages(self, output):
        if not (output.startswith("ERROR") or "SecurityException" in output):
            for line in output.splitlines():
                line = line.strip()
                if not line.startswith("package:"):
                    continue
                pkg = line[len("package:"):].strip()
                if pkg in self._packages_buf:
                    self._packages_buf[pkg]["status"] = "Disabled"

        system_paths = (
            "/system/", "/product/", "/vendor/",
            "/system_ext/", "/oem/", "/my_preload/",
            "/apex/", "/my_bigball/",
        )
        self.all_apps = []
        for pkg, info in self._packages_buf.items():
            is_system = any(p in info["path"] for p in system_paths)
            self.all_apps.append((
                pkg,
                info["status"],
                "System" if is_system else "User",
            ))

        self.all_apps.sort(key=lambda x: x[self.COL_PKG])
        self.display_apps(self.all_apps)
        self.set_loading(False)
        self.set_status(f"Загружено: {len(self.all_apps)} приложений")
        self._packages_buf.clear()

    # ── Отображение ───────────────────────────────────────────────────────────

    def display_apps(self, apps: list):
        self.app_table.setSortingEnabled(False)
        self.app_table.setRowCount(0)

        for pkg, status, app_type in apps:
            row = self.app_table.rowCount()
            self.app_table.insertRow(row)

            item_pkg    = QTableWidgetItem(pkg)
            item_status = QTableWidgetItem(status)
            item_type   = QTableWidgetItem(app_type)

            item_status.setTextAlignment(Qt.AlignCenter)
            item_type.setTextAlignment(Qt.AlignCenter)

            row_color = QColor(CLR_ROW_DISABLED if status == "Disabled" else CLR_ROW_ENABLED)
            for item in (item_pkg, item_status, item_type):
                item.setBackground(row_color)

            item_status.setForeground(
                QColor(CLR_RED if status == "Disabled" else CLR_GREEN)
            )
            item_type.setForeground(
                QColor(CLR_TEXT_DIM if app_type == "System" else CLR_TEXT)
            )

            self.app_table.setItem(row, self.COL_PKG,    item_pkg)
            self.app_table.setItem(row, self.COL_STATUS, item_status)
            self.app_table.setItem(row, self.COL_TYPE,   item_type)

        self.app_table.setSortingEnabled(True)

    # ── Фильтры ───────────────────────────────────────────────────────────────

    def _apply_filters(self):
        query      = self.search_input.text().lower().strip()
        type_flt   = self.filter_type.currentText()
        status_flt = self.filter_status.currentText()

        filtered = [
            (pkg, status, app_type)
            for pkg, status, app_type in self.all_apps
            if (not query or query in pkg.lower())
            and (type_flt   == "Все" or app_type == type_flt)
            and (status_flt == "Все" or status   == status_flt)
        ]

        self.display_apps(filtered)
        total = len(self.all_apps)
        count = len(filtered)
        suffix = f"  (показано {count} из {total})" if count != total else f"  ({total})"
        self.set_status(f"Приложений{suffix}")

    def _clear_filters(self):
        self.search_input.clear()
        self.filter_type.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)

    # ── Описание ──────────────────────────────────────────────────────────────

    def clear_app_desc(self):
        self.app_desc_label.setText(
            f"<span style='color:{CLR_TEXT_DIM}'>"
            f"Выберите приложение для просмотра информации.</span>"
        )

    def update_app_desc(self):
        row = self.app_table.currentRow()
        if row == -1:
            self.clear_app_desc()
            return

        pkg    = self.app_table.item(row, self.COL_PKG).text()
        status = self.app_table.item(row, self.COL_STATUS).text()
        info   = self.uad_info.get(pkg)

        status_color = CLR_RED if status == "Disabled" else CLR_GREEN
        status_str   = f"<span style='color:{status_color}'>{status}</span>"

        if not info:
            self.app_desc_label.setText(
                f"<b>{pkg}</b>  ·  {status_str}<br>"
                f"<span style='color:{CLR_TEXT_DIM}'>Нет информации в uad_lists.json</span>"
            )
            return

        app_type = info.get("list", "Unknown")
        desc     = info.get("description", "Нет описания.")
        removal  = info.get("removal", "Recommended")

        removal_colors = {
            "Recommended": CLR_GREEN,
            "Advanced":    CLR_YELLOW,
            "Expert":      CLR_RED,
        }
        rc = removal_colors.get(removal, CLR_TEXT)
        self.app_desc_label.setText(
            f"<b>{pkg}</b>  ·  {status_str}  ·  "
            f"List: {app_type}  ·  "
            f"Removal: <span style='color:{rc}'>{removal}</span><br>"
            f"<span style='color:{CLR_TEXT_DIM}'>{desc}</span>"
        )

    # ── Действия ──────────────────────────────────────────────────────────────

    def install_apk(self):
        device = self.device_combo.currentText()
        if not device:
            QMessageBox.warning(self, "Ошибка", "Не выбрано устройство")
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите APK", "", "APK Files (*.apk)"
        )
        if not filepath:
            return
        self.set_loading(True)
        self.set_status(f"Устанавливаю {Path(filepath).name}…")
        self.run_adb_command(
            f'adb -s {device} install -r "{filepath}"',
            self._handle_install_result
        )

    @pyqtSlot(str)
    def _handle_install_result(self, output):
        self.set_loading(False)
        if "Success" in output:
            QMessageBox.information(self, "Установка", "Приложение успешно установлено")
            QTimer.singleShot(300, self.load_all_apps)
        else:
            QMessageBox.warning(self, "Ошибка установки", f"Не удалось установить:\n{output}")

    def change_app_state(self, action: str):
        device = self.device_combo.currentText()
        row    = self.app_table.currentRow()
        if not device:
            QMessageBox.warning(self, "Ошибка", "Не выбрано устройство")
            return
        if row == -1:
            QMessageBox.warning(self, "Ошибка", "Не выбрано приложение")
            return

        pkg = self.app_table.item(row, self.COL_PKG).text()
        cmd = "disable-user" if action == "disable" else "enable"
        self.run_adb_command(
            f"adb -s {device} shell pm {cmd} {PM_USER} {pkg}",
            lambda _: QTimer.singleShot(300, self.load_all_apps)
        )

    def uninstall_app(self):
        device = self.device_combo.currentText()
        row    = self.app_table.currentRow()
        if not device or row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите устройство и приложение")
            return

        pkg      = self.app_table.item(row, self.COL_PKG).text()
        app_type = self.app_table.item(row, self.COL_TYPE).text()

        if app_type == "System":
            reply = QMessageBox.warning(
                self, "Внимание",
                f"Удаление системного приложения может нарушить работу устройства.\n\n"
                f"Пакет: {pkg}\n\nПродолжить?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.run_adb_command(
            f"adb -s {device} shell pm uninstall --user 0 {pkg}",
            lambda _: QTimer.singleShot(300, self.load_all_apps)
        )

    # ── ADB worker ────────────────────────────────────────────────────────────

    def run_adb_command(self, command: str, callback):
        worker = AdbWorker(command)
        worker.output.connect(callback)
        worker.finished.connect(
            lambda w=worker: self.workers.remove(w) if w in self.workers else None
        )
        self.workers.append(worker)
        worker.start()

    # ── Cleanup ───────────────────────────────────────────────────────────────

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
