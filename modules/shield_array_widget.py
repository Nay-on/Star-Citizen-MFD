from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt

class ShieldArrayWidget(QWidget):
    def __init__(self, action_callback, parent=None):
        super().__init__(parent)
        self.action_callback = action_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("SHIELD ARRAY")
        title.setObjectName("panel_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grp_fwd = self._create_shield_group("FRONT", "SHIELD_FWD", "SHIELD_BACK")
        grid.addWidget(grp_fwd, 0, 1)
        grp_left = self._create_shield_group("LEFT", "SHIELD_LEFT", "SHIELD_RIGHT")
        grid.addWidget(grp_left, 1, 0)
        grp_right = self._create_shield_group("RIGHT", "SHIELD_RIGHT", "SHIELD_LEFT")
        grid.addWidget(grp_right, 1, 2)
        grp_back = self._create_shield_group("BACK", "SHIELD_BACK", "SHIELD_FWD")
        grid.addWidget(grp_back, 2, 1)

        btn_reset = QPushButton("RST")
        btn_reset.setFixedSize(80, 80)
        btn_reset.setObjectName("btn_shd_reset")
        btn_reset.clicked.connect(lambda: self.action_callback("SHIELD_RESET", "SHIELD RESET"))
        btn_reset.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        grid.addWidget(btn_reset, 1, 1, Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(grid)

    def _create_shield_group(self, label, inc_action, dec_action):
        w = QFrame()
        w.setStyleSheet("background-color: rgba(0,20,40,0.4); border: 1px solid #4444ff; border-radius: 4px;")

        l = QVBoxLayout(w)
        l.setContentsMargins(2,2,2,2)
        l.setSpacing(2)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#aaaaff; font-size:12px; border:none; background:transparent;")
        l.addWidget(lbl)

        h = QHBoxLayout()
        h.setSpacing(2)

        bd = QPushButton("-")
        bd.setFixedSize(50,50)
        bd.setObjectName("btn_shield_dec")
        bd.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        bd.clicked.connect(lambda: self.action_callback(dec_action, f"SHIELD {label} (-)"))

        bi = QPushButton("+")
        bi.setFixedSize(50,50)
        bi.setObjectName("btn_shield_inc")
        bi.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        bi.clicked.connect(lambda: self.action_callback(inc_action, f"SHIELD {label} (+)"))

        h.addWidget(bd)
        h.addWidget(bi)
        l.addLayout(h)
        return w
