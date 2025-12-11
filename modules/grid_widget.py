from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import Qt
from modules.draggable_module import DraggableModule

class GridWidget(QWidget):
    def __init__(self, modules_dict, main_window, parent=None):
        super().__init__(parent)
        self.modules_dict = modules_dict
        self.main_window = main_window # Reference to the main window to interact with the module list
        self.layout = QGridLayout(self)
        self.layout.setSpacing(15)

        # Define a fixed grid size suitable for a 1080p screen.
        self.rows = 3
        self.cols = 4

        # Initialize grid with stretch factors to ensure cells resize correctly
        for r in range(self.rows):
            self.layout.setRowStretch(r, 0) # Rows with widgets should not expand
        for c in range(self.cols):
            self.layout.setColumnStretch(c, 1)

        # Add a spacer row at the bottom to absorb extra vertical space
        self.layout.setRowStretch(self.rows, 1)

        self.setAcceptDrops(True)

    def add_module(self, module: DraggableModule, row: int, col: int, rowspan: int = 1, colspan: int = 1):
        self.layout.addWidget(module, row, col, rowspan, colspan)

    def get_cell_from_pos(self, pos):
        """Calculates the grid cell (row, column) from a QPoint."""
        # First, check if the position is over an existing widget for accuracy
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget() and item.geometry().contains(pos):
                r, c, _, _ = self.layout.getItemPosition(i)
                return r, c

        # If not over a widget (empty cell), calculate based on overall grid geometry
        cell_width = self.width() / self.cols if self.cols > 0 else self.width()
        cell_height = self.height() / self.rows if self.rows > 0 else self.height()

        # Clamp values to be within the grid boundaries
        c = max(0, min(int(pos.x() // cell_width), self.cols - 1))
        r = max(0, min(int(pos.y() // cell_height), self.rows - 1))

        return r, c

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if not mime_data.hasText():
            event.ignore()
            return

        module_id = mime_data.text()
        # The source widget is the widget that initiated the drag
        source_widget = event.source()

        if not isinstance(source_widget, DraggableModule):
            event.ignore()
            return

        pos = event.position().toPoint()
        target_row, target_col = self.get_cell_from_pos(pos)

        target_item = self.layout.itemAtPosition(target_row, target_col)
        target_widget = target_item.widget() if target_item else None

        is_internal_move = source_widget.parent() == self

        if is_internal_move:
            # Reorganizing widgets already on the grid
            source_index = self.layout.indexOf(source_widget)
            sr, sc, srs, scs = self.layout.getItemPosition(source_index)

            if target_widget and target_widget != source_widget:
                # Target cell is occupied, swap widgets
                self.layout.removeWidget(source_widget)
                self.layout.removeWidget(target_widget)
                self.layout.addWidget(source_widget, target_row, target_col, srs, scs)
                self.layout.addWidget(target_widget, sr, sc, srs, scs)
            elif not target_widget:
                # Target cell is empty, just move the widget
                self.layout.removeWidget(source_widget)
                self.layout.addWidget(source_widget, target_row, target_col, srs, scs)

            event.acceptProposedAction()

        else:
            # Adding a new widget from the drawer
            if target_widget:
                # Target cell is occupied, reject the drop for new widgets
                event.ignore()
                return
            else:
                # Target cell is empty, add the new widget
                source_widget.setParent(self)
                source_widget.show()
                self.layout.addWidget(source_widget, target_row, target_col)

                # Remove the item from the source module_list in the drawer
                list_widget = self.main_window.module_list
                items = list_widget.findItems(module_id, Qt.MatchFlag.MatchExactly)
                if items:
                    list_widget.takeItem(list_widget.row(items[0]))

                event.acceptProposedAction()
