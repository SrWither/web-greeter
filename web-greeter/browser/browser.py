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

from bridge.devtools import DevTools
import os
from typing import (
    Dict,
    Tuple,
    TypeVar,
)

# 3rd-Party Libs
from PyQt5.QtCore import QUrl, Qt, QCoreApplication, QFile
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QMainWindow
from PyQt5.QtWebEngineCore import QWebEngineUrlScheme
from PyQt5.QtWebEngineWidgets import QWebEngineScript, QWebEngineProfile, QWebEngineSettings, QWebEngineView
from PyQt5.QtGui import QColor
from PyQt5.QtWebChannel import QWebChannel

from browser.error_prompt import WebPage, errorPrompt
from browser.url_scheme import QtUrlSchemeHandler
from browser.interceptor import QtUrlRequestInterceptor

from logger import logger
from config import web_greeter_config
from bridge import Greeter, Config, ThemeUtils
import resources

# Typing Helpers
BridgeObjects = Tuple['BridgeObject']
Url = TypeVar('Url', str, QUrl)

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

class Application:
    app: QApplication
    desktop: QDesktopWidget
    window: QMainWindow
    states = WINDOW_STATES

    def __init__(self):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

        self.app = QApplication([])
        self.window = QMainWindow()
        self.desktop = self.app.desktop()

        self.window.setAttribute(Qt.WA_DeleteOnClose)
        self.window.setWindowTitle("Web Greeter")

        self.window.setWindowFlags(self.window.windowFlags() | Qt.FramelessWindowHint)

        self.window.setWindowFlags(
            self.window.windowFlags() | Qt.MaximizeUsingFullscreenGeometryHint
        )

        state = self.states['NORMAL']
        try:
            self.window.windowHandle().setWindowState(state)
        except Exception:
            self.window.setWindowState(state)

        self.window.setCursor(Qt.ArrowCursor)

        self.app.aboutToQuit.connect(self._before_exit)

    def _before_exit(self):
        pass

    def show(self):
        self.window.show()
        logger.debug("Window is ready")

    def run(self) -> int:
        logger.debug("Web Greeter started")
        return self.app.exec_()


class Browser(Application):
    url_scheme: QWebEngineUrlScheme

    def __init__(self):
        super().__init__()
        self.init()
        self.load()

    def init(self):
        logger.debug("Initializing Browser Window")
        web_greeter_config["config"]["greeter"]["debug_mode"] = True

        if web_greeter_config["config"]["greeter"]["debug_mode"]:
            os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '12345'

        url_scheme = "web-greeter"
        self.url_scheme = QWebEngineUrlScheme(url_scheme.encode())
        self.url_scheme.setDefaultPort(QWebEngineUrlScheme.SpecialPort.PortUnspecified)
        self.url_scheme.setFlags(QWebEngineUrlScheme.Flag.SecureScheme or
                                 QWebEngineUrlScheme.Flag.LocalScheme or
                                 QWebEngineUrlScheme.Flag.LocalAccessAllowed)
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
            self.devtools = DevTools()

        if web_greeter_config["config"]["greeter"]["secure_mode"]:
            self.profile.setUrlRequestInterceptor(self.interceptor)

        self.page.setBackgroundColor(QColor(0, 0, 0))

        self.view.show()
        self.window.setCentralWidget(self.view)

        logger.debug("Browser Window created")

        self.show()

    def load(self):
        self.greeter = Greeter()
        self.greeter_config = Config()
        self.theme_utils = ThemeUtils(self.greeter)

        self.bridge_objects = (self.greeter, self.greeter_config, self.theme_utils)
        self.initialize_bridge_objects()
        self.load_script(':/_greeter/js/bundle.js', 'Web Greeter Bundle')
        self.load_theme()

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
        theme = web_greeter_config["config"]["greeter"]["theme"]
        dir = "/usr/share/web-greeter/themes/"
        path_to_theme = os.path.join(dir, theme, "index.html")
        def_theme = "gruvbox"

        if (theme.startswith("/")): path_to_theme = theme
        elif (theme.__contains__(".") or theme.__contains__("/")):
            path_to_theme = os.path.join(os.getcwd(), theme)

        if (not path_to_theme.endswith(".html")):
            path_to_theme = os.path.join(path_to_theme, "index.html")

        if (not os.path.exists(path_to_theme)):
            print("Path does not exists")
            path_to_theme = os.path.join(dir, def_theme, "index.html")

        url = QUrl("web-greeter://app/{0}".format(path_to_theme))
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
        self.page.scripts().insert(self._get_channel_api_script())
        self.bridge_initialized = True

    def initialize_bridge_objects(self) -> None:
        if not self.bridge_initialized:
            self._init_bridge_channel()
        registered_objects = self.channel.registeredObjects()

        for obj in self.bridge_objects:
            if obj not in registered_objects:
                self.channel.registerObject(obj._name, obj)
                # print("Registered", obj._name)

    def load_script(self, path: Url, name: str):
        script = self._create_webengine_script(path, name)
        self.page.scripts().insert(script)

