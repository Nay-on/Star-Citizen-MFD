import sys
import psutil
import json
import os
import random
import time
import urllib.request
import shutil
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QGridLayout, 
                             QWidget, QLabel, QVBoxLayout, QFrame, QHBoxLayout, 
                             QDialog, QScrollArea, QProgressBar, QTextEdit, QComboBox,
                             QLineEdit, QFileDialog, QMessageBox, QTabWidget, QListWidget, QDockWidget, QListWidgetItem, QBoxLayout)
from PyQt6.QtCore import Qt, QTimer, QTime, QRectF, QEvent, QPointF, QRect, QThread, pyqtSignal, QPropertyAnimation
from modules.clock_widget import ClockWidget
from modules.draggable_module import DraggableModule
from modules.grid_widget import GridWidget
from modules.hardware_monitor_widget import HardwareMonitorWidget
from modules.command_log_widget import CommandLogWidget
from modules.shield_array_widget import ShieldArrayWidget
from modules.flight_systems_widget import FlightSystemsWidget
from modules.power_distribution_widget import PowerDistributionWidget
from modules.shared_widgets import HoldButton
from modules.calculator_widget import CalculatorWidget
from modules.auec_calculator_widget import AUECCalculatorWidget
from modules.team_management_widget import TeamManagementWidget
from PyQt6.QtGui import QColor, QPalette, QBrush, QPainter, QPen, QPainterPath, QLinearGradient, QPolygonF, QFont, QRadialGradient

class Controller:
    def press(self, key): print(f"[MOCK] Pressing: {key}")
    def release(self, key): print(f"[MOCK] Releasing: {key}")
class Key:
    alt_l = 'alt_l'

APP_NAME = "RSI_MFD"
base_data_dir = os.getenv('LOCALAPPDATA')
if base_data_dir is None:
    base_data_dir = os.path.join(os.getenv('HOME', '/tmp'), '.config')
FIXED_APPDATA_DIR = os.path.join(base_data_dir, APP_NAME)
LOCATION_MAP_FILE = os.path.join(FIXED_APPDATA_DIR, "storage_location.json")
CONFIG_FILENAME = "sc_mfd_config.json"
NOTES_FILENAME = "sc_mfd_notes.txt"

def ensure_initial_setup():
    if not os.path.exists(FIXED_APPDATA_DIR):
        os.makedirs(FIXED_APPDATA_DIR)
    current_data_path = FIXED_APPDATA_DIR
    if os.path.exists(LOCATION_MAP_FILE):
        try:
            with open(LOCATION_MAP_FILE, 'r') as f:
                data = json.load(f)
                stored_path = data.get("data_path")
                if stored_path and os.path.exists(stored_path):
                    current_data_path = stored_path
        except: pass
    else:
        update_location_map(FIXED_APPDATA_DIR)
    local_config = os.path.join(os.getcwd(), CONFIG_FILENAME)
    local_notes = os.path.join(os.getcwd(), NOTES_FILENAME)
    target_config = os.path.join(current_data_path, CONFIG_FILENAME)
    target_notes = os.path.join(current_data_path, NOTES_FILENAME)
    if os.path.exists(local_config) and not os.path.exists(target_config):
        try: shutil.move(local_config, target_config)
        except Exception: pass
    if os.path.exists(local_notes) and not os.path.exists(target_notes):
        try: shutil.move(local_notes, target_notes)
        except Exception: pass
    return current_data_path

def update_location_map(new_path):
    try:
        with open(LOCATION_MAP_FILE, 'w') as f:
            json.dump({"data_path": new_path}, f)
    except Exception: pass

CURRENT_DATA_DIR = ensure_initial_setup()

def get_config_path(): return os.path.join(CURRENT_DATA_DIR, CONFIG_FILENAME)
def get_notes_path(): return os.path.join(CURRENT_DATA_DIR, NOTES_FILENAME)

DEFAULT_CONFIG = {
    "TARGET_SCREEN_INDEX": 1,
    "WEAPON_POWER": "f5", "ENGINE_POWER": "f6", "SHIELD_POWER": "f7", "POWER_RESET": "f8",
    "SHIELD_FWD": "up", "SHIELD_BACK": "down", "SHIELD_LEFT": "left", "SHIELD_RIGHT": "right", "SHIELD_RESET": "insert",
    "LANDING": "n", "QUANTUM": "b", "ENGINES": "i", 
    "DOORS": "k", "LIGHTS": "l", "SCAN": "v", 
    "FLIGHT_READY": "r", "EXIT_SEAT": "y",
    "SPACE_BRAKE": "x", "DECOUPLED": "c", "VTOL": "k",
    "DECOY": "h", "NOISE": "j",
    "ATC_KEY_BASE": "n",
    "TEAM_ROLES": ["Commander", "Pilot", "Gunner", "Engineer"],
    "RSS_URL": "https://leonick.se/feeds/rsi/atom"
}

BOOT_SEQUENCE_LOGS = [
    "BIOS CHECK... OK", "LOADING KERNEL... OK", "MOUNTING VIRTUAL DRIVES...",
    "CONNECTING TO RSI NETWORK...", "AUTHENTICATING USER...", "LOADING GRAPHICS ENGINE...",
    "CALIBRATING TOUCH SENSORS...", "SYSTEM READY."
]

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f: 
                conf = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in conf: conf[k] = v
                return conf
        except: return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(get_config_path(), 'w') as f: json.dump(config, f, indent=4)

def get_key_object(key_str):
    try:
        if len(key_str) == 1: return key_str
        return getattr(Key, key_str)
    except AttributeError: return key_str

