from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, QTime, Qt

class ClockWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("clock_module")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.time_lbl = QLabel("00:00:00")
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_lbl.setStyleSheet("""
            font-size: 30px;
            color: white;
            font-family: 'Consolas';
            border: 1px solid #334455;
            border-radius: 5px;
            margin-bottom: 10px;
        """)

        layout.addWidget(self.time_lbl)

        # Timer to update the clock every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def update_time(self):
        """ Updates the time displayed on the label. """
        self.time_lbl.setText(QTime.currentTime().toString("HH:mm:ss"))
