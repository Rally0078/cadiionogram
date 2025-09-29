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
    QTableWidget,
    QTableWidgetItem,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QAbstractScrollArea
)
from PySide6.QtGui import QFont
from PySide6.QtCore import QSize, Qt
from src.ionogramparser.mdxreader import MDreader
import sys
import time
from datetime import datetime
import configparser
from pathlib import Path
from itertools import starmap
import platform

class CADIreader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.cfg_file = Path("./config.ini")
        os_name = platform.system()

        if not self.cfg_file.exists():
            self.cfg_file.touch()
            if os_name == "Windows":
                self.config['Locations'] = {'DefaultInputDirectory': 'C:\\CADIinput',
                                            'DefaultOutputDirectory': 'C:\\CADIoutput',
                                            "polanoutputdirectory": "C:\\cdata",
                                            "cachedir": "C:\\cdata\\parquetcache"}
            elif os_name == "Linux" or os_name == "Darwin":
                self.config['Locations'] = {'DefaultInputDirectory': '~/CADIinput',
                                            'DefaultOutputDirectory': '~/CADIoutput',
                                            "polanoutputdirectory": "~/cdata",
                                            "cachedir": "~/cdata/parquetcache"}
            else:
                print("OS is not supported!")
                return                
                
            self.polan_dir = Path(self.config['Locations']['polanoutputdirectory'])
            self.input_dir = Path(self.config['Locations']['DefaultInputDirectory'])
            self.parquet_cache_dir = Path(self.config['Locations']['cachedir'])
            with open(self.cfg_file, 'w') as f:
                self.config.write(f)
        else:
            self.config.read(self.cfg_file)
            self.polan_dir = Path(self.config['Locations']['polanoutputdirectory'])
            self.input_dir = Path(self.config['Locations']['DefaultInputDirectory'])
            self.parquet_cache_dir = Path(self.config['Locations']['cachedir'])
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("CADI reader")
        self.setMinimumSize(QSize(1024, 576))
        self.move(300, 85)
        self.layout_window = QVBoxLayout()
        self.layout_window_h = QHBoxLayout()
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
        
        self.layout_window.addWidget(self.read_button)
        self.layout_window.addWidget(self.set_data_folder_button)
        self.layout_window.addWidget(self.set_output_folder_button)
        self.layout_window_small_h = QHBoxLayout()
        self.layout_window_small_h.addWidget(self.md3_checkbox)
        self.layout_window_small_h.addWidget(self.md4_checkbox)
        self.layout_window_small_h.addStretch()
        self.layout_window_small_h.setSpacing(0)
        self.layout_window_small_h.setContentsMargins(0,10,0,10)
        self.layout_window.addLayout(self.layout_window_small_h)
        self.layout_window.addWidget(self.input_textbox, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout_window.addWidget(self.output_textbox, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.layout_window.setContentsMargins(25, 0, 100, 0)
        self.layout_window.setSpacing(0)
        self.layout_window_h.addLayout(self.layout_window)

        self.layout_window_tables = [QVBoxLayout(), QVBoxLayout()]
        for layout_table in self.layout_window_tables:
            layout_table.setContentsMargins(0, 0, 0, 0)
            layout_table.setSpacing(0)
            self.layout_window_h.addLayout(layout_table)
        self.layout_window_h.setContentsMargins(0, 10, 0, 0)
        self.layout_window_h.setSpacing(0)
        self.layout_window_h.addStretch()

        #self.layout_window_h.addWidget(QPushButton("Test"), alignment=Qt.AlignCenter)
        self.container = QWidget()
        
        self.dlg = QDialog(self)
        self.dlg.setWindowTitle("Error!")
        self.layout_window_dlg = QVBoxLayout()
        self.textbox_errormsg = QLabel("")
        self.button_dlg_close = QDialogButtonBox.StandardButton.Close
        self.buttonBox_dlg = QDialogButtonBox(self.button_dlg_close)
        self.buttonBox_dlg.clicked.connect(self.dlg.close)
        self.layout_window_dlg.addWidget(self.textbox_errormsg)
        self.layout_window_dlg.addWidget(self.buttonBox_dlg)
        self.dlg.setLayout(self.layout_window_dlg)

        self.container.setLayout(self.layout_window_h)
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
            raw_reader = mdxreader.MDreader()
            args = []
            if self.md3_checkbox.isChecked():
                args.append((Path(self.directory), 'md3', Path(self.output_dir), raw_reader, True, 'loky'))
            if self.md4_checkbox.isChecked():
                args.append((Path(self.directory), 'md4', Path(self.output_dir), raw_reader, True, 'loky'))
            start_time = time.perf_counter()
            results = list(starmap(csv_writer.write_csv_day, args))
            end_time = time.perf_counter()
            keys_list = ['site', 'datetime', 'extension', 'ndops', 'filetype', 'nfreqs', 'minheight', 'maxheight', 'pps', 'dtime']
            print(len(self.layout_window_tables))
            for idx, result in enumerate(results):
                metadata, path = result
                metadata_table = QTableWidget()
                metadata_table.setRowCount(len(keys_list))
                metadata_table.setColumnCount(2)
                metadata_table.setHorizontalHeaderLabels(['Property', 'Value'])
                metadata_table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
                #metadata_table.setSizePolicy(QSizePolicy.Expanding, QAbstractScrollArea.AdjustToContents)
                for idy, key in enumerate(keys_list):
                    header_key = QTableWidgetItem(key)
                    if type(metadata[key]) == datetime:
                        header_value = QTableWidgetItem(metadata[key].strftime("%Y-%m-%d"))
                    else:
                        header_value = QTableWidgetItem(str(metadata[key]))
                    metadata_table.setItem(idy, 0, header_key)
                    metadata_table.setItem(idy, 1, header_value)
                metadata_title = QLabel(f"{metadata['extension']} header in folder")
                spacer = QSpacerItem(25, 200)
                
                
                if not self.layout_window_tables[idx].isEmpty():
                    old_title = self.layout_window_tables[idx].itemAt(0).widget()
                    old_table = self.layout_window_tables[idx].itemAt(1).widget()
                    old_spacer = self.layout_window_tables[idx].itemAt(2)
                    self.layout_window_tables[idx].removeWidget(old_table)
                    self.layout_window_tables[idx].removeWidget(old_title)
                    self.layout_window_tables[idx].removeItem(old_spacer)
                    old_table.deleteLater()
                    old_title.deleteLater()
                    
                self.layout_window_tables[idx].addWidget(metadata_title, alignment=Qt.AlignmentFlag.AlignLeft)
                self.layout_window_tables[idx].addWidget(metadata_table, alignment=Qt.AlignmentFlag.AlignLeft)
                self.layout_window_tables[idx].addSpacerItem(spacer)

                if idx == 0 and not self.layout_window_tables[1].isEmpty():
                    old_title = self.layout_window_tables[1].itemAt(0).widget()
                    old_table = self.layout_window_tables[1].itemAt(1).widget()
                    old_spacer = self.layout_window_tables[1].itemAt(2)
                    self.layout_window_tables[1].removeWidget(old_table)
                    self.layout_window_tables[1].removeWidget(old_title)
                    self.layout_window_tables[1].removeItem(old_spacer)
                    old_table.deleteLater()
                    old_title.deleteLater()
                
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