class RSSWorker(QThread):
    data_refreshed = pyqtSignal(list)
    def __init__(self, rss_url):
        super().__init__()
        self.rss_url = rss_url
    def run(self):
        try:
            req = urllib.request.Request(self.rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read(); root = ET.fromstring(xml_data); ns = {'atom': 'http://www.w3.org/2005/Atom'}; news_items = []
                entries = root.findall('atom:entry', ns)
                for entry in entries[:6]: 
                    title_elem = entry.find('atom:title', ns); updated_elem = entry.find('atom:updated', ns)
                    if title_elem is not None:
                        title = title_elem.text; date_str = ""
                        if updated_elem is not None: date_str = updated_elem.text[:10]
                        news_items.append((date_str, title))
                self.data_refreshed.emit(news_items)
        except Exception: self.data_refreshed.emit([("ERROR", "COMM-LINK OFFLINE (Check Network)")])

class NotesWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("ENTER MISSION COORDINATES / TRADING NOTES...")
        self.setStyleSheet("background-color: #050505; border: 1px solid #2affea; color: #2affea; font-family: 'Consolas'; font-size: 13px;")
        self.load_notes()
        self.textChanged.connect(self.save_notes)
    def load_notes(self):
        path = get_notes_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding='utf-8') as f: self.setText(f.read())
            except: pass
    def save_notes(self):
        try:
            with open(get_notes_path(), "w", encoding='utf-8') as f: f.write(self.toPlainText())
        except Exception: pass

class ActionOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0; self.triggered = False; self.active = False; self.color = QColor(255, 0, 0); self.text_main = "ACTION"; self.stripe_offset = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True); self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True); self.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.show()
    def set_config(self, color, text): self.color = color; self.text_main = text
    def set_state(self, active, progress=0.0, triggered=False):
        self.active = active; self.progress = progress; self.triggered = triggered
        if active:
            self.stripe_offset += 2.0
            if self.stripe_offset > 60: self.stripe_offset = 0
        self.update() 
    def paintEvent(self, event):
        if not self.active: return
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing); w, h = self.width(), self.height(); cx, cy = w / 2, h / 2
        painter.setBrush(QColor(0, 0, 0, 180)); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(int(cx-150), int(cy-150), 300, 300)
        rect = QRectF(cx-120, cy-120, 240, 240); pen_track = QPen(QColor(50, 50, 50, 200), 15); painter.setPen(pen_track); painter.drawEllipse(rect)
        prog_color = self.color.lighter(150) if self.triggered else self.color
        pen_prog = QPen(prog_color, 15); pen_prog.setCapStyle(Qt.PenCapStyle.RoundCap); painter.setPen(pen_prog); span_angle = int(-360 * self.progress * 16); painter.drawArc(rect, 90 * 16, span_angle)
        painter.setPen(QColor(255, 255, 255)); font = painter.font(); font.setPointSize(24 if self.triggered else 18); font.setBold(True); font.setFamily("Verdana"); painter.setFont(font)
        txt = f"{self.text_main}\nENGAGED" if self.triggered else f"{self.text_main}\n{int(self.progress*100)}%"; painter.drawText(QRectF(cx-150, cy-150, 300, 300), Qt.AlignmentFlag.AlignCenter, txt)
        bar_height = 60; stripe_width = 30
        def draw_caution_tape(rect_zone):
            painter.save(); painter.setClipRect(rect_zone); bg_color = QColor(self.color.red(), self.color.green(), self.color.blue(), 100); painter.fillRect(rect_zone, bg_color)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor(0, 0, 0, 220))
            start_x = -bar_height; current_x = start_x + self.stripe_offset
            while current_x < w + bar_height:
                poly = QPolygonF([QPointF(current_x, rect_zone.top()), QPointF(current_x + stripe_width, rect_zone.top()), QPointF(current_x + stripe_width - bar_height, rect_zone.bottom()), QPointF(current_x - bar_height, rect_zone.bottom())]); painter.drawPolygon(poly); current_x += stripe_width * 2
            painter.setPen(QPen(self.color, 3)); line_y = bar_height if rect_zone.top() == 0 else h - bar_height; painter.drawLine(0, line_y, w, line_y); painter.restore()
        draw_caution_tape(QRect(0, 0, w, bar_height)); draw_caution_tape(QRect(0, h - bar_height, w, bar_height))

class SystemOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.mode = "NONE"; self.logs = []; self.opacity = 1.0; self.shutdown_y_scale = 1.0; self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True); self.show()
    def set_mode(self, mode):
        self.mode = mode
        if mode == "BOOT": self.opacity = 1.0; self.logs = []; self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        elif mode == "SHUTDOWN": self.opacity = 1.0; self.shutdown_y_scale = 1.0; self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.update()
    def add_log(self, text): self.logs.append(text); self.logs.pop(0) if len(self.logs) > 8 else None; self.update()
    def set_opacity(self, val):
        self.opacity = val
        if self.opacity <= 0: self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.update()
    def paintEvent(self, event):
        if self.opacity <= 0 and self.mode == "BOOT": return
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing); w, h = self.width(), self.height()
        if self.mode == "SHUTDOWN":
            painter.setBrush(QColor(0, 0, 0)); painter.setPen(Qt.PenStyle.NoPen); visible_h = h * self.shutdown_y_scale; painter.fillRect(self.rect(), QColor(0, 0, 0))
            if self.shutdown_y_scale < 0.05: painter.setPen(QPen(QColor(255, 255, 255), 2)); painter.drawLine(0, int(h/2), w, int(h/2)); return
            painter.setPen(QColor(255, 50, 50)); font = painter.font(); font.setPointSize(30); font.setBold(True); font.setFamily("Consolas"); painter.setFont(font); painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "SYSTEM DISENGAGED"); return
        if self.mode == "BOOT":
            painter.setOpacity(self.opacity); painter.fillRect(self.rect(), QColor(0, 0, 0)); painter.setPen(QColor(42, 255, 234)); font = painter.font(); font.setPointSize(24); font.setBold(True); font.setFamily("Verdana"); painter.setFont(font); painter.drawText(QRect(0, 100, w, 50), Qt.AlignmentFlag.AlignCenter, "RSI SYSTEMS // BOOTLOADER")
            font.setPointSize(12); font.setFamily("Consolas"); painter.setFont(font); y_pos = h - 200
            for line in self.logs: painter.drawText(50, y_pos, line); y_pos += 20
            bar_w = w - 100; painter.setPen(QPen(QColor(42, 255, 234), 2)); painter.drawRect(50, h - 50, bar_w, 20)
            max_fill = bar_w - 8
            fill_w = int(max_fill * (len(self.logs) / 8.0))
            painter.fillRect(54, h - 46, fill_w, 12, QColor(42, 255, 234))

