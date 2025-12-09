import sys
import psutil
import json
import os
import random
import time
import urllib.request
import shutil  # Pour déplacer les fichiers
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QGridLayout, 
                             QWidget, QLabel, QVBoxLayout, QFrame, QHBoxLayout, 
                             QDialog, QScrollArea, QProgressBar, QTextEdit, QComboBox,
                             QLineEdit, QFileDialog, QMessageBox) # Nouveaux widgets
from PyQt6.QtCore import Qt, QTimer, QTime, QRectF, QEvent, QPointF, QRect, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QBrush, QPainter, QPen, QPainterPath, QLinearGradient, QPolygonF, QFont, QRadialGradient
from pynput.keyboard import Controller, Key

# --- GESTION DES CHEMINS (PATH SYSTEM) ---
APP_NAME = "RSI_MFD"
# Le dossier "Ancre" qui ne bouge jamais (AppData/Local/RSI_MFD)
FIXED_APPDATA_DIR = os.path.join(os.getenv('LOCALAPPDATA'), APP_NAME)
# Le fichier qui sait où sont les données
LOCATION_MAP_FILE = os.path.join(FIXED_APPDATA_DIR, "storage_location.json")

# Noms des fichiers
CONFIG_FILENAME = "sc_mfd_config.json"
NOTES_FILENAME = "sc_mfd_notes.txt"

def ensure_initial_setup():
    """Initialise les dossiers et migre les fichiers si nécessaire."""
    if not os.path.exists(FIXED_APPDATA_DIR):
        os.makedirs(FIXED_APPDATA_DIR)

    # 1. Déterminer où sont les données actuelles
    current_data_path = FIXED_APPDATA_DIR # Par défaut
    
    if os.path.exists(LOCATION_MAP_FILE):
        try:
            with open(LOCATION_MAP_FILE, 'r') as f:
                data = json.load(f)
                stored_path = data.get("data_path")
                if stored_path and os.path.exists(stored_path):
                    current_data_path = stored_path
        except: pass
    else:
        # Création du fichier de map par défaut
        update_location_map(FIXED_APPDATA_DIR)

    # 2. Migration : Si des fichiers sont à côté du script (ancienne version), on les import
    local_config = os.path.join(os.getcwd(), CONFIG_FILENAME)
    local_notes = os.path.join(os.getcwd(), NOTES_FILENAME)
    
    target_config = os.path.join(current_data_path, CONFIG_FILENAME)
    target_notes = os.path.join(current_data_path, NOTES_FILENAME)

    if os.path.exists(local_config) and not os.path.exists(target_config):
        try: shutil.move(local_config, target_config); print("Migrated config to AppData")
        except Exception as e: print(f"Migration error: {e}")
            
    if os.path.exists(local_notes) and not os.path.exists(target_notes):
        try: shutil.move(local_notes, target_notes); print("Migrated notes to AppData")
        except Exception as e: print(f"Migration error: {e}")

    return current_data_path

def update_location_map(new_path):
    """Met à jour le fichier pointeur dans AppData."""
    try:
        with open(LOCATION_MAP_FILE, 'w') as f:
            json.dump({"data_path": new_path}, f)
    except Exception as e: print(f"Error updating map: {e}")

# Initialisation globale du chemin
CURRENT_DATA_DIR = ensure_initial_setup()

# --- CONFIGURATION FICHIER ---
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
    "ATC_KEY_BASE": "n"
}

SCI_FI_LOGS = [
    "Scanning local grid...", "Quantum fuel injection: NOMINAL", "Shield harmonics: 98%",
    "Coolant pressure: STABLE", "Incoming transmission blocked", "UEE Signature verified",
    "Radar sweep complete", "Thruster calibration...", "Weapon capacitors: CHARGING",
    "Life support: ACTIVE", "Gravity generator: 1.0G", "Proxy link established",
    "Data packet received (42kb)", "Background radiation: LOW", "System optimized"
]

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

# --- THREAD RSS WORKER ---
class RSSWorker(QThread):
    data_refreshed = pyqtSignal(list)
    def run(self):
        url = "https://leonick.se/feeds/rsi/atom"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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
        except Exception as e: print(f"RSS Error: {e}"); self.data_refreshed.emit([("ERROR", "COMM-LINK OFFLINE (Check Network)")])

