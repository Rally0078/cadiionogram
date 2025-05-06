from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QLabel,
    QLineEdit,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QMenu,
    QFileDialog
)
from PySide6.QtGui import QAction, QFont
from PySide6.QtCore import QSize, Qt, QObject, QThread, Signal, Slot
import sys
import configparser
from pathlib import Path
from functools import partial

class CADIreader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CADI reader")
        self.setMinimumSize(QSize(1280, 720))
        self.move(300, 150)
        self.layout = QVBoxLayout()
        self.read_button = QPushButton('Read from folder')
        self.set_data_folder_button = QPushButton('Set Data Folder')
        self.textbox = QLabel("Currently chosen directory:")
        self.directory = None
        self.read_button.clicked.connect(self._read_button_click)

        set_data_folder_button_font: QFont = self.set_data_folder_button.font()
        set_data_folder_button_font.setPointSize(15)
        read_button_font: QFont = self.read_button.font()
        read_button_font.setPointSize(15)
        self.read_button.setFont(read_button_font)
        self.set_data_folder_button.setFont(set_data_folder_button_font)
        self.read_button.setFixedSize(QSize(228, 128))
        self.set_data_folder_button.setFixedSize(QSize(228, 128))
        
        self.layout.addWidget(self.read_button, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.set_data_folder_button, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.textbox, alignment=Qt.AlignTop)
        self.layout.setContentsMargins(50, 0, 100, 10)
        self.layout.setSpacing(0)
        self.container = QWidget()
        
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

    def _read_button_click(self):
        location = QFileDialog.getExistingDirectory(self, 'Open Folder containing data',  options=QFileDialog.DontUseNativeDialog)
        self.directory = location
        print(f"Currently chosen directory: {location}")
        self.textbox.setText(f"Currently chosen directory: {location}")
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CADIreader()
    window.show()

    app.exec()
