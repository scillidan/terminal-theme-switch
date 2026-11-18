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
for launcher in terminal-theme-switch opencode-theme yazi-theme; do
    chmod +x "$data/bin/$launcher"
    ln -sfn "$data/bin/$launcher" "$bin/$launcher"
done

# Zellij's Run action uses the Windows-style name on both platforms.
cat >"$data/$name.cmd" <<EOF
#!/bin/sh
exec python3 "$data/$name.py" "\$@"
EOF
chmod +x "$data/$name.cmd"
ln -sfn "$data/$name.cmd" "$bin/$name.cmd"

"$bin/$name" path