# --- WIDGET NOTES PERSISTANTES ---
class NotesWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("ENTER MISSION COORDINATES / TRADING NOTES...")
        self.setStyleSheet("""
            background-color: #050505; 
            border: 1px solid #2affea; 
            color: #2affea; 
            font-family: 'Consolas'; 
            font-size: 13px;
        """)
        self.load_notes()
        self.textChanged.connect(self.save_notes)

    def load_notes(self):
        path = get_notes_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding='utf-8') as f:
                    self.setText(f.read())
            except: pass

    def save_notes(self):
        try:
            with open(get_notes_path(), "w", encoding='utf-8') as f:
                f.write(self.toPlainText())
        except Exception as e:
            print(f"Error saving notes: {e}")

# --- CLASSE BOUTON ROBUSTE ---
class HoldButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.on_press_callback = None
        self.on_release_callback = None
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def event(self, e):
        typ = e.type()
        if typ == QEvent.Type.TouchBegin:
            if self.on_press_callback: self.on_press_callback()
            e.accept(); return True
        elif typ == QEvent.Type.TouchEnd or typ == QEvent.Type.TouchCancel:
            if self.on_release_callback: self.on_release_callback()
            e.accept(); return True
        return super().event(e)
    def mousePressEvent(self, e):
        if self.on_press_callback: self.on_press_callback()
        super().mousePressEvent(e)
    def mouseReleaseEvent(self, e):
        if self.on_release_callback: self.on_release_callback()
        super().mouseReleaseEvent(e)

# --- OVERLAYS ---
class ActionOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0; self.triggered = False; self.active = False; self.color = QColor(255, 0, 0); self.text_main = "ACTION"; self.stripe_offset = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True); self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True); self.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.show()
    def set_config(self, color, text): self.color = color; self.text_main = text
    def set_state(self, active, progress=0.0, triggered=False):
        self.active = active; self.progress = progress; self.triggered = triggered
        if active:
            self.stripe_offset += 2.0; 
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
        self.opacity = val; 
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
            bar_w = w - 100; painter.setPen(QPen(QColor(42, 255, 234), 2)); painter.drawRect(50, h - 50, bar_w, 20); 
            max_fill = bar_w - 8 
            fill_w = int(max_fill * (len(self.logs) / 8.0)); 
            painter.fillRect(54, h - 46, fill_w, 12, QColor(42, 255, 234))

