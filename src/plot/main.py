import sys
from src.ui.mainwidget import MainWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow
)
from pathlib import Path
import configparser


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = configparser.ConfigParser()
        self.cfg_file = Path("./config.ini")

        if not self.cfg_file.exists():
            self.cfg_file.touch()
            self.config['Locations'] = {'DefaultInputDirectory': 'C:\\CADIinput',
                                        'DefaultOutputDirectory': 'C:\\CADIoutput',
                                        "polanoutputdirectory": "C:\\cdata"}
            self.polan_dir = Path(self.config['Locations']['polanoutputdirectory'])
            with open(self.cfg_file, 'w') as f:
                self.config.write(f)
        else:
            self.config.read(self.cfg_file)
            self.polan_dir = Path(self.config['Locations']['polanoutputdirectory'])
        self.main_widget = MainWidget()
        self.main_widget.polan_dir = self.polan_dir
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