class SettingsDialog(QDialog):
    def __init__(self, current_config, main_window_ref, parent=None):
        super().__init__(parent); self.main_window = main_window_ref; self.setWindowTitle("SYSTEM CONFIGURATION"); self.resize(600, 900); self.config = current_config; self.listening_btn = None
        self.setStyleSheet("QDialog { background-color: #000000; color: #2affea; font-family: 'Verdana'; border: 2px solid #2affea; } QLabel { color: #2affea; font-weight: bold; } QComboBox { background-color: #000000; color: #2affea; border: 1px solid #2affea; padding: 5px; font-size: 14px; font-weight: bold; } QComboBox::drop-down { border: 0px; } QComboBox QAbstractItemView { background-color: #000000; color: #2affea; selection-background-color: #2affea; selection-color: #000000; border: 1px solid #2affea; outline: none; } QLineEdit { background: #001111; color: #aaaaaa; border: 1px solid #2affea; padding: 5px; }")
        layout = QVBoxLayout(self)
        path_frame = QFrame(); path_frame.setStyleSheet("border: 1px solid #444444; margin-bottom: 10px; padding: 5px;")
        pl = QVBoxLayout(path_frame)
        pl.addWidget(QLabel("DATA STORAGE PATH"))
        self.path_display = QLineEdit(CURRENT_DATA_DIR)
        self.path_display.setReadOnly(True)
        pl.addWidget(self.path_display)
        btn_change_path = QPushButton("MOVE DATA FOLDER")
        btn_change_path.setStyleSheet("background-color: #222222; color: #2affea; font-weight: bold;")
        btn_change_path.clicked.connect(self.change_data_path)
        pl.addWidget(btn_change_path)
        layout.addWidget(path_frame)
        screen_frame = QFrame(); screen_frame.setStyleSheet("border: 1px solid #2affea; margin-bottom: 10px;"); sl = QVBoxLayout(screen_frame); sl.addWidget(QLabel("DISPLAY OUTPUT SELECTION")); self.screen_combo = QComboBox()
        for i, s in enumerate(QApplication.screens()): self.screen_combo.addItem(f"MONITOR {i} - [{s.size().width()}x{s.size().height()}]")
        current_idx = self.config.get("TARGET_SCREEN_INDEX", 1)
        if current_idx < len(QApplication.screens()): self.screen_combo.setCurrentIndex(current_idx)
        sl.addWidget(self.screen_combo); btn_move = QPushButton("TEST & MOVE TO SCREEN"); btn_move.setStyleSheet("background-color: #2affea; color: black; font-weight: bold; padding: 10px;"); btn_move.clicked.connect(self.trigger_move_screen); sl.addWidget(btn_move); layout.addWidget(screen_frame)

        # Drawer position setting
        drawer_frame = QFrame(); drawer_frame.setStyleSheet("border: 1px solid #444444; margin-bottom: 10px; padding: 5px;")
        drawer_layout = QVBoxLayout(drawer_frame)
        drawer_layout.addWidget(QLabel("DRAWER POSITION"))
        self.drawer_pos_combo = QComboBox()
        self.drawer_pos_combo.addItems(["Left", "Right", "Top", "Bottom"])
        self.drawer_pos_combo.setCurrentText(self.config.get("DRAWER_POSITION", "Left"))
        drawer_layout.addWidget(self.drawer_pos_combo)
        layout.addWidget(drawer_frame)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        keybindings_widget = QWidget()
        keybindings_layout = QVBoxLayout(keybindings_widget)
        keybindings_layout.addWidget(QLabel("KEY BINDINGS CONFIGURATION")); scroll = QScrollArea(); scroll.setWidgetResizable(True); content = QWidget(); self.grid = QGridLayout(content); content.setStyleSheet("background-color: #000000;"); row = 0; self.buttons = {}
        for action, key_val in self.config.items():
            if action == "TARGET_SCREEN_INDEX": continue
            if isinstance(key_val, dict) or isinstance(key_val, list): continue
            lbl = QLabel(action); btn = QPushButton(str(key_val).upper()); btn.setProperty("action", action); btn.setStyleSheet("border: 1px solid #2affea; padding: 5px; background: #002222; color: #2affea;"); btn.clicked.connect(lambda ch, b=btn: self.start_list(b)); self.grid.addWidget(lbl, row, 0); self.grid.addWidget(btn, row, 1); self.buttons[action] = btn; row += 1
        scroll.setWidget(content)
        keybindings_layout.addWidget(scroll)
        self.tabs.addTab(keybindings_widget, "Key Bindings")
        modules_config_widget = QWidget()
        self.modules_layout = QVBoxLayout(modules_config_widget)
        self.modules_layout.addWidget(QLabel("Team Roles Configuration"))
        self.team_roles_list = QListWidget()
        self.modules_layout.addWidget(self.team_roles_list)
        self.current_team_roles = self.config.get("TEAM_ROLES", ["Commander", "Pilot", "Gunner", "Engineer"])
        self.team_roles_list.addItems(self.current_team_roles)
        role_input_layout = QHBoxLayout()
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("New role name...")
        role_input_layout.addWidget(self.role_input)
        add_role_btn = QPushButton("Add Role")
        add_role_btn.clicked.connect(self.add_team_role)
        role_input_layout.addWidget(add_role_btn)
        remove_role_btn = QPushButton("Remove Selected Role")
        remove_role_btn.clicked.connect(self.remove_team_role)
        role_input_layout.addWidget(remove_role_btn)
        self.modules_layout.addLayout(role_input_layout)
        self.modules_layout.addSpacing(20)
        self.modules_layout.addWidget(QLabel("RSS Feed URL"))
        self.rss_url_input = QLineEdit()
        current_rss_url = self.config.get("RSS_URL", "https://leonick.se/feeds/rsi/atom")
        self.rss_url_input.setText(current_rss_url)
        self.modules_layout.addWidget(self.rss_url_input)
        self.tabs.addTab(modules_config_widget, "Modules Configuration")
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("RESET DEFAULTS")
        reset_btn.setStyleSheet("background-color: #550000; color: #ffaaaa; padding: 10px; font-weight: bold; margin-top: 10px; border: 1px solid #ff5555;")
        reset_btn.clicked.connect(self.reset_defaults)
        save = QPushButton("SAVE CONFIG"); save.clicked.connect(self.save_and_exit); save.setStyleSheet("background-color: #2affea; color: black; padding: 10px; font-weight: bold; margin-top: 10px;")
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)
    def add_team_role(self):
        new_role = self.role_input.text()
        if new_role and new_role not in self.current_team_roles:
            self.current_team_roles.append(new_role)
            self.team_roles_list.addItem(new_role)
            self.role_input.clear()
    def remove_team_role(self):
        selected_items = self.team_roles_list.selectedItems()
        if not selected_items: return
        for item in selected_items:
            role_to_remove = item.text()
            if role_to_remove in self.current_team_roles:
                self.current_team_roles.remove(role_to_remove)
            self.team_roles_list.takeItem(self.team_roles_list.row(item))
    def change_data_path(self):
        global CURRENT_DATA_DIR
        new_dir = QFileDialog.getExistingDirectory(self, "Select New Data Folder", CURRENT_DATA_DIR)
        if new_dir and new_dir != CURRENT_DATA_DIR:
            try:
                old_conf = os.path.join(CURRENT_DATA_DIR, CONFIG_FILENAME)
                old_notes = os.path.join(CURRENT_DATA_DIR, NOTES_FILENAME)
                new_conf = os.path.join(new_dir, CONFIG_FILENAME)
                new_notes = os.path.join(new_dir, NOTES_FILENAME)
                if os.path.exists(old_conf): shutil.move(old_conf, new_conf)
                if os.path.exists(old_notes): shutil.move(old_notes, new_notes)
                CURRENT_DATA_DIR = new_dir
                update_location_map(new_dir)
                self.path_display.setText(new_dir)
                QMessageBox.information(self, "Success", "Data folder moved successfully!")
                self.main_window.notes_widget.load_notes()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to move files: {e}")
    def reset_defaults(self):
        for key, value in DEFAULT_CONFIG.items():
            if key != "TARGET_SCREEN_INDEX": 
                self.config[key] = value
        for action, btn in self.buttons.items():
            if action in self.config:
                btn.setText(str(self.config[action]).upper())
    def trigger_move_screen(self): idx = self.screen_combo.currentIndex(); self.main_window.switch_screen(idx); self.config["TARGET_SCREEN_INDEX"] = idx
    def save_and_exit(self):
        self.config["TARGET_SCREEN_INDEX"] = self.screen_combo.currentIndex()
        self.config["TEAM_ROLES"] = self.current_team_roles
        self.config["RSS_URL"] = self.rss_url_input.text()
        self.config["DRAWER_POSITION"] = self.drawer_pos_combo.currentText()
        self.accept()
    def start_list(self, btn): self.listening_btn = btn; btn.setText("..."); self.grabKeyboard()
    def keyPressEvent(self, event):
        if self.listening_btn:
            k = event.text().lower() if event.text() else "unknown"
            if event.key() == Qt.Key.Key_Up: k="up"
            elif event.key() == Qt.Key.Key_Down: k="down"
            elif event.key() == Qt.Key.Key_Left: k="left"
            elif event.key() == Qt.Key.Key_Right: k="right"
            elif event.key() == Qt.Key.Key_Insert: k="insert"
            elif event.key() >= Qt.Key.Key_F1 and event.key() <= Qt.Key.Key_F12: k=f"f{event.key()-Qt.Key.Key_F1+1}"
            self.config[self.listening_btn.property("action")] = k; self.listening_btn.setText(k.upper()); self.releaseKeyboard(); self.listening_btn = None
        else: super().keyPressEvent(event)