# --- SETTINGS DIALOG ---
class SettingsDialog(QDialog):
    def __init__(self, current_config, main_window_ref, parent=None):
        super().__init__(parent); self.main_window = main_window_ref; self.setWindowTitle("SYSTEM CONFIGURATION"); self.resize(600, 900); self.config = current_config; self.listening_btn = None
        self.setStyleSheet("QDialog { background-color: #000000; color: #2affea; font-family: 'Verdana'; border: 2px solid #2affea; } QLabel { color: #2affea; font-weight: bold; } QComboBox { background-color: #000000; color: #2affea; border: 1px solid #2affea; padding: 5px; font-size: 14px; font-weight: bold; } QComboBox::drop-down { border: 0px; } QComboBox QAbstractItemView { background-color: #000000; color: #2affea; selection-background-color: #2affea; selection-color: #000000; border: 1px solid #2affea; outline: none; } QLineEdit { background: #001111; color: #aaaaaa; border: 1px solid #2affea; padding: 5px; }")
        
        layout = QVBoxLayout(self)

        # --- PATH MANAGEMENT ---
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
        # -----------------------

        screen_frame = QFrame(); screen_frame.setStyleSheet("border: 1px solid #2affea; margin-bottom: 10px;"); sl = QVBoxLayout(screen_frame); sl.addWidget(QLabel("DISPLAY OUTPUT SELECTION")); self.screen_combo = QComboBox()
        for i, s in enumerate(QApplication.screens()): self.screen_combo.addItem(f"MONITOR {i} - [{s.size().width()}x{s.size().height()}]")
        current_idx = self.config.get("TARGET_SCREEN_INDEX", 1); 
        if current_idx < len(QApplication.screens()): self.screen_combo.setCurrentIndex(current_idx)
        sl.addWidget(self.screen_combo); btn_move = QPushButton("TEST & MOVE TO SCREEN"); btn_move.setStyleSheet("background-color: #2affea; color: black; font-weight: bold; padding: 10px;"); btn_move.clicked.connect(self.trigger_move_screen); sl.addWidget(btn_move); layout.addWidget(screen_frame)
        layout.addWidget(QLabel("KEY BINDINGS CONFIGURATION")); scroll = QScrollArea(); scroll.setWidgetResizable(True); content = QWidget(); self.grid = QGridLayout(content); content.setStyleSheet("background-color: #000000;"); row = 0; self.buttons = {}
        for action, key_val in self.config.items():
            if action == "TARGET_SCREEN_INDEX": continue
            lbl = QLabel(action); btn = QPushButton(str(key_val).upper()); btn.setProperty("action", action); btn.setStyleSheet("border: 1px solid #2affea; padding: 5px; background: #002222; color: #2affea;"); btn.clicked.connect(lambda ch, b=btn: self.start_list(b)); self.grid.addWidget(lbl, row, 0); self.grid.addWidget(btn, row, 1); self.buttons[action] = btn; row += 1
        scroll.setWidget(content); layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("RESET DEFAULTS")
        reset_btn.setStyleSheet("background-color: #550000; color: #ffaaaa; padding: 10px; font-weight: bold; margin-top: 10px; border: 1px solid #ff5555;")
        reset_btn.clicked.connect(self.reset_defaults)
        
        save = QPushButton("SAVE CONFIG"); save.clicked.connect(self.save_and_exit); save.setStyleSheet("background-color: #2affea; color: black; padding: 10px; font-weight: bold; margin-top: 10px;")
        
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(save)
        layout.addLayout(btn_layout)

    def change_data_path(self):
        global CURRENT_DATA_DIR # Déplacé ici pour corriger l'erreur de portée
        
        new_dir = QFileDialog.getExistingDirectory(self, "Select New Data Folder", CURRENT_DATA_DIR)
        if new_dir and new_dir != CURRENT_DATA_DIR:
            try:
                # 1. Déplacer les fichiers existants
                old_conf = os.path.join(CURRENT_DATA_DIR, CONFIG_FILENAME)
                old_notes = os.path.join(CURRENT_DATA_DIR, NOTES_FILENAME)
                
                new_conf = os.path.join(new_dir, CONFIG_FILENAME)
                new_notes = os.path.join(new_dir, NOTES_FILENAME)

                if os.path.exists(old_conf): shutil.move(old_conf, new_conf)
                if os.path.exists(old_notes): shutil.move(old_notes, new_notes)
                
                # 2. Mettre à jour la map globale
                CURRENT_DATA_DIR = new_dir
                update_location_map(new_dir)
                
                # 3. Update UI
                self.path_display.setText(new_dir)
                QMessageBox.information(self, "Success", "Data folder moved successfully!")
                
                # 4. Recharger les notes dans la fenêtre principale si nécessaire
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
    def save_and_exit(self): self.config["TARGET_SCREEN_INDEX"] = self.screen_combo.currentIndex(); self.accept()
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

