from concurrent.futures import ThreadPoolExecutor, as_completed

from anki.notes import Note as AnkiNote
from aqt.qt import QSettings
from PyQt6.QtCore import QThread, pyqtSignal

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
        settings: QSettings,  # might be cleaner to pass in the fields we need directly, not sure,
        missing_field_is_error: bool = False,
    ):
        super().__init__()
        self.notes = notes
        self.total_items = len(notes)
        self.client = client
        self.settings = settings
        self.note_fields = settings.value(
            SettingsNames.DESTINATION_FIELD_SETTING_NAME, type="QStringList"
        )
        self.response_keys = settings.value(
            SettingsNames.RESPONSE_KEYS_SETTING_NAME, type="QStringList"
        )
        self.missing_field_is_error = missing_field_is_error
        self.current_index = 0

    def run(self):
        """
        Processes all notes concurrently, by calling the LLM client.
        """
        max_rpm = self._get_max_rpm()
        max_workers = max(1, max_rpm)
        prompts = []
        for i in range(self.current_index, self.total_items):
            note = self.notes[i]
            prompt = self.client.get_user_prompt(note, self.missing_field_is_error)
            prompts.append((note, prompt))

        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.client.call, [prompt]): (note, prompt)
                for note, prompt in prompts
            }
            for future in as_completed(futures):
                note, prompt = futures[future]
                try:
                    response = future.result()
                except ExternalException as e:
                    for pending in futures:
                        if not pending.done():
                            pending.cancel()
                    self.error.emit(str(e))
                    return
                for note_field, response_key in zip(
                    self.note_fields, self.response_keys
                ):
                    note[note_field] = response[response_key]
                note.col.update_note(note)
                completed += 1
                self.progress_updated.emit(
                    int((completed / self.total_items) * 100),
                    f"Processed: {prompt}",
                )

        self.current_index = self.total_items
        self.finished.emit()

    def _get_max_rpm(self) -> int:
        value = self.settings.value(
            SettingsNames.MAX_RPM_SETTING_NAME,
            defaultValue=10,
            type=int,
        )
        try:
            return int(value)
        except (TypeError, ValueError):
            return 10
