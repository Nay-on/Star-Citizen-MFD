from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QComboBox,
                             QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt

class AddMissionDialog(QDialog):
    """A dialog to add a new mission with a name and an amount."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Mission")

        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Mission Name (e.g., 'Bounty Hunting')")
        layout.addWidget(QLabel("Mission:"))
        layout.addWidget(self.name_input)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("aUEC Reward")
        layout.addWidget(QLabel("Amount:"))
        layout.addWidget(self.amount_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class AUECCalculatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.total_auec = 0
        self.crew = {} # {name: percentage}

        main_layout = QVBoxLayout(self)

        title = QLabel("aUEC CALCULATOR")
        title.setObjectName("panel_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # --- Total Display ---
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("TOTAL aUEC:"))
        self.total_display = QLabel("0 aUEC")
        self.total_display.setStyleSheet("font-size: 18px; font-weight: bold; color: #2affea;")
        total_layout.addWidget(self.total_display)
        total_layout.addStretch()
        main_layout.addLayout(total_layout)

        # --- Missions ---
        main_layout.addWidget(QLabel("Missions Log:"))
        self.missions_list = QListWidget()
        main_layout.addWidget(self.missions_list)

        add_mission_btn = QPushButton("Add Mission")
        add_mission_btn.clicked.connect(self.add_mission)
        main_layout.addWidget(add_mission_btn)

        # --- Crew Management ---
        main_layout.addWidget(QLabel("Crew Members:"))
        self.crew_list = QListWidget()
        main_layout.addWidget(self.crew_list)

        crew_input_layout = QHBoxLayout()
        self.crew_name_input = QLineEdit()
        self.crew_name_input.setPlaceholderText("Crew member name...")
        crew_input_layout.addWidget(self.crew_name_input)
        add_crew_btn = QPushButton("Add")
        add_crew_btn.clicked.connect(self.add_crew_member)
        crew_input_layout.addWidget(add_crew_btn)
        main_layout.addLayout(crew_input_layout)

        # --- Splitting ---
        split_layout = QHBoxLayout()
        self.split_combo = QComboBox()
        self.split_combo.addItems(["Split Equally", "Split by Percentage"])
        split_layout.addWidget(self.split_combo)

        split_btn = QPushButton("Calculate Split")
        split_btn.clicked.connect(self.calculate_split)
        split_layout.addWidget(split_btn)
        main_layout.addLayout(split_layout)

        # --- Results Display ---
        self.results_display = QLabel("Results will be shown here.")
        self.results_display.setStyleSheet("font-size: 14px; border: 1px solid #333; padding: 5px; min-height: 100px;")
        self.results_display.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_display.setWordWrap(True)
        main_layout.addWidget(self.results_display)

    def add_mission(self):
        dialog = AddMissionDialog(self)
        if dialog.exec():
            name = dialog.name_input.text()
            amount_str = dialog.amount_input.text()
            try:
                amount = int(amount_str)
                self.total_auec += amount

                item = QListWidgetItem(f"{name}: {amount} aUEC")
                self.missions_list.addItem(item)

                self.update_total_display()
            except ValueError:
                # Handle error (e.g., show a message box)
                pass

    def add_crew_member(self):
        name = self.crew_name_input.text()
        if name and name not in self.crew:
            self.crew[name] = 0 # Default percentage
            item = QListWidgetItem(name)
            self.crew_list.addItem(item)
            self.crew_name_input.clear()

    def calculate_split(self):
        crew_count = len(self.crew)
        if crew_count == 0:
            self.results_display.setText("Add crew members to calculate a split.")
            return

        split_mode = self.split_combo.currentText()

        if split_mode == "Split Equally":
            if self.total_auec == 0:
                self.results_display.setText("Total aUEC is 0. Nothing to split.")
                return

            share = self.total_auec / crew_count
            results_text = "EQUAL SPLIT:\n"
            for member in self.crew.keys():
                results_text += f"- {member}: {share:,.2f} aUEC\n"
            self.results_display.setText(results_text)

        elif split_mode == "Split by Percentage":
            self.results_display.setText("Percentage split is not yet implemented.")

    def update_total_display(self):
        self.total_display.setText(f"{self.total_auec} aUEC")
