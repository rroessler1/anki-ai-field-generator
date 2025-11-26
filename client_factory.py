"""
Factory that returns the corrent LLM Client configurations.
"""

from .claude_client import ClaudeClient
from .claude_dialog import ClaudeDialog
from .deepseek_client import DeepseekClient
from .deepseek_dialog import DeepSeekDialog
from .gemini_client import GeminiClient
from .gemini_dialog import GeminiDialog
from .llm_client import LLMClient
from .main_window import MainWindow
from .note_processor import NoteProcessor
from .openai_client import OpenAIClient
from .openai_dialog import OpenAIDialog
from .prompt_config import PromptConfig
from .progress_bar import ProgressDialog
from .settings import get_settings, set_new_settings_group
from .user_base_dialog import UserBaseDialog


class ClientFactory:
    """
    Factory that returns the corrent LLM Client configurations.
    """

    valid_clients = ["Claude", "OpenAI", "DeepSeek", "Gemini"]

    def __init__(self, browser):
        self.app_settings, self.client_name = get_settings()
        self.client_name = "Claude" # TODO
        self.browser = browser
        self.notes = [
            browser.mw.col.get_note(note_id) for note_id in browser.selectedNotes()
        ]

    def update_client(self, client_name: str):
        assert (
            client_name in ClientFactory.valid_clients
        ), f"{client_name} is not implemented as a LLM Client."
        self.client_name = client_name
        set_new_settings_group(self.app_settings, self.client_name)

    def get_client(self) -> LLMClient:
        """
        Factory method that returns the LLM Client implementation.
        Add an implementation for each Client you add.
        """
        prompt_config = PromptConfig(self.app_settings)
        if self.client_name == "OpenAI":
            llm_client = OpenAIClient(prompt_config)
            return llm_client
        if self.client_name == "DeepSeek":
            llm_client = DeepseekClient(prompt_config)
            return llm_client
        if self.client_name == "Claude":
            llm_client = ClaudeClient(prompt_config)
            return llm_client
        if self.client_name == "Gemini":
            llm_client = GeminiClient(prompt_config)
            return llm_client
        raise NotImplementedError(f"No LLM client implemented for {self.client_name}")

    def get_dialog(self) -> UserBaseDialog:
        """
        Factory method that returns the settings dialog for the user for each LLM.
        Client. Add an implementation for each Client you add.
        """
        if self.client_name == "OpenAI":
            return OpenAIDialog(self.app_settings, self.notes)
        if self.client_name == "DeepSeek":
            return DeepSeekDialog(self.app_settings, self.notes)
        if self.client_name == "Claude":
            return ClaudeDialog(self.app_settings, self.notes)
        if self.client_name == "Gemini":
            return GeminiDialog(self.app_settings, self.notes)
        raise NotImplementedError(
            f"No user settings dialog implemented for {self.client_name}"
        )

    def show(self):
        """
        Displays the user settings UI.
        """
        # self.get_dialog(self.client_name).show(notes)
        self.mw = MainWindow(
            self, lambda: self.on_submit(browser=self.browser, notes=self.notes)
        )
        self.mw.show()

    def on_submit(self, browser, notes):
        """
        Called once the user confirms the card modifications.
        This also refreshes the settings and the LLM client, as the user may have
        changed them.
        """
        note_processor = NoteProcessor(notes, self.get_client(), self.app_settings)
        dialog = ProgressDialog(note_processor, success_callback=self.mw.close)
        dialog.exec()
        browser.mw.reset()
