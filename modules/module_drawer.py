from PyQt6.QtWidgets import QDockWidget, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class ModuleDrawer(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setAcceptDrops(True)

        self.module_list = QListWidget()
        self.module_list.setDragEnabled(True)
        self.setWidget(self.module_list)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if not mime_data.hasText():
            return

        module_id = mime_data.text()
        main_window = self.parent()
        source_widget = main_window.modules.get(module_id)

        if source_widget and source_widget.parent() != self.module_list:
            source_widget.hide()
            main_window.grid_widget.layout.removeWidget(source_widget)

            item = QListWidgetItem(module_id)
            item.setData(Qt.ItemDataRole.UserRole, module_id)
            self.module_list.addItem(item)

            event.acceptProposedAction()
