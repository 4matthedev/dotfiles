-- ============================================================
--  NORD HYPRLAND CONFIGURATION
--  Hyprland 0.57.2 · Arch Linux · NVIDIA RTX 3060
-- ============================================================

local mainMod = "SUPER"

-- Set to false if you ever want a completely static desktop.
local animationsEnabled = true

-- Programs
local terminal    = "kitty"
local fileManager = "thunar"
local menu        = "wofi --show drun"
local browser     = "flatpak run app.zen_browser.zen"

-- ==========================================
-- MONITOR
-- ==========================================

hl.monitor({
    output   = "HDMI-A-1",
    mode     = "1920x1080@180",
    position = "auto",
    scale    = 1,
})

-- ==========================================
-- ENVIRONMENT
-- ==========================================

hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Adwaita")

-- Wayland first, with an X11 fallback for stubborn Qt apps.
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")

-- Let Electron apps (VS Code, etc.) use Wayland.
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")

-- ==========================================
-- LOOK AND FEEL
-- ==========================================

hl.config({
    general = {
        gaps_in     = 2,
        gaps_out    = 6,
        border_size = 2,

        col = {
            active_border = {
                colors = { "rgba(88c0d0ee)", "rgba(8fbcbbee)" },
                angle  = 45,
            },
            inactive_border = "rgba(4c566aaa)",
        },

        resize_on_border = false,
        allow_tearing    = false,

        layout = "dwindle",
    },

    decoration = {
        rounding       = 0,
        rounding_power = 2,

        active_opacity     = 1.0,
        inactive_opacity   = 1.0,
        fullscreen_opacity = 1.0,

        shadow = {
            enabled      = true,
            range        = 4,
            render_power = 3,
            color        = 0x55000000,
        },

        blur = {
            enabled           = true,
            size              = 5,
            passes            = 2,
            vibrancy          = 0.15,
            new_optimizations = true,
            xray              = false,
            noise             = 0.02,
            contrast          = 1.0,
            brightness        = 1.0,
        },
    },

    animations = {
        enabled = true,
    },
})

-- ==========================================
-- ANIMATIONS
-- ==========================================

hl.curve("easeOutQuint", { type = "bezier", points = { {0.23, 1}, {0.32, 1} } })

hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1} } })
hl.curve("linear",         { type = "bezier", points = { {0, 0},       {1, 1}       } })
hl.curve("almostLinear",   { type = "bezier", points = { {0.5, 0.5},   {0.75, 1}    } })
hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1}     } })

hl.animation({
  leaf = "windowsIn",
  enabled = true,
  speed = 3.28,
  bezier = "easeOutQuint",
  style = "popin 87%"
})

hl.animation({
  leaf = "windowsOut",
  enabled = true,
  speed = 1.19,
  bezier = "linear",
  style = "popin 87%"
})

hl.animation({ leaf = "windows",     enabled = false })
hl.animation({ leaf = "workspaces", enabled = false })
hl.animation({ leaf = "fade",       enabled = false })
hl.animation({ leaf = "layers",     enabled = false })

-- ==========================================
-- LAYOUT
-- ==========================================

hl.config({
    dwindle = {
        preserve_split = true,
        smart_resizing = true,
    },
})

-- ==========================================
-- INPUT
-- ==========================================

hl.config({
    input = {
        kb_layout = "de",

        follow_mouse = 1,
        sensitivity  = 0,

        repeat_rate  = 40,
        repeat_delay = 250,

        touchpad = {
            natural_scroll     = false,
            tap_to_click       = true,
            disable_while_typing = true,
        },
    },

    -- Three-finger horizontal swipe changes workspace.
    gestures = {
        workspace_swipe_distance           = 300,
        workspace_swipe_cancel_ratio       = 0.2,
        workspace_swipe_min_speed_to_force = 30,
        workspace_swipe_direction_lock     = true,
        workspace_swipe_forever            = true,
    },

    -- Press the same workspace key twice to bounce back.
    binds = {
        workspace_back_and_forth = true,
        allow_workspace_cycles   = true,
    },

    misc = {
        force_default_wallpaper   = 0,
        disable_hyprland_logo     = true,
        disable_splash_rendering  = true,
        close_special_on_empty    = true,
    },
})

hl.gesture({
    fingers   = 3,
    direction = "horizontal",
    action    = "workspace",
})

-- ==========================================
-- AUTOSTART
-- ==========================================

hl.on("hyprland.start", function()
    hl.exec_cmd("env GTK_MODULES=gail:atk-bridge waybar")
    hl.exec_cmd("mako")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
end)

-- ==========================================
-- APPLICATION SHORTCUTS
-- ==========================================

