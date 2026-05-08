"""Loader for Universal Android Debloater lists"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class UADLoader:
    """Loads and manages UAD (Universal Android Debloater) lists"""
    
    def __init__(self):
        self.uad_info: Dict[str, dict] = {}
        self._data_loaded = False
    
    def load_lists(self) -> bool:
        """
        Load UAD lists from JSON file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        # Try multiple possible locations for the data file
        possible_paths = [
            Path(__file__).parent / "uad_lists.json",
            Path(__file__).parent.parent.parent.parent / "uad_lists.json",  # Project root
            Path("data") / "uad_lists.json",
            Path.home() / ".local" / "share" / "android-manager" / "uad_lists.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                return self._load_from_file(path)
        
        logger.warning("No UAD lists found in any location")
        return False
    
    def _load_from_file(self, path: Path) -> bool:
        """
        Load UAD data from a specific file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            for entry in data:
                package = entry.get("id")
                if package:
                    self.uad_info[package] = entry
            
            self._data_loaded = True
            logger.info(f"Loaded {len(self.uad_info)} UAD entries from {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load UAD lists from {path}: {e}")
            return False
    
    def get_app_info(self, package: str) -> Optional[dict]:
        """
        Get UAD information for a package.
        
        Args:
            package: Package name
            
        Returns:
            Dictionary with app info or None if not found
        """
        if not self._data_loaded:
            self.load_lists()
        
        return self.uad_info.get(package)
    
    def has_info(self, package: str) -> bool:
        """
        Check if UAD info exists for package.
        
        Args:
            package: Package name
            
        Returns:
            True if info exists
        """
        return self.get_app_info(package) is not None
