import sys
from src.ui.mainwidget import MainWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox
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
            'data': {
                'defaultoutputformat': 'csv',
                'sep': ',',
                'filetype': 'whole'
            },
            'plotting': {
                'powercolormap': 'jet_r',
                'dopcolormap': 'viridis',
                'scattersize': '6',
                'powerlimit': '50',
                'maxfreq': '20'
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

        self._build_menu_bar()

        self.showMaximized()

    def _build_menu_bar(self):
        main_widget = self.main_widget
        menu_bar = self.menuBar()

        # ── File ──────────────────────────────────────────────────────────
        file_menu = menu_bar.addMenu("&File")

        self.action_open_folder = file_menu.addAction("&Open Folder...")
        self.action_open_folder.setShortcut("Ctrl+O")
        self.action_open_folder.triggered.connect(main_widget.open_folder)

        file_menu.addSeparator()

        self.action_save_plot = file_menu.addAction("Save &Plot...")
        self.action_save_plot.setShortcut("Ctrl+S")
        self.action_save_plot.setEnabled(False)
        self.action_save_plot.triggered.connect(main_widget._run_save_fig_callback)

        self.action_save_data = file_menu.addAction("Save &Data...")
        self.action_save_data.setShortcut("Ctrl+Shift+S")
        self.action_save_data.triggered.connect(main_widget._run_save_data_callback)

        file_menu.addSeparator()

        action_exit = file_menu.addAction("E&xit")
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)

        # ── Help ──────────────────────────────────────────────────────────
        help_menu = menu_bar.addMenu("&Help")

        action_about = help_menu.addAction("&About")
        action_about.triggered.connect(self._show_about)

        # Expose menu actions on main_widget so it can enable/disable them
        main_widget._menu_action_save_plot = self.action_save_plot
        main_widget._menu_action_save_data = self.action_save_data

    def _show_about(self):
        QMessageBox.about(
            self,
            "About CADI Ionogram Tool",
            "<b>CADI Ionogram Tool</b><br>"
            "Ionogram analysis and visualisation tool developed at EGRL, Indian Institute of Geomagnetism under DECA Project."
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
