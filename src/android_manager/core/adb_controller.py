"""ADB controller for Android device management"""

import re
import subprocess
from typing import List, Optional
from PyQt5.QtCore import QThread, pyqtSignal


class PackageInfo:
    """Package information container"""
    def __init__(self, package: str, status: str, app_type: str, path: str):
        self.package = package
        self.status = status
        self.app_type = app_type
        self.path = path


class AdbWorker(QThread):
    """Worker thread for ADB commands"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, command: List[str], timeout: int = 30):
        super().__init__()
        self.command = command
        self.timeout = timeout
    
    def run(self) -> None:
        """Execute ADB command in thread"""
        try:
            result = subprocess.run(
                self.command,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = (result.stdout or "") + (result.stderr or "")
            
            if result.returncode != 0 and "error" in output.lower():
                self.error.emit(output.strip())
            else:
                self.finished.emit(output.strip())
                
        except subprocess.TimeoutExpired:
            self.error.emit(f"Command timed out after {self.timeout}s")
        except Exception as e:
            self.error.emit(f"Command failed: {str(e)}")


class AdbController:
    """Controller for ADB operations"""
    
    @staticmethod
    def validate_package_name(package: str) -> bool:
        """Validate Android package name format"""
        pattern = r'^[a-zA-Z][\w\.\-]*$'
        return bool(re.match(pattern, package))
    
    @staticmethod
    def get_adb_command(*args) -> List[str]:
        """Create ADB command with arguments"""
        return ["adb", *args]
    
    def __init__(self):
        self.workers = []
    
    def get_devices(self, callback, error_callback=None) -> None:
        """Get list of connected devices"""
        worker = AdbWorker(self.get_adb_command("devices"))
        worker.finished.connect(callback)
        if error_callback:
            worker.error.connect(error_callback)
        self._start_worker(worker)
    
    def get_packages(self, device: str, user_id: str = "0", 
                    callback=None, error_callback=None) -> None:
        """Get all packages from device"""
        worker = AdbWorker(self.get_adb_command(
            "-s", device, "shell", "pm", "list", "packages", "-f",
            "--user", user_id
        ))
        worker.finished.connect(callback if callback else lambda x: None)
        if error_callback:
            worker.error.connect(error_callback)
        self._start_worker(worker)
    
    def get_disabled_packages(self, device: str, user_id: str = "0",
                            callback=None, error_callback=None) -> None:
        """Get disabled packages from device"""
        worker = AdbWorker(self.get_adb_command(
            "-s", device, "shell", "pm", "list", "packages", "-d",
            "--user", user_id
        ))
        worker.finished.connect(callback if callback else lambda x: None)
        if error_callback:
            worker.error.connect(error_callback)
        self._start_worker(worker)
    
    def change_package_state(self, device: str, action: str, package: str,
                           user_id: str = "0", callback=None, 
                           error_callback=None) -> None:
        """Enable or disable package"""
        if not self.validate_package_name(package):
            if error_callback:
                error_callback(f"Invalid package name: {package}")
            return
        
        pm_action = "disable-user" if action == "disable" else "enable"
        
        worker = AdbWorker(self.get_adb_command(
            "-s", device, "shell", "pm", pm_action,
            "--user", user_id, package
        ))
        worker.finished.connect(callback if callback else lambda x: None)
        if error_callback:
            worker.error.connect(error_callback)
        self._start_worker(worker)
    
    def uninstall_package(self, device: str, package: str,
                         user_id: str = "0", callback=None,
                         error_callback=None) -> None:
        """Uninstall package"""
        if not self.validate_package_name(package):
            if error_callback:
                error_callback(f"Invalid package name: {package}")
            return
        
        worker = AdbWorker(self.get_adb_command(
            "-s", device, "shell", "pm", "uninstall",
            "--user", user_id, package
        ))
        worker.finished.connect(callback if callback else lambda x: None)
        if error_callback:
            worker.error.connect(error_callback)
        self._start_worker(worker)
    
    def install_apk(self, device: str, apk_path: str,
                   callback=None, error_callback=None) -> None:
        """Install APK file"""
        worker = AdbWorker(self.get_adb_command(
            "-s", device, "install", "-r", apk_path
        ), timeout=120)
        worker.finished.connect(callback if callback else lambda x: None)
        if error_callback:
            worker.error.connect(error_callback)
        self._start_worker(worker)
    
    def get_device_properties(self, device: str, callback=None,
                            error_callback=None) -> None:
        """Get device properties"""
        worker = AdbWorker(self.get_adb_command(
            "-s", device, "shell", "getprop"
        ))
        worker.finished.connect(callback if callback else lambda x: None)
        if error_callback:
            worker.error.connect(error_callback)
        self._start_worker(worker)
    
    def _start_worker(self, worker: AdbWorker) -> None:
        """Start worker and track it"""
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda msg: self._cleanup_worker(worker))
        self.workers.append(worker)
        worker.start()
    
    def _cleanup_worker(self, worker: AdbWorker) -> None:
        """Remove worker from tracking list"""
        if worker in self.workers:
            self.workers.remove(worker)
            worker.deleteLater()
    
    def cleanup(self) -> None:
        """Cleanup all running workers"""
        for worker in self.workers[:]:
            if worker.isRunning():
                worker.quit()
                worker.wait()
            worker.deleteLater()
        self.workers.clear()
