from collections.abc import Callable
from PyQt6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QComboBox,
)

from .profiles import ProfileDB
from .settings import SettingsNames
from .ui_tools import UITools
from .user_base_dialog import UserBaseDialog


#  Main Window
class MainWindow(QMainWindow):
    def __init__(self, client_factory, on_submit: Callable):
        super().__init__()
        # The client factory is already initialized with the current profile
        self.client_factory = client_factory
        self.profile_db = ProfileDB()

        # In MainWindow, UITools is only used for creating labels
        # Therefore we can initialize it with None values
        self.ui_tools = UITools(None, None)

        self.setWindowTitle("Anki AI - Update Your Flashcards with AI")
        screen = QApplication.primaryScreen().geometry()
        width = 1100
        height = 800
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()

        # Dropdown for selecting profiles
        profile_options_layout = QHBoxLayout()
        profile_options_layout.addWidget(self.ui_tools.create_label("Select Profile:"))
        self.profile_selector = QComboBox()
        all_profiles = self.profile_db.get_all_profiles()
        self.profile_selector.addItems(all_profiles)
        self.profile_selector.setCurrentIndex(
            all_profiles.index(self.profile_db.get_current_profile_name())
        )
        self.profile_selector.currentIndexChanged.connect(self.switch_profile)
        self.profile_selector.setFixedWidth(200)
        profile_options_layout.addWidget(self.profile_selector)

        # Buttons
        create_btn = QPushButton("Create")
        create_btn.setFixedWidth(80)
        create_btn.clicked.connect(self.create_profile)
        profile_options_layout.addWidget(create_btn)

        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(80)
        save_btn.clicked.connect(self.save_profile)
        profile_options_layout.addWidget(save_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(80)
        delete_btn.clicked.connect(self.delete_profile)
        profile_options_layout.addWidget(delete_btn)

        profile_options_layout.addStretch()
        self.layout.addLayout(profile_options_layout)

        # Dropdown for selecting clients
        llm_options_layout = QHBoxLayout()
        llm_options_layout.addWidget(self.ui_tools.create_label("Select LLM:"))
        self.client_selector = QComboBox()
        self.client_selector.addItems(client_factory.valid_clients)
        self.client_selector.currentIndexChanged.connect(self.switch_client)
        self.client_selector.setFixedWidth(200)
        llm_options_layout.addWidget(self.client_selector)
        llm_options_layout.addStretch()
        self.layout.addLayout(llm_options_layout)

        # Container for the clients' sublayout
        client_ui_container = QWidget()
        self.client_ui_layout = QVBoxLayout()
        self.client_ui_layout.setContentsMargins(0, 0, 0, 0)
        client_ui_container.setLayout(self.client_ui_layout)
        self.layout.addWidget(client_ui_container)
        # Placeholder for the client sublayout
        self.current_client_widget: UserBaseDialog = client_factory.get_dialog()

        central_widget.setLayout(self.layout)

        # Initialize default UI based on the current profile
        self.switch_profile()

        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(lambda: self.accept(on_submit))
        button_box.rejected.connect(self.close)
        self.layout.addWidget(button_box)

    def create_profile(self):
        profile_name, ok = QInputDialog.getText(
            self, "Create New Profile", "Enter profile name:"
        )
        if ok and profile_name:
            self.profile_db.create_new_profile(profile_name)
            # TODO: can try calling self.layout.update() instead
            self.profile_selector.addItem(profile_name)
            self.profile_selector.setCurrentText(profile_name)
            # TODO: check
            # self.switch_profile()

    def delete_profile(self):
        current_profile = self.profile_selector.currentText()
        self.profile_db.delete_profile(current_profile)
        self.profile_selector.removeItem(self.profile_selector.currentIndex())
        new_profile = self.profile_db.get_current_profile_name()
        self.profile_selector.setCurrentText(new_profile)
        # TODO: check
        # self.switch_profile()

    def save_profile(self):
        self.profile_db.save_profile_data(
            self.profile_selector.currentText(), self.get_all_user_json_settings()
        )

    def get_all_user_json_settings(self):
        json_settings = self.current_client_widget.create_json_settings()
        # TODO: this shouldn't be both here and in profiles.py, it's messy
        json_settings[SettingsNames.LLM_CLIENT_NAME] = (
            self.client_selector.currentText()
        )
        return json_settings

    def switch_profile(self):
        current_profile = self.profile_selector.currentText()
        self.profile_db._save_profile_as_currently_selected(current_profile)
        profile_data = self.profile_db.load_profile_data()
        self.client_factory.update_user_settings(profile_data)
        llm_client_name = self.profile_db.get_llm_client_name()
        if not llm_client_name:
            raise AssertionError("LLM client name not found in profile data.")
        if llm_client_name:
            self.client_selector.setCurrentIndex(
                self.client_factory.valid_clients.index(llm_client_name)
            )
            self.switch_client()

    def switch_client(self):
        # Grab the current UI settings
        self.client_factory.update_user_settings(self.get_all_user_json_settings())

        # Remove the existing client UI
        if self.current_client_widget:
            self.client_ui_layout.removeWidget(self.current_client_widget)
            # Not strictly necessary, but better for memory management
            self.current_client_widget.deleteLater()

        self.client_factory.update_client(
            self.client_selector.currentText()
        )
        self.current_client_widget = self.client_factory.get_dialog()
        self.client_ui_layout.addWidget(self.current_client_widget)
        self.current_client_widget.show()
        self.layout.update()

    def accept(self, on_submit: Callable):
        """
        Saves settings when user accepts.
        """
        # This order is important, because the accept() saves settings
        # which the on_submit might need
        if self.current_client_widget.accept():
            self.save_profile()
            on_submit()
