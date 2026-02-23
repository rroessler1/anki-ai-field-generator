from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

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
        self.completed_indices = (
            set()
        )  # Track which notes have been successfully processed
        self._cancelled = False  # Flag for graceful cancellation

    def cancel(self):
        """Request graceful cancellation of processing."""
        self._cancelled = True

    def run(self):
        """
        Processes all notes concurrently, by calling the LLM client.
        Uses a sliding window pattern to avoid loading all prompts into memory.
        """
        self._cancelled = False
        max_concurrent_requests = self._get_max_concurrent_requests()
        max_workers = max(1, max_concurrent_requests)

        completed = len(self.completed_indices)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            note_iter = iter(
                (i, note)
                for i, note in enumerate(self.notes)
                if i not in self.completed_indices  # Skip already-completed notes
            )

            # Fill initial batch (buffer of 2x workers to keep threads busy)
            for _ in range(min(max_workers * 2, self.total_items)):
                try:
                    i, note = next(note_iter)
                    prompt = self.client.get_user_prompt(
                        note, self.missing_field_is_error
                    )
                    future = executor.submit(self.client.call, [prompt])
                    futures[future] = (i, note, prompt)
                except StopIteration:
                    break

            # Process completions and submit new work
            while futures:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)

                for future in done:
                    i, note, prompt = futures[future]
                    try:
                        response = future.result()
                    except ExternalException as e:
                        # Cancel all pending futures
                        for pending in futures:
                            if not pending.done():
                                pending.cancel()
                        self.error.emit(str(e))
                        return

                    # Update note fields
                    for note_field, response_key in zip(
                        self.note_fields, self.response_keys
                    ):
                        field_value = response[response_key]
                        if isinstance(field_value, str):
                            field_value = field_value.replace("\n", "<br>")
                        note[note_field] = field_value
                    note.col.update_note(note)
                    self.completed_indices.add(
                        i
                    )  # Mark this note as successfully completed

                    completed += 1
                    self.progress_updated.emit(
                        int((completed / self.total_items) * 100),
                        f"Processed: {prompt}",
                    )

                    # Remove completed future
                    del futures[future]

                # Check for cancellation AFTER saving completed work
                if self._cancelled:
                    # Cancel all pending futures
                    for pending in futures:
                        if not pending.done():
                            pending.cancel()
                    return

                # Submit new work for each completed future
                for _ in range(len(done)):
                    try:
                        i, note = next(note_iter)
                        prompt = self.client.get_user_prompt(
                            note, self.missing_field_is_error
                        )
                        new_future = executor.submit(self.client.call, [prompt])
                        futures[new_future] = (i, note, prompt)
                    except StopIteration:
                        break

        self.completed_indices.clear()  # Clear on full completion
        self.finished.emit()

    def _get_max_concurrent_requests(self) -> int:
        value = self.settings.value(
            SettingsNames.MAX_CONCURRENT_REQUESTS_SETTING_NAME,
            defaultValue=10,
            type=int,
        )
        try:
            return int(value)
        except (TypeError, ValueError):
            return 10
