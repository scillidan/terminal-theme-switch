# terminal-theme-switch

Switch the shared terminal theme between system, dark, and light.

## Install

Windows:

```pwsh
scoop bucket add bash https://github.com/scillidan/scoop-bash
scoop install bash/terminal-theme-switch
```

Linux:

```sh
./install.sh
```

## Usage

```sh
terminal-theme-switch          # print the current mode and appearance
terminal-theme-switch cycle    # system -> dark -> light -> system
terminal-theme-switch dark
terminal-theme-switch light
terminal-theme-switch system
terminal-theme-switch path     # print the plugin directory
terminal-theme-switch yazi     # print a YAZI_CONFIG_HOME overlay for this appearance
```

## Integrations

Use `terminal-theme-switch path` as the plugin directory.

- WezTerm: load `integrations/wezterm.lua` and call `setup(config)` after the
  config is built.
- Neovim: load `integrations/nvim.lua` and call `setup()`.
- Zellij: paste `integrations/zellij.kdl` into the `tmux` mode.
- Yazi: set `YAZI_CONFIG_HOME` to the output of `terminal-theme-switch yazi`.

State file: `%LOCALAPPDATA%\terminal-theme\state` on Windows,
`$XDG_STATE_HOME/terminal-theme/state` elsewhere.
