#!/usr/bin/env python3
"""
g13d_gui — Native PyQt6 GUI companion for ecraven/g13d
Configure Logitech G13 key profiles and bindings visually.
https://github.com/otoa-kiyori/g13d_gui
"""

import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QDialog, QRadioButton, QButtonGroup,
    QCheckBox, QDialogButtonBox, QStatusBar, QInputDialog, QMessageBox,
    QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush, QFontMetrics

# ─── Configuration ────────────────────────────────────────────────────────────

BIND_FILE = Path.home() / ".g13" / "g13.bind"
G13_PIPE  = Path("/tmp/g13-0")

# All valid key names accepted by g13d
VALID_KEYS = [
    "0","1","2","3","4","5","6","7","8","9",
    "A","B","C","D","E","F","G","H","I","J","K","L","M",
    "N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
    "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
    "F13","F14","F15","F16","F17","F18","F19","F20","F21","F22","F23","F24",
    "ESC","TAB","BACKSPACE","ENTER","SPACE","DELETE","INSERT",
    "HOME","END","PAGEUP","PAGEDOWN",
    "UP","DOWN","LEFT","RIGHT",
    "LEFTCTRL","RIGHTCTRL","LEFTSHIFT","RIGHTSHIFT","LEFTALT","RIGHTALT",
    "LEFTBRACE","RIGHTBRACE","CAPSLOCK","NUMLOCK","SCROLLLOCK",
    "MINUS","EQUAL","SEMICOLON","APOSTROPHE","GRAVE","BACKSLASH","COMMA","DOT","SLASH",
    "KP0","KP1","KP2","KP3","KP4","KP5","KP6","KP7","KP8","KP9",
    "KPPLUS","KPMINUS","KPASTERISK","KPSLASH","KPDOT",
    "NEXTSONG","PREVIOUSSONG","PLAYPAUSE","STOPCD",
]

# G13 hardware keys (left side = G-keys, right side = special)
G13_KEYS = [
    "G1","G2","G3","G4","G5","G6","G7",
    "G8","G9","G10","G11","G12","G13","G14",
    "G15","G16","G17","G18","G19",
    "G20","G21","G22",
    "L1","L2","L3","L4",
    "M1","M2","M3","MR",
    "STICK_UP","STICK_DOWN","STICK_LEFT","STICK_RIGHT",
    "LEFT","BD","TOP",
]

# ─── Colors ───────────────────────────────────────────────────────────────────

COLORS = {
    "bg":           "#f0f0f0",
    "device":       "#e0e0e0",
    "g_key":        "#c8daf5",
    "g_key_border": "#6a9fd8",
    "m_key":        "#fde8b0",
    "m_key_border": "#c8960a",
    "l_key":        "#dac8f0",
    "l_key_border": "#9a6ad8",
    "stick":        "#b8e8c8",
    "stick_border": "#2a9a4a",
    "special":      "#d8d8d8",
    "special_border":"#888888",
    "text":         "#1a1a1a",
    "text_dim":     "#888888",
    "unbound":      "#bbbbbb",
    "highlight":    "#c87000",
}

# ─── Parser ───────────────────────────────────────────────────────────────────

def parse_bind_file(path: Path) -> dict[str, dict[str, str]]:
    """Parse g13d bind file → {profile_name: {key: value}}"""
    profiles: dict[str, dict[str, str]] = {}
    current = "default"
    profiles[current] = {}

    if not path.exists():
        return profiles

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if not parts:
            continue
        cmd = parts[0].lower()
        if cmd == "profile" and len(parts) == 2:
            current = parts[1].strip()
            if current not in profiles:
                profiles[current] = {}
        elif cmd == "bind" and len(parts) == 2:
            rest = parts[1].split(None, 1)
            if len(rest) == 2:
                key, val = rest[0].strip(), rest[1].strip()
                profiles[current][key] = val

    return profiles


