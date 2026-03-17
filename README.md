# g13d_gui

A native PyQt6 GUI companion for [ecraven/g13](https://github.com/ecraven/g13) — visually configure Logitech G13 key profiles and bindings on Linux.

> **This tool does not modify or replace g13d.** It is a frontend for the bind file and the g13d command pipe. All key mapping is still handled by g13d itself.

![Python](https://img.shields.io/badge/python-3.13-blue) ![PyQt6](https://img.shields.io/badge/PyQt6-6.x-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- Visual G13 device layout — click any key to configure it
- Color-coded key zones (G-keys, M-keys, L/thumb keys, stick zones, special buttons)
- Full profile management — create, duplicate, delete profiles
- **Switch Now** — instantly switch the active G13 profile via `/tmp/g13-0` pipe (no restart)
- **Save + Reload** — write bind file and restart the g13d service
- Supports all binding types: single keys, modifier combos, and profile-switch commands
- Configures M1/M2/M3/MR, L1–L4, stick zones, LEFT, BD — everything g13d supports
- Native KDE Plasma Wayland — no browser, no Java, no server

---

## Requirements

- Logitech G13 with [ecraven/g13d](https://github.com/ecraven/g13) installed and running
- Python 3.10+
- PyQt6

```bash
sudo apt install python3-pyqt6
```

---

## Install & Run

```bash
git clone https://github.com/otoa-kiyori/g13d_gui.git
cd g13d_gui
python3 g13d_gui.py
```

The app reads `~/.g13/g13.bind` automatically on startup.

---

## Usage

| Action | How |
|--------|-----|
| Edit a key | Click it on the device canvas |
| Switch profiles | Select from dropdown → **⚡ Switch Now** |
| Save changes | **💾 Save bind file** |
| Apply to G13 | **🔄 Save + Reload service** (requires sudo for systemctl) |
| Add profile | **+ New** button |
| Duplicate profile | **Duplicate** button |

### Reload requires sudo
The "Save + Reload" button runs `sudo systemctl restart g13`. If you use a passwordless sudo window script (like `req_no_sudo`), activate it before clicking Reload. Otherwise just use Save and restart manually.

---

## Bind file location

Default: `~/.g13/g13.bind`

g13d service must be configured to load it:
```ini
# /etc/systemd/system/g13.service
ExecStart=/usr/local/bin/g13d --config /home/youruser/.g13/g13.bind
```

---

## Key binding format

g13d uses its own key names (no `KEY_` prefix in the bind file, but with it in combos):

```
bind G1 KEY_ESC
bind G4 KEY_UP
bind G15 KEY_LEFTSHIFT
bind STICK_UP KEY_LEFTCTRL+KEY_B
bind M2 !profile firestorm
```

g13d_gui handles all of this automatically.

---

## Credits

Built by **[Claude](https://claude.ai)** (Anthropic) for **[otoa-kiyori](https://github.com/otoa-kiyori)**.

Companion to [ecraven/g13](https://github.com/ecraven/g13) — the userspace G13 driver this tool is designed around.

---

## License

MIT — see [LICENSE](LICENSE)
