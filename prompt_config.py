import re

from aqt.qt import QSettings

from .settings import SettingsNames


class PromptConfig:
    """
    Stores all the user configuration needed to create a prompt and parse the response
    """

    def __init__(self, settings: QSettings):
        self.settings: QSettings = settings
        if self.settings:
            self._load_settings()

    @classmethod
    def create_test_instance(cls, api_key, system_prompt, user_prompt, response_keys):
        """For testing only"""
        obj = cls(None)

        obj.api_key = api_key
        obj.system_prompt = system_prompt
        obj.user_prompt = user_prompt
        obj.response_keys = response_keys
        obj.required_fields = obj._extract_text_between_braces(obj.user_prompt)
        return obj

    def refresh(self) -> None:
        self._load_settings()

    def _load_settings(self) -> None:
        self.api_key: str = self.settings.value(
            SettingsNames.API_KEY_SETTING_NAME, defaultValue="", type=str
        )
        self.base_url: str = self.settings.value(
            SettingsNames.BASE_URL_SETTING_NAME, defaultValue="", type=str
        )
        self.model: str = self.settings.value(
            SettingsNames.MODEL_SETTING_NAME, defaultValue="", type=str
        )
        self.system_prompt: str = self.settings.value(
            SettingsNames.SYSTEM_PROMPT_SETTING_NAME, defaultValue="", type=str
        )
        self.user_prompt: str = self.settings.value(
            SettingsNames.USER_PROMPT_SETTING_NAME, defaultValue="", type=str
        )
        self.response_keys: list[str] = self.settings.value(
            SettingsNames.RESPONSE_KEYS_SETTING_NAME,
            defaultValue=[],
            type="QStringList",
        )
        self.required_fields: list[str] = self._extract_text_between_braces(
            self.user_prompt
        )

    def _extract_text_between_braces(self, input_string):
        # Regular expression to match content between braces { }
        pattern = r"\{(.*?)\}"
        matches = re.findall(pattern, input_string)
        # Remove blank matches
        return [m for m in matches if m]
