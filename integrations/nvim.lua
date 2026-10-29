-- Neovim integration for terminal-theme-switch.
local M = {}

local state_root
if vim.fn.has("win32") == 1 then
	state_root = vim.env.LOCALAPPDATA or (vim.env.USERPROFILE .. "/AppData/Local")
else
	state_root = vim.env.XDG_STATE_HOME or (vim.env.HOME .. "/.local/state")
end
local state_file = state_root .. "/terminal-theme/state"
local last_appearance

local function apply(appearance)
	local scheme = appearance == "light" and "lauds" or "vanta"
	if vim.g.colors_name == scheme and vim.o.background == appearance then
		return
	end
	vim.o.background = appearance
	vim.cmd.colorscheme(scheme)
end

local function saved_appearance()
	local ok, lines = pcall(vim.fn.readfile, state_file)
	if not ok then
		return
	end
	local appearance = lines[2]
	if appearance == "dark" or appearance == "light" then
		return appearance
	end
end

local function run(command)
	local result = vim.system({ "terminal-theme-switch", command }, { text = true }):wait()
	if result.code ~= 0 then
		vim.notify("terminal-theme-switch: " .. vim.trim(result.stderr), vim.log.levels.ERROR)
		return
	end
	local appearance = vim.split(vim.trim(result.stdout), " ")[2]
	if appearance == "dark" or appearance == "light" then
		last_appearance = appearance
		apply(appearance)
	end
end

function M.cycle()
	run("cycle")
end

function M.setup()
	run("refresh")
	last_appearance = last_appearance or saved_appearance() or "dark"
	apply(last_appearance)

	local timer = vim.uv.new_timer()
	timer:start(
		1000,
		1000,
		vim.schedule_wrap(function()
			local appearance = saved_appearance()
			if appearance and appearance ~= last_appearance then
				last_appearance = appearance
				apply(appearance)
			end
		end)
	)
end

return M
