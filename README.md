# Web Greeter for LightDM on FreeBSD

A modern, visually appealing greeter for LightDM, that allows to create web based themes with HTML, CSS and JavaScript.

This is a try to update the [Antergos web-greeter](https://github.com/Antergos/web-greeter), following what they left.

As this is based on the [master release](https://github.com/Antergos/web-greeter/tree/master), which does some API changes, actual themes would need to do changes to work correctly.

Checkout [nody-greeter][nody-greeter], a greeter made in **Node.js** with **Electron**! (Actually, faster than Web Greeter)

## [See Live Demo][live_demo]

Gruvbox and Dracula themes!

## Features

-   Create themes with HTML, CSS and JavaScript!
-   Should work everywhere.
-   JavaScript error handling, allowing to load the default theme.
-   Themes could be simple, or very complex.
-   Battery and brightness control.
-   Tab completion for zsh and bash.

## Available distro packages

### Arch

-   AUR: https://aur.archlinux.org/packages/web-greeter/

```sh
yay -S web-greeter
```

### Ubuntu

Download from the [latest release](https://github.com/JezerM/web-greeter/releases/latest) and
install with apt.

```sh
apt install ./web-greeter-VER.deb
```

### FreeBSD
clone the repository
and run the following command as superuser:
```
make install
```

## Dependencies

|       FreeBSD                    | arch                   | ubuntu                    | fedora                | openSUSE               | debian             |
| ------------------------- | ---------------------- | ------------------------- | --------------------- | ---------------------- | ------------------------- |
| **lightdm**               | lightdm                | liblightdm-gobject-1-dev  | lightdm-gobject-devel | liblightdm-gobject-1-0 | liblightdm-gobject-dev    |
| **py38-gobject3**         | python-gobject         | python3-gi                | pygobject3            | python3-gobject        | python3-gi                |
| **py38-qt5**              | python-pyqt5           | python3-pyqt5             | python3-qt5           | python3-qt5            | python3-pyqt5             |
| **py38-qt5-webengine**    | python-pyqt5-webengine | python3-pyqt5.qtwebengine | python3-qt5-webengine | python3-qtwebengine    | python3-pyqt5.qtwebengine |
| **py38-ruamel.yaml**      | python-ruamel-yaml     | python3-ruamel.yaml       | python3-ruamel-yaml   | python3-ruamel-yaml    | python3-ruamel.yaml       |
| **py38-pyinotify**        | python-pyinotify       | python3-pyinotify         | python3-inotify       | python3-inotify        | python3-pyinotify         |
|                           | qt5-webengine          | libqt5webengine5          | qt5-qtwebengine       | libqt5-qtwebengine     | libqt5webengine5          |
|                           | gobject-introspection  | gobject-introspection     | gobject-introspection | gobject-introspection  | gobject-introspection     |
|                           | libxcb                 | libxcb1-dev               | libxcb-devel          | libxcb                 | libxcb1-dev               |
|                           | libx11                 | libx11-dev                | libX11-devel          | libx11                 | libx11-dev                |

> Note: web-greeter does not work in Fedora. See #19

### Build dependencies

-   rsync
-   make (GNU Version)
-   pyrcc5 (Should be installed with above dependencies)
-   base-devel (build-essential)

### PIP

-   PyGObject
-   PyQt5
-   PyQtWebEngine
-   ruamel.yaml
-   pyinotify

PIP dependencies are no longer required as long as common dependencies are satisfied. However, you
can install PIP dependencies with:

```sh
pip install -r requirements.txt
```

> **_NOTE_** If using PIP, be sure to install these dependencies as root. Yet, no recommended.

## Download & Install

```sh
git clone https://github.com/JezerM/web-greeter.git
cd web-greeter
sudo make install
```

This will build **web-greeter** and package all the files to be installed.

See [latest release][releases].

### Uninstall

Use `sudo make uninstall` to uninstall web-greeter, but preserving web-greeter.yml and themes.
Either, use `sudo make uninstall_all` to remove everting related to web-greeter.

## Theme JavaScript API

[Antergos][antergos] documentation is no longer available, although it is accesible through [Web Archive][webarchive]. Current and updated documentation is available at [gh-pages][gh-pages].

You can access the man-pages `man web-greeter` for some documentation and explanation. Also, you can explore the provided [themes](./themes) for real use cases.

Aditionally, you can install the TypeScript types definitions inside your theme with npm:

```sh
npm install nody-greeter-types
```

## Aditional features

### Brightness control

`acpi` is the only tool needed to control the brightness, besides a compatible device. This functionality is based on [acpilight][acpilight] replacement for `xbacklight`.

udev rules are needed to be applied before using it, check [acpilight rules][acpilight_rules]. Then, lightdm will need to be allowed to change backlight values, to do so add lightdm user to **video** group: `sudo usermod -a -G video lightdm`

Enable it inside `/etc/lightdm/web-greeter.yml`

### Battery status

`acpi` and `acpi_listen` are the only tools you need (and a battery). This functionality is based on ["bat" widget][bat_widget] from ["lain" awesome-wm library][lain].

You can enable it inside `/etc/lightdm/web-greeter.yml`

## Debugging

You can run the greeter from within your desktop session if you add the following line to the desktop file for your session located in `/usr/local/xsessions/`: `X-LightDM-Allow-Greeter=true`.

You have to log out and log back in after adding that line. Then you can run the greeter from command line.

Themes can be opened with a debug console if you set `debug_mode` as `true` inside `/etc/lightdm/web-greeter.yml`. Or, you could run the `web-greeter` with the parameter `--debug`. I recommend to use the last one, as it is easier and handy.

```sh
web-greeter --debug
```

Check `web-greeter --help` for more commands.

> **_Note:_** Do not use `lightdm --test-mode` as it is not supported.

## Troubleshooting

Before setting **web-greeter** as your LightDM Greeter, you should make sure it does work also with LightDM:

-   Run **web-greeter** as root with `--no-sandbox` flag ("Unable to determine socket to daemon" and "XLib" related errors are expected)
-   Run `lightdm --test-mode`. Although it's not supported, it could help to debug lightdm.

### LightDM crashes and tries to recover over and over again

LightDM does this when the greeter crashes, so it could mean **web-greeter** was not installed correctly, or some dependencies were updated/removed after a distro update.

### Import errors

If you see something like this: `ImportError: libQt5WebEngineCore.so.5: undefined symbol: _ZNSt12out_of_rangeC1EPKc, version Qt_5`, check out this [StackOverflow response](https://stackoverflow.com/a/68811630).

With some PyQt5 import errors like `ModuleNotFoundError: No module named 'PyQt5.QtWebEngineWidgets'`, check out this [GitHub response](https://github.com/spyder-ide/spyder/issues/8952#issuecomment-499418456).

web-greeter related import errors:

-   `AttributeError: module 'globals' has no attribute 'greeter'` means some exception happened inside the Browser constructor, maybe related to LightDM or PyQt5.
-   `ModuleNotFoundError: No module named 'resources'` could mean `path/to/web-greeter-clone/web-greeter/resources.py` was not compiled with pyrcc5 in the build/install methods.

[antergos]: https://github.com/Antergos "Antergos"
[nody-greeter]: https://github.com/JezerM/nody-greeter "Nody Greeter"
[cx_freeze]: https://github.com/marcelotduarte/cx_Freeze "cx_Freeze"
[acpilight]: https://gitlab.com/wavexx/acpilight/ "acpilight"
[acpilight_rules]: https://gitlab.com/wavexx/acpilight/-/blob/master/90-backlight.rules "udev rules"
[bat_widget]: https://github.com/lcpz/lain/blob/master/widget/bat.lua "Battery widget"
[lain]: https://github.com/lcpz/lain "Lain awesome library"
[webarchive]: https://web.archive.org/web/20190524032923/https://doclets.io/Antergos/web-greeter/stable "Web Archive"
[gh-pages]: https://jezerm.github.io/web-greeter/ "API Documentation"
[live_demo]: https://jezerm.github.io/web-greeter-themes/ "Live Demo"
[releases]: https://github.com/JezerM/web-greeter/releases "Releases"
