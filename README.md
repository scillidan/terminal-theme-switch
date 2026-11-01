# terminal-theme-switch

Switch the shared terminal theme between system, dark, and light across WezTerm,
Alacritty, Zellij, Neovim, OpenCode, and Yazi.

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

The installer puts `terminal-theme-switch`, `opencode-theme`, `yazi-theme`, and
`alacritty-theme` on `PATH`. Keep `terminal-theme-switch` on `PATH` when using
any integration.

## Usage

```sh
terminal-theme-switch          # print the current mode and appearance
terminal-theme-switch cycle    # system -> dark -> light -> system
terminal-theme-switch dark
terminal-theme-switch light
terminal-theme-switch system
terminal-theme-switch path     # print the plugin directory
terminal-theme-switch yazi     # print a YAZI_CONFIG_HOME overlay for this appearance
terminal-theme-switch alacritty # print the stable Alacritty theme import
alacritty-theme                # launch Alacritty with the current theme
```

State file: `%LOCALAPPDATA%\terminal-theme-switch\state` on Windows,
`$XDG_STATE_HOME/terminal-theme-switch/state` elsewhere. The previous
`terminal-theme` directory is still read once as a fallback so an existing saved
mode is preserved.

## Application integrations

### Alacritty

`terminal-theme-switch alacritty` writes the current WezTerm-compatible palette
to a stable runtime file and prints its path:

- Windows: `%LOCALAPPDATA%\terminal-theme-switch\alacritty.toml`
- Linux: `$XDG_STATE_HOME/terminal-theme-switch/alacritty.toml`, or
  `~/.local/state/terminal-theme-switch/alacritty.toml`

Import that file from Alacritty without adding a second main config. `alacritty-theme`
syncs it and passes it through `--option=general.import=[...]`. Personal wrappers in
`Share/scripts/win/alacritty.cmd` and `Share/scripts/arch/alacritty.sh` add the
platform config, working directory, and shell. Every `dark`, `light`, `system`, `cycle`,
or `refresh` command updates the same file so Alacritty's `live_config_reload` can
follow changes.

The source palettes live in `~/Share/dotfiles/.config/alacritty/themes`:

- `builtin_dark.toml`: WezTerm `Builtin Dark`
- `one_light.toml`: WezTerm `One Light (Gogh)`

Both files are generated from the installed WezTerm's `wezterm.color.get_builtin_schemes()`
API, so the normal and bright ANSI colors, foreground, background, cursor, and selection
colors match WezTerm. Regenerate them with
`~/Share/dotfiles/.config/alacritty/themes/export-from-wezterm.lua` if WezTerm's builtin
definitions change.

### Bash, OpenCode, and Yazi

The installed launchers replace the `opencode-theme()` and `yazi-theme()`
functions previously added to `~/.config/bash/functions.bash`; no shell
function or other manual Bash configuration is needed. Start the applications
with:

```sh
opencode-theme
yazi-theme
```

Use these names instead of `opencode` and `yazi` when the applications should
follow the shared theme at launch. Existing `OPENCODE_CLI_CONFIG_CONTENT` and
`YAZI_CONFIG_HOME` values take precedence and are left unchanged.

`yazi-theme` requires the normal Yazi `theme.toml` to contain both `dark` and
`light` entries in its `[flavor]` table. On Windows this file is normally
`%APPDATA%\yazi\config\theme.toml`; on Linux it is
`$XDG_CONFIG_HOME/yazi/theme.toml` or `~/.config/yazi/theme.toml`.

### Neovim

Install the `vanta` and `lauds` colorschemes, then create
`~/.config/nvim/lua/config/theme.lua` with this loader:

```lua
local M = {}

local function plugin_path()
  local ok, result = pcall(function()
    return vim.system({ "terminal-theme-switch", "path" }, { text = true }):wait()
  end)
  if ok and result.code == 0 then
    return vim.trim(result.stdout)
  end
end

local integration
local path = plugin_path()
if path and path ~= "" then
  local ok, mod = pcall(dofile, path .. "/integrations/nvim.lua")
  if ok then
    integration = mod
  else
    vim.notify("terminal-theme-switch: " .. tostring(mod), vim.log.levels.ERROR)
  end
end

function M.cycle()
  if integration then
    integration.cycle()
  end
end

function M.setup()
  if integration then
    integration.setup()
  end
end

return M
```

Call `setup()` after the colorschemes have been loaded. For example, in the
colorscheme's lazy.nvim `config` function:

```lua
require("config.theme").setup()
```

To bind the shared cycle command to a key:

```lua
vim.keymap.set("n", "<leader>sth", function()
  require("config.theme").cycle()
end, { desc = "Toggle theme" })
```

The integration applies the current appearance at startup and watches the
state file for changes made by other applications.

### WezTerm

In `~/.config/wezterm/wezterm.lua`, after defining `wezterm` and `config`, load
the integration from the path reported by the CLI:

```lua
local theme
do
  local path_args
  if wezterm.target_triple == "x86_64-pc-windows-msvc" then
    path_args = { "cmd.exe", "/c", "terminal-theme-switch", "path" }
  else
    path_args = { "terminal-theme-switch", "path" }
  end
  local called, ok, out, err = pcall(wezterm.run_child_process, path_args)
  if not called then
    wezterm.log_error("terminal-theme-switch: " .. tostring(ok))
  elseif ok and out and out ~= "" then
    local loaded, chunk, load_err = pcall(loadfile, out:gsub("%s+$", "") .. "/integrations/wezterm.lua")
    if loaded and chunk then
      local ok_chunk, mod = pcall(chunk)
      if ok_chunk then
        theme = mod
      else
        wezterm.log_error("terminal-theme-switch: " .. tostring(mod))
      end
    else
      wezterm.log_error("terminal-theme-switch: " .. tostring(load_err))
    end
  elseif err and err ~= "" then
    wezterm.log_error("terminal-theme-switch: " .. tostring(err))
  end
end
```

After the rest of the config is built, and before `return config`, call:

```lua
if theme then
  local ok, err = pcall(theme.setup, config)
  if not ok then
    wezterm.log_error("terminal-theme-switch: " .. tostring(err))
  end
end
```

This adds `LEADER|SHIFT+C` to cycle the shared theme and synchronizes WezTerm
when its appearance or the shared state changes.

### Zellij

In `~/.config/zellij/config/config.kdl`, choose the dark and light themes used
when `terminal-theme-switch` refreshes Zellij:

```kdl
theme "vesper"
theme_dark "vesper"
theme_light "everforest-light"
```

Replace these theme names with installed Zellij themes as needed. Then paste
the contents of `integrations/zellij.kdl` into the existing `tmux` keybind mode:

```kdl
keybinds {
    tmux {
        bind "T" {
            Run "terminal-theme-switch.cmd" "cycle" {
                floating true
                close_on_exit true
            }
            SwitchToMode "normal";
        }
    }
}
```

Keep any existing `tmux` bindings when merging this block. The `.cmd` command
name is intentional on both Windows and Linux; `install.sh` provides it on
Linux for Zellij's `Run` action.
