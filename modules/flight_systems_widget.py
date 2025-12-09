from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from modules.shared_widgets import HoldButton

class FlightSystemsWidget(QWidget):
    def __init__(self, action_callback, hold_start_callback, hold_stop_callback, atc_callback, parent=None):
        super().__init__(parent)

        self.action_callback = action_callback
        self.hold_start_callback = hold_start_callback
        self.hold_stop_callback = hold_stop_callback
        self.atc_callback = atc_callback

        layout = QGridLayout(self)
        layout.addWidget(QLabel("FLIGHT SYSTEMS"), 0, 0, 1, 3)

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

        r, c = 1, 0
        for t, a, is_toggle in btns:
            b = QPushButton(t)
            b.setMinimumHeight(60)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            if is_toggle:
                b.setCheckable(True)
            b.clicked.connect(lambda ch, x=a, text=t: self.action_callback(x, text))
            layout.addWidget(b, r, c)
            c += 1
            if c > 1:
                c = 0
                r += 1

        r += 1
        layout.addWidget(QLabel("LANDING SERVICES"), r, 0, 1, 2)

        r += 1
        btn_atc = QPushButton("CALL ATC (REQ LAND)")
        btn_atc.setMinimumHeight(70)
        btn_atc.setStyleSheet("border-color: #ffff00; color: #ffff00;")
        btn_atc.clicked.connect(self.atc_callback)
        btn_atc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(btn_atc, r, 0)

        btn_al = HoldButton("AUTO LAND (HOLD)")
        btn_al.setMinimumHeight(70)
        btn_al.setStyleSheet("border-color: #00ff00; color: #00ff00;")
        btn_al.on_press_callback = lambda: self.hold_start_callback("AUTOLAND")
        btn_al.on_release_callback = self.hold_stop_callback
        layout.addWidget(btn_al, r, 1)

        r += 1
        btn_exit = QPushButton("EXIT SEAT")
        btn_exit.setMinimumHeight(60)
        btn_exit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_exit.clicked.connect(lambda: self.action_callback("EXIT_SEAT", "SYSTEM: EXITING SEAT"))
        layout.addWidget(btn_exit, r, 0)

        ej = HoldButton("EJECT (HOLD)")
        ej.setObjectName("btn_danger")
        ej.setMinimumHeight(60)
        ej.on_press_callback = lambda: self.hold_start_callback("EJECT")
        ej.on_release_callback = self.hold_stop_callback
        layout.addWidget(ej, r, 1)
