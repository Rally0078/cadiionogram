from PySide6.QtWidgets import QTableWidget
from PySide6.QtCore import Qt, Signal
from datetime import datetime
#from src.plot.metadatakeys import keys_list
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QGridLayout,
    QLabel, QHBoxLayout, QTableWidget,
    QSpacerItem, QTableWidgetItem, QComboBox,
)

class MetadataTableWidget(QWidget):
    dropdown_changed = Signal(str)
    right_dropdown_changed = Signal(str)
    left_clicked = Signal()
    right_clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout_table = QVBoxLayout(self)
        self.layout_table.setContentsMargins(10, 0, 10, 0)
        self.layout_table.setSpacing(10)
        self.timepartitions_layout = QHBoxLayout()
        self.timepartitions_dropdown = QComboBox()
        self.timepartitions_dropdown.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.end_timepartitions_dropdown = QComboBox()
        self.end_timepartitions_dropdown.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.end_timepartitions_dropdown.currentTextChanged.connect(self._on_right_dropdown_changed)

        self.end_timepartitions_dropdown.setVisible(False)
        self.pointers_label = QLabel()
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")
        self.timepartitions_dropdown.currentTextChanged.connect(self._on_dropdown_changed)

        self.left_button.clicked.connect(self.left_clicked.emit)
        self.right_button.clicked.connect(self.right_clicked.emit)
        self.lpointer = 0
        self.rpointer = 0

    def _on_dropdown_changed(self, text: str):
        self.dropdown_changed.emit(text)
    
    def _on_right_dropdown_changed(self, text: str):
        self.right_dropdown_changed.emit(text)

    #Update metadata table
    def update_metadata(self, metadata: dict, keys_list: list[str]):       
        #Disconnect signal if already connected    
        try:
            self.timepartitions_dropdown.currentTextChanged.disconnect(self._on_dropdown_changed)
            self.end_timepartitions_dropdown.currentTextChanged.disconnect(self._on_right_dropdown_changed)
        except TypeError:
            pass    
        self.timepartitions_dropdown.clear()
        self.timepartitions_dropdown.addItems(list(metadata['timepartitions'].keys()))
        self.timepartitions_dropdown.setCurrentIndex(0)
        self.end_timepartitions_dropdown.clear()
        self.end_timepartitions_dropdown.addItems(list(metadata['timepartitions'].keys()))
        self.end_timepartitions_dropdown.setCurrentIndex(-1)
        self.timepartitions_dropdown.currentTextChanged.connect(self._on_dropdown_changed)
        self.end_timepartitions_dropdown.currentTextChanged.connect(self._on_right_dropdown_changed)
        
        # Create new widgets
        metadata_title = QLabel(f"{metadata['extension']} header")
        metadata_table = QTableWidget()
        metadata_table.setRowCount(len(keys_list))
        metadata_table.setColumnCount(2)
        metadata_table.setHorizontalHeaderLabels(['Property', 'Value'])
        metadata_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)

        for idy, key in enumerate(keys_list):
            header_key = QTableWidgetItem(key)
            value = metadata[key]
            if isinstance(value, datetime):
                header_value = QTableWidgetItem(value.strftime("%Y-%m-%d"))
            else:
                header_value = QTableWidgetItem(str(value))
            metadata_table.setItem(idy, 0, header_key)
            metadata_table.setItem(idy, 1, header_value)

        metadata_table.resizeColumnsToContents()
        metadata_table.resizeRowsToContents()
        metadata_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        spacer = QSpacerItem(10, 100)

        #If layout table is not empty, delete and update old widgets
        if not self.layout_table.isEmpty():
            old_title = self.layout_table.itemAt(0).widget()
            old_table = self.layout_table.itemAt(1).widget()
            old_spacer = self.layout_table.itemAt(2)
            old_dropdown = None
            old_arrow_layout = None

            for i in range(self.layout_table.count()):
                item = self.layout_table.itemAt(i)
                if item.layout() == self.arrow_layout:  # safer check
                    old_arrow_layout = item
                    continue
                elif item.layout() == self.timepartitions_layout:
                    old_dropdown = item
                    continue
            

            if old_arrow_layout:
                self.layout_table.removeItem(old_arrow_layout)
            if old_dropdown:
                self.layout_table.removeItem(old_dropdown)

            self.pointers_label.setText("")
            old_left_timedropdown = self.timepartitions_layout.itemAt(0).widget()
            old_right_timedropdown = self.timepartitions_layout.itemAt(1).widget()
            
            # Remove old dynamic widgets
            self.layout_table.removeWidget(old_table)
            self.layout_table.removeWidget(old_title)
            self.layout_table.removeItem(old_spacer)
            self.timepartitions_layout.removeWidget(old_left_timedropdown)
            self.timepartitions_layout.removeWidget(old_right_timedropdown)
            
            old_table.deleteLater()
            old_title.deleteLater()
        
        self.timepartitions_layout.addWidget(self.timepartitions_dropdown, alignment=Qt.AlignLeft)
        self.timepartitions_layout.addWidget(self.end_timepartitions_dropdown, alignment=Qt.AlignLeft)
        self.layout_table.addWidget(metadata_title, alignment=Qt.AlignLeft)
        self.layout_table.addWidget(metadata_table, alignment=Qt.AlignLeft)
        self.layout_table.addSpacerItem(spacer)
        self.layout_table.addLayout(self.timepartitions_layout)
        self.layout_table.addWidget(self.pointers_label, alignment=Qt.AlignLeft)

        self.arrow_layout = QHBoxLayout()
        self.arrow_layout.addWidget(self.left_button)
        self.arrow_layout.addWidget(self.right_button)
        self.arrow_layout.setAlignment(Qt.AlignTop)

        self.layout_table.addLayout(self.arrow_layout) 
        self.layout_table.update()

    def set_pointers(self, lpointer, rpointer):
        self.lpointer = lpointer
        self.rpointer = rpointer
        self.pointers_label.setText(f"Left = {self.lpointer}, right = {self.rpointer}")

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())