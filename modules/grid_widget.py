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
        # Get the widget that is being dragged
        source_widget = event.source()
        if source_widget is None:
            return

        # Find the new position for the widget
        pos = event.position().toPoint()

        # Find the cell in the grid layout that is under the mouse cursor
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget.geometry().contains(pos):
                # We found the target widget, let's swap positions
                # This is a simplified approach. A real implementation
                # would be more complex to handle empty cells and resizing.

                # Get the positions of the source and target widgets
                source_index = self.layout.indexOf(source_widget)
                target_index = self.layout.indexOf(widget)

                if source_index != -1 and target_index != -1:
                    # Get row, col, rowspan, colspan for both widgets
                    sr, sc, srs, scs = self.layout.getItemPosition(source_index)
                    tr, tc, trs, tcs = self.layout.getItemPosition(target_index)

                    # Remove both widgets from the layout
                    self.layout.removeWidget(source_widget)
                    self.layout.removeWidget(widget)

                    # Add them back in swapped positions
                    self.layout.addWidget(source_widget, tr, tc, trs, tcs)
                    self.layout.addWidget(widget, sr, sc, srs, scs)

                    event.acceptProposedAction()
                    return

        event.ignore()
