import sys
from src.ui.mainwidget import MainWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow
)
from pathlib import Path
import configparser
import platform

class MainWindow(QMainWindow):
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
        self.main_widget = MainWidget()
        self.main_widget.polan_dir = self.polan_dir
        self.main_widget.input_dir = self.input_dir
        self.main_widget.parquet_cache_dir = self.parquet_cache_dir
        self.setWindowTitle("CADI Ionogram Plotter")
        self.setCentralWidget(self.main_widget)
        self.resize(1366, 768)
        self.setMinimumSize(1280, 720)
        self.showMaximized()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