hl.bind(mainMod .. " + RETURN", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + D",      hl.dsp.exec_cmd(menu))
hl.bind(mainMod .. " + E",      hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + B",      hl.dsp.exec_cmd(browser))

-- ==========================================
-- WINDOW CONTROLS
-- ==========================================

hl.bind(mainMod .. " + Q",       hl.dsp.window.close())
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.exit())

hl.bind(mainMod .. " + F",        hl.dsp.window.fullscreen({ action = "toggle" }))
hl.bind(mainMod .. " + SHIFT + F", hl.dsp.window.fullscreen({ action = "toggle", mode = "maximized" }))
hl.bind(mainMod .. " + SPACE",    hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + P",        hl.dsp.window.pseudo())
hl.bind(mainMod .. " + SHIFT + P", hl.dsp.window.pin({ action = "toggle" }))
hl.bind(mainMod .. " + J",        hl.dsp.layout("togglesplit"))

-- Window groups (tabs)
hl.bind(mainMod .. " + G",         hl.dsp.group.toggle())
hl.bind(mainMod .. " + SHIFT + G", hl.dsp.window.deny_from_group({ action = "toggle" }))

-- ==========================================
-- FOCUS MOVEMENT
-- ==========================================

hl.bind(mainMod .. " + left",  hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up",    hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down",  hl.dsp.focus({ direction = "down" }))

-- ==========================================
-- MOVE WINDOWS
-- ==========================================

hl.bind(mainMod .. " + SHIFT + left",  hl.dsp.window.move({ direction = "left" }))
hl.bind(mainMod .. " + SHIFT + right", hl.dsp.window.move({ direction = "right" }))
hl.bind(mainMod .. " + SHIFT + up",    hl.dsp.window.move({ direction = "up" }))
hl.bind(mainMod .. " + SHIFT + down",  hl.dsp.window.move({ direction = "down" }))

-- ==========================================
-- RESIZE WINDOWS
-- ==========================================

local resizeStep = 40

hl.bind(mainMod .. " + CTRL + left",  hl.dsp.window.resize({ x = -resizeStep, y = 0, relative = true }), { repeating = true })
hl.bind(mainMod .. " + CTRL + right", hl.dsp.window.resize({ x =  resizeStep, y = 0, relative = true }), { repeating = true })
hl.bind(mainMod .. " + CTRL + up",    hl.dsp.window.resize({ x = 0, y = -resizeStep, relative = true }), { repeating = true })
hl.bind(mainMod .. " + CTRL + down",  hl.dsp.window.resize({ x = 0, y =  resizeStep, relative = true }), { repeating = true })

-- ==========================================
-- WORKSPACES 1-10
-- ==========================================

for i = 1, 10 do
    local key = i % 10

    hl.bind(mainMod .. " + " .. key,
        hl.dsp.focus({ workspace = i }))

    hl.bind(mainMod .. " + SHIFT + " .. key,
        hl.dsp.window.move({ workspace = i }))
end

-- ==========================================
-- WORKSPACE NAVIGATION
-- ==========================================

hl.bind(mainMod .. " + TAB",       hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + SHIFT + TAB", hl.dsp.focus({ workspace = "e-1" }))

-- Scrollable workspaces
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Scratchpad (special workspace)
hl.bind(mainMod .. " + U",         hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + U", hl.dsp.window.move({ workspace = "special:magic" }))

-- ==========================================
-- MOUSE
-- ==========================================

hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- ==========================================
-- MEDIA KEYS
-- ==========================================

hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      { locked = true, repeating = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     { locked = true, repeating = true })
hl.bind("XF86AudioMicMute",     hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   { locked = true, repeating = true })

hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })

-- ==========================================
-- SCREENSHOTS
-- ==========================================

hl.bind(mainMod .. " + SHIFT + S", hl.dsp.exec_cmd(
    'mkdir -p "$HOME/Pictures/Screenshots" && grim -g "$(slurp)" - | tee "$HOME/Pictures/Screenshots/$(date +%Y-%m-%d_%H-%M-%S).png" | wl-copy'
))

hl.bind("Print", hl.dsp.exec_cmd(
    'mkdir -p "$HOME/Pictures/Screenshots" && grim - | tee "$HOME/Pictures/Screenshots/$(date +%Y-%m-%d_%H-%M-%S).png" | wl-copy'
))

-- ==========================================
-- CONFIG RELOAD
-- ==========================================

hl.bind(mainMod .. " + SHIFT + R", hl.dsp.reload_config())

-- ==========================================
-- WINDOW RULES
-- ==========================================

-- Ignore maximize requests from applications.
hl.window_rule({
    name  = "suppress-maximize",
    match = { class = ".*" },

    suppress_event = "maximize",
})

-- Fix dragging issues with XWayland windows.
hl.window_rule({
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },

    no_focus = true,
})

-- Floating utility windows
hl.window_rule({
    name  = "pavucontrol",
    match = { class = "pavucontrol" },

    float  = true,
    center = true,
    size   = "900 650",
})

-- Keep GPG/SSH pinentry dialogs focused.
hl.window_rule({
    name  = "pinentry",
    match = { class = "pinentry" },

    stay_focused = true,
})
