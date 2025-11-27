import json
from typing import Dict, List, Optional

from .settings import get_settings, set_new_settings_group, SettingsNames


class ProfileDB:
    """
    Loads and saves user profiles.
    """

    CURRENT_PROFILE_KEY = "current_profile_name"
    DEFAULT_PROFILE_NAME = "Default"
    PROFILE_LIST_KEY = "profile_templates_list"
    PROFILE_PREFIX = "profile_template_"

    def __init__(self):
        self.app_settings, _ = get_settings()
        self._create_default_profile_if_none_exists()

    def _create_default_profile_if_none_exists(self):
        """Ensure that a default profile exists."""
        profile_list = self.get_all_profiles()
        if len(profile_list) == 0:
            profile_list.append(self.DEFAULT_PROFILE_NAME)
            self._save_all_profiles(profile_list)
            self._save_user_active_profile(self.DEFAULT_PROFILE_NAME)

    def _get_profile_data_config_key(self, profile_name: str) -> str:
        return f"{self.PROFILE_PREFIX}{profile_name}"

    def _save_all_profiles(self, profiles: List[str]) -> None:
        self.app_settings.setValue(self.PROFILE_LIST_KEY, profiles)

    def _save_user_active_profile(self, profile_name: str) -> None:
        self.app_settings.setValue(self.CURRENT_PROFILE_KEY, profile_name)

    def get_all_profiles(self) -> List[str]:
        """Get list of all profile names."""
        profile_list = self.app_settings.value(
            self.PROFILE_LIST_KEY, type="QStringList"
        )
        assert (
            profile_list is not None and len(profile_list) > 0
        ), "There should be at least one profile."
        return profile_list

    def get_current_profile_name(self) -> str:
        return self.app_settings.value(self.CURRENT_PROFILE_KEY)

    def get_llm_client_name(self) -> str:
        return self.load_profile_data().get(SettingsNames.LLM_CLIENT_NAME)

    def create_new_profile(self, name: str) -> None:
        all_profiles = self.get_all_profiles()
        # Can only create one profile with a given name
        if name in all_profiles:
            return
        all_profiles.append(name)
        self._save_all_profiles(all_profiles)
        self._save_user_active_profile(name)

    def delete_profile(self, name: str):
        all_profiles = self.get_all_profiles()

        if len(all_profiles) <= 1:
            return
        if name not in all_profiles:
            return

        idx = all_profiles.index(name)
        all_profiles.remove(name)
        self.app_settings.remove(self._get_profile_data_config_key(name))

        new_active_profile_name = (
            all_profiles[idx] if idx < len(all_profiles) else all_profiles[-1]
        )
        self._save_all_profiles(all_profiles)
        self._save_user_active_profile(new_active_profile_name)

    def load_profile_data(self) -> Dict[str, str]:
        """
        Load configuration data for the given name.
        Returns None if configuration doesn't exist.
        """
        profile_name = self.get_current_profile_name()
        config_key = self._get_profile_data_config_key(profile_name)
        config_json = self.app_settings.value(config_key)
        assert (
            config_json is not None
        ), f"Profile data for '{profile_name}' should exist."
        return json.loads(config_json)

    def save_profile_data(
        self, profile_name: str, profile_data: Dict[str, str]
    ) -> bool:
        """
        Save a profile with the given name and data.
        Returns True if successful, False if profile_name is invalid.
        """
        if not profile_name or profile_name.strip() == "":
            return False

        profile_name = profile_name.strip()

        # Save the profile data
        config_key = self._get_profile_data_config_key(profile_name)
        self.app_settings.setValue(config_key, json.dumps(profile_data))

        profile_list = self.get_all_profiles()
        assert (
            profile_name in profile_list
        ), f"Profile {profile_name} should exist in profile list."
        return True
