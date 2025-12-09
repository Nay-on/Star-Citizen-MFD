import ast
import operator

from PyQt6.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

# --- Safe Evaluator ---
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

def safe_eval(expr):
    """
    Safely evaluates a string expression containing basic arithmetic operations.
    """
    try:
        node = ast.parse(expr, mode='eval').body
    except (SyntaxError, ValueError):
        raise ValueError("Invalid syntax")

    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant): # For Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):
            op = ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Operator not allowed: {type(node.op).__name__}")
            left = _eval(node.left)
            right = _eval(node.right)
            return op(left, right)
        else:
            raise ValueError(f"Node type not allowed: {type(node).__name__}")

    return _eval(node)

class CalculatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        title = QLabel("CALCULATOR")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("panel_title")
        layout.addWidget(title)

        # Display screen for the calculator
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setStyleSheet("font-size: 24px; border: 1px solid #2affea; padding: 5px;")
        layout.addWidget(self.display)

        # Grid for the buttons
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        positions = [(i, j) for i in range(4) for j in range(4)]

        for position, text in zip(positions, buttons):
            button = QPushButton(text)
            button.setMinimumHeight(40)
            button.clicked.connect(self.on_button_click)
            grid_layout.addWidget(button, *position)

        layout.addLayout(grid_layout)

        # Add a clear button
        clear_button = QPushButton("CLEAR")
        clear_button.setMinimumHeight(40)
        clear_button.setStyleSheet("background-color: #550000; color: #ffaaaa; border: 1px solid #ff5555;")
        clear_button.clicked.connect(self.on_clear_click)
        layout.addWidget(clear_button)

        self.current_input = ""

    def on_button_click(self):
        button = self.sender()
        text = button.text()

        if text == "=":
            try:
                result = str(safe_eval(self.current_input))
                self.display.setText(result)
                self.current_input = result
            except Exception:
                self.display.setText("Error")
                self.current_input = ""
        else:
            self.current_input += text
            self.display.setText(self.current_input)

    def on_clear_click(self):
        self.current_input = ""
        self.display.clear()
