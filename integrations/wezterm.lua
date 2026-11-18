-- WezTerm integration for terminal-theme-switch.
local wezterm = require("wezterm")

local M = {}

local light_scheme = "One Light (Gogh)"
local dark_scheme = "Builtin Dark"

local state_root
if wezterm.target_triple == "x86_64-pc-windows-msvc" then
	state_root = os.getenv("LOCALAPPDATA") or (os.getenv("USERPROFILE") .. "\\AppData\\Local")
else
	state_root = os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")
end
local state_file = state_root .. "/terminal-theme/state"
local last_published

local function read_theme_state()
	local file = io.open(state_file, "r")
	if not file then
		return "system", nil
	end
	local mode = file:read("l")
	local appearance = file:read("l")
	file:close()
	if mode ~= "dark" and mode ~= "light" then
		mode = "system"
	end
	return mode, appearance
end

local function command_args(command)
	if wezterm.target_triple == "x86_64-pc-windows-msvc" then
		return { "cmd.exe", "/c", "terminal-theme-switch", command }
	end
	return { "terminal-theme-switch", command }
end

local function run(command)
	local called, ok, _, stderr = pcall(wezterm.run_child_process, command_args(command))
	if not called then
		wezterm.log_error("terminal-theme-switch: " .. tostring(ok))
		return false
	end
	if not ok then
		wezterm.log_error("terminal-theme-switch: " .. tostring(stderr))
		return false
	end
	return true
end

local function sync(window)
	local mode, saved_appearance = read_theme_state()
	local appearance = mode
	if mode == "system" then
		appearance = window:get_appearance():find("Dark") and "dark" or "light"
	end
	local scheme = appearance == "light" and light_scheme or dark_scheme
	local overrides = window:get_config_overrides() or {}
	if overrides.color_scheme ~= scheme then
		overrides.color_scheme = scheme
		window:set_config_overrides(overrides)
	end
	local published = mode .. ":" .. appearance
	if saved_appearance ~= appearance and last_published ~= published then
		last_published = published
		run("refresh")
	end
end

local function cycle(window)
	run("cycle")
	sync(window)
end

function M.setup(config)
	config.color_scheme = dark_scheme
	config.keys = config.keys or {}
	table.insert(config.keys, {
		key = "C",
		mods = "LEADER|SHIFT",
		action = wezterm.action_callback(function(window)
			cycle(window)
		end),
	})
	wezterm.on("window-config-reloaded", function(window)
		sync(window)
	end)
	wezterm.on("update-status", function(window)
		sync(window)
	end)
end

return M
