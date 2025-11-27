from anki.notes import Note as AnkiNote
from PyQt6.QtCore import QThread, pyqtSignal

from typing import Dict

from .exceptions import ExternalException
from .llm_client import LLMClient
from .settings import SettingsNames


class NoteProcessor(QThread):
    """
    Stores the relevant information from a note that will be sent to GPT for modification.
    """

    progress_updated = pyqtSignal(int, str)  # Signal to update progress bar and label
    finished = pyqtSignal()  # Signal for when processing is done
    error = pyqtSignal(str)  # Signal for when processing is done

    def __init__(
        self,
        notes: list[AnkiNote],
        client: LLMClient,
        settings: Dict[
            str, str
        ],  # might be cleaner to pass in the fields we need directly, not sure,
        missing_field_is_error: bool = False,
    ):
        super().__init__()
        self.notes = notes
        self.total_items = len(notes)
        self.client = client
        self.note_fields = settings.get(
            SettingsNames.DESTINATION_FIELD_SETTING_NAME, []
        )
        self.response_keys = settings.get(SettingsNames.RESPONSE_KEYS_SETTING_NAME, [])
        self.missing_field_is_error = missing_field_is_error
        self.current_index = 0

    def run(self):
        """
        Processes all notes sequentially, by calling the LLM client.
        """
        for i in range(self.current_index, self.total_items):
            note = self.notes[self.current_index]
            prompt = self.client.get_user_prompt(note, self.missing_field_is_error)
            self.progress_updated.emit(
                int((i / self.total_items) * 100),
                f"Processing: {prompt}",
            )
            try:
                response = self.client.call([prompt])
            except ExternalException as e:
                self.error.emit(str(e))
                return
            for note_field, response_key in zip(self.note_fields, self.response_keys):
                note[note_field] = response[response_key]
            note.col.update_note(note)
            self.current_index += 1

        self.finished.emit()
