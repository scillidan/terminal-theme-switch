# terminal-theme-switch

Switch the shared terminal theme between system, dark, and light across WezTerm,
Alacritty, Zellij, Neovim, OpenCode, Yazi, eilmeldung, and (on Windows)
Keypirinha.

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

To remove the installed files and launcher symlinks, run `./uninstall.sh`. The
state file under `$XDG_STATE_HOME` is kept.

The installer puts `terminal-theme-switch`, `opencode-theme`, `yazi-theme`,
`alacritty-theme`, and `eilmeldung-theme` on `PATH`. On Windows the Scoop
package also provides `keypirinha-theme`. Keep `terminal-theme-switch` on `PATH`
when using any integration.

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
terminal-theme-switch eilmeldung # print an eilmeldung config directory for this appearance
terminal-theme-switch keypirinha # apply the theme to a running Keypirinha (Windows)
alacritty-theme                # launch Alacritty with the current theme
eilmeldung-theme               # launch eilmeldung with the current theme
keypirinha-theme               # launch Keypirinha with the current theme (Windows)
```

State file: `%LOCALAPPDATA%\terminal-theme-switch\state` on Windows,
`$XDG_STATE_HOME/terminal-theme-switch/state` elsewhere. The previous
`terminal-theme` directory is still read once as a fallback so an existing saved
mode is preserved.

## Where theme values live

`terminal-theme-switch` stores no palettes and hard-codes no theme names. The
dark and light identifiers stay in each application's own configuration, which
remains the single source of truth:

- Yazi reads `dark`/`light` from `[flavor]` in its `theme.toml`.
- Zellij reads `theme_dark`/`theme_light` from its `config.kdl`.
- OpenCode follows `theme.mode`; it does not need a theme name.
- Neovim and WezTerm receive the two colorscheme names from the user's config
  through `setup({ dark = ..., light = ... })`.
- Alacritty, eilmeldung, and Keypirinha have no native dark/light pair, so they
  use the small sidecar or section shown below in the same config location.

Theme files stay in each application's native theme directory (for example
`~/.config/alacritty/themes` or eilmeldung's `themes` directory). The switcher
only writes generated overlays to its state directory
(`%LOCALAPPDATA%\terminal-theme-switch` on Windows,
`$XDG_STATE_HOME/terminal-theme-switch` elsewhere). This keeps the app as the
authority that validates names, leaves the install directory untouched, and
means removing the switcher leaves every theme intact.

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

The source palettes stay in `~/Share/dotfiles/.config/alacritty/themes`. Pick
the dark and light files in `themes/terminal-theme-switch.toml`:

```toml
dark = "builtin_dark.toml"
light = "one_light.toml"
```

The files in that directory are generated from the installed WezTerm's
`wezterm.color.get_builtin_schemes()` API, so the normal and bright ANSI colors,
foreground, background, cursor, and selection colors match WezTerm. Regenerate
them with `~/Share/dotfiles/.config/alacritty/themes/export-from-wezterm.lua` if
WezTerm's builtin definitions change.

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

### eilmeldung

Start eilmeldung with:

```sh
eilmeldung-theme
```

Pick the Base16 themes in `terminal-theme-switch.toml` next to the real
`config.toml` (for a symlinked config, this is the symlink target's directory):

```toml
dark = "flexoki-dark"
light = "flexoki-light"
```

The launcher builds a config directory under
`%LOCALAPPDATA%\terminal-theme-switch\eilmeldung` (or
`$XDG_STATE_HOME/terminal-theme-switch/eilmeldung`) and starts eilmeldung with
`--config-dir`, so `config.toml` itself is never rewritten. The generated file is
a copy of your config with only the theme line changed; the state directory is
per-user, so any login settings in `config.toml` keep the same ACL as the
original. It is refreshed on every theme change, so a running eilmeldung follows
the switch through its normal config auto-reload. An explicit `--config-dir`
argument takes precedence and is passed through unchanged.

### Keypirinha (Windows)

Declare the pair in `%SCOOP%\apps\keypirinha\current\portable\Profile\User\keypirinha.ini`:

```ini
[terminal-theme-switch]
dark = Vanta
light = VantaNegate
```

Every `dark`, `light`, `system`, `cycle`, or `refresh` command rewrites only the
`theme =` value in `[gui]`. Keypirinha detects the change and applies it at
runtime; there is no restart. `keypirinha-theme` applies the current theme and
starts Keypirinha when it is not already running.

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

function M.setup(opts)
  if integration then
    integration.setup(opts)
  end
end

return M
```

Call `setup({ dark = ..., light = ... })` after the colorschemes have been
loaded, naming the colorschemes you already use. For example, in the
colorscheme's lazy.nvim `config` function:

```lua
require("config.theme").setup({ dark = "vanta", light = "lauds" })
```

To bind the shared cycle command to a key:

```lua
vim.keymap.set("n", "<leader>sth", function()
  require("config.theme").cycle()
end, { desc = "Toggle theme" })
```

The integration applies the current appearance at startup and watches the
state file for changes made by other applications. Passing both colorscheme
names is required; without them `setup` reports an error and does nothing.

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

After the rest of the config is built, and before `return config`, call it with
the two schemes you already use:

```lua
if theme then
  local ok, err = pcall(theme.setup, config, {
    dark = "Builtin Dark",
    light = "One Light (Gogh)",
  })
  if not ok then
    wezterm.log_error("terminal-theme-switch: " .. tostring(err))
  end
end
```

This adds `LEADER|SHIFT+C` to cycle the shared theme and synchronizes WezTerm
when its appearance or the shared state changes. Passing both scheme names is
required; without them the integration logs an error and registers nothing.

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
