#!/usr/bin/env bash
set -euo pipefail

CONFIG="$USERHOME/Share/dotfiles/.config/alacritty/alacritty.toml"

exec alacritty \
	--config-file "$CONFIG" \
	--option "general.import=['terminal-theme-switch alacritty']" \
	--working-directory "$USERHOME/Downloads" \
	"$@" \
	--command "${SHELL:-/bin/bash}" -l
