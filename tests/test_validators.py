"""Tests for validation utilities"""

import pytest
from src.android_manager.utils.validators import (
    validate_package_name,
    validate_apk_path,
    sanitize_device_id
)


def test_validate_package_name():
    """Test package name validation"""
    # Valid names
    assert validate_package_name("com.example.app")
    assert validate_package_name("org.mozilla.firefox")
    assert validate_package_name("com.android.chrome")
    
    # Invalid names
    assert not validate_package_name("")
    assert not validate_package_name("123invalid")
    assert not validate_package_name("invalid;package")
    assert not validate_package_name("invalid package")


def test_validate_apk_path():
    """Test APK path validation"""
    assert validate_apk_path("/path/to/app.apk")
    assert validate_apk_path("C:\\Users\\test\\app.apk")
    assert not validate_apk_path("/path/to/file.txt")
    assert not validate_apk_path("")
    assert not validate_apk_path(None)


def test_sanitize_device_id():
    """Test device ID sanitization"""
    assert sanitize_device_id("emulator-5554") == "emulator-5554"
    assert sanitize_device_id("192.168.1.100:5555") == "192.168.1.100:5555"
    assert sanitize_device_id("invalid;device") == "invaliddevice"
    assert sanitize_device_id("") is None
