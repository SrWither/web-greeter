# -*- coding: utf-8 -*-
#
#  browser.py
#
#  Copyright © 2017 Antergos
#  Copyright © 2021 JezerM
#
#  This file is part of Web Greeter.
#
#  Web Greeter is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  Web Greeter is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  The following additional terms are in effect as per Section 7 of the license:
#
#  The preservation of all legal notices and author attributions in
#  the material or in the Appropriate Legal Notices displayed
#  by works containing it is required.
#
#  You should have received a copy of the GNU General Public License
#  along with Web Greeter; If not, see <http://www.gnu.org/licenses/>.

# Standard lib

import re
import sys
import os
from typing import (
    Dict,
    Tuple,
    TypeVar,
)

# 3rd-Party Libs
from PyQt5.QtCore import QUrl, Qt, QCoreApplication, QFile, QSize
from PyQt5.QtWebEngineCore import QWebEngineUrlScheme
from PyQt5.QtWidgets import (
    QAction, QApplication, QDesktopWidget,
    QDockWidget, QMainWindow, QLayout, qApp, QWidget
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineScript, QWebEngineProfile,
    QWebEngineSettings, QWebEngineView, QWebEnginePage
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWebChannel import QWebChannel
from bridge.Config import Config
from bridge.Greeter import Greeter
from bridge.ThemeUtils import ThemeUtils

from browser.error_prompt import WebPage
from browser.url_scheme import QtUrlSchemeHandler
from browser.interceptor import QtUrlRequestInterceptor
from browser.window import MainWindow

from logger import logger
from config import web_greeter_config
from bindings.screensaver import screensaver

# pylint: disable-next=unused-import
# Do not ever remove this import
import resources

# Typing Helpers
BridgeObjects = Tuple["BridgeObject"]
Url = TypeVar("Url", str, QUrl)

os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"

WINDOW_STATES = {
    'NORMAL': Qt.WindowNoState,
    'MINIMIZED': Qt.WindowMinimized,
    'MAXIMIZED': Qt.WindowMaximized,
    'FULLSCREEN': Qt.WindowFullScreen,
}  # type: Dict[str, Qt.WindowState]

DISABLED_SETTINGS = [
    'PluginsEnabled',  # Qt 5.6+
]

ENABLED_SETTINGS = [
    'FocusOnNavigationEnabled',      # Qt 5.8+
    'FullScreenSupportEnabled',      # Qt 5.6+
    'LocalContentCanAccessFileUrls',
    'ScreenCaptureEnabled',          # Qt 5.7+
    'ScrollAnimatorEnabled',
    'FocusOnNavigationEnabled',      # Qt 5.11+
]

def get_default_cursor():
    """Gets the default cursor theme"""
    default_theme = "/usr/local/share/icons/default/index.theme"
    cursor_theme = ""
    matched = None
    try:
        with open(default_theme, "r", encoding = "utf-8") as file:
            matched = re.search(r"Inherits=.*", file.read())
    except IOError:
        return ""
    if not matched:
        logger.error("Default cursor couldn't be get")
        return ""
    cursor_theme = matched.group().replace("Inherits=", "")
    return cursor_theme

class Application:
    """Main application"""
    app: QApplication
    desktop: QDesktopWidget
    window: QMainWindow
    states = WINDOW_STATES
    greeter: Greeter
    greeter_config: Config
    theme_utils: ThemeUtils
    bridge_objects: Tuple[Greeter, Config, ThemeUtils]

    def __init__(self):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.desktop = self.app.desktop()

        self.window.setAttribute(Qt.WA_DeleteOnClose)
        self.window.setWindowTitle("Web Greeter")

        self.window.setWindowFlags(
            self.window.windowFlags() | Qt.MaximizeUsingFullscreenGeometryHint
        )

        if web_greeter_config["app"]["frame"]:
            self._init_menu_bar()
        else:
            self.window.setWindowFlags(
                self.window.windowFlags() | Qt.FramelessWindowHint
            )

        screen_size = self.desktop.availableGeometry().size()

        self.window.setBaseSize(screen_size)
        self.window.resize(screen_size)

        state = self.states['NORMAL']
        if web_greeter_config["app"]["fullscreen"]:
            state = self.states["FULLSCREEN"]

        try:
            self.window.windowHandle().setWindowState(state)
        except (AttributeError, TypeError):
            self.window.setWindowState(state)

        self.window.setCursor(Qt.ArrowCursor)

        timeout = web_greeter_config["config"]["greeter"]["screensaver_timeout"]
        screensaver.set_screensaver(timeout or 300)

        cursor_theme = web_greeter_config["config"]["greeter"]["icon_theme"]
        if cursor_theme is not None:
            os.environ["XCURSOR_THEME"] = cursor_theme
        else:
            os.environ["XCURSOR_THEME"] = get_default_cursor()

        self.app.aboutToQuit.connect(self._before_exit)

    @classmethod
    def _before_exit(cls):
        """Runs before exit"""
        screensaver.reset_screensaver()

    def show(self):
        """Show window"""
        self.window.show()
        logger.debug("Window is ready")

    def run(self) -> int:
        """Runs the application"""
        logger.debug("Web Greeter started")
        return self.app.exec_()

    def _init_menu_bar(self):
        exit_action = QAction(QIcon('exit.png'), '&Exit', self.window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(qApp.quit)

        menu_bar = self.window.menuBar()

        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu('&Edit')
        edit_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu('&View')
        view_menu.addAction(exit_action)

        about_menu = menu_bar.addMenu('&About')
        about_menu.addAction(exit_action)

class NoneLayout(QLayout):
    """Layout that shows nothing"""
    @classmethod
    def count(cls) -> int:
        # pylint: disable=missing-function-docstring
        return 0

    @classmethod
    def sizeHint(cls) -> QSize:
        # pylint: disable=invalid-name,missing-function-docstring
        size = QSize(0, 0)
        return size

    @classmethod
    def minimumSizeHint(cls) -> QSize:
        # pylint: disable=invalid-name,missing-function-docstring
        size = QSize(0, 0)
        return size


class Browser(Application):
    # pylint: disable=too-many-instance-attributes
    """The main browser"""
    url_scheme: QWebEngineUrlScheme
    bridge_initialized: bool
    dev_view: QWebEngineView
    dev_page: WebPage
    qdock: QDockWidget

    def __init__(self):
        super().__init__()
        self.init()
        # self.load()

    def init(self):
        """Initialize browser"""
        logger.debug("Initializing Browser Window")

        if web_greeter_config["config"]["greeter"]["debug_mode"]:
            os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '12345'

        url_scheme = "web-greeter"
        self.url_scheme = QWebEngineUrlScheme(url_scheme.encode())
        self.url_scheme.setDefaultPort(QWebEngineUrlScheme.PortUnspecified)
        self.url_scheme.setFlags(QWebEngineUrlScheme.SecureScheme or
                                 QWebEngineUrlScheme.LocalScheme or
                                 QWebEngineUrlScheme.LocalAccessAllowed)
        QWebEngineUrlScheme.registerScheme(self.url_scheme)

        self.profile = QWebEngineProfile.defaultProfile()
        self.interceptor = QtUrlRequestInterceptor(url_scheme)
        self.url_scheme_handler = QtUrlSchemeHandler()

        self.view = QWebEngineView(parent=self.window)
        self.page = WebPage()
        self.view.setPage(self.page)

        self.channel = QWebChannel(self.page)
        self.bridge_initialized = False

        self.profile.installUrlSchemeHandler(url_scheme.encode(), self.url_scheme_handler)

        self._initialize_page()

        if web_greeter_config["config"]["greeter"]["debug_mode"]:
            self._initialize_devtools()
        else:
            self.view.setContextMenuPolicy(Qt.PreventContextMenu)

        if web_greeter_config["config"]["greeter"]["secure_mode"]:
            if hasattr(QWebEngineProfile, "setUrlRequestInterceptor"):
                self.profile.setUrlRequestInterceptor(self.interceptor)
            else: # Older Qt5 versions
                self.profile.setRequestInterceptor(self.interceptor)

        self.page.setBackgroundColor(QColor(0, 0, 0))
        self.window.setStyleSheet("""QMainWindow, QWebEngineView {
	                                background: #000000;
                                 }""")

        self.window.setCentralWidget(self.view)

        logger.debug("Browser Window created")

    def load(self):
        """Load theme and initialize bridge"""
        self.load_theme()

        self.bridge_objects = (self.greeter, self.greeter_config, self.theme_utils)
        self.initialize_bridge_objects()
        self.load_script(':/_greeter/js/bundle.js', 'Web Greeter Bundle')

    def _initialize_devtools(self):
        self.dev_view = QWebEngineView(parent=self.window)
        self.dev_page = QWebEnginePage()
        self.dev_view.setPage(self.dev_page)
        self.page.setDevToolsPage(self.dev_page)

        self.qdock = QDockWidget()
        self.qdock.setWidget(self.dev_view)
        titlebar = QWidget(self.qdock)
        layout = NoneLayout()
        titlebar.setLayout(layout)
        self.qdock.setTitleBarWidget(titlebar)

        self.window.addDockWidget(Qt.RightDockWidgetArea, self.qdock)
        self.qdock.hide()
        logger.debug("DevTools initialized")

    def toggle_devtools(self):
        """Toggle devtools"""
        if not web_greeter_config["config"]["greeter"]["debug_mode"]:
            return
        win_size = self.window.size()
        # dev_size = self.qdock.size()

        self.qdock.resize(int(win_size.width() / 2), int(win_size.height()))

        if self.qdock.isVisible():
            self.qdock.hide()
            self.view.setFocus()
        else:
            self.qdock.show()
            self.dev_view.setFocus()

    def _initialize_page(self):
        page_settings = self.page.settings().globalSettings()

        if not web_greeter_config["config"]["greeter"]["secure_mode"]:
            ENABLED_SETTINGS.append('LocalContentCanAccessRemoteUrls')
        else:
            DISABLED_SETTINGS.append('LocalContentCanAccessRemoteUrls')

        for setting in DISABLED_SETTINGS:
            try:
                page_settings.setAttribute(getattr(QWebEngineSettings, setting), False)
            except AttributeError:
                pass

        for setting in ENABLED_SETTINGS:
            try:
                page_settings.setAttribute(getattr(QWebEngineSettings, setting), True)
            except AttributeError:
                pass

        self.page.setView(self.view)

    def load_theme(self):
        """Load theme"""
        theme = web_greeter_config["config"]["greeter"]["theme"]
        dir_t = "/usr/local/share/web-greeter/themes/"
        path_to_theme = os.path.join(dir_t, theme, "index.html")
        def_theme = "gruvbox"

        if theme.startswith("/"):
            path_to_theme = theme
        elif theme.__contains__(".") or theme.__contains__("/"):
            path_to_theme = os.path.join(os.getcwd(), theme)
            path_to_theme = os.path.realpath(path_to_theme)

        if not path_to_theme.endswith(".html"):
            path_to_theme = os.path.join(path_to_theme, "index.html")

        if not os.path.exists(path_to_theme):
            print("Path does not exists", path_to_theme)
            path_to_theme = os.path.join(dir_t, def_theme, "index.html")

        web_greeter_config["config"]["greeter"]["theme"] = path_to_theme

        url = QUrl(f"web-greeter://app/{path_to_theme}")
        self.page.load(url)

        logger.debug("Theme loaded")

    @staticmethod
    def _create_webengine_script(path: Url, name: str) -> QWebEngineScript:
        script = QWebEngineScript()
        script_file = QFile(path)

        # print(script_file, path)

        if script_file.open(QFile.ReadOnly):
            script_string = str(script_file.readAll(), 'utf-8')

            script.setInjectionPoint(QWebEngineScript.DocumentCreation)
            script.setName(name)
            script.setWorldId(QWebEngineScript.MainWorld)
            script.setSourceCode(script_string)
            # print(script_string)

        return script

    def _get_channel_api_script(self) -> QWebEngineScript:
        return self._create_webengine_script(':/qtwebchannel/qwebchannel.js', 'QWebChannel API')

    def _init_bridge_channel(self) -> None:
        self.page.setWebChannel(self.channel)
        self.bridge_initialized = True

    def initialize_bridge_objects(self) -> None:
        """Initialize bridge objects :D"""
        if not self.bridge_initialized:
            self._init_bridge_channel()
        registered_objects = self.channel.registeredObjects()

        for obj in self.bridge_objects:
            if obj not in registered_objects:
                # pylint: disable=protected-access
                self.channel.registerObject(obj._name, obj)
                # print("Registered", obj._name)

    def load_script(self, path: Url, name: str):
        """Loads a script in page"""
        qt_api = self._get_channel_api_script()
        qt_api_source = qt_api.sourceCode()
        script = self._create_webengine_script(path, name)
        script.setSourceCode(qt_api_source + "\n" + script.sourceCode())
        self.page.scripts().insert(script)