class SC_ControlDeck(QMainWindow):
    def __init__(self):
        super().__init__()
        self.keyboard = Controller()
        self.config = load_config()
        self.telemetry_tick_count = 0
        self.setWindowTitle("RSI MFD")
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.hold_active_mode = None; self.hold_triggered = False; self.hold_progress = 0.0
        self.hold_timer = QTimer(); self.hold_timer.setInterval(16); self.hold_timer.timeout.connect(self.update_hold_sequence) 
        self.hold_grace_timer = QTimer(); self.hold_grace_timer.setInterval(200); self.hold_grace_timer.setSingleShot(True); self.hold_grace_timer.timeout.connect(self.finalize_hold_stop)
        self.rss_worker = RSSWorker(self.config.get("RSS_URL", DEFAULT_CONFIG["RSS_URL"]))
        self.rss_worker.data_refreshed.connect(self.update_rss_display)
        self.rss_refresh_timer = QTimer()
        self.rss_refresh_timer.setInterval(15 * 60 * 1000) 
        self.rss_refresh_timer.timeout.connect(self.rss_worker.start)
        # Main layout setup
        main_widget = QWidget()
        self.global_layout = QVBoxLayout(main_widget)
        self.global_layout.setContentsMargins(10, 10, 10, 10)
        self.global_layout.setSpacing(5)

        self.create_header()

        # New main layout with a dynamic layout for the drawer and the grid
        self.main_content_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.main_content_layout.setSpacing(0)
        self.main_content_layout.setContentsMargins(0, 0, 0, 0)

        # Create the drawer panel (it will be configured and placed by setup_drawer_layout)
        self.drawer_frame = QFrame()
        self.drawer_frame.setObjectName("drawer_frame")
        drawer_layout = QVBoxLayout(self.drawer_frame)
        drawer_layout.setContentsMargins(5, 5, 5, 5)

        self.module_list = QListWidget()
        self.module_list.setDragEnabled(True)
        drawer_layout.addWidget(self.module_list)

        # Create the drawer toggle button
        self.drawer_toggle_btn = QPushButton()
        self.drawer_toggle_btn.setObjectName("drawer_toggle_btn")
        self.drawer_toggle_btn.clicked.connect(self.toggle_drawer)
        self.is_drawer_open = True

        # Grid widget setup
        self.modules = self.create_all_modules()
        self.grid_widget = GridWidget(self.modules, self)

        # Initial setup of the drawer layout
        self.setup_drawer_layout()

        self.global_layout.addLayout(self.main_content_layout, 1) # Add with stretch factor

        self.setup_modules()
        self.create_footer()
        self.action_overlay = ActionOverlay(self); self.action_overlay.resize(self.size()); self.action_overlay.raise_()
        self.sys_overlay = SystemOverlay(self); self.sys_overlay.resize(self.size()); self.sys_overlay.raise_()
        self.timer = QTimer(); self.timer.timeout.connect(self.update_telemetry); self.timer.start(1000)
        self.apply_styles()
        QTimer.singleShot(100, self.start_boot_sequence)
        QTimer.singleShot(2000, self.rss_worker.start)
    def resizeEvent(self, event):
        if hasattr(self, 'action_overlay'): self.action_overlay.resize(self.size()); self.action_overlay.raise_()
        if hasattr(self, 'sys_overlay'): self.sys_overlay.resize(self.size()); self.sys_overlay.raise_()
        super().resizeEvent(event)

    def setup_drawer_layout(self):
        # Clear the existing layout
        if self.main_content_layout.count() > 0:
            for i in reversed(range(self.main_content_layout.count())):
                self.main_content_layout.itemAt(i).widget().setParent(None)

        pos = self.config.get("DRAWER_POSITION", "Left")

        if pos in ["Left", "Right"]:
            self.main_content_layout.setDirection(QBoxLayout.Direction.LeftToRight if pos == "Left" else QBoxLayout.Direction.RightToLeft)
            self.drawer_frame.setFixedWidth(200)
            self.drawer_frame.setFixedHeight(9999) # Set a large value to allow vertical stretch
            self.drawer_toggle_btn.setFixedSize(20, 60)
            self.drawer_toggle_btn.setText("<" if self.is_drawer_open else ">")
        else: # Top, Bottom
            self.main_content_layout.setDirection(QBoxLayout.Direction.TopToBottom if pos == "Top" else QBoxLayout.Direction.BottomToTop)
            self.drawer_frame.setFixedHeight(200)
            self.drawer_frame.setFixedWidth(9999)
            self.drawer_toggle_btn.setFixedSize(60, 20)
            self.drawer_toggle_btn.setText("^" if self.is_drawer_open else "v")

        # Add widgets in the correct order based on position
        if pos == "Left":
            self.main_content_layout.addWidget(self.drawer_frame)
            self.main_content_layout.addWidget(self.drawer_toggle_btn)
            self.main_content_layout.addWidget(self.grid_widget)
        elif pos == "Right":
            self.main_content_layout.addWidget(self.grid_widget)
            self.main_content_layout.addWidget(self.drawer_toggle_btn)
            self.main_content_layout.addWidget(self.drawer_frame)
        elif pos == "Top":
            self.main_content_layout.addWidget(self.drawer_frame)
            self.main_content_layout.addWidget(self.drawer_toggle_btn)
            self.main_content_layout.addWidget(self.grid_widget)
        else: # Bottom
            self.main_content_layout.addWidget(self.grid_widget)
            self.main_content_layout.addWidget(self.drawer_toggle_btn)
            self.main_content_layout.addWidget(self.drawer_frame)

        # Make the grid widget stretch to fill the available space
        if pos in ["Left", "Top"]:
            self.main_content_layout.setStretch(2, 1)
        else: # Right, Bottom
            self.main_content_layout.setStretch(0, 1)


    def create_all_modules(self):
        return {
            "flight_systems": self.create_systems_panel(),
            "shield_array": self.create_shield_facing_panel(),
            "power_distribution": self.create_power_increments_panel(),
            "telemetry": self.create_telemetry_panel(),
            "calculator": self.create_calculator_panel(),
            "auec_calculator": self.create_auec_calculator_panel(),
            "team_management": self.create_team_management_panel()
        }

    def setup_modules(self):
        layout_config = self.config.get("MODULE_LAYOUT")

        modules_on_grid = []

        # Load layout from config if it exists
        if layout_config:
            for module_id, pos in layout_config.items():
                if module_id in self.modules:
                    self.grid_widget.add_module(self.modules[module_id], pos['row'], pos['col'])
                    modules_on_grid.append(module_id)
        else:
            default_grid_modules = ["flight_systems", "shield_array", "power_distribution", "telemetry"]
            for i, module_id in enumerate(default_grid_modules):
                self.grid_widget.add_module(self.modules[module_id], 0, i)
                modules_on_grid.append(module_id)

        for module_id, module_widget in self.modules.items():
            if module_id not in modules_on_grid:
                item = QListWidgetItem(module_id)
                item.setData(Qt.ItemDataRole.UserRole, module_id) # Store the ID in the item
                self.module_list.addItem(item)
                module_widget.hide()
    def cleanup_background_tasks(self):
        # Stop all running timers and threads to prevent RuntimeError on shutdown
        self.timer.stop()
        self.rss_refresh_timer.stop()
        self.hold_timer.stop()
        if self.rss_worker.isRunning():
            self.rss_worker.quit()
            self.rss_worker.wait()

    def closeEvent(self, event):
        self.cleanup_background_tasks()

        # Save the layout of modules currently on the grid
        layout_config = {}
        for i in range(self.grid_widget.layout.count()):
            widget = self.grid_widget.layout.itemAt(i).widget()
            if isinstance(widget, DraggableModule):
                pos = self.grid_widget.layout.getItemPosition(i)
                layout_config[widget.module_id] = {"row": pos[0], "col": pos[1]}
        self.config["MODULE_LAYOUT"] = layout_config
        save_config(self.config)
        super().closeEvent(event)
    def switch_screen(self, screen_index):
        screens = QApplication.screens()
        if screen_index < len(screens): target_screen = screens[screen_index]; self.showNormal(); self.windowHandle().setScreen(target_screen); self.move(target_screen.geometry().x(), target_screen.geometry().y()); self.showFullScreen()
    def update_rss_display(self, items):
        try:
            if not hasattr(self, 'rss_list') or not self.rss_list:
                return
            self.rss_list.clear()
            html = ""
            for date, title in items:
                if date == "ERROR": html += f'<div style="margin-bottom:5px;"><span style="color:#ff5555;">[OFFLINE]</span> {title}</div>'
                else: html += f'<div style="margin-bottom:8px;"><span style="color:#2affea; font-weight:bold;">[{date}]</span><br/><span style="color:#eeeeee;">{title}</span></div>'
            self.rss_list.setHtml(html)
        except RuntimeError as e:
            print(f"Error in update_rss_display: {e}")
    def start_boot_sequence(self): self.sys_overlay.set_mode("BOOT"); self.boot_step = 0; self.boot_timer = QTimer(); self.boot_timer.setInterval(200); self.boot_timer.timeout.connect(self.update_boot); self.boot_timer.start()
    def update_boot(self):
        try:
            if self.boot_step < len(BOOT_SEQUENCE_LOGS): self.sys_overlay.add_log(BOOT_SEQUENCE_LOGS[self.boot_step]); self.boot_step += 1
            else: self.boot_timer.stop(); self.fade_timer = QTimer(); self.fade_timer.setInterval(50); self.fade_timer.timeout.connect(self.fade_out_boot); self.fade_timer.start()
        except RuntimeError as e:
            print(f"Error in update_boot: {e}")
    def fade_out_boot(self):
        try:
            op = self.sys_overlay.opacity - 0.05
            if op <= 0: op = 0; self.fade_timer.stop(); self.sys_overlay.set_opacity(0)
            else: self.sys_overlay.set_opacity(op)
        except RuntimeError as e:
            print(f"Error in fade_out_boot: {e}")
    def start_shutdown_sequence(self):
        self.cleanup_background_tasks()
        self.sys_overlay.set_mode("SHUTDOWN")
        self.shutdown_timer = QTimer()
        self.shutdown_timer.setInterval(20)
        self.shutdown_timer.timeout.connect(self.update_shutdown)
        self.shutdown_timer.start()
    def update_shutdown(self):
        try:
            scale = self.sys_overlay.shutdown_y_scale - 0.02
            if scale <= 0: scale = 0; self.shutdown_timer.stop(); self.close()
            self.sys_overlay.shutdown_y_scale = scale; self.sys_overlay.update()
        except RuntimeError as e:
            print(f"Error in update_shutdown: {e}")
    def open_settings(self):
        dlg = SettingsDialog(self.config, self, self)
        if dlg.exec():
            self.config = dlg.config
            save_config(self.config)
            self.setup_drawer_layout() # Re-apply the layout based on new settings
            if hasattr(self, 'team_management_widget'):
                new_roles = self.config.get("TEAM_ROLES", [])
                roles_dict = {role: "Unassigned" for role in new_roles}
                self.team_management_widget.set_roles(roles_dict)
            new_rss_url = self.config.get("RSS_URL", DEFAULT_CONFIG["RSS_URL"])
            if self.rss_worker.rss_url != new_rss_url:
                self.rss_worker.rss_url = new_rss_url
                self.rss_worker.start()

    def toggle_drawer(self):
        try:
            pos = self.config.get("DRAWER_POSITION", "Left")

            if pos in ["Left", "Right"]:
                prop = b"minimumWidth"
                start_val = self.drawer_frame.width()
                end_val = 0 if self.is_drawer_open else 200
                open_char, close_char = ("<", ">") if pos == "Left" else (">", "<")
            else: # Top, Bottom
                prop = b"minimumHeight"
                start_val = self.drawer_frame.height()
                end_val = 0 if self.is_drawer_open else 200
                open_char, close_char = ("^", "v") if pos == "Top" else ("v", "^")

            self.animation = QPropertyAnimation(self.drawer_frame, prop)
            self.animation.setDuration(300)
            self.animation.setStartValue(start_val)
            self.animation.setEndValue(end_val)
            self.animation.start()

            self.is_drawer_open = not self.is_drawer_open
            self.drawer_toggle_btn.setText(close_char if self.is_drawer_open else open_char)
        except RuntimeError as e:
            print(f"Error in toggle_drawer: {e}")

    def start_hold(self, mode):
        if self.hold_active_mode != mode:
            self.hold_active_mode = mode; self.hold_triggered = False; self.hold_progress = 0.0
            color = QColor(255, 0, 0) if mode == "EJECT" else QColor(0, 255, 0)
            text = "EJECTING" if mode == "EJECT" else "AUTO-LAND"
            self.action_overlay.set_config(color, text)
        if self.hold_grace_timer.isActive(): self.hold_grace_timer.stop(); return
        self.action_overlay.set_state(True, self.hold_progress, self.hold_triggered); self.hold_timer.start(); self.command_log_widget.add_log_entry(f"SYSTEM: {mode} SEQUENCE INITIATED...", is_user_action=True)
    def stop_hold(self): self.hold_grace_timer.start()
    def finalize_hold_stop(self):
        self.hold_timer.stop(); self.action_overlay.set_state(False)
        if self.hold_triggered:
            if self.hold_active_mode == "EJECT": k = get_key_object(self.config["EXIT_SEAT"]); self.keyboard.release(k); self.command_log_widget.add_log_entry("EJECT: RELEASED", is_user_action=True)
        else: self.command_log_widget.add_log_entry(f"SYSTEM: {self.hold_active_mode} ABORTED", is_user_action=True)
        self.hold_active_mode = None
    def update_hold_sequence(self):
        try:
            self.hold_progress += (0.016 / 2.0)
            if self.hold_progress >= 1.0: self.hold_progress = 1.0; self.trigger_hold_action() if not self.hold_triggered else None; self.hold_triggered = True
            self.action_overlay.set_state(True, self.hold_progress, self.hold_triggered)
        except RuntimeError as e:
            print(f"Error in update_hold_sequence: {e}")
    def trigger_hold_action(self):
        if self.hold_active_mode == "EJECT": k = get_key_object(self.config["EXIT_SEAT"]); self.keyboard.press(k); self.command_log_widget.add_log_entry("WARNING: CANOPY JETTISONED", is_user_action=True)
        elif self.hold_active_mode == "AUTOLAND": k = get_key_object(self.config["LANDING"]); self.command_log_widget.add_log_entry("FLIGHT: AUTO-LAND ENGAGED", is_user_action=True); self.keyboard.press(k); QTimer.singleShot(3000, lambda: self.finish_auto_land_macro(k))
    def finish_auto_land_macro(self, k): self.keyboard.release(k); self.command_log_widget.add_log_entry("FLIGHT: AUTO-LAND SIGNAL COMPLETE", is_user_action=True)
    def send_action(self, action_name, custom_log_text=None, silent=False):
        k = get_key_object(self.config.get(action_name))
        if k: self.keyboard.press(k); self.keyboard.release(k); self.command_log_widget.add_log_entry(custom_log_text if custom_log_text else f"CMD: {action_name}", is_user_action=True) if not silent else None
    def call_atc(self): k = get_key_object(self.config.get("ATC_KEY_BASE", "n")); self.command_log_widget.add_log_entry("COMMS: HAILING LANDING SERVICES...", is_user_action=True); self.keyboard.press(Key.alt_l); self.keyboard.press(k); time.sleep(0.1); self.keyboard.release(k); self.keyboard.release(Key.alt_l); self.command_log_widget.add_log_entry("COMMS: REQUEST SENT", is_user_action=True)
    def create_header(self): frame = QFrame(); frame.setObjectName("header_frame"); frame.setMaximumHeight(60); layout = QHBoxLayout(frame); lbl_brand = QLabel("RSI SYSTEMS // CONSTELLATION CLASS"); lbl_brand.setStyleSheet("font-size: 20px; font-weight: bold; letter-spacing: 3px; color: #2affea;"); lbl_id = QLabel("UEE ID: 948-Alpha-7"); lbl_id.setStyleSheet("color: #aaaaaa; font-family: 'Consolas';"); layout.addWidget(lbl_brand); layout.addStretch(); layout.addWidget(lbl_id); self.global_layout.addWidget(frame)
    def create_footer(self): frame = QFrame(); frame.setObjectName("header_frame"); frame.setMaximumHeight(40); layout = QHBoxLayout(frame); self.status_lbl = QLabel("SYSTEM STATUS: ONLINE"); self.status_lbl.setStyleSheet("color: #44ff44; font-weight: bold;"); layout.addWidget(self.status_lbl); layout.addStretch(); layout.addWidget(QLabel("VERSION 33.1 [DATA PATH FIX]")); self.global_layout.addWidget(frame)
    def create_telemetry_panel(self):
        module = DraggableModule("telemetry")
        layout = QVBoxLayout(module)
        self.hardware_monitor_widget = HardwareMonitorWidget()
        layout.addWidget(self.hardware_monitor_widget)
        layout.addSpacing(20)
        self.command_log_widget = CommandLogWidget()
        layout.addWidget(self.command_log_widget)
        layout.addStretch()
        self.clock_widget = ClockWidget()
        layout.addWidget(self.clock_widget)
        h_btn = QVBoxLayout(); h_btn.setSpacing(10); sett=QPushButton("SYSTEM CONFIG"); sett.setStyleSheet("font-size: 18px; border: 2px solid #888888; color: #cccccc;"); sett.setMinimumHeight(80); sett.clicked.connect(self.open_settings)
        quit_btn=QPushButton("DISCONNECT"); quit_btn.setObjectName("close_btn"); quit_btn.setMinimumHeight(80); quit_btn.setStyleSheet("font-size: 18px; background-color: #330000; color: #ff5555; border: 2px solid #ff0000;"); quit_btn.clicked.connect(self.start_shutdown_sequence); h_btn.addWidget(sett); h_btn.addWidget(quit_btn); layout.addLayout(h_btn)
        return module
    def update_telemetry(self):
        try:
            self.telemetry_tick_count += 1
            if self.telemetry_tick_count % 300 == 0 or self.telemetry_tick_count == 1:
                game_running = False
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'] == "StarCitizen.exe":
                            game_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass

                if not hasattr(self, 'status_lbl') or not self.status_lbl:
                    return

                if game_running:
                    self.status_lbl.setText("SYSTEM STATUS: ONLINE")
                    self.status_lbl.setStyleSheet("color: #44ff44; font-weight: bold;")
                else:
                    self.status_lbl.setText("SYSTEM STATUS: OFFLINE")
                    self.status_lbl.setStyleSheet("color: #44ff44; font-weight: bold;")
        except RuntimeError as e:
            print(f"Error in update_telemetry: {e}")
    def create_shield_facing_panel(self):
        module = DraggableModule("shield_array")
        layout = QVBoxLayout(module)
        shield_widget = ShieldArrayWidget(self.send_action)
        layout.addWidget(shield_widget)
        layout.addSpacing(20); layout.addWidget(QLabel("RSI SUB-SPACE COMM-LINK")); self.rss_list = QTextEdit(); self.rss_list.setReadOnly(True); self.rss_list.setObjectName("log_console"); self.rss_list.setStyleSheet("background-color: #050505; border: 1px solid #2affea; color: #2affea; font-family: 'Verdana'; font-size: 11px; padding: 5px;"); layout.addWidget(self.rss_list)
        return module
    def create_calculator_panel(self):
        module = DraggableModule("calculator")
        layout = QVBoxLayout(module)
        calc_widget = CalculatorWidget()
        layout.addWidget(calc_widget)
        return module
    def create_auec_calculator_panel(self):
        module = DraggableModule("auec_calculator")
        layout = QVBoxLayout(module)
        auec_calc_widget = AUECCalculatorWidget()
        layout.addWidget(auec_calc_widget)
        return module
    def create_team_management_panel(self):
        module = DraggableModule("team_management")
        layout = QVBoxLayout(module)
        self.team_management_widget = TeamManagementWidget()
        layout.addWidget(self.team_management_widget)
        return module
    def create_systems_panel(self):
        module = DraggableModule("flight_systems")
        layout = QVBoxLayout(module)
        flight_systems_widget = FlightSystemsWidget(self.send_action, self.start_hold, self.stop_hold, self.call_atc)
        layout.addWidget(flight_systems_widget)
        return module
    def create_power_increments_panel(self):
        module = DraggableModule("power_distribution")
        layout = QVBoxLayout(module)
        self.notes_widget = NotesWidget()
        power_dist_widget = PowerDistributionWidget(self.send_action, self.decrease_power_logic, self.notes_widget)
        layout.addWidget(power_dist_widget)
        return module
    def decrease_power_logic(self, target): self.command_log_widget.add_log_entry(f"REBALANCING: DECREASE {target}", is_user_action=True); self.send_action("SHIELD_POWER", silent=True) if target=="WEAPONS" else None; self.send_action("ENGINE_POWER", silent=True) if target=="WEAPONS" else None; self.send_action("WEAPON_POWER", silent=True) if target=="SHIELDS" else None; self.send_action("ENGINE_POWER", silent=True) if target=="SHIELDS" else None; self.send_action("WEAPON_POWER", silent=True) if target=="ENGINES" else None; self.send_action("SHIELD_POWER", silent=True) if target=="ENGINES" else None
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #000000; }
            QWidget { font-family: 'Verdana'; font-size: 14px; }
            QFrame#panel_frame { background-color: #0a0a0a; border: 1px solid #2affea; border-radius: 0px; border-right: 5px solid #2affea; }
            QFrame#header_frame { background-color: #0a0a0a; border-bottom: 2px solid #2affea; }
            QLabel { color: #2affea; font-weight: bold; }
            QLabel#panel_title { font-size: 18px; border-bottom: 1px dashed #2affea; margin-bottom: 15px; padding-bottom: 5px; color: #ffffff;}
            QTextEdit#log_console { background-color: #000000; border: 1px dotted #004400; font-family: 'Consolas'; font-size: 11px; }
            QPushButton { background-color: rgba(42, 255, 234, 0.08); color: #2affea; border: 1px solid #2affea; border-radius: 2px; font-weight: bold; }
            QPushButton:pressed { background-color: #2affea; color: black; }
            QPushButton:checked { background-color: #2affea; color: black; border: 2px solid #ffffff; }
            QPushButton:hover { background-color: rgba(42, 255, 234, 0.2); border: 1px solid white; }
            QPushButton#btn_shd_reset { color: #ffaa00; border: 2px solid #ffaa00; font-size: 16px; }
            QPushButton#btn_shd_reset:pressed { background-color: #ffaa00; color: black; }
            QPushButton#btn_shield_inc, QPushButton#btn_shield_dec { font-size: 24px; border: 1px solid #4444ff; color: #4444ff; background-color: rgba(0,0,50,0.3); }
            QPushButton#btn_weapons_inc, QPushButton#btn_weapons_dec { color: #ff4444; border-color: #ff4444; font-size: 20px; }
            QPushButton#btn_engines_inc, QPushButton#btn_engines_dec { color: #44ff44; border-color: #44ff44; font-size: 20px; }
            QPushButton#btn_shields_inc, QPushButton#btn_shields_dec { color: #4444ff; border-color: #4444ff; font-size: 20px; }
            QPushButton#close_btn { background-color: #220000; color: #aa0000; border: 1px solid #550000; }
            QPushButton#btn_danger { color: #ffaa00; border: 1px dashed #ffaa00; }
            QProgressBar { border: 1px solid #334455; background-color: #000000; text-align: center; color: white; }
            QFrame#drawer_frame { background-color: #050505; border-right: 2px solid #2affea; }
            QPushButton#drawer_toggle_btn {
                background-color: #0a0a0a;
                border: 1px solid #2affea;
                border-left: none;
                color: #2affea;
                font-size: 16px;
                font-weight: bold;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            QPushButton#drawer_toggle_btn:hover { background-color: rgba(42, 255, 234, 0.2); }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SC_ControlDeck()
    saved_screen_idx = window.config.get("TARGET_SCREEN_INDEX", 1)
    screens = app.screens()
    if saved_screen_idx < len(screens): window.switch_screen(saved_screen_idx)
    else: window.show()
    sys.exit(app.exec())
