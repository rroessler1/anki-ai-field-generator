from typing import List

from .settings import get_settings, set_new_settings_group


# load all profiles

# return list of all profiles and currently selected one

# should have save and load methods

# ok, this should only handle the saving and loading, but not any UI stuff

class ProfileDB:
    """
    Loads and saves user profiles.
    """

    def __init__(self):
        self.app_settings, self.current_profile = get_settings()
        self.current_profile = "Default" # TODO
        # TODO
        self.all_profiles = ["Default", "Foo"]

    def get_all_profiles(self) -> List:
        # TODO: load from app_settings
        return self.all_profiles
    
    def get_current_profile(self) -> str:
        return self.current_profile
    
    def get_llm_client_name(self, profile) -> str:
        # TODO: load from actual profile
        return "OpenAI"
    
    def create_new_profile(self, name: str) -> None:
        self.all_profiles.append(name)
        self.current_profile = name

    def delete_profile(self, name: str):
        if len(self.all_profiles) <= 1:
            return
        current_profile_idx = self.all_profiles.index(name)
        self.all_profiles.remove(name)
        self.current_profile = self.all_profiles[current_profile_idx] if current_profile_idx < len(self.all_profiles) else self.all_profiles[-1]
    
