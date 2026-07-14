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

        # Ensure sites.json exists and is populated
        from src.utils.siteinfo import get_sites_json_path, DEFAULT_SITES
        import json
        sites_path = get_sites_json_path()
        if not sites_path.exists():
            sites_path.parent.mkdir(parents=True, exist_ok=True)
            with open(sites_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SITES, f, indent=4)

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
            },
            'plotting': {
                'powercolormap': 'jet_r',
                'dopcolormap': 'viridis',
                'scattersize': '6',
                'powerlimit': '50'
            },
            'realheightanalysis': {
                'interpmode': 'old',
                'savecleanformat': 'true',
                'start': '0.0',
                'amode': '0.0',
                'valley': '0.00',
                'list': '0'
            },
            'scaling': {
                'linewidth': '2',
                'scalingoption1': 'F',
                'scalingoption2': 'E',
                'scalingoption3': 'IE',
                'enableESscaling': 'true',
                'enablespreadFscaling': 'true'
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

        self.main_widget = MainWidget(config=self.config)
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
