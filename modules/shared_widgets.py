from PyQt6.QtWidgets import QPushButton, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QEvent
from modules.draggable_module import DraggableModule

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

class DroppableListWidget(QListWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        source_widget = event.source()

        # Check if the source is a DraggableModule from the grid
        if isinstance(source_widget, DraggableModule) and source_widget.parent() == self.main_window.grid_widget:
            module_id = source_widget.module_id

            # Add the item back to the list
            item = QListWidgetItem(module_id)
            item.setData(Qt.ItemDataRole.UserRole, module_id)
            self.addItem(item)

            # Hide the widget on the grid (it will be reparented/deleted by the grid logic)
            source_widget.hide()
            self.main_window.grid_widget.layout.removeWidget(source_widget)
            source_widget.setParent(None)

            event.acceptProposedAction()
        else:
            super().dropEvent(event)
