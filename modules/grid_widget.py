from PyQt6.QtWidgets import QWidget, QGridLayout
from modules.draggable_module import DraggableModule

class GridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(15)
        self.setAcceptDrops(True) # Important for drag-and-drop

    def add_module(self, module: DraggableModule, row: int, col: int, rowspan: int = 1, colspan: int = 1):
        self.layout.addWidget(module, row, col, rowspan, colspan)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if not mime_data.hasText():
            return

        module_id = mime_data.text()
        main_window = self.parent().parent().parent() # Kludgy way to get the main window
        source_widget = main_window.modules.get(module_id)

        if source_widget is None:
            return

        pos = event.position().toPoint()

        # Find an empty cell or a target to swap with
        target_pos = self.layout.getItemPosition(self.layout.indexOf(self.layout.itemAtPosition(pos)))

        if source_widget.parent() == self:
            # Swapping widgets already on the grid
            target_widget = self.layout.itemAtPosition(pos).widget()
            if target_widget:
                source_index = self.layout.indexOf(source_widget)
                target_index = self.layout.indexOf(target_widget)

                sr, sc, srs, scs = self.layout.getItemPosition(source_index)
                tr, tc, trs, tcs = self.layout.getItemPosition(target_index)

                self.layout.removeWidget(source_widget)
                self.layout.removeWidget(target_widget)

                self.layout.addWidget(source_widget, tr, tc, trs, tcs)
                self.layout.addWidget(target_widget, sr, sc, srs, scs)
                event.acceptProposedAction()
        else:
            # Adding a new widget from the drawer
            # For simplicity, we'll just add it to the first available empty cell
            for r in range(self.layout.rowCount() + 1):
                for c in range(self.layout.columnCount() + 1):
                    if self.layout.itemAtPosition(r, c) is None:
                        source_widget.show()
                        self.layout.addWidget(source_widget, r, c)
                        main_window.module_list.takeItem(main_window.module_list.row(main_window.module_list.findItems(module_id, Qt.MatchFlag.MatchExactly)[0]))
                        event.acceptProposedAction()
                        return
