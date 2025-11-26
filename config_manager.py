from aqt.qt import QSettings
from typing import Dict, List, Optional
import json


class ConfigManager:
    """Manages saving and loading of configuration templates."""

    CONFIG_LIST_KEY = "config_templates_list"
    CONFIG_PREFIX = "config_template_"
    CURRENT_CONFIG_KEY = "current_config_name"
    DEFAULT_CONFIG_NAME = "Default"

    def __init__(self, settings: QSettings):
        self.settings = settings
        self._create_default_config_if_none_exists()
        # TODO: not sure if it should do this or not, depends who owns the state
        self.set_current_config(self.get_current_config_name())

    def _create_default_config_if_none_exists(self):
        """Ensure that a default configuration exists."""
        config_list = self.get_config_names()
        if len(config_list) == 0:
            config_list.append(self.DEFAULT_CONFIG_NAME)
            self.settings.setValue(self.CONFIG_LIST_KEY, config_list)

    def get_config_names(self) -> List[str]:
        """Get list of all configuration names."""
        config_list = self.settings.value(self.CONFIG_LIST_KEY, type="QStringList")
        return config_list if config_list else []

    def get_current_config_name(self) -> str:
        """Get the currently selected configuration name."""
        return self.settings.value(self.CURRENT_CONFIG_KEY, self.get_config_names()[0])

    def set_current_config(self, config_name: str):
        """Set the currently selected configuration."""
        assert (
            config_name in self.get_config_names()
        ), f"Config '{config_name}' does not exist."
        self.settings.setValue(self.CURRENT_CONFIG_KEY, config_name)

    def save_config(self, config_name: str, config_data: Dict[str, str]) -> bool:
        """
        Save a configuration with the given name and data.
        Returns True if successful, False if config_name is invalid.
        """
        if not config_name or config_name.strip() == "":
            return False

        config_name = config_name.strip()

        # Save the configuration data
        config_key = f"{self.CONFIG_PREFIX}{config_name}"
        self.settings.setValue(config_key, json.dumps(config_data))

        # Add to config list if not already present
        config_list = self.get_config_names()
        if config_name not in config_list:
            config_list.append(config_name)
            self.settings.setValue(self.CONFIG_LIST_KEY, config_list)

        return True

    def load_config(self, config_name: str) -> Optional[Dict[str, str]]:
        """
        Load configuration data for the given name.
        Returns None if configuration doesn't exist.
        """
        config_key = f"{self.CONFIG_PREFIX}{config_name}"
        config_json = self.settings.value(config_key)

        if config_json:
            try:
                return json.loads(config_json)
            except json.JSONDecodeError:
                return None
        return None

    def delete_config(self, config_name: str) -> bool:
        """
        Delete a configuration. Cannot delete the configuration if only one remains.
        Returns True if successful, False if config cannot be deleted.
        """
        config_list = self.get_config_names()
        if len(config_list) <= 1:
            return False

        if config_name not in config_list:
            return False

        # Remove from list
        index = config_list.index(config_name)
        config_list.remove(config_name)
        self.settings.setValue(self.CONFIG_LIST_KEY, config_list)

        # Remove the configuration data
        config_key = f"{self.CONFIG_PREFIX}{config_name}"
        self.settings.remove(config_key)

        # If this was the current config, switch to default
        # TODO FLUP: but then I'm not sure this belongs here... but it's very nice here
        if self.get_current_config_name() == config_name:
            new_config = config_list[max(0, index - 1)]
            self.set_current_config(new_config)

        return True

    def config_exists(self, config_name: str) -> bool:
        """Check if a configuration with the given name exists."""
        return config_name in self.get_config_names()
