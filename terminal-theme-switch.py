#!/usr/bin/env python3
"""Shared dark/light/system preference for terminal applications."""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

MODES = ("system", "dark", "light")
CYCLE = {"system": "dark", "dark": "light", "light": "system"}

if os.name == "nt":
    state_root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
else:
    state_root = Path(
        os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
    )

STATE_DIR = state_root / "terminal-theme-switch"
STATE_FILE = STATE_DIR / "state"
LEGACY_STATE_FILE = state_root / "terminal-theme" / "state"
INTEGRATIONS_DIR = Path(__file__).parent / "integrations"
USERHOME = Path(os.environ.get("USERHOME") or Path.home())
ALACRITTY_THEMES_DIR = (
    USERHOME / "Share" / "dotfiles" / ".config" / "alacritty" / "themes"
)
ALACRITTY_SWITCH_FILE = ALACRITTY_THEMES_DIR / "terminal-theme-switch.toml"
KEYPIRINHA_SECTION = "[terminal-theme-switch]"
EILMELDUNG_SWITCH_FILE = "terminal-theme-switch.toml"


def _read_theme_pair(path):
    """Read the dark/light theme names from a tool-owned sidecar file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, None
    pair = {}
    for line in text.splitlines():
        match = re.match(r'\s*(dark|light)\s*=\s*"?([^"]*)"?\s*$', line)
        if match:
            pair[match.group(1)] = match.group(2).strip()
    return pair.get("dark"), pair.get("light")


def _read_mode(path):
    try:
        mode = path.read_text(encoding="utf-8").splitlines()[0].strip()
        return mode if mode in MODES else "system"
    except (OSError, IndexError):
        return None


def saved_mode():
    for path in (STATE_FILE, LEGACY_STATE_FILE):
        mode = _read_mode(path)
        if mode is not None:
            return mode
    return "system"


def system_appearance():
    if os.name == "nt":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            with key:
                return (
                    "light"
                    if winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                    else "dark"
                )
        except OSError:
            return "dark"

    try:
        result = subprocess.run(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.freedesktop.portal.Desktop",
                "--object-path",
                "/org/freedesktop/portal/desktop",
                "--method",
                "org.freedesktop.portal.Settings.ReadOne",
                "org.freedesktop.appearance",
                "color-scheme",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        match = re.search(r"uint32\s+([12])", result.stdout)
        if match:
            return "dark" if match.group(1) == "1" else "light"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "dark"


def current_appearance():
    mode = saved_mode()
    return system_appearance() if mode == "system" else mode


def _replace_with_retry(temporary, target):
    # Windows readers can briefly hold the destination without delete sharing.
    for attempt in range(100):
        try:
            os.replace(temporary, target)
            return
        except PermissionError:
            if os.name != "nt" or attempt == 99:
                temporary.unlink(missing_ok=True)
                raise
            time.sleep(0.01)


def _write_text(path, text):
    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(text)


def alacritty_theme_source(appearance):
    if appearance not in ("dark", "light"):
        raise ValueError(f"unknown appearance: {appearance}")
    dark, light = _read_theme_pair(ALACRITTY_SWITCH_FILE)
    name = light if appearance == "light" else dark
    if not name:
        raise SystemExit(f"alacritty: set dark/light in {ALACRITTY_SWITCH_FILE}")
    return ALACRITTY_THEMES_DIR / name


def sync_alacritty(appearance):
    source = alacritty_theme_source(appearance)
    if not source.is_file():
        raise SystemExit(f"alacritty: cannot find theme source {source}")
    target = STATE_DIR / "alacritty.toml"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    shutil.copyfile(source, temporary)
    _replace_with_retry(temporary, target)
    return target


def eilmeldung_config_dir():
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "eilmeldung"
    home = Path.home() / ".config" / "eilmeldung"
    if (home / "config.toml").is_file():
        return home
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "christo-auer" / "eilmeldung" / "config"
    return home


def _theme_toml(text, name):
    """Set [theme] base16_theme while preserving every other line."""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    header = None
    end = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if header is not None:
                end = i
                break
            if stripped == "[theme]":
                header = i
    if header is None:
        lines.extend(["", "[theme]", f'base16_theme = "{name}"'])
    else:
        for i in range(header + 1, end):
            if re.match(r"\s*base16_theme\s*=", lines[i]):
                indent = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
                lines[i] = f'{indent}base16_theme = "{name}"'
                break
        else:
            lines.insert(header + 1, f'base16_theme = "{name}"')
    return newline.join(lines).rstrip() + newline


def eilmeldung_config_home(appearance=None):
    config_dir = eilmeldung_config_dir()
    source = config_dir / "config.toml"
    if not source.is_file():
        raise SystemExit(f"eilmeldung: cannot find {source}")

    if appearance not in ("dark", "light"):
        appearance = current_appearance()
    # Follow the dotfiles symlink so the sidecar stays next to the real file.
    real_dir = Path(os.path.realpath(source)).parent
    sidecar = real_dir / EILMELDUNG_SWITCH_FILE
    dark, light = _read_theme_pair(sidecar)
    name = light if appearance == "light" else dark
    if not name:
        raise SystemExit(f"eilmeldung: set dark/light in {sidecar}")

    overlay = STATE_DIR / "eilmeldung"
    overlay.mkdir(parents=True, exist_ok=True)
    target = overlay / "config.toml"
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    _write_text(temporary, _theme_toml(source.read_text(encoding="utf-8"), name))
    _replace_with_retry(temporary, target)
    themes = real_dir / "themes"
    if themes.is_dir():
        _replace_dir(overlay / "themes", themes)
    return overlay


def sync_eilmeldung(appearance):
    if not (STATE_DIR / "eilmeldung" / "config.toml").is_file():
        return None
    try:
        return eilmeldung_config_home(appearance)
    except (OSError, SystemExit):
        return None


def keypirinha_config_file():
    if os.name != "nt":
        return None
    base = os.environ.get("SCOOP") or (Path.home() / "scoop")
    return (
        Path(base)
        / "apps"
        / "keypirinha"
        / "current"
        / "portable"
        / "Profile"
        / "User"
        / "keypirinha.ini"
    )


def _keypirinha_theme_pair(text):
    dark = light = None
    section = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped
            continue
        if section != KEYPIRINHA_SECTION:
            continue
        match = re.match(r'(dark|light)\s*=\s*"?([^"]*)"?\s*$', stripped)
        if match:
            if match.group(1) == "dark":
                dark = match.group(2).strip()
            else:
                light = match.group(2).strip()
    return dark, light


def _keypirinha_set_theme(text, value):
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    gui = None
    end = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if gui is not None:
                end = i
                break
            if stripped.lower() == "[gui]":
                gui = i
    if gui is None:
        lines.extend(["", "[gui]", f"theme = {value}"])
    else:
        for i in range(gui + 1, end):
            if re.match(r"\s*theme\s*=", lines[i]):
                lines[i] = f"theme = {value}"
                break
        else:
            lines.insert(gui + 1, f"theme = {value}")
    return newline.join(lines).rstrip() + newline


def sync_keypirinha(appearance):
    path = keypirinha_config_file()
    if path is None or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    dark, light = _keypirinha_theme_pair(text)
    value = light if appearance == "light" else dark
    if not value:
        return None
    updated = _keypirinha_set_theme(text, value)
    if updated == text:
        return path
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    _write_text(temporary, updated)
    _replace_with_retry(temporary, path)
    return path


def yazi_config_dir():
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "yazi" / "config" if os.name == "nt" else base / "yazi"


def _flavor_names(theme_text):
    light = dark = None
    in_flavor = False
    for line in theme_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_flavor = stripped == "[flavor]"
            continue
        if not in_flavor:
            continue
        match = re.match(r'(light|dark)\s*=\s*"([^"]+)"', stripped)
        if match:
            if match.group(1) == "light":
                light = match.group(2)
            else:
                dark = match.group(2)
    return light, dark


def _flavor_theme(theme_text, flavor):
    lines = []
    in_flavor = False
    replaced = False
    for line in theme_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_flavor = False
            if stripped == "[flavor]":
                lines.extend(
                    ["[flavor]", f'dark = "{flavor}"', f'light = "{flavor}"', ""]
                )
                replaced = True
                in_flavor = True
                continue
        if in_flavor:
            continue
        lines.append(line)
    if not replaced:
        lines.extend(["", "[flavor]", f'dark = "{flavor}"', f'light = "{flavor}"'])
    return "\n".join(lines).strip() + "\n"


def _replace_dir(link, target):
    if os.path.lexists(link):
        try:
            if link.resolve() == target.resolve():
                return
        except OSError:
            pass
        if link.is_dir() and not link.is_symlink():
            os.rmdir(link)
        else:
            link.unlink()
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            check=True,
        )
    else:
        link.symlink_to(target, target_is_directory=True)


def yazi_config_home(appearance=None):
    config = yazi_config_dir()
    theme_file = config / "theme.toml"
    try:
        theme_text = theme_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"yazi: cannot read {theme_file}: {exc}")

    if appearance not in ("dark", "light"):
        appearance = current_appearance()
    light, dark = _flavor_names(theme_text)
    flavor = light if appearance == "light" else dark
    if not flavor:
        flavor = dark or light
    if not flavor:
        raise SystemExit("yazi: no [flavor] light/dark in theme.toml")

    overlay = STATE_DIR / "yazi" / appearance
    overlay.mkdir(parents=True, exist_ok=True)
    for name in ("plugins", "flavors"):
        source = config / name
        if source.is_dir():
            _replace_dir(overlay / name, source)
    for name in ("yazi.toml", "keymap.toml", "init.lua", "package.toml"):
        source = config / name
        if source.is_file():
            shutil.copy2(source, overlay / name)
    (overlay / "theme.toml").write_text(
        _flavor_theme(theme_text, flavor), encoding="utf-8"
    )
    return overlay


def sync_zellij(appearance):
    """Also supports terminals without CSI 2031 appearance notifications."""
    try:
        sessions = subprocess.run(
            ["zellij", "list-sessions", "--short"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if sessions.returncode:
            return
        for session in sessions.stdout.splitlines():
            subprocess.run(
                ["zellij", "--session", session, "action", f"set-{appearance}-theme"],
                capture_output=True,
                timeout=2,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired):
        pass


def refresh(mode):
    appearance = system_appearance() if mode == "system" else mode
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_name(f".{STATE_FILE.name}.{os.getpid()}.tmp")
    temporary.write_text(f"{mode}\n{appearance}\n", encoding="utf-8")
    _replace_with_retry(temporary, STATE_FILE)
    sync_alacritty(appearance)
    sync_eilmeldung(appearance)
    sync_keypirinha(appearance)
    sync_zellij(appearance)
    return appearance


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "get"
    if command not in (
        *MODES,
        "get",
        "refresh",
        "cycle",
        "path",
        "yazi",
        "alacritty",
        "eilmeldung",
        "keypirinha",
    ):
        raise SystemExit(
            f"usage: {Path(sys.argv[0]).name} "
            "[get|refresh|cycle|system|dark|light|path|yazi|alacritty|"
            "eilmeldung|keypirinha]"
        )

    if command == "path":
        # Do not resolve symlinks: on Windows this keeps Scoop's "current"
        # junction stable across updates.
        print(Path(os.path.abspath(__file__)).parent)
        return

    if command == "yazi":
        print(yazi_config_home())
        return

    if command == "alacritty":
        print(sync_alacritty(current_appearance()))
        return

    if command == "eilmeldung":
        print(eilmeldung_config_home())
        return

    if command == "keypirinha":
        path = sync_keypirinha(current_appearance())
        if path:
            print(path)
        return

    mode = saved_mode()
    if command == "cycle":
        mode = CYCLE[mode]
    elif command in MODES:
        mode = command

    if command in ("get",):
        appearance = system_appearance() if mode == "system" else mode
    else:
        appearance = refresh(mode)
    print(mode, appearance)


if __name__ == "__main__":
    main()
