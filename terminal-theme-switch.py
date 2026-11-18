#!/usr/bin/env python3
"""Shared dark/light/system preference for terminal applications."""

import os
from pathlib import Path
import re
import subprocess
import sys
import time

MODES = ("system", "dark", "light")
CYCLE = {"system": "dark", "dark": "light", "light": "system"}

if os.name == "nt":
    state_root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
else:
    state_root = Path(
        os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
    )

# Keep the original data directory so integrations that still read the old
# path keep working while they are migrated to this plugin.
STATE_FILE = state_root / "terminal-theme" / "state"


def saved_mode():
    try:
        mode = STATE_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
        return mode if mode in MODES else "system"
    except (OSError, IndexError):
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
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_name(f".{STATE_FILE.name}.{os.getpid()}.tmp")
    temporary.write_text(f"{mode}\n{appearance}\n", encoding="utf-8")
    # Windows readers can briefly hold the destination without delete sharing.
    for attempt in range(100):
        try:
            os.replace(temporary, STATE_FILE)
            break
        except PermissionError:
            if os.name != "nt" or attempt == 99:
                temporary.unlink(missing_ok=True)
                raise
            time.sleep(0.01)
    sync_zellij(appearance)
    return appearance


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "get"
    if command not in (*MODES, "get", "refresh", "cycle", "path"):
        raise SystemExit(
            f"usage: {Path(sys.argv[0]).name} "
            "[get|refresh|cycle|system|dark|light|path]"
        )

    if command == "path":
        print(Path(__file__).resolve().parent)
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
