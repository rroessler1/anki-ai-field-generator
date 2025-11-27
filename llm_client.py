"""Generic interface for a LLM client."""

from abc import ABC, abstractmethod
from anki.notes import Note as AnkiNote

from .prompt_config import PromptConfig


class LLMClient(ABC):
    """
    Generic interface for a LLM client.
    """
    debug: bool = True

    @property
    @abstractmethod
    def prompt_config(self) -> PromptConfig:
        """Configuration to read prompt attributes"""

    @abstractmethod
    def call(self, prompts: list[str]) -> dict:
        """
        Accepts a list of prompts, and returns a list of responses, one per prompt.
        The responses are a list of key-value pairs.
        """

    def fill_string_with_note_fields(
        self, s: str, note: AnkiNote, missing_field_is_error=False
    ) -> str:
        """
        Replaces any keys in {braces} in the string with actual values from the Note.
        Substitutes a blank string if the Note did not have the corresponding key.
        """

        class DefaultDict(dict):
            """
            Replaces missing key with blank.
            """

            def __missing__(self, key):
                if missing_field_is_error:
                    raise RuntimeError(f"NoteID {note.id} does not have field {key}.")
                return ""

        return s.format_map(DefaultDict(dict(zip(note.keys(), note.values()))))

    def get_user_prompt(self, note: AnkiNote, missing_field_is_error=False) -> str:
        """
        Creates the prompt by filling in fields from the Note.
        """
        return self.fill_string_with_note_fields(
            self.prompt_config.user_prompt, note, missing_field_is_error
        )
