from aqt.qt import QSettings


SETTINGS_ORGANIZATION = "github_rroessler1"
SETTINGS_APPLICATION = "anki-gpt-plugin"

class SettingsNames():
    API_KEY_SETTING_NAME = "api_key"
    SYSTEM_PROMPT_SETTING_NAME = "system_prompt"
    USER_PROMPT_SETTING_NAME = "user_prompt"
    RESPONSE_KEYS_SETTING_NAME = "response_keys"

def get_settings():
    return QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
