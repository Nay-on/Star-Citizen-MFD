from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import Qt
from modules.draggable_module import DraggableModule

class GridWidget(QWidget):
    def __init__(self, modules_dict, parent=None):
        super().__init__(parent)
        self.modules_dict = modules_dict
        self.layout = QGridLayout(self)
        self.layout.setSpacing(15)
        self.setAcceptDrops(True) # Important for drag-and-drop

    def add_module(self, module: DraggableModule, row: int, col: int, rowspan: int = 1, colspan: int = 1):
        self.layout.addWidget(module, row, col, rowspan, colspan)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        pos = event.position().toPoint()
        mime_data = event.mimeData()
        if not mime_data.hasText():
            return

        module_id = mime_data.text()
        source_widget = self.modules_dict.get(module_id)
        if not source_widget:
            return

        # --- Find target widget and its position ---
        target_widget = self.childAt(pos)
        while target_widget and not isinstance(target_widget, DraggableModule):
            target_widget = target_widget.parent()

        # --- Find target cell coordinates ---
        target_row, target_col = -1, -1
        if target_widget:
            idx = self.layout.indexOf(target_widget)
            if idx != -1:
                target_row, target_col, _, _ = self.layout.getItemPosition(idx)
        else:
            for r in range(self.layout.rowCount() + 1):
                for c in range(self.layout.columnCount() + 1):
                    if self.layout.cellRect(r, c).contains(pos):
                        target_row, target_col = r, c
                        break
                if target_row != -1:
                    break

        if target_row == -1 or target_col == -1:
            return

        # --- Handle Drag & Drop Logic ---
        # Case 1: Source is from the grid (move or swap)
        if source_widget.parent() == self:
            source_idx = self.layout.indexOf(source_widget)
            sr, sc, srs, scs = self.layout.getItemPosition(source_idx)

            if (sr, sc) == (target_row, target_col):
                return

            if target_widget and target_widget != source_widget:
                tr, tc, trs, tcs = self.layout.getItemPosition(self.layout.indexOf(target_widget))
                self.layout.removeWidget(source_widget)
                self.layout.removeWidget(target_widget)
                self.layout.addWidget(source_widget, tr, tc, trs, tcs)
                self.layout.addWidget(target_widget, sr, sc, srs, scs)
            else:
                self.layout.removeWidget(source_widget)
                self.layout.addWidget(source_widget, target_row, target_col, srs, scs)

            event.acceptProposedAction()

        # Case 2: Source is from the drawer (add)
        else:
            if target_widget:
                return # Don't allow dropping on an existing widget

            source_widget.show()
            self.layout.addWidget(source_widget, target_row, target_col)

            main_window = self.parent()
            if hasattr(main_window, 'module_list'):
                items = main_window.module_list.findItems(module_id, Qt.MatchFlag.MatchExactly)
                if items:
                    main_window.module_list.takeItem(main_window.module_list.row(items[0]))
            event.acceptProposedAction()
