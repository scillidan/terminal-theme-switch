#!/bin/sh
set -eu

name=terminal-theme-switch
data="${XDG_DATA_HOME:-$HOME/.local/share}/$name"
bin="${XDG_BIN_HOME:-$HOME/.local/bin}"

for link in "$bin"/*; do
	[ -L "$link" ] || continue
	target=$(readlink "$link") || continue
	case $target in
	"$data"/*) rm -f "$link" ;;
	esac
done

rm -rf "$data"
