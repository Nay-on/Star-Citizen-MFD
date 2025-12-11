from PyQt6.QtWidgets import QFrame, QApplication, QSizePolicy
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag

class DraggableModule(QFrame):
    def __init__(self, module_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName("panel_frame")
        self.module_id = module_id
        # Prevent the widget from expanding vertically
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            # Use the unique ID to identify the widget
            mime_data.setText(self.module_id)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)
