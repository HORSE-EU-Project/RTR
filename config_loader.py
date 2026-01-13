"""
Configuration loader for RTR system
Provides utilities to load and reload configuration files dynamically
"""
import json
import os
from typing import Dict, Optional
from pathlib import Path
import threading


class ConfigLoader:
    """
    Singleton class to manage configuration loading and reloading
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.config_dir = Path(__file__).parent / "RTR_configurations"
        self._mitigation_ansible_map: Dict[str, str] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration files"""
        self._load_mitigation_ansible_map()
    
    def _load_mitigation_ansible_map(self):
        """Load the mitigation action to Ansible playbook mapping"""
        config_path = self.config_dir / "mitigation_ansible_map.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._mitigation_ansible_map = data.get("action_name_to_playbook", {})
            print(f"✅ Loaded mitigation_ansible_map.json with {len(self._mitigation_ansible_map)} action mappings")
        except FileNotFoundError:
            print(f"⚠️ Configuration file not found: {config_path}")
            print(f"   Using empty configuration")
            self._mitigation_ansible_map = {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON in {config_path}: {e}")
            print(f"   Using empty configuration")
            self._mitigation_ansible_map = {}
        except Exception as e:
            print(f"❌ Unexpected error loading {config_path}: {e}")
            print(f"   Using empty configuration")
            self._mitigation_ansible_map = {}
    
    def get_playbook_path(self, action_name: str) -> str:
        """
        Get the Ansible playbook path for a given action name
        
        Args:
            action_name: The name of the mitigation action (case-insensitive)
            
        Returns:
            str: The path to the Ansible playbook
            
        Raises:
            ValueError: If the action name is not found in the configuration
        """
        action_name_upper = action_name.upper()
        
        if action_name_upper not in self._mitigation_ansible_map:
            available_actions = ', '.join(sorted(self._mitigation_ansible_map.keys()))
            raise ValueError(
                f"No playbook mapping found for action '{action_name}'. "
                f"Available actions (case insensitive): {available_actions}"
            )
        
        return self._mitigation_ansible_map[action_name_upper]
    
    def get_all_action_mappings(self) -> Dict[str, str]:
        """Get a copy of all action to playbook mappings"""
        return self._mitigation_ansible_map.copy()
    
    def reload_configs(self) -> Dict[str, str]:
        """
        Reload all configuration files
        
        Returns:
            Dict with status information about the reload
        """
        print("🔄 Reloading RTR configurations...")
        
        old_count = len(self._mitigation_ansible_map)
        self._load_all_configs()
        new_count = len(self._mitigation_ansible_map)
        
        status = {
            "status": "success",
            "message": "Configurations reloaded successfully",
            "mitigation_ansible_map": {
                "previous_count": old_count,
                "current_count": new_count,
                "actions": list(self._mitigation_ansible_map.keys())
            }
        }
        
        print(f"✅ Configurations reloaded: {new_count} action mappings loaded")
        return status


# Global singleton instance
_config_loader_instance: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """
    Get the global ConfigLoader singleton instance
    
    Returns:
        ConfigLoader: The singleton configuration loader instance
    """
    global _config_loader_instance
    if _config_loader_instance is None:
        _config_loader_instance = ConfigLoader()
    return _config_loader_instance


def reload_configurations() -> Dict[str, str]:
    """
    Reload all configurations
    
    Returns:
        Dict with status information about the reload
    """
    loader = get_config_loader()
    return loader.reload_configs()


def get_playbook_for_action(action_name: str) -> str:
    """
    Get the playbook path for a given action name
    
    Args:
        action_name: The name of the mitigation action
        
    Returns:
        str: The path to the Ansible playbook
        
    Raises:
        ValueError: If the action name is not found
    """
    loader = get_config_loader()
    return loader.get_playbook_path(action_name)


if __name__ == "__main__":
    # Test the configuration loader
    print("Testing ConfigLoader...")
    
    loader = get_config_loader()
    print(f"\nLoaded {len(loader.get_all_action_mappings())} action mappings")
    
    # Test getting a playbook
    try:
        playbook = get_playbook_for_action("DNS_RATE_LIMIT")
        print(f"\nDNS_RATE_LIMIT -> {playbook}")
    except ValueError as e:
        print(f"\nError: {e}")
    
    # Test with unknown action
    try:
        playbook = get_playbook_for_action("UNKNOWN_ACTION")
        print(f"\nUNKNOWN_ACTION -> {playbook}")
    except ValueError as e:
        print(f"\nExpected error for unknown action: {e}")
    
    # Test reload
    print("\nTesting reload...")
    status = reload_configurations()
    print(f"Reload status: {status}")
