"""Validation utilities"""

import re
from typing import Optional


def validate_package_name(package: str) -> bool:
    """
    Validate Android package name format.
    
    Args:
        package: Package name to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z][\w\.\-]*$'
    return bool(re.match(pattern, package))


def validate_apk_path(path: str) -> bool:
    """
    Validate APK file path.
    
    Args:
        path: Path to APK file
        
    Returns:
        True if valid, False otherwise
    """
    return path.lower().endswith('.apk') if path else False


def sanitize_device_id(device_id: str) -> Optional[str]:
    """
    Sanitize device ID string.
    
    Args:
        device_id: Raw device ID
        
    Returns:
        Sanitized device ID or None if invalid
    """
    # Remove any non-alphanumeric characters except common separators
    device_id = re.sub(r'[^\w\.\-\:]', '', device_id)
    return device_id if device_id else None
