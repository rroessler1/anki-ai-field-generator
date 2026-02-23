from collections.abc import Callable
from PyQt6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QHBoxLayout,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QComboBox,
)

from .ui_tools import UITools


#  Main Window
class MainWindow(QMainWindow):
    def __init__(self, client_factory, on_submit: Callable):
        super().__init__()
        self.client_factory = client_factory
        # Don't need to set the below parameters as we're not saving any data
        self.ui_tools = UITools(None, None)

        self.setWindowTitle("Anki AI - Update Your Flashcards with AI")
        screen = QApplication.primaryScreen().geometry()
        width = 1100
        height = 900
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()

        # Dropdown for selecting clients
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.ui_tools.create_label("Select LLM:"))
        self.client_selector = QComboBox()
        self.client_selector.addItems(client_factory.valid_clients)
        self.client_selector.currentIndexChanged.connect(self.switch_client)
        self.client_selector.setFixedWidth(200)
        h_layout.addWidget(self.client_selector)
        h_layout.addStretch()
        self.layout.addLayout(h_layout)

        # Container for the clients' sublayout
        client_ui_container = QWidget()
        self.client_ui_layout = QVBoxLayout()
        self.client_ui_layout.setContentsMargins(0, 0, 0, 0)
        client_ui_container.setLayout(self.client_ui_layout)
        self.layout.addWidget(client_ui_container)
        # Placeholder for the client sublayout
        self.current_client_widget = None

        central_widget.setLayout(self.layout)

        # Initialize default UI based on the selected client
        self.client_selector.setCurrentIndex(
            client_factory.valid_clients.index(client_factory.client_name)
        )
        self.switch_client()

        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box = QDialogButtonBox(buttons)
        button_box.accepted.connect(lambda: self.accept(on_submit))
        button_box.rejected.connect(self.close)
        self.layout.addWidget(button_box)

    def switch_client(self):
        client_name = self.client_selector.currentText()
        # Remove the existing client UI
        if self.current_client_widget:
            self.client_ui_layout.removeWidget(self.current_client_widget)
            # Not strictly necessary, but better for memory management
            self.current_client_widget.deleteLater()

        self.client_factory.update_client(client_name)
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
            on_submit()