def write_bind_file(path: Path, profiles: dict[str, dict[str, str]]):
    """Write profiles back to bind file format."""
    lines = []
    for name, bindings in profiles.items():
        if name == "default":
            continue  # write default last
        lines.append(f"profile {name}")
        for key, val in bindings.items():
            lines.append(f"bind {key} {val}")
    # default profile always last (ensures g13d starts in default)
    lines.append("profile default")
    for key, val in profiles.get("default", {}).items():
        lines.append(f"bind {key} {val}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")

# ─── Key Edit Dialog ──────────────────────────────────────────────────────────

class KeyEditDialog(QDialog):
    def __init__(self, key_name: str, current_value: str, profile_names: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure: {key_name}")
        self.setMinimumWidth(360)
        self.result_value = current_value

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Mode selector
        self.radio_key     = QRadioButton("Key binding")
        self.radio_profile = QRadioButton("Profile switch")
        self.radio_unbound = QRadioButton("Unbound")
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.radio_key)
        mode_group.addButton(self.radio_profile)
        mode_group.addButton(self.radio_unbound)

        mode_row = QHBoxLayout()
        mode_row.addWidget(self.radio_key)
        mode_row.addWidget(self.radio_profile)
        mode_row.addWidget(self.radio_unbound)
        layout.addLayout(mode_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #444;")
        layout.addWidget(sep)

        # ── Key binding panel ──
        self.key_panel = QWidget()
        kp = QVBoxLayout(self.key_panel)
        kp.setContentsMargins(0, 0, 0, 0)

        mod_row = QHBoxLayout()
        self.cb_ctrl  = QCheckBox("Ctrl")
        self.cb_shift = QCheckBox("Shift")
        self.cb_alt   = QCheckBox("Alt")
        mod_row.addWidget(QLabel("Modifiers:"))
        mod_row.addWidget(self.cb_ctrl)
        mod_row.addWidget(self.cb_shift)
        mod_row.addWidget(self.cb_alt)
        mod_row.addStretch()
        kp.addLayout(mod_row)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Key:"))
        self.key_combo = QComboBox()
        self.key_combo.addItems(["(none)"] + sorted(VALID_KEYS))
        self.key_combo.setMinimumWidth(160)
        key_row.addWidget(self.key_combo)
        key_row.addStretch()
        kp.addLayout(key_row)
        layout.addWidget(self.key_panel)

        # ── Profile switch panel ──
        self.profile_panel = QWidget()
        pp = QHBoxLayout(self.profile_panel)
        pp.setContentsMargins(0, 0, 0, 0)
        pp.addWidget(QLabel("Switch to profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(profile_names)
        pp.addWidget(self.profile_combo)
        pp.addStretch()
        layout.addWidget(self.profile_panel)

        # Preview
        self.preview = QLabel()
        self.preview.setStyleSheet(f"color: {COLORS['highlight']}; font-family: monospace;")
        layout.addWidget(self.preview)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Connect signals
        self.radio_key.toggled.connect(self._update_panels)
        self.radio_profile.toggled.connect(self._update_panels)
        self.radio_unbound.toggled.connect(self._update_panels)
        self.cb_ctrl.toggled.connect(self._update_preview)
        self.cb_shift.toggled.connect(self._update_preview)
        self.cb_alt.toggled.connect(self._update_preview)
        self.key_combo.currentTextChanged.connect(self._update_preview)
        self.profile_combo.currentTextChanged.connect(self._update_preview)

        self._load(current_value)

    def _load(self, value: str):
        if not value:
            self.radio_unbound.setChecked(True)
        elif value.startswith("!profile "):
            self.radio_profile.setChecked(True)
            target = value[len("!profile "):].strip()
            idx = self.profile_combo.findText(target)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
        else:
            self.radio_key.setChecked(True)
            # Parse KEY_LEFTCTRL+KEY_SHIFT+KEY_F → modifiers + base key
            parts = value.split("+")
            base = parts[-1]
            mods = [p.upper() for p in parts[:-1]]
            self.cb_ctrl.setChecked(any("CTRL" in m for m in mods))
            self.cb_shift.setChecked(any("SHIFT" in m for m in mods))
            self.cb_alt.setChecked(any("ALT" in m for m in mods))
            # Strip KEY_ prefix for combo lookup
            base_name = base.replace("KEY_", "")
            idx = self.key_combo.findText(base_name)
            if idx >= 0:
                self.key_combo.setCurrentIndex(idx)
        self._update_panels()

    def _update_panels(self):
        self.key_panel.setVisible(self.radio_key.isChecked())
        self.profile_panel.setVisible(self.radio_profile.isChecked())
        self._update_preview()

    def _update_preview(self):
        self.preview.setText(f"→  {self._build_value()}")

    def _build_value(self) -> str:
        if self.radio_unbound.isChecked():
            return "(unbound)"
        if self.radio_profile.isChecked():
            return f"!profile {self.profile_combo.currentText()}"
        # Key binding
        parts = []
        if self.cb_ctrl.isChecked():  parts.append("KEY_LEFTCTRL")
        if self.cb_shift.isChecked(): parts.append("KEY_LEFTSHIFT")
        if self.cb_alt.isChecked():   parts.append("KEY_LEFTALT")
        key = self.key_combo.currentText()
        if key and key != "(none)":
            parts.append(f"KEY_{key}")
        return "+".join(parts) if parts else "(unbound)"

    def _accept(self):
        val = self._build_value()
        self.result_value = "" if val == "(unbound)" else val
        self.accept()

# ─── Key Button ───────────────────────────────────────────────────────────────

def _key_style(bg: str, border: str, text_color: str = COLORS["text"]) -> str:
    return f"""
        QPushButton {{
            background-color: {bg};
            border: 1px solid {border};
            border-radius: 4px;
            color: {text_color};
            font-family: 'Courier New', monospace;
            font-size: 11px;
            font-weight: 500;
            padding: 2px;
        }}
        QPushButton:hover {{
            background-color: {border};
            border-color: {COLORS['highlight']};
        }}
        QPushButton:pressed {{
            border: 2px solid {COLORS['highlight']};
        }}
    """

ZONE_STYLES = {
    "g":       _key_style(COLORS["g_key"],       COLORS["g_key_border"]),
    "m":       _key_style(COLORS["m_key"],       COLORS["m_key_border"]),
    "l":       _key_style(COLORS["l_key"],       COLORS["l_key_border"]),
    "stick":   _key_style(COLORS["stick"],       COLORS["stick_border"]),
    "special": _key_style(COLORS["special"],     COLORS["special_border"]),
}

def zone_for(key: str) -> str:
    if key.startswith("G"):      return "g"
    if key.startswith("M"):      return "m"
    if key.startswith("L"):      return "l"
    if key.startswith("STICK"):  return "stick"
    return "special"

# ─── Device Canvas ────────────────────────────────────────────────────────────

class DeviceCanvas(QWidget):
    """Visual G13 layout — absolute-positioned key buttons."""

    # (key_name, x, y, w, h)  — all in pixels on 760×380 canvas
    KEY_POSITIONS = [
        # ── Mode buttons (top left) ──
        ("M1",   10,  8, 42, 22), ("M2",  56,  8, 42, 22),
        ("M3",  102,  8, 42, 22), ("MR", 148,  8, 42, 22),

        # ── G row 1 ──
        ("G1",   10, 50, 52, 36), ("G2",  66, 50, 52, 36), ("G3", 122, 50, 52, 36),
        ("G4",  178, 50, 52, 36), ("G5", 234, 50, 52, 36), ("G6", 290, 50, 52, 36),
        ("G7",  346, 50, 52, 36),

        # ── G row 2 ──
        ("G8",   10, 92, 52, 36), ("G9",  66, 92, 52, 36), ("G10",122, 92, 52, 36),
        ("G11", 178, 92, 52, 36), ("G12",234, 92, 52, 36), ("G13",290, 92, 52, 36),
        ("G14", 346, 92, 52, 36),

        # ── G row 3 ──
        ("G15",  10,134, 52, 36), ("G16", 66,134, 52, 36), ("G17",122,134, 52, 36),
        ("G18", 178,134, 52, 36), ("G19",234,134, 52, 36),

        # ── Bottom row: G20-G22 ──
        ("G20", 456,280, 52, 36), ("G21",512,280, 52, 36), ("G22",568,280, 52, 36),

        # ── Thumb / L keys ──
        ("L1",  10, 220, 42, 36), ("L2",  56, 220, 42, 36),
        ("L3",  10, 260, 42, 36), ("L4",  56, 260, 42, 36),

        # ── Special flat buttons ──
        ("LEFT",130, 220, 52, 28), ("BD",  186, 220, 52, 28),

        # ── Stick zone buttons ──
        ("STICK_UP",   148, 190, 44, 26),
        ("STICK_DOWN", 148, 248, 44, 26),
        ("STICK_LEFT", 100, 220, 44, 26),
        ("STICK_RIGHT",196, 220, 44, 26),
    ]

    def __init__(self, on_key_click, parent=None):
        super().__init__(parent)
        self.on_key_click = on_key_click
        self.setFixedSize(640, 320)
        self.buttons: dict[str, QPushButton] = {}
        self.setStyleSheet(f"background-color: {COLORS['device']}; border-radius: 16px; border: 2px solid #aaaaaa;")

        for key, x, y, w, h in self.KEY_POSITIONS:
            btn = QPushButton(self)
            btn.setGeometry(x, y, w, h)
            btn.setStyleSheet(ZONE_STYLES[zone_for(key)])
            btn.setToolTip(key)
            btn.clicked.connect(lambda checked, k=key: self.on_key_click(k))
            self.buttons[key] = btn

    def update_bindings(self, bindings: dict[str, str]):
        for key, btn in self.buttons.items():
            val = bindings.get(key, "")
            label = self._short_label(key, val)
            btn.setText(label)
            # Dim unbound keys
            zone = zone_for(key)
            if val:
                btn.setStyleSheet(ZONE_STYLES[zone])
            else:
                btn.setStyleSheet(
                    ZONE_STYLES[zone].replace(
                        f"color: {COLORS['text']}", f"color: {COLORS['text_dim']}"
                    )
                )

    def _short_label(self, key: str, val: str) -> str:
        top = key  # key name on first line
        if not val:
            return f"{key}\n—"
        # Shorten value
        v = val.replace("KEY_LEFTCTRL+", "^").replace("KEY_LEFTSHIFT+", "⇧") \
               .replace("KEY_LEFTALT+", "⌥").replace("KEY_", "")
        if v.startswith("!profile "):
            v = "→" + v[9:]
        # Truncate
        if len(v) > 9:
            v = v[:8] + "…"
        return f"{key}\n{v}"

# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("g13d_gui — G13 Profile Configurator")
        self.profiles: dict[str, dict[str, str]] = {}
        self.current_profile = "default"
        self._load_profiles()

        self._build_ui()
        self._refresh_profile_combo()
        self._refresh_canvas()

    def _load_profiles(self):
        self.profiles = parse_bind_file(BIND_FILE)
        if not self.profiles:
            self.profiles = {"default": {}}

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # ── Top bar ──
        top = QHBoxLayout()
        top.addWidget(QLabel("Profile:"))

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(160)
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        top.addWidget(self.profile_combo)

        btn_new = QPushButton("+ New")
        btn_new.clicked.connect(self._new_profile)
        btn_dup = QPushButton("Duplicate")
        btn_dup.clicked.connect(self._duplicate_profile)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._delete_profile)
        top.addWidget(btn_new)
        top.addWidget(btn_dup)
        top.addWidget(btn_del)
        top.addSpacing(20)

        self.btn_switch = QPushButton("⚡ Switch Now")
        self.btn_switch.setToolTip("Switch G13 to this profile instantly (writes to /tmp/g13-0)")
        self.btn_switch.clicked.connect(self._switch_now)
        self.btn_switch.setStyleSheet(f"background-color: #1a3a1a; color: #88ff88; font-weight: bold;")
        top.addWidget(self.btn_switch)
        top.addStretch()
        root.addLayout(top)

        # ── Device canvas ──
        canvas_wrap = QHBoxLayout()
        canvas_wrap.addStretch()
        self.canvas = DeviceCanvas(self._on_key_click)
        canvas_wrap.addWidget(self.canvas)
        canvas_wrap.addStretch()
        root.addLayout(canvas_wrap)

        # ── Bottom bar ──
        bot = QHBoxLayout()
        btn_save = QPushButton("💾 Save bind file")
        btn_save.clicked.connect(self._save)
        btn_reload = QPushButton("🔄 Save + Reload service")
        btn_reload.clicked.connect(self._save_and_reload)
        btn_reload.setStyleSheet("background-color: #1a2a3a; color: #88aaff; font-weight: bold;")
        bot.addStretch()
        bot.addWidget(btn_save)
        bot.addWidget(btn_reload)
        root.addLayout(bot)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Loaded: " + str(BIND_FILE))

    def _refresh_profile_combo(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(list(self.profiles.keys()))
        idx = self.profile_combo.findText(self.current_profile)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        self.profile_combo.blockSignals(False)

    def _refresh_canvas(self):
        bindings = self.profiles.get(self.current_profile, {})
        self.canvas.update_bindings(bindings)

    def _on_profile_changed(self, name: str):
        if name:
            self.current_profile = name
            self._refresh_canvas()

    def _on_key_click(self, key: str):
        bindings = self.profiles.setdefault(self.current_profile, {})
        current_val = bindings.get(key, "")
        dlg = KeyEditDialog(key, current_val, list(self.profiles.keys()), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.result_value:
                bindings[key] = dlg.result_value
            else:
                bindings.pop(key, None)
            self._refresh_canvas()
            self.status.showMessage(f"Updated {key} → {dlg.result_value or '(unbound)'}")

    def _new_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if ok and name.strip():
            name = name.strip()
            if name in self.profiles:
                QMessageBox.warning(self, "Exists", f"Profile '{name}' already exists.")
                return
            self.profiles[name] = {}
            self.current_profile = name
            self._refresh_profile_combo()
            self._refresh_canvas()

    def _duplicate_profile(self):
        name, ok = QInputDialog.getText(
            self, "Duplicate Profile",
            f"New name for copy of '{self.current_profile}':"
        )
        if ok and name.strip():
            name = name.strip()
            self.profiles[name] = dict(self.profiles.get(self.current_profile, {}))
            self.current_profile = name
            self._refresh_profile_combo()
            self._refresh_canvas()

    def _delete_profile(self):
        if len(self.profiles) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "At least one profile must remain.")
            return
        reply = QMessageBox.question(
            self, "Delete Profile",
            f"Delete profile '{self.current_profile}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.profiles[self.current_profile]
            self.current_profile = next(iter(self.profiles))
            self._refresh_profile_combo()
            self._refresh_canvas()

    def _switch_now(self):
        if not G13_PIPE.exists():
            self.status.showMessage("⚠ /tmp/g13-0 pipe not found — is g13d running?")
            return
        try:
            G13_PIPE.write_text(f"profile {self.current_profile}\n")
            self.status.showMessage(f"⚡ Switched G13 to profile: {self.current_profile}")
        except Exception as e:
            self.status.showMessage(f"Error switching profile: {e}")

    def _save(self):
        try:
            write_bind_file(BIND_FILE, self.profiles)
            self.status.showMessage(f"✓ Saved → {BIND_FILE}")
        except Exception as e:
            self.status.showMessage(f"Save error: {e}")

    def _save_and_reload(self):
        self._save()
        try:
            subprocess.run(["sudo", "systemctl", "restart", "g13"], check=True, timeout=10)
            self.status.showMessage("✓ Saved and g13d service reloaded.")
        except subprocess.CalledProcessError:
            self.status.showMessage("⚠ Save OK — service restart failed (sudo required). Run req_no_sudo first.")
        except Exception as e:
            self.status.showMessage(f"Reload error: {e}")

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("g13d_gui")
    app.setOrganizationName("otoa-kiyori")

    # Light palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(COLORS["bg"]))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#f5f5f5"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(COLORS["highlight"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    font = app.font()
    font.setPointSize(11)
    app.setFont(font)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
