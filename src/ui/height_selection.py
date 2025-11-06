from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QLabel
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QDoubleValidator

class HeightSelector(QWidget):
    start_height_changed = Signal(float)
    end_height_changed = Signal(float)
    def __init__(self, parent=None, start_height=90, end_height=1000):
        super().__init__(parent)
        self.start_height = start_height
        self.end_height = end_height
        self.start_height_line = QLineEdit(placeholderText='Start(km)')
        self.end_height_line = QLineEdit(placeholderText='End(km)')
        self.start_text = QLabel("Height Range")
        self.layout_horizontal = QHBoxLayout(self)
        self.layout_horizontal.addWidget(self.start_text)
        self.layout_horizontal.addWidget(self.start_height_line)

        self.layout_horizontal.addWidget(self.end_height_line)
        input_validator = QDoubleValidator(bottom=0, top=1024)
        self.start_height_line.setValidator(input_validator)
        self.end_height_line.setValidator(input_validator)
        self.start_height_line.textChanged.connect(self._emit_start_height_changed)
        self.end_height_line.textChanged.connect(self._emit_end_height_changed)

    def _emit_start_height_changed(self, start_height: str):
        if start_height == '':
            start_height = '0'
        self.start_height_changed.emit(float(start_height))
    
    def _emit_end_height_changed(self, end_height: str):
        if end_height == '':
            end_height = '0'
        self.end_height_changed.emit(float(end_height))