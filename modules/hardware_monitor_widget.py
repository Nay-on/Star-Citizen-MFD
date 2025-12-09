import psutil
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QProgressBar
from PyQt6.QtCore import QTimer

class HardwareMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tick_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("HARDWARE MONITOR")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        hw_grid = QGridLayout()

        # CPU Bar
        self.bar_cpu = QProgressBar()
        self.bar_cpu.setFormat("CPU %p%")
        self.bar_cpu.setStyleSheet("QProgressBar::chunk { background-color: #2affea; }")
        hw_grid.addWidget(QLabel("CPU"), 0, 0)
        hw_grid.addWidget(self.bar_cpu, 0, 1)

        # RAM Bar
        self.bar_ram = QProgressBar()
        self.bar_ram.setFormat("RAM %p%")
        self.bar_ram.setStyleSheet("QProgressBar::chunk { background-color: #ffaa00; }")
        hw_grid.addWidget(QLabel("RAM"), 1, 0)
        hw_grid.addWidget(self.bar_ram, 1, 1)

        # Disk Bar
        self.bar_disk = QProgressBar()
        self.bar_disk.setFormat("DISK %p%")
        self.bar_disk.setStyleSheet("QProgressBar::chunk { background-color: #ff5555; }")
        hw_grid.addWidget(QLabel("DSK"), 2, 0)
        hw_grid.addWidget(self.bar_disk, 2, 1)

        # Swap Bar
        self.bar_swap = QProgressBar()
        self.bar_swap.setFormat("SWAP %p%")
        self.bar_swap.setStyleSheet("QProgressBar::chunk { background-color: #aa55ff; }")
        hw_grid.addWidget(QLabel("SWP"), 3, 0)
        hw_grid.addWidget(self.bar_swap, 3, 1)

        layout.addLayout(hw_grid)

        # Timer to update stats
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000) # Update every second

    def update_stats(self):
        """Updates the hardware stats."""
        self.tick_count += 1
        self.bar_cpu.setValue(int(psutil.cpu_percent()))
        self.bar_ram.setValue(int(psutil.virtual_memory().percent))

        # These don't need to be updated as frequently
        if self.tick_count % 300 == 0 or self.tick_count == 1:
            try:
                self.bar_disk.setValue(int(psutil.disk_usage('/').percent))
            except Exception:
                pass
            try:
                self.bar_swap.setValue(int(psutil.swap_memory().percent))
            except Exception:
                pass
