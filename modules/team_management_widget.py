from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class TeamManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.team_roles = {
            "Commander": "Unassigned",
            "Pilot": "Unassigned",
            "Gunner": "Unassigned",
            "Engineer": "Unassigned"
        }

        layout = QVBoxLayout(self)

        title = QLabel("TEAM MANAGEMENT")
        title.setObjectName("panel_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.roles_list = QListWidget()
        layout.addWidget(self.roles_list)

        self.update_display()

    def set_roles(self, new_roles):
        """Allows updating roles from the settings panel."""
        self.team_roles = new_roles
        self.update_display()

    def assign_member(self, role, member_name):
        """Assigns a member to a role."""
        if role in self.team_roles:
            self.team_roles[role] = member_name
            self.update_display()

    def update_display(self):
        """Updates the list widget with the current roles and assignments."""
        self.roles_list.clear()
        for role, member in self.team_roles.items():
            item_text = f"{role}: {member}"
            item = QListWidgetItem(item_text)
            self.roles_list.addItem(item)