# --- MAIN WINDOW ---
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

        self.rss_worker = RSSWorker()
        self.rss_worker.data_refreshed.connect(self.update_rss_display)
        self.rss_refresh_timer = QTimer()
        self.rss_refresh_timer.setInterval(15 * 60 * 1000) 
        self.rss_refresh_timer.timeout.connect(self.rss_worker.start)

        main_widget = QWidget(); self.setCentralWidget(main_widget)
        self.global_layout = QVBoxLayout(main_widget); self.global_layout.setContentsMargins(10, 10, 10, 10); self.global_layout.setSpacing(5)
        self.create_header()
        body_frame = QFrame(); self.main_layout = QGridLayout(body_frame); self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(15); self.global_layout.addWidget(body_frame)
        self.create_systems_panel(0, 0); self.create_shield_facing_panel(0, 1); self.create_power_increments_panel(0, 2); self.create_telemetry_panel(0, 3); self.create_footer()
        
        self.action_overlay = ActionOverlay(self); self.action_overlay.resize(self.size()); self.action_overlay.raise_()
        self.sys_overlay = SystemOverlay(self); self.sys_overlay.resize(self.size()); self.sys_overlay.raise_()

        self.timer = QTimer(); self.timer.timeout.connect(self.update_telemetry); self.timer.start(1000)
        self.log_timer = QTimer(); self.log_timer.timeout.connect(self.add_random_log); self.log_timer.start(4000)
        self.apply_styles()
        
        QTimer.singleShot(100, self.start_boot_sequence)
        
        QTimer.singleShot(2000, self.rss_worker.start)

    def resizeEvent(self, event):
        if hasattr(self, 'action_overlay'): self.action_overlay.resize(self.size()); self.action_overlay.raise_()
        if hasattr(self, 'sys_overlay'): self.sys_overlay.resize(self.size()); self.sys_overlay.raise_()
        super().resizeEvent(event)
    def switch_screen(self, screen_index):
        screens = QApplication.screens(); 
        if screen_index < len(screens): target_screen = screens[screen_index]; self.showNormal(); self.windowHandle().setScreen(target_screen); self.move(target_screen.geometry().x(), target_screen.geometry().y()); self.showFullScreen()

    def update_rss_display(self, items):
        if not hasattr(self, 'rss_list'): return
        self.rss_list.clear()
        html = ""
        for date, title in items:
            if date == "ERROR": html += f'<div style="margin-bottom:5px;"><span style="color:#ff5555;">[OFFLINE]</span> {title}</div>'
            else: html += f'<div style="margin-bottom:8px;"><span style="color:#2affea; font-weight:bold;">[{date}]</span><br/><span style="color:#eeeeee;">{title}</span></div>'
        self.rss_list.setHtml(html)

    def start_boot_sequence(self): self.sys_overlay.set_mode("BOOT"); self.boot_step = 0; self.boot_timer = QTimer(); self.boot_timer.setInterval(200); self.boot_timer.timeout.connect(self.update_boot); self.boot_timer.start()
    def update_boot(self):
        if self.boot_step < len(BOOT_SEQUENCE_LOGS): self.sys_overlay.add_log(BOOT_SEQUENCE_LOGS[self.boot_step]); self.boot_step += 1
        else: self.boot_timer.stop(); self.fade_timer = QTimer(); self.fade_timer.setInterval(50); self.fade_timer.timeout.connect(self.fade_out_boot); self.fade_timer.start()
    def fade_out_boot(self):
        op = self.sys_overlay.opacity - 0.05
        if op <= 0: op = 0; self.fade_timer.stop(); self.sys_overlay.set_opacity(0)
        else: self.sys_overlay.set_opacity(op)
    def start_shutdown_sequence(self): self.sys_overlay.set_mode("SHUTDOWN"); self.shutdown_timer = QTimer(); self.shutdown_timer.setInterval(20); self.shutdown_timer.timeout.connect(self.update_shutdown); self.shutdown_timer.start()
    def update_shutdown(self):
        scale = self.sys_overlay.shutdown_y_scale - 0.02
        if scale <= 0: scale = 0; self.shutdown_timer.stop(); QApplication.quit()
        self.sys_overlay.shutdown_y_scale = scale; self.sys_overlay.update()

    def open_settings(self):
        dlg = SettingsDialog(self.config, self, self)
        if dlg.exec():
            self.config = dlg.config
            save_config(self.config)

    def start_hold(self, mode):
        if self.hold_active_mode != mode:
            self.hold_active_mode = mode; self.hold_triggered = False; self.hold_progress = 0.0; 
            color = QColor(255, 0, 0) if mode == "EJECT" else QColor(0, 255, 0)
            text = "EJECTING" if mode == "EJECT" else "AUTO-LAND"
            self.action_overlay.set_config(color, text)
        if self.hold_grace_timer.isActive(): self.hold_grace_timer.stop(); return
        self.action_overlay.set_state(True, self.hold_progress, self.hold_triggered); self.hold_timer.start(); self.add_log_entry(f"SYSTEM: {mode} SEQUENCE INITIATED...", is_user_action=True)
    def stop_hold(self): self.hold_grace_timer.start()
    def finalize_hold_stop(self):
        self.hold_timer.stop(); self.action_overlay.set_state(False)
        if self.hold_triggered:
            if self.hold_active_mode == "EJECT": k = get_key_object(self.config["EXIT_SEAT"]); self.keyboard.release(k); self.add_log_entry("EJECT: RELEASED", is_user_action=True)
        else: self.add_log_entry(f"SYSTEM: {self.hold_active_mode} ABORTED", is_user_action=True)
        self.hold_active_mode = None
    def update_hold_sequence(self):
        self.hold_progress += (0.016 / 2.0)
        if self.hold_progress >= 1.0: self.hold_progress = 1.0; self.trigger_hold_action() if not self.hold_triggered else None; self.hold_triggered = True
        self.action_overlay.set_state(True, self.hold_progress, self.hold_triggered)
    def trigger_hold_action(self):
        if self.hold_active_mode == "EJECT": k = get_key_object(self.config["EXIT_SEAT"]); self.keyboard.press(k); self.add_log_entry("WARNING: CANOPY JETTISONED", is_user_action=True)
        elif self.hold_active_mode == "AUTOLAND": k = get_key_object(self.config["LANDING"]); self.add_log_entry("FLIGHT: AUTO-LAND ENGAGED", is_user_action=True); self.keyboard.press(k); QTimer.singleShot(3000, lambda: self.finish_auto_land_macro(k))
    def finish_auto_land_macro(self, k): self.keyboard.release(k); self.add_log_entry("FLIGHT: AUTO-LAND SIGNAL COMPLETE", is_user_action=True)

    def send_action(self, action_name, custom_log_text=None, silent=False):
        k = get_key_object(self.config.get(action_name)); 
        if k: self.keyboard.press(k); self.keyboard.release(k); self.add_log_entry(custom_log_text if custom_log_text else f"CMD: {action_name}", is_user_action=True) if not silent else None
    def call_atc(self): k = get_key_object(self.config.get("ATC_KEY_BASE", "n")); self.add_log_entry("COMMS: HAILING LANDING SERVICES...", is_user_action=True); self.keyboard.press(Key.alt_l); self.keyboard.press(k); time.sleep(0.1); self.keyboard.release(k); self.keyboard.release(Key.alt_l); self.add_log_entry("COMMS: REQUEST SENT", is_user_action=True)
    def add_log_entry(self, text, is_user_action=False): ts = QTime.currentTime().toString("HH:mm:ss"); fmt = f'<span style="color:#ffffff; font-weight:bold;">[{ts}] > {text}</span>' if is_user_action else f'<span style="color:#00aa00;">[{ts}] > {text}</span>'; self.log_console.append(fmt); sb = self.log_console.verticalScrollBar(); sb.setValue(sb.maximum())
    def add_random_log(self): self.add_log_entry(random.choice(SCI_FI_LOGS), is_user_action=False)

    def create_header(self): frame = QFrame(); frame.setObjectName("header_frame"); frame.setMaximumHeight(60); layout = QHBoxLayout(frame); lbl_brand = QLabel("RSI SYSTEMS // CONSTELLATION CLASS"); lbl_brand.setStyleSheet("font-size: 20px; font-weight: bold; letter-spacing: 3px; color: #2affea;"); lbl_id = QLabel("UEE ID: 948-Alpha-7"); lbl_id.setStyleSheet("color: #aaaaaa; font-family: 'Consolas';"); layout.addWidget(lbl_brand); layout.addStretch(); layout.addWidget(lbl_id); self.global_layout.addWidget(frame)
    def create_footer(self): frame = QFrame(); frame.setObjectName("header_frame"); frame.setMaximumHeight(40); layout = QHBoxLayout(frame); self.status_lbl = QLabel("SYSTEM STATUS: ONLINE"); self.status_lbl.setStyleSheet("color: #44ff44; font-weight: bold;"); layout.addWidget(self.status_lbl); layout.addStretch(); layout.addWidget(QLabel("VERSION 33.1 [DATA PATH FIX]")); self.global_layout.addWidget(frame)
    def create_telemetry_panel(self, row, col):
        frame = QFrame(); frame.setObjectName("panel_frame"); layout = QVBoxLayout(frame); hw = QGridLayout(); layout.addWidget(QLabel("HARDWARE MONITOR"))
        
        self.bar_cpu = QProgressBar(); self.bar_cpu.setFormat("CPU %p%"); self.bar_cpu.setStyleSheet("QProgressBar::chunk { background-color: #2affea; }"); hw.addWidget(QLabel("CPU"), 0, 0); hw.addWidget(self.bar_cpu, 0, 1)
        self.bar_ram = QProgressBar(); self.bar_ram.setFormat("RAM %p%"); self.bar_ram.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }"); hw.addWidget(QLabel("RAM"), 1, 0); hw.addWidget(self.bar_ram, 1, 1)
        self.bar_disk = QProgressBar(); self.bar_disk.setFormat("DISK %p%"); self.bar_disk.setStyleSheet("QProgressBar::chunk { background-color: #ff5555; }"); hw.addWidget(QLabel("DSK"), 2, 0); hw.addWidget(self.bar_disk, 2, 1)
        self.bar_swap = QProgressBar(); self.bar_swap.setFormat("SWAP %p%"); self.bar_swap.setStyleSheet("QProgressBar::chunk { background-color: #aa55ff; }"); hw.addWidget(QLabel("SWP"), 3, 0); hw.addWidget(self.bar_swap, 3, 1)
        
        layout.addLayout(hw); layout.addSpacing(20)
        
        layout.addWidget(QLabel("COMMAND LOGS")); self.log_console = QTextEdit(); self.log_console.setReadOnly(True); self.log_console.setObjectName("log_console"); self.log_console.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); layout.addWidget(self.log_console); layout.addStretch()
        self.time_lbl=QLabel("00:00:00"); self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); self.time_lbl.setStyleSheet("font-size:30px; color:white; font-family:'Consolas'; border: 1px solid #334455; border-radius: 5px; margin-bottom: 10px;"); layout.addWidget(self.time_lbl)
        h_btn = QVBoxLayout(); h_btn.setSpacing(10); sett=QPushButton("SYSTEM CONFIG"); sett.setStyleSheet("font-size: 18px; border: 2px solid #888888; color: #cccccc;"); sett.setMinimumHeight(80); sett.clicked.connect(self.open_settings)
        quit_btn=QPushButton("DISCONNECT"); quit_btn.setObjectName("close_btn"); quit_btn.setMinimumHeight(80); quit_btn.setStyleSheet("font-size: 18px; background-color: #330000; color: #ff5555; border: 2px solid #ff0000;"); quit_btn.clicked.connect(self.start_shutdown_sequence); h_btn.addWidget(sett); h_btn.addWidget(quit_btn); layout.addLayout(h_btn); self.main_layout.addWidget(frame, row, col)
        
    def update_telemetry(self): 
        self.telemetry_tick_count += 1
        self.time_lbl.setText(QTime.currentTime().toString("HH:mm:ss"))
        self.bar_cpu.setValue(int(psutil.cpu_percent()))
        self.bar_ram.setValue(int(psutil.virtual_memory().percent))
        
        if self.telemetry_tick_count % 300 == 0 or self.telemetry_tick_count == 1:
            try: self.bar_disk.setValue(int(psutil.disk_usage('/').percent))
            except: pass
            try: self.bar_swap.setValue(int(psutil.swap_memory().percent))
            except: pass
            
            game_running = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] == "StarCitizen.exe":
                        game_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if game_running:
                self.status_lbl.setText("SYSTEM STATUS: ONLINE")
                self.status_lbl.setStyleSheet("color: #44ff44; font-weight: bold;")
            else:
                self.status_lbl.setText("SYSTEM STATUS: OFFLINE")
                self.status_lbl.setStyleSheet("color: #ff4444; font-weight: bold;")

    def create_shield_facing_panel(self, row, col):
        frame = QFrame(); frame.setObjectName("panel_frame"); layout = QVBoxLayout(frame)
        title = QLabel("SHIELD ARRAY"); title.setObjectName("panel_title"); title.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(title)
        grid = QGridLayout(); grid.setSpacing(10); grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grp_fwd = self.create_shield_group("FRONT", "SHIELD_FWD", "SHIELD_BACK"); grid.addWidget(grp_fwd, 0, 1)
        grp_left = self.create_shield_group("LEFT", "SHIELD_LEFT", "SHIELD_RIGHT"); grid.addWidget(grp_left, 1, 0)
        grp_right = self.create_shield_group("RIGHT", "SHIELD_RIGHT", "SHIELD_LEFT"); grid.addWidget(grp_right, 1, 2)
        grp_back = self.create_shield_group("BACK", "SHIELD_BACK", "SHIELD_FWD"); grid.addWidget(grp_back, 2, 1)
        btn_reset = QPushButton("RST"); btn_reset.setFixedSize(80, 80); btn_reset.setObjectName("btn_shd_reset"); btn_reset.clicked.connect(lambda: self.send_action("SHIELD_RESET", "SHIELD RESET")); btn_reset.setFocusPolicy(Qt.FocusPolicy.NoFocus); grid.addWidget(btn_reset, 1, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(grid)
        layout.addSpacing(20); layout.addWidget(QLabel("RSI SUB-SPACE COMM-LINK")); self.rss_list = QTextEdit(); self.rss_list.setReadOnly(True); self.rss_list.setObjectName("log_console"); self.rss_list.setStyleSheet("background-color: #050505; border: 1px solid #2affea; color: #2affea; font-family: 'Verdana'; font-size: 11px; padding: 5px;"); layout.addWidget(self.rss_list)
        self.main_layout.addWidget(frame, row, col)

    def create_shield_group(self, label, inc, dec):
        w = QFrame(); w.setStyleSheet("background-color: rgba(0,20,40,0.4); border: 1px solid #4444ff; border-radius: 4px;"); l = QVBoxLayout(w); l.setContentsMargins(2,2,2,2); l.setSpacing(2); lbl = QLabel(label); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl.setStyleSheet("color:#aaaaff; font-size:12px; border:none; background:transparent;"); l.addWidget(lbl); h = QHBoxLayout(); h.setSpacing(2); 
        
        bd = QPushButton("-"); bd.setFixedSize(50,50); bd.setObjectName("btn_shield_dec"); bd.setFocusPolicy(Qt.FocusPolicy.NoFocus); bd.clicked.connect(lambda: self.send_action(dec, f"SHIELD {label} (-)")); 
        bi = QPushButton("+"); bi.setFixedSize(50,50); bi.setObjectName("btn_shield_inc"); bi.setFocusPolicy(Qt.FocusPolicy.NoFocus); bi.clicked.connect(lambda: self.send_action(inc, f"SHIELD {label} (+)")); 

        h.addWidget(bd); h.addWidget(bi); l.addLayout(h); return w

    def create_systems_panel(self, row, col):
        frame = QFrame(); frame.setObjectName("panel_frame"); layout = QGridLayout(frame); layout.addWidget(QLabel("FLIGHT SYSTEMS"), 0, 0, 1, 3) 
        
        btns = [
            ("FLIGHT READY", "FLIGHT_READY", True), 
            ("ENGINES", "ENGINES", True), 
            ("QUANTUM", "QUANTUM", True),     
            ("SCAN MODE", "SCAN", False), 
            ("LANDING GEAR", "LANDING", True), 
            ("DOORS", "DOORS", True),         
            ("LIGHTS", "LIGHTS", True),       
            ("SPACE BRAKE", "SPACE_BRAKE", False), 
            ("DECOUPLED", "DECOUPLED", True), 
            ("VTOL MODE", "VTOL", True)
        ]
        
        r,c=1,0
        for t, a, is_toggle in btns:
            b = QPushButton(t); b.setMinimumHeight(60); b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            if is_toggle: b.setCheckable(True)
            b.clicked.connect(lambda ch, x=a, text=t: self.send_action(x, text))
            layout.addWidget(b,r,c); c+=1; 
            if c>1: c=0; r+=1 
        r += 1; layout.addWidget(QLabel("LANDING SERVICES"), r, 0, 1, 2); r += 1; btn_atc = QPushButton("CALL ATC (REQ LAND)"); btn_atc.setMinimumHeight(70); btn_atc.setStyleSheet("border-color: #ffff00; color: #ffff00;"); btn_atc.clicked.connect(self.call_atc); btn_atc.setFocusPolicy(Qt.FocusPolicy.NoFocus); layout.addWidget(btn_atc, r, 0); btn_al = HoldButton("AUTO LAND (HOLD)"); btn_al.setMinimumHeight(70); btn_al.setStyleSheet("border-color: #00ff00; color: #00ff00;"); btn_al.on_press_callback = lambda: self.start_hold("AUTOLAND"); btn_al.on_release_callback = self.stop_hold; layout.addWidget(btn_al, r, 1)
        r += 1; 
        
        btn_exit = QPushButton("EXIT SEAT"); 
        btn_exit.setMinimumHeight(60); 
        btn_exit.setFocusPolicy(Qt.FocusPolicy.NoFocus);
        btn_exit.clicked.connect(lambda: self.send_action("EXIT_SEAT", "SYSTEM: EXITING SEAT"));
        layout.addWidget(btn_exit, r, 0);

        ej = HoldButton("EJECT (HOLD)"); 
        ej.setObjectName("btn_danger"); 
        ej.setMinimumHeight(60); 
        ej.on_press_callback = lambda: self.start_hold("EJECT"); 
        ej.on_release_callback = self.stop_hold; 
        layout.addWidget(ej, r, 1);
        
        self.main_layout.addWidget(frame, row, col)

    def create_power_increments_panel(self, row, col):
        frame = QFrame(); frame.setObjectName("panel_frame"); layout = QGridLayout(frame); 
        lbl = QLabel("POWER DISTRIBUTION"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(lbl, 0, 0, 1, 3)
        
        def add_pwr(idx, name, key_base): 
            dec=QPushButton("-"); dec.setFixedSize(60,80); dec.setObjectName(f"btn_{name.lower()}_dec"); dec.setFocusPolicy(Qt.FocusPolicy.NoFocus); dec.clicked.connect(lambda: self.decrease_power_logic(name)); 
            inc=QPushButton("+"); inc.setFixedSize(60,80); inc.setObjectName(f"btn_{name.lower()}_inc"); inc.setFocusPolicy(Qt.FocusPolicy.NoFocus); inc.clicked.connect(lambda: self.send_action(key_base, f"PWR: {name} (+)")); 
            lbl=QLabel(name); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl.setStyleSheet("color:white; font-weight:bold;"); layout.addWidget(dec,idx,0); layout.addWidget(lbl,idx,1); layout.addWidget(inc,idx,2)
        
        add_pwr(1, "WEAPONS", "WEAPON_POWER"); add_pwr(2, "SHIELDS", "SHIELD_POWER"); add_pwr(3, "ENGINES", "ENGINE_POWER"); rst=QPushButton("RESET DISTRIB."); rst.setMinimumHeight(60); rst.setFocusPolicy(Qt.FocusPolicy.NoFocus); rst.clicked.connect(lambda: self.send_action("POWER_RESET", "PWR: RESET DISTRIB")); layout.addWidget(rst,4,0,1,3)
        layout.addWidget(QLabel("COUNTERMEASURES"), 5, 0, 1, 3); btn_decoy = QPushButton("DECOY (FLARES)"); btn_decoy.setMinimumHeight(70); btn_decoy.setObjectName("btn_weapons_inc"); btn_decoy.setFocusPolicy(Qt.FocusPolicy.NoFocus); btn_decoy.clicked.connect(lambda: self.send_action("DECOY", "DEFENSE: DECOY LAUNCHED")); layout.addWidget(btn_decoy, 6, 0, 1, 3); btn_noise = QPushButton("NOISE (CHAFFS)"); btn_noise.setMinimumHeight(70); btn_noise.setStyleSheet("color: #aaaaaa; border-color: #aaaaaa;"); btn_noise.setFocusPolicy(Qt.FocusPolicy.NoFocus); btn_noise.clicked.connect(lambda: self.send_action("NOISE", "DEFENSE: NOISE FIELD ACTIVE")); layout.addWidget(btn_noise, 7, 0, 1, 3)
        
        layout.addWidget(QLabel("MISSION NOTES"))
        self.notes_widget = NotesWidget()
        layout.addWidget(self.notes_widget, 8, 0, 1, 3)
        
        self.main_layout.addWidget(frame, row, col)

    def decrease_power_logic(self, target): self.add_log_entry(f"REBALANCING: DECREASE {target}", is_user_action=True); self.send_action("SHIELD_POWER", silent=True) if target=="WEAPONS" else None; self.send_action("ENGINE_POWER", silent=True) if target=="WEAPONS" else None; self.send_action("WEAPON_POWER", silent=True) if target=="SHIELDS" else None; self.send_action("ENGINE_POWER", silent=True) if target=="SHIELDS" else None; self.send_action("WEAPON_POWER", silent=True) if target=="ENGINES" else None; self.send_action("SHIELD_POWER", silent=True) if target=="ENGINES" else None

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
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SC_ControlDeck()
    saved_screen_idx = window.config.get("TARGET_SCREEN_INDEX", 1)
    screens = app.screens()
    if saved_screen_idx < len(screens): window.switch_screen(saved_screen_idx)
    else: window.show()
    sys.exit(app.exec())