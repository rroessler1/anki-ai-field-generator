from aqt import mw
from aqt.qt import QAction, QMenu
from anki import hooks

from .client_factory import ClientFactory
from .profiles import ProfileDB


def on_setup_menus(browser):
    def display_ui():
        client_factory = ClientFactory(browser, ProfileDB())
        client_factory.show()

    menu = QMenu("Anki AI", browser.form.menubar)
    browser.form.menubar.addMenu(menu)
    cps_action = QAction("Update Your Flashcards with AI", mw)
    cps_action.triggered.connect(display_ui)
    menu.addAction(cps_action)


hooks.addHook("browser.setupMenus", on_setup_menus)
