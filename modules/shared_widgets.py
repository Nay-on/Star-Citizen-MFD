from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QEvent

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
