# g13d_gui

A native PyQt6 GUI companion for [ecraven/g13](https://github.com/ecraven/g13) — visually configure Logitech G13 key profiles and bindings on Linux.

> **This tool does not modify or replace g13d.** It is a frontend for the bind file and the g13d command pipe. All key mapping is still handled by g13d itself.

![Python](https://img.shields.io/badge/python-3.10+-blue) ![PyQt6](https://img.shields.io/badge/PyQt6-6.x-green) ![License](https://img.shields.io/badge/license-CC0-lightgrey)

---

## Requirements

### Hardware
- Logitech G13 Advanced Gameboard

### Driver (required — g13d_gui is a frontend for this)
- [ecraven/g13](https://github.com/ecraven/g13) — userspace G13 driver

Build and install from source:
```bash
sudo apt install build-essential libusb-1.0-0-dev libboost-all-dev
git clone https://github.com/ecraven/g13.git
cd g13
make
sudo make install
```

The driver must be running as a systemd service. Example service file:
```ini
# /etc/systemd/system/g13.service
[Unit]
Description=Logitech G13 daemon
After=multi-user.target

[Service]
ExecStart=/usr/local/bin/g13d --config /home/youruser/.g13/g13.bind
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable --now g13
```

USB access (create `/etc/udev/rules.d/91-g13.rules`):
```
SUBSYSTEM=="usb", ATTR{idVendor}=="046d", ATTR{idProduct}=="c21c", GROUP="plugdev", MODE="0660"
```

Then reload udev and add yourself to the `plugdev` group:
```bash
sudo udevadm control --reload-rules
sudo usermod -aG plugdev $USER
```

### Python
- Python 3.10 or newer

### Python dependency — PyQt6

**Debian/Ubuntu (recommended):**
```bash
sudo apt install python3-pyqt6
```

**pip (alternative):**
```bash
pip install -r requirements.txt
```

> No other Python packages are required. The app uses only PyQt6 and Python stdlib.

---

## Install & Run

```bash
git clone https://github.com/otoa-kiyori/g13d_gui.git
cd g13d_gui
python3 g13d_gui.py
```

The app reads `~/.g13/g13.bind` automatically on startup. If the file does not exist, it starts with an empty default profile.

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

### Switch Now
Writes `profile <name>` directly to the g13d command pipe at `/tmp/g13-0`. The G13 switches instantly without restarting the service. Requires g13d to be running.

### Save + Reload
Saves the bind file then runs `sudo systemctl restart g13`. Requires passwordless sudo for systemctl, or enter your password in the terminal that launched g13d_gui.

---

## Bind file location

Default: `~/.g13/g13.bind`

g13d_gui reads and writes this file. Profiles are written in the order they appear, with `profile default` always last (so g13d starts in the default profile).

---

## Key binding format

g13d uses `KEY_` prefixed names, with `+` for modifier combos:

```
bind G1 KEY_ESC
bind G4 KEY_UP
bind G15 KEY_LEFTSHIFT
bind STICK_UP KEY_LEFTCTRL+KEY_B
bind M2 !profile firestorm
```

g13d_gui handles all of this automatically.

---

## Features

- Visual G13 device layout — click any key to configure it
- Color-coded key zones (G-keys, M-keys, L/thumb keys, stick zones, special buttons)
- Full profile management — create, duplicate, delete profiles
- **Switch Now** — instantly switch the active G13 profile via `/tmp/g13-0` pipe (no restart)
- **Save + Reload** — write bind file and restart the g13d service
- Supports all binding types: single keys, modifier combos, and profile-switch commands
- Configures M1/M2/M3/MR, L1–L4, stick directions, LEFT, BD, TOP
- Native desktop app — no browser, no Java, no server, no network

---

## Credits

Conceived and directed by **[otoa-kiyori](https://github.com/otoa-kiyori)**.
Code written by **[Claude](https://claude.ai)** (Anthropic).

> Note: I wanted to manage my G13 profiles quickly on g13d so I asked Claude Code to make this UI.

Companion to [ecraven/g13](https://github.com/ecraven/g13) — the userspace G13 driver this tool is designed around.

---

## License

CC0 1.0 Universal — public domain. See [LICENSE](LICENSE)
