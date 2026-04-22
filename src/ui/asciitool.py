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
import pandas as pd
from PySide6.QtGui import QFont
from PySide6.QtCore import QSize, Qt
from src.ionogramparser.mdxreader import MDreader
from src.utils.pandasutils import PandasUtils
from src.utils.powerpreprocessing import convert_amplitude_to_power
from src.ui.metadatatable import MetadataTableWidget
from src.errorhandlers.errorhandling import BadIndicesInData
import csv
from src.ui.metadatakeys import cadi_keys_list
import json
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
        os_name = platform.system()
        
        if os_name == "Windows":
            # On Windows, keep it in the application directory when frozen, or CWD
            if getattr(sys, 'frozen', False):
                self.cfg_file = Path(sys.executable).parent / "config.ini"
            else:
                self.cfg_file = Path("./config.ini")
        else:
            # Use ~/.config/egrliono/config.ini for Linux/macOS (AppImage friendly)
            config_dir = Path.home() / ".config" / "egrliono"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.cfg_file = config_dir / "config.ini"

        # Define default configuration
        defaults = {
            'Locations': {
                'DefaultInputDirectory': 'C:\\CADIinput' if os_name == "Windows" else '~/CADIinput',
                'DefaultOutputDirectory': 'C:\\CADIoutput' if os_name == "Windows" else '~/CADIoutput',
                'polanoutputdirectory': 'C:\\cdata' if os_name == "Windows" else '~/cdata',
                'cachedir': 'C:\\cdata\\parquetcache' if os_name == "Windows" else '~/cdata/parquetcache'
            }
        }

        # Load existing config if it exists
        if self.cfg_file.exists():
            self.config.read(self.cfg_file)

        # Ensure all defaults are present
        updated = False
        for section, keys in defaults.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                updated = True
            for key, value in keys.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
                    updated = True

        # Save if it's new or was updated with missing defaults
        if updated or not self.cfg_file.exists():
            with open(self.cfg_file, 'w') as f:
                self.config.write(f)

        self.polan_dir = Path(self.config['Locations']['polanoutputdirectory'])
        self.input_dir = Path(self.config['Locations']['DefaultInputDirectory'])
        self.output_dir = Path(self.config['Locations']['DefaultOutputDirectory'])
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
        self.button_group.setExclusive(True)
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
        self.metadata_table = MetadataTableWidget(needs_buttons=False)
        self.layout_window_h.addWidget(self.metadata_table)
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
        self.textbox_msg = QLabel("")
        self.button_dlg_close = QDialogButtonBox.StandardButton.Close
        self.buttonBox_dlg = QDialogButtonBox(self.button_dlg_close)
        self.buttonBox_dlg.clicked.connect(self.dlg.close)
        self.layout_window_dlg.addWidget(self.textbox_msg)
        self.layout_window_dlg.addWidget(self.buttonBox_dlg)
        self.dlg.setLayout(self.layout_window_dlg)

        self.container.setLayout(self.layout_window_h)
        self.setCentralWidget(self.container)

    def _read_button_click(self):
        location = QFileDialog.getExistingDirectory(self, 'Open Folder containing data',dir=str(self.input_dir))
        if not (self.md3_checkbox.isChecked()) and not (self.md4_checkbox.isChecked()):
            self._display_dialog('Error!', "You must choose atleast one extension using the checkboxes.")
            return
        if len(location) == 0:
            print(f"Data directory cant be empty!")
            self._display_dialog('Error!', "Data directory cant be empty!")
            return
        else:
            try:
                self.directory = location
                print(f"Currently chosen directory: {self.directory}")
                self.input_textbox.setText(f"Currently chosen directory: {self.directory}")
                csv_writer = PandasUtils
                args = []
                filetype = ''
                if self.md3_checkbox.isChecked():
                    filetype = 'MD3'
                    for file in Path(self.directory).glob('*.md3'):
                        args.append((file, ))
                elif self.md4_checkbox.isChecked():
                    filetype = 'MD4'
                    for file in Path(self.directory).glob('*.md4'):
                        args.append((file, ))
                start_time = time.perf_counter()
                raw_data_all = list(starmap(MDreader.read_raw_data, args))
                if len(raw_data_all) == 0:
                    self._display_dialog('Error!', "No data found!")
                    return
                end_time = time.perf_counter()
                output_folder_name = raw_data_all[0][1]['datetime'].strftime('%d%m%Y')
                root_output_path = Path(self.output_dir) / Path(filetype) / Path(output_folder_name)
                root_output_path.mkdir(parents=True, exist_ok=True)
                for raw_data in raw_data_all:
                    file_list, metadata, height, frequency, freqs, dop_shifts, complex_signal = raw_data
                    len_data = len(complex_signal)
                    final_partition_rindex = list(metadata['timepartitions'].values())[-1]
                    if len_data != final_partition_rindex:
                        raise BadIndicesInData(metadata, complex_signal, file_list[0])
                    if isinstance(metadata['datetime'], datetime):
                        time_str = metadata['datetime'].strftime('%H%M%S')
                    else:
                        continue
                    file_name = file_list[0]
                    metadata_path = root_output_path / Path(f"header{time_str}.json")
                    sensors_path = root_output_path / Path(f"sensor_data{time_str}.csv")
                    df: pd.DataFrame = csv_writer.create_pandas_from_arrays(metadata, frequency, height, dop_shifts, complex_signal)
                    heights: pd.Series = df['height (km)']
                    new_heights = heights.convert_dtypes(convert_integer=True)
                    power = convert_amplitude_to_power(complex_signal)
                    df['height (km)'] = new_heights
                    df['power'] = power
                    df["freq (Hz)"] /=1e6
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=4, default=str)
                    df.to_csv(sensors_path, date_format='%d %m %Y %H %M %S', sep='\t', float_format='%.3f', header=False)
                print(f"Output files written in {(end_time-start_time):.4f} seconds")
                self._display_dialog('Done!', f"Saved ASCII decoded data to {root_output_path}")
            except BadIndicesInData as e:
                print(e)
                self._display_dialog('Error!', str(e))
            except Exception as e:
                print(f"An error has occurred: {e}")

    def _display_dialog(self, title, message):
        self.dlg.setWindowTitle(title)
        self.textbox_msg.setText(message)
        self.dlg.exec()
        self._cleanup_dlg()

    def _cleanup_dlg(self):
        self.dlg.setWindowTitle("")
        self.textbox_msg.setText("")

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
            print(f"Input directory cant be empty!")
            self._display_dialog('Error!', "Input directory cant be empty!")
            return

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
            print(f"Output directory cant be empty!")
            self._display_dialog('Error!', "Output directory cant be empty!")
            return
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CADIreader()
    window.show()
    app.exec()