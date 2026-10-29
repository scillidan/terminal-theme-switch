#!/bin/sh
set -eu

name=terminal-theme-switch
data="${XDG_DATA_HOME:-$HOME/.local/share}/$name"
bin="${XDG_BIN_HOME:-$HOME/.local/bin}"
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

rm -rf "$data"
mkdir -p "$data" "$bin"
cp "$src/terminal-theme-switch.py" "$data/"
cp -R "$src/integrations" "$data/"
cp -R "$src/bin" "$data/"
chmod +x "$data/bin/terminal-theme-switch"
ln -sfn "$data/bin/terminal-theme-switch" "$bin/$name"

"$bin/$name" path
