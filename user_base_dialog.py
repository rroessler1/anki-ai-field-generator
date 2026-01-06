from abc import ABCMeta, abstractmethod
from anki.notes import Note as AnkiNote
from aqt.qt import (
    QSettings,
    QWidget,
    QHBoxLayout,
    QMessageBox,
    QVBoxLayout,
    Qt,
    QScrollArea,
)
from PyQt6 import QtCore
from .settings import SettingsNames
from .two_col_layout import DynamicForm
from .ui_tools import UITools


# I think I should have:
# - something generic that adds menubar things
# - something generic that loads settings
# - ideally something generic-ish that passes information through
# - an action-custom dialog


class MyMeta(ABCMeta, type(QtCore.QObject)):
    pass


class UserBaseDialog(QWidget, metaclass=MyMeta):
    def __init__(self, app_settings: QSettings, selected_notes: list[AnkiNote]):
        super().__init__()
        self._width = 500
        self.app_settings: QSettings = app_settings
        self.selected_notes = selected_notes
        self.ui_tools: UITools = UITools(app_settings, self._width)

    def show(self):
        if self.layout() is not None:
            QWidget().setLayout(self.layout())  # Clears any existing layout
        card_fields = sorted(
            {field for note in self.selected_notes for field in note.keys()}
        )

        self.resize(self._width * 2 + 20, 750)
        container_widget = QWidget()
        main_layout = QHBoxLayout(container_widget)

        left_container = QWidget()
        left_container.setMaximumWidth(self._width)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_container.setLayout(left_layout)

        self.add_models_dropdown(left_layout)
        self.add_api_key(left_layout)
        self.add_base_url(left_layout)
        self.add_max_rpm(left_layout)
        self.add_system_prompt(
            left_layout, self.system_prompt_description, self.system_prompt_placeholder
        )
        left_layout.addStretch()

        # Right Column
        right_container = QWidget()
        right_container.setMaximumWidth(self._width)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_container.setLayout(right_layout)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # User Prompt
        self.add_user_prompt(
            right_layout, self.user_prompt_description, self.user_prompt_placeholder
        )
        # Available Fields
        right_layout.addWidget(
            self.ui_tools.create_descriptive_text(
                f"Available fields: {', '.join(card_fields)}"
            )
        )

        # Destination Configuration
        right_layout.addWidget(
            self.ui_tools.create_label("Save the AI output to the Anki fields:")
        )
        right_layout.addWidget(
            self.ui_tools.create_descriptive_text(self.mapping_instruction_text)
        )
        self.two_col_form = DynamicForm(
            self.app_settings.value(
                SettingsNames.RESPONSE_KEYS_SETTING_NAME, type="QStringList"
            ),
            self.app_settings.value(
                SettingsNames.DESTINATION_FIELD_SETTING_NAME, type="QStringList"
            ),
            card_fields,
        )
        right_layout.addWidget(self.two_col_form)

        # Misc
        right_layout.addWidget(
            self.ui_tools.create_label(
                f"{len(self.selected_notes)} cards selected. Modify cards?"
            )
        )

        main_layout.addWidget(left_container)
        main_layout.addWidget(right_container)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_widget)

        final_layout = QVBoxLayout(self)
        final_layout.addWidget(scroll_area)
        self.setLayout(final_layout)
        return self

    @property
    @abstractmethod
    def service_name(self):
        """User friendly name of the service, e.g. 'OpenAI'"""

    @property
    @abstractmethod
    def models(self) -> list[str]:
        """Array of the names of the available models"""

    @property
    @abstractmethod
    def base_url(self):
        """Default base URL for the service"""

    @property
    @abstractmethod
    def system_prompt_description(self):
        """User friendly description for the system prompt"""

    @property
    @abstractmethod
    def system_prompt_placeholder(self):
        """Optional placeholder text for the system prompt"""

    @property
    @abstractmethod
    def user_prompt_description(self):
        """User friendly description for the user prompt"""

    @property
    @abstractmethod
    def user_prompt_placeholder(self):
        """Optional placeholder text for the user prompt"""

    @property
    def mapping_instruction_text(self):
        """User friendly description for the JSON key to Note field mapping instructions"""
        return """
        For each piece of information you told the AI to give you in the System Prompt, enter it here, and select the Field on your Card where you want to save it.<br><br>
        <b>Example:</b> If you asked the AI for a German sentence and its translation, and your Anki Fields are <code>de_sentence</code> and <code>en_sentence</code>, enter:
        <pre>exampleSentence de_sentence<br>translation en_sentence</pre>
        """

    def add_models_dropdown(self, layout):
        layout.addWidget(self.ui_tools.create_label("Model Name:"))
        layout.addWidget(
            self.ui_tools.create_dropdown(
                SettingsNames.MODEL_SETTING_NAME, self.models, allow_custom=True
            )
        )

    def add_api_key(self, layout):
        layout.addWidget(self.ui_tools.create_label(f"{self.service_name} API Key:"))
        layout.addWidget(
            self.ui_tools.create_text_entry(SettingsNames.API_KEY_SETTING_NAME)
        )

    def add_base_url(self, layout):
        layout.addWidget(self.ui_tools.create_label("Base URL (optional):"))
        layout.addWidget(
            self.ui_tools.create_text_entry(
                SettingsNames.BASE_URL_SETTING_NAME,
                placeholder=self.base_url,
            )
        )

    def add_max_rpm(self, layout):
        layout.addWidget(self.ui_tools.create_label("Max RPM (concurrent requests):"))
        layout.addWidget(
            self.ui_tools.create_text_entry(
                SettingsNames.MAX_RPM_SETTING_NAME,
                placeholder="10",
                default_value="10",
            )
        )

    def add_system_prompt(
        self, layout, system_prompt_description, system_prompt_placeholder
    ):
        layout.addWidget(self.ui_tools.create_label("System Prompt:"))
        layout.addWidget(
            self.ui_tools.create_descriptive_text(system_prompt_description)
        )
        layout.addWidget(
            self.ui_tools.create_text_edit(
                SettingsNames.SYSTEM_PROMPT_SETTING_NAME,
                system_prompt_placeholder,
                max_height=350,
            )
        )

    def add_user_prompt(self, layout, user_prompt_description, user_prompt_placeholder):
        layout.addWidget(self.ui_tools.create_label("User Prompt:"))
        layout.addWidget(self.ui_tools.create_descriptive_text(user_prompt_description))
        layout.addWidget(
            self.ui_tools.create_text_edit(
                SettingsNames.USER_PROMPT_SETTING_NAME,
                user_prompt_placeholder,
                max_height=200,
            )
        )

    def accept(self) -> bool:
        """
        Saves settings when user accepts. Returns False if invalid.
        """
        if not self.are_settings_valid():
            return False
        self.ui_tools.save_settings()
        keys, fields = self.two_col_form.get_inputs()
        self.app_settings.setValue(SettingsNames.RESPONSE_KEYS_SETTING_NAME, keys)
        self.app_settings.setValue(
            SettingsNames.DESTINATION_FIELD_SETTING_NAME,
            fields,
        )
        return True

    def are_settings_valid(self) -> bool:
        """
        Returns True if all required settings are present, False otherwise.
        Displays an error dialog if some are missing.
        """
        settings = self.ui_tools.get_settings()
        if (
            SettingsNames.API_KEY_SETTING_NAME not in settings
            or not settings[SettingsNames.API_KEY_SETTING_NAME]
        ):
            show_error_message("Please enter an API key.")
            return False
        if (
            SettingsNames.USER_PROMPT_SETTING_NAME not in settings
            or not settings[SettingsNames.USER_PROMPT_SETTING_NAME]
        ):
            show_error_message("Please enter a prompt.")
            return False

        keys, fields = self.two_col_form.get_inputs()
        if len(keys) == 0 or len(fields) == 0:
            show_error_message("You must save at least one AI Output to one Field.")
            return False

        return True


def show_error_message(message: str):
    """Displays a popup with the message"""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Error")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()  # Display the message box
