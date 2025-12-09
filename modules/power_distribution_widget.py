from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class PowerDistributionWidget(QWidget):
    def __init__(self, action_callback, decrease_power_callback, notes_widget, parent=None):
        super().__init__(parent)
        self.action_callback = action_callback
        self.decrease_power_callback = decrease_power_callback

        layout = QGridLayout(self)

        lbl = QLabel("POWER DISTRIBUTION")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl, 0, 0, 1, 3)

        self._add_pwr(layout, 1, "WEAPONS", "WEAPON_POWER")
        self._add_pwr(layout, 2, "SHIELDS", "SHIELD_POWER")
        self._add_pwr(layout, 3, "ENGINES", "ENGINE_POWER")

        rst = QPushButton("RESET DISTRIB.")
        rst.setMinimumHeight(60)
        rst.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        rst.clicked.connect(lambda: self.action_callback("POWER_RESET", "PWR: RESET DISTRIB"))
        layout.addWidget(rst, 4, 0, 1, 3)

        layout.addWidget(QLabel("COUNTERMEASURES"), 5, 0, 1, 3)

        btn_decoy = QPushButton("DECOY (FLARES)")
        btn_decoy.setMinimumHeight(70)
        btn_decoy.setObjectName("btn_weapons_inc")
        btn_decoy.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_decoy.clicked.connect(lambda: self.action_callback("DECOY", "DEFENSE: DECOY LAUNCHED"))
        layout.addWidget(btn_decoy, 6, 0, 1, 3)

        btn_noise = QPushButton("NOISE (CHAFFS)")
        btn_noise.setMinimumHeight(70)
        btn_noise.setStyleSheet("color: #aaaaaa; border-color: #aaaaaa;")
        btn_noise.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_noise.clicked.connect(lambda: self.action_callback("NOISE", "DEFENSE: NOISE FIELD ACTIVE"))
        layout.addWidget(btn_noise, 7, 0, 1, 3)

        layout.addWidget(QLabel("MISSION NOTES"))
        layout.addWidget(notes_widget, 8, 0, 1, 3)

    def _add_pwr(self, layout, idx, name, key_base):
        dec = QPushButton("-")
        dec.setFixedSize(60, 80)
        dec.setObjectName(f"btn_{name.lower()}_dec")
        dec.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        dec.clicked.connect(lambda: self.decrease_power_callback(name))

        inc = QPushButton("+")
        inc.setFixedSize(60, 80)
        inc.setObjectName(f"btn_{name.lower()}_inc")
        inc.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        inc.clicked.connect(lambda: self.action_callback(key_base, f"PWR: {name} (+)"))

        lbl = QLabel(name)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:white; font-weight:bold;")

        layout.addWidget(dec, idx, 0)
        layout.addWidget(lbl, idx, 1)
        layout.addWidget(inc, idx, 2)
