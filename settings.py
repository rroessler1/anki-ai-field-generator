from aqt.qt import QSettings


SETTINGS_ORGANIZATION = "github_rroessler1"
SETTINGS_APPLICATION = "anki-gpt-plugin"


class SettingsNames:
    API_KEY_SETTING_NAME = "api_key"
    BASE_URL_SETTING_NAME = "base_url"
    DESTINATION_FIELD_SETTING_NAME = "destination_field"
    LLM_CLIENT_NAME = "llm_client_name"
    MAX_RPM_SETTING_NAME = "max_rpm"
    MODEL_SETTING_NAME = "model"
    SYSTEM_PROMPT_SETTING_NAME = "system_prompt"
    USER_PROMPT_SETTING_NAME = "user_prompt"
    RESPONSE_KEYS_SETTING_NAME = "response_keys"


def get_settings() -> QSettings:
    """Returns a tuple of the settings and the groupName."""
    settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    client_name = settings.value(
        SettingsNames.LLM_CLIENT_NAME,
        defaultValue="Claude",
        type=str,
    )
    settings.beginGroup(client_name)
    return settings, client_name


def set_new_settings_group(settings: QSettings, client_name: str):
    """Sets a new group. This mutates the object!"""
    settings.endGroup()
    settings.setValue(SettingsNames.LLM_CLIENT_NAME, client_name)
    settings.beginGroup(client_name)
