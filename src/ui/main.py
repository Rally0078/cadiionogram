if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()

from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QButtonGroup,
    QMenu,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout
)
from PySide6.QtGui import QFont
from PySide6.QtCore import QSize, Qt
from src.cadiparser import readrawdata, csvio
import sys
import time
import configparser
from pathlib import Path
from itertools import starmap

class CADIreader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.cfg_file = Path("./config.ini")

        if not self.cfg_file.exists():
            self.cfg_file.touch()
            self.config['Locations'] = {'DefaultInputDirectory': 'C:\\CADIinput',
                                        'DefaultOutputDirectory': 'C:\\CADIoutput'}
            self.input_dir = Path("C:\\CADIinput")
            self.output_dir = Path("C:\\CADIoutput")
            with open(self.cfg_file, 'w') as f:
                self.config.write(f)
        else:
            self.config.read(self.cfg_file)
            self.input_dir = Path(self.config['Locations']['DefaultInputDirectory'])
            self.output_dir = Path(self.config['Locations']['DefaultOutputDirectory'])
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("CADI reader")
        self.setMinimumSize(QSize(1024, 576))
        self.move(150, 80)
        self.layout = QVBoxLayout()
        self.layout_h = QHBoxLayout()
        self.read_button = QPushButton('Read from folder')
        self.set_data_folder_button = QPushButton('Set Default Input Folder')
        self.set_output_folder_button = QPushButton('Set Output folder')
        self.directory = self.input_dir
        self.input_textbox = QLabel(f"Currently chosen input directory: {self.input_dir}")
        self.output_textbox = QLabel(f"Current default input directory: {self.input_dir}\nCurrently chosen output directory: {self.output_dir}")
        self.md3_checkbox = QCheckBox("md3 format")
        self.md4_checkbox = QCheckBox("md4 format")
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.md3_checkbox)
        self.button_group.addButton(self.md4_checkbox)
        self.button_group.setExclusive(False)
        self.read_button.clicked.connect(self._read_button_click)
        self.set_data_folder_button.clicked.connect(self._set_input_dir)
        self.set_output_folder_button.clicked.connect(self._set_output_dir)

        set_data_folder_button_font: QFont = self.set_data_folder_button.font()
        set_data_folder_button_font.setPointSize(15)
        read_button_font: QFont = self.read_button.font()
        read_button_font.setPointSize(15)
        set_output_folder_button_font: QFont = self.set_output_folder_button.font()
        set_output_folder_button_font.setPointSize(15)

        self.read_button.setFont(read_button_font)
        self.read_button.setFixedSize(QSize(228, 128))
        self.set_data_folder_button.setFont(set_data_folder_button_font)
        self.set_data_folder_button.setFixedSize(QSize(228, 128))
        self.set_output_folder_button.setFont(set_output_folder_button_font)
        self.set_output_folder_button.setFixedSize(QSize(228, 128))
        
        self.layout.addWidget(self.read_button)
        self.layout.addWidget(self.set_data_folder_button)
        self.layout.addWidget(self.set_output_folder_button)
        self.layout_small_h = QHBoxLayout()
        self.layout_small_h.addWidget(self.md3_checkbox)
        self.layout_small_h.addWidget(self.md4_checkbox)
        self.layout_small_h.addStretch()
        self.layout_small_h.setSpacing(0)
        self.layout_small_h.setContentsMargins(0,10,0,10)
        self.layout.addLayout(self.layout_small_h)
        self.layout.addWidget(self.input_textbox, alignment=Qt.AlignTop)
        self.layout.addWidget(self.output_textbox, alignment=Qt.AlignTop)
        
        self.layout.setContentsMargins(25, 0, 100, 0)
        self.layout.setSpacing(0)
        self.layout_h.addLayout(self.layout)
        #self.layout_h.addWidget(QPushButton("Test"), alignment=Qt.AlignCenter)
        self.container = QWidget()
        
        self.dlg = QDialog(self)
        self.dlg.setWindowTitle("Error!")
        self.layout_dlg = QVBoxLayout()
        self.textbox_errormsg = QLabel("")
        self.button_dlg_close = QDialogButtonBox.Close
        self.buttonBox_dlg = QDialogButtonBox(self.button_dlg_close)
        self.buttonBox_dlg.clicked.connect(self.dlg.close)
        self.layout_dlg.addWidget(self.textbox_errormsg)
        self.layout_dlg.addWidget(self.buttonBox_dlg)
        self.dlg.setLayout(self.layout_dlg)

        self.container.setLayout(self.layout_h)
        self.setCentralWidget(self.container)

    def _read_button_click(self):
        location = QFileDialog.getExistingDirectory(self, 'Open Folder containing data',dir=str(self.input_dir))
        if not (self.md3_checkbox.isChecked()) and not (self.md4_checkbox.isChecked()):
            self.textbox_errormsg.setText("You must choose atleast one extension using the checkboxes.")
            self.dlg.exec()
            return
        if len(location) == 0:
            print(f"Path cant be empty")
            return
        else:
            self.directory = location
            print(f"Currently chosen directory: {self.directory}")
            self.input_textbox.setText(f"Currently chosen directory: {self.directory}")
            csv_writer = csvio.CSVtools()
            raw_reader = readrawdata.MDreader()
            args = []
            if self.md3_checkbox.isChecked():
                args.append((Path(self.directory), 'md3', Path(self.output_dir), raw_reader, True))
            if self.md4_checkbox.isChecked():
                args.append((Path(self.directory), 'md4', Path(self.output_dir), raw_reader, True))
            start_time = time.perf_counter()
            results = list(starmap(csv_writer.write_csv_day, args))
            end_time = time.perf_counter()
            print(f"Output files written in {(end_time-start_time):.4f} seconds")

    def _set_input_dir(self):
        location = QFileDialog.getExistingDirectory(self, 'Open folder to set as default input folder',dir=str(self.input_dir))
        if len(location) !=0 :
            self.input_dir = location
            print(f"Currently chosen input directory: {self.input_dir}")
            self.output_textbox.setText(f"Current default input directory: {self.input_dir}\nCurrently chosen output directory: {self.output_dir}")
            self.config['Locations']['DefaultInputDirectory'] = self.input_dir
            with open(self.cfg_file, 'w') as f:
                self.config.write(f)
        else:
            print(f"Path cant be empty")

    def _set_output_dir(self):
        location = QFileDialog.getExistingDirectory(self, 'Open folder to set as default output folder',dir=str(self.output_dir))
        if len(location) !=0 :
            self.output_dir = location
            print(f"Currently chosen output directory: {self.output_dir}")
            self.output_textbox.setText(f"Current default input directory: {self.input_dir}\nCurrently chosen output directory: {self.output_dir}")
            self.config['Locations']['DefaultOutputDirectory'] = self.output_dir
            with open(self.cfg_file, 'w') as f:
                self.config.write(f)
        else:
            print(f"Path cant be empty")
        
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CADIreader()
    window.show()

    app.exec()
