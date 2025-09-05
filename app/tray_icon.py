from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QCoreApplication
import os

from infra.paths import resource_path


class TrayIcon(QSystemTrayIcon):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self._setup()

    def _setup(self):
        icon_path = resource_path(os.path.join('assets', 'app_icon.ico'))
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            self.setIcon(QIcon())
        menu = QMenu()

        self.show_action = QAction("시간표 보기", menu)
        self.show_action.triggered.connect(self.widget.show)
        menu.addAction(self.show_action)

        menu.addSeparator()

        self.exit_action = QAction("종료", menu)
        self.exit_action.triggered.connect(QCoreApplication.instance().quit)
        menu.addAction(self.exit_action)

        self.setContextMenu(menu)


