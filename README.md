# sway

Monochrome sway desktop on Wayland, with SwayFX's rounded corners, blur and shadows where your distro can get it, and a Settings window (`SUPER + ALT + M`) for network (Wi-Fi, Ethernet, IP and DNS, VPN, proxy), Bluetooth, sound, displays and brightness, power modes (power saver, balanced, performance), the wallpaper (and a wallpaper slideshow), the look (bar styles, a 12- or 24-hour clock, window opacity, corners, gaps) and the keys. The bar is [Waybar](https://github.com/Alexays/Waybar), the cursor [Capitaine Cursors](assets/cursors).

## Install on Linux

Fedora (Workstation, KDE Plasma, the Sway spin and the other spins; Fedora 45 is the main target), Arch and its relatives (CachyOS, EndeavourOS, Manjaro), Debian 13, Ubuntu 24.04 and newer and its flavours, Pop!_OS, Linux Mint. It goes next to the desktop you have (GNOME, KDE, Cinnamon, Xfce...), which stays as it is.

```bash
git clone --depth 1 https://github.com/OmitGhostly/sway.git
cd sway
./install.sh
```

or in one line:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/OmitGhostly/sway/main/install.sh)
```

Afterwards, log out and pick **Sway** at the login screen; the installer tells you where for yours. GNOME's login screen: click your name, then the gear icon at the bottom right. KDE: the "Desktop Session" menu under the password box (SDDM: the session menu at the bottom left). Linux Mint and other LightDM login screens: the small round icon next to your name, or the session icon at the top right.

**SwayFX.** [SwayFX](https://github.com/wlrfx/swayfx) is sway with rounded corners, blur and shadows; it reads the same config. On Fedora the installer gets it from its own COPR ([swayfx/swayfx](https://copr.fedorainfracloud.org/coprs/swayfx/swayfx/)); a sway you already have (the Fedora Sway spin) is swapped for it, and the uninstaller swaps it back. If the COPR has no build for your Fedora release yet (it can lag a few weeks behind a new release), you get plain sway; running `./install.sh` again later picks SwayFX up. On Arch it comes from your repos or the AUR (with paru or yay), when sway isn't installed already. Debian, Ubuntu and Mint have no package, so they get plain sway: everything works the same, with square corners and no blur or shadows. `./install.sh --no-swayfx` installs plain sway everywhere.

**NVIDIA.** With NVIDIA's own driver, sway only starts when it's told to (`--unsupported-gpu`). The installer adds a second login entry, **Sway (NVIDIA)**, that does that. AMD, Intel and the open-source NVIDIA driver need nothing extra.

On Ubuntu 24.04 and Linux Mint 22, which don't package Ghostty or fastfetch, the installer gets them as `.deb` files: Ghostty 1.3.1 (the last version for Ubuntu 24.04) from [ghostty-ubuntu](https://github.com/mkasberg/ghostty-ubuntu), the community package listed on ghostty.org, and fastfetch from its own releases. Both are installed with apt, so the uninstaller removes them again. Their Waybar (0.9) can't tell the workspace items which screen they're on, so with two screens both bars show the workspaces of the screen you're on. Debian, Ubuntu and Mint also ship rofi 1.7, which runs through XWayland: its menus open on the screen with the mouse pointer, and the window switcher (`SUPER + A`) gets its list of windows from sway instead of from rofi.

The file manager is [yazi](https://yazi-rs.github.io), opened in the terminal; folders opened from other programs go there too. On Fedora it comes from the [lihaohong/yazi](https://copr.fedorainfracloud.org/coprs/lihaohong/yazi/) COPR, on Debian/Ubuntu from the Snap Store (or yazi's own release build), elsewhere from your repos. Thunar stays installed, and Settings > Keybindings switches between them.

It can sit next to the i3 version of this desktop. They share the terminal, notification and greeting settings (`~/.config/kitty`, `ghostty`, `dunst`, `fastfetch`...): the one installed last puts its copies there and keeps the other one's as backups (`*.bak-*`). Its uninstaller puts those back.

Your keyboard layout, key repeat and touchpad tapping are in `~/.config/sway/input.conf`. That file is yours: updates keep it. Settings > Displays writes `outputs.conf` (resolution, refresh rate, scale, position, rotation) and Settings > Mouse writes `mouse.conf`; those are kept too.

## Updates

After a system update (`pacman -Syu`, `dnf upgrade`, `apt upgrade`) you get a notification when a newer version of this config is on GitHub. Nothing changes until you install it:

```bash
swaydots-update
```

What you set in the Settings window is kept, and so are `input.conf`, `outputs.conf` and your wallpaper. Other files you edited by hand in `~/.config` (the Ghostty config, the sway config...) are replaced, and `swaydots-update --undo` puts back the version from before. Your own Ghostty settings belong in `~/.config/ghostty-local.conf`: Ghostty reads it last, and updates never touch it.

| Command | Does |
|---|---|
| `swaydots-update --check` | only say whether there is a newer version |
| `swaydots-update --status` | the installed version, and a newer one if there is |
| `swaydots-update --undo` | go back to the config from before the last update |
| `swaydots-update --off` / `--on` | no more checks after system updates / checks again |

## Uninstall

```bash
./uninstall.sh
```

| Option | Does |
|---|---|
| `--yes` | no questions: config, sway and added programs |
| `--config-only` | config only, keep sway and programs |
| `--all-programs` | also offer programs you already had |
| `--no-restore` | don't restore your old configs |
| `--force` | remove sway even if it's your only desktop |
| `--dry-run` | show, change nothing |

## Keybinds

`SUPER` = Windows key. `SUPER + H` shows this list.

### Apps

| Key | Action |
|---|---|
| `SUPER + D` | App launcher (rofi) |
| `SUPER + Enter` | Open terminal |
| `SUPER + E` | File manager |
| `SUPER + B` | Open default browser |
| `SUPER + C` | SSH session manager |
| `SUPER + H` | Help / cheat sheet |
| `SUPER + SHIFT + K` | Search keybinds |
| `SUPER + S` | Web search |
| `SUPER + A` | Window switcher (overview replacement) |
| `SUPER + CTRL + S` | Window switcher |
| `SUPER + ALT + E` | Emoji menu |
| `SUPER + ALT + C` | Calculator |
| `SUPER + ALT + V` | Clipboard manager |
| `SUPER + SHIFT + M` | Online music |
| `SUPER + SHIFT + E` | Quick settings menu |
| `SUPER + CTRL + R` | Rofi theme selector |
| `SUPER + CTRL + SHIFT + R` | Rofi theme selector (modified) |
| `SUPER + CTRL + K` | Kitty theme selector |
| `SUPER + SHIFT + O` | Change oh-my-zsh theme |
| `SUPER + ALT + R` | Refresh bar, colors, menus |
| `SUPER + SHIFT + Enter` | Drop-down terminal |
| `SUPER + ALT + D` | Display layout (Settings > Displays) |
| `SUPER + ALT + M` | Settings window (network: Wi-Fi, Ethernet, IP and DNS, VPN, proxy; Bluetooth, sound, displays, appearance, colors, themes, mouse and cursor, keybinds) |

### Look

| Key | Action |
|---|---|
| `SUPER + W` | Select wallpaper |
| `CTRL + ALT + W` | Random wallpaper |
| `SUPER + ALT + O` | Toggle effects (SwayFX: blur/rounding/shadows; window transparency) |
| `SUPER + CTRL + O` | Toggle active window opacity |
| `SUPER + SHIFT + G` | Toggle game mode |
| `SUPER + N` | Toggle night light |
| `SUPER + CTRL + ALT + B` | Toggle bar on/off |
| `SUPER + SHIFT + N` | Notification history |

### Session

| Key | Action |
|---|---|
| `SUPER + Q` | Close active window |
| `SUPER + SHIFT + Q` | Terminate active process |
| `CTRL + ALT + L` | Lock screen |
| `CTRL + ALT + P` | Power menu |
| `CTRL + ALT + Delete` | Exit / power menu |
| `SUPER + SHIFT + C` | Reload sway config |
| `SUPER + SHIFT + R` | Reload sway config (windows stay where they are) |

### Windows

| Key | Action |
|---|---|
| `SUPER + SHIFT + F` | Fullscreen |
| `SUPER + F` | Fullscreen (maximize) |
| `SUPER + Space` | Toggle floating |
| `SUPER + CTRL + Space` | Floating: standard size, centered |
| `SUPER + ALT + L` | Toggle layout (split/tabbed/stacking) |
| `SUPER + ALT + 1` | Layout: side by side (the normal split layout) |
| `SUPER + ALT + 2` | Layout: stacking |
| `SUPER + ALT + 3` | Layout: tabbed (monocle-like) |
| `SUPER + G` | Toggle group (tabbed/split) |
| `SUPER + SHIFT + I` | Toggle split direction |
| `SUPER + ALT + T` | Toggle spiral tiling like Hyprland (on) / classic side by side (off) |
| `SUPER + CTRL + H` | Focus parent container (group) |
| `SUPER + CTRL + J` | Focus child container |
| `SUPER + \` | Split next window horizontally |
| `SUPER + -` | Split next window vertically |
| `SUPER + SHIFT + T` | Toggle sticky |
| `SUPER + SHIFT + Space` | Focus: switch tiling/floating |
| `SUPER + J` | Focus next |
| `SUPER + K` | Focus previous |
| `ALT + Tab` | Focus next (alt-tab) |
| `ALT + SHIFT + Tab` | Focus previous (alt-shift-tab) |
| `SUPER + ←` | Focus left |
| `SUPER + ↓` | Focus down |
| `SUPER + ↑` | Focus up |
| `SUPER + →` | Focus right |
| `SUPER + CTRL + ←` | Move window left |
| `SUPER + CTRL + ↓` | Move window down |
| `SUPER + CTRL + ↑` | Move window up |
| `SUPER + CTRL + →` | Move window right |
| `SUPER + SHIFT + ←` | Resize: narrower |
| `SUPER + SHIFT + →` | Resize: wider |
| `SUPER + SHIFT + ↑` | Resize: shorter |
| `SUPER + SHIFT + ↓` | Resize: taller |
| `SUPER + SHIFT + U` | Move to scratchpad (special workspace) |
| `SUPER + U` | Toggle scratchpad (special workspace) |

### Workspaces

| Key | Action |
|---|---|
| `SUPER + 1 … 0` | Workspace 1 - 10 |
| `SUPER + SHIFT + 1 … 0` | Move to workspace 1 - 10 (follow) |
| `SUPER + CTRL + 1 … 0` | Move silently to workspace 1 - 10 |
| `SUPER + Tab` | Next workspace |
| `SUPER + SHIFT + Tab` | Previous workspace |
| `SUPER + .` | Next workspace (.) |
| `SUPER + ,` | Previous workspace (,) |
| `SUPER + scroll down` | Next workspace (scroll) |
| `SUPER + scroll up` | Previous workspace (scroll) |
| `SUPER + SHIFT + ]` | Move to next workspace (follow) |
| `SUPER + SHIFT + [` | Move to previous workspace (follow) |
| `SUPER + CTRL + ]` | Move silently to next workspace |
| `SUPER + CTRL + [` | Move silently to previous workspace |
| `SUPER + CTRL + F9` | Workspace to left monitor |
| `SUPER + CTRL + F10` | Workspace to right monitor |
| `SUPER + CTRL + F11` | Workspace to upper monitor |
| `SUPER + CTRL + F12` | Workspace to lower monitor |

## Files

| Repo | Installed to | What |
|---|---|---|
| `config/sway/` | `~/.config/sway/` | sway, scripts, Settings |
| `config/waybar/` | `~/.config/waybar/` | bar |
| `config/dunst/` | `~/.config/dunst/` | notifications |
| `config/ghostty/` | `~/.config/ghostty/` | terminal |
| `config/kitty/` | `~/.config/kitty/` | terminal |
| `config/yazi/` | `~/.config/yazi/` | file manager colours |
| `config/fastfetch/` | `~/.config/fastfetch/` | greeting |
| `config/cava/` | `~/.config/cava/` | visualiser |
| `config/swappy/` | `~/.config/swappy/` | screenshot editor |
| `config/gtk-3.0/` | `~/.config/gtk-3.0/` | dark GTK |
| `wallpapers/` | `~/Pictures/wallpapers/` | wallpapers |
| `assets/cursors/` | `~/.local/share/icons/capitaine-cursors` | cursor (LGPL-3.0) |
| `uninstall.sh` | `~/.local/bin/swaydots-uninstall` | uninstaller |
| `tools/` | - | dev tools |

GPL-3.0 · based on [Hyprland-Dots](https://github.com/LinuxBeginnings/Hyprland-Dots)
