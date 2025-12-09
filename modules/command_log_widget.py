import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtCore import QTimer, QTime, Qt

SCI_FI_LOGS = [
    "Scanning local grid...", "Quantum fuel injection: NOMINAL", "Shield harmonics: 98%",
    "Coolant pressure: STABLE", "Incoming transmission blocked", "UEE Signature verified",
    "Radar sweep complete", "Thruster calibration...", "Weapon capacitors: CHARGING",
    "Life support: ACTIVE", "Gravity generator: 1.0G", "Proxy link established",
    "Data packet received (42kb)", "Background radiation: LOW", "System optimized"
]

class CommandLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("COMMAND LOGS")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setObjectName("log_console")
        self.log_console.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.log_console)

        # Timer for random sci-fi logs
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.add_random_log)
        self.log_timer.start(4000)

    def add_log_entry(self, text, is_user_action=False):
        """Adds a new entry to the log console."""
        ts = QTime.currentTime().toString("HH:mm:ss")
        if is_user_action:
            fmt = f'<span style="color:#ffffff; font-weight:bold;">[{ts}] > {text}</span>'
        else:
            fmt = f'<span style="color:#00aa00;">[{ts}] > {text}</span>'

        self.log_console.append(fmt)
        # Auto-scroll to the bottom
        sb = self.log_console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def add_random_log(self):
        """Adds a random sci-fi log entry."""
        self.add_log_entry(random.choice(SCI_FI_LOGS), is_user_action=False)
