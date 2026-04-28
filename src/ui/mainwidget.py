from configparser import ConfigParser
from pathlib import Path
from src.ui.metadatatable import MetadataTableWidget
from src.ui.freq_list_dropdown import CheckableDropdown
from src.plotstate.factory import PlotStateFactory
from src.ui.mainwidgetservice import MainWidgetService
from src.ui.metadatakeys import cadi_keys_list, sameer_keys_list
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, 
    QCheckBox, QButtonGroup,
    QGridLayout, QDialog, QDialogButtonBox,
    QComboBox, QHBoxLayout
)

class MainWidget(QWidget):
    md3_options = ['Range Time Frequency', 'Range Time Intensity', 'EW-NS timeseries', 'Drift velocity timeseries']
    md4_options = ['Display ionogram', 'Real height analysis', 'Scale ionogram', 'EW-NS vs Range', 'Range Time Intensity']
    
    def __init__(self):
        super().__init__()
        self.polan_dir = None
        self.service = MainWidgetService(self)
        # Canvas parameters to be used later
        self.canvas_layout_row = 2
        self.canvas_layout_col = 3
        self.canvas_layout_rowspan = 8
        self.canvas_layout_colspan = 3
        self.canvas_widget = None
        self.current_plot_state = None
        self.has_handled_calculation = False

        # Folder selector buttons and label
        self.label = QLabel("No folder selected")
        self.button = QPushButton("Select Folder")
        
        # Multi-folder selection
        self.multi_folder_checkbox = QCheckBox("multi-folder")
        self.multi_folder_checkbox.toggled.connect(self._on_multi_folder_toggled)
        self.multi_folder_dropdown = QComboBox()
        self.multi_folder_dropdown.setVisible(False)
        self.multi_folder_dropdown.currentIndexChanged.connect(self._on_multi_folder_index_changed)
        self.multi_folder_data = []
        self.files_list = []

        # Filetype selection
        self.button.clicked.connect(self.open_folder)
        self.md3_checkbox = QCheckBox("md3 format")
        self.md4_checkbox = QCheckBox("md4 format")
        self.iono_checkbox = QCheckBox("iono format")
        self.md4_checkbox.setChecked(True)
        self.filetype_button_group = QButtonGroup()
        self.filetype_button_group.addButton(self.md3_checkbox)
        self.filetype_button_group.addButton(self.md4_checkbox)
        self.filetype_button_group.addButton(self.iono_checkbox)
        self.filetype_button_group.setExclusive(True)
        self.md3_checkbox.stateChanged.connect(self._on_tickbox_changed)
        self.md4_checkbox.stateChanged.connect(self._on_tickbox_changed)
        self.iono_checkbox.stateChanged.connect(self._on_tickbox_changed)
        
        # POLAN button
        self.polan_button = QPushButton("POLAN")
        self.polan_button.setVisible(False)  # Hidden initially
        self.polan_button.clicked.connect(self._polan_manual_helper)
        
        # Add Reset Zoom button
        self.reset_zoom_button = QPushButton("Reset Zoom")
        self.reset_zoom_button.setVisible(False)  # Hidden initially
        self.reset_zoom_button.clicked.connect(self._reset_zoom_helper)
        
        # Save Scaling button
        self.save_scale_button = QPushButton("Save Scaling")
        self.save_scale_button.setVisible(False)  # Hidden initially
        self.save_scale_button.clicked.connect(self._save_manual_scale)
        self.clear_scale_button = QPushButton("Clear Scaling")
        self.clear_scale_button.setVisible(False)  # Hidden initially
        self.clear_scale_button.clicked.connect(self._clean_scaled_canvas)
        
        # Manual scaling modes
        self.scale_mode_group = QButtonGroup()
        self.f_scale_box = QCheckBox('Scale F')
        self.e_scale_box = QCheckBox('Scale E')
        self.ie_scale_box = QCheckBox('Scale IE')
        self.scale_mode_group.addButton(self.f_scale_box)
        self.scale_mode_group.addButton(self.e_scale_box)
        self.scale_mode_group.addButton(self.ie_scale_box)
        self.scale_mode_group.setExclusive(True)
        self.f_scale_box.setVisible(False)
        self.e_scale_box.setVisible(False)
        self.ie_scale_box.setVisible(False)
        
        # ES Scaling controls
        self.es_scaling_label = QLabel("ES scaling")
        self.es_scaling_label.setVisible(False)
        self.es_scaling_dropdown = QComboBox()
        self.es_scaling_options = ["None", "ES(Q)", "ES(B)", "ES(H)", "ES(S)"]
        self.es_scaling_dropdown.addItems(self.es_scaling_options)
        self.es_scaling_dropdown.setCurrentIndex(0)
        self.es_scaling_dropdown.setVisible(False)
        self.es_scaling_dropdown.currentIndexChanged.connect(self._on_es_scaling_changed)
        self._es_scaling_mode = 0

        # Mode selection dropdown
        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(MainWidget.md4_options)
        
        # Create container widget + layout for dropdown + Run button
        self.mode_dropdown_container = QWidget()
        self.mode_dropdown_layout = QHBoxLayout()
        self.mode_dropdown_layout.setContentsMargins(0, 0, 0, 0)
        self.mode_dropdown_layout.setSpacing(5)
        self.mode_dropdown_container.setLayout(self.mode_dropdown_layout)

        # Add mode selection dropdown and Run button to this layout
        self.run_button = QPushButton("Run")
        self.run_button.setEnabled(False)
        self.mode_dropdown_layout.addWidget(self.mode_dropdown)
        self.mode_dropdown_layout.addWidget(self.run_button)
        self.run_button.clicked.connect(self._run_button_callback)
        
        self.freq_selector = CheckableDropdown(text="Select Frequencies")
        self.freq_selector.setVisible(False)
        self.freq_selector.selectionChanged.connect(self._on_freq_selector_updated)
        
        # Grid layout
        layout = QGridLayout()
        layout.addWidget(self.button, 1, 0)
        layout.addWidget(self.multi_folder_dropdown, 1, 1)
        layout.addWidget(self.multi_folder_checkbox, 1, 2)
        layout.addWidget(self.md3_checkbox, 2, 0)
        layout.addWidget(self.md4_checkbox, 2, 1)
        layout.addWidget(self.iono_checkbox, 2, 2)
        layout.addWidget(self.mode_dropdown_container, 3, 0, 1, 2)
        layout.setColumnStretch(4, 1)

        # Custom table widget for metadata table and navigation
        self.table_widget = MetadataTableWidget()
        self.table_widget.end_timepartitions_dropdown.setVisible(False)

        # Add table widget, POLAN, and scaling buttons to the layout        
        layout.addWidget(self.table_widget, 4, 0, 2, 2)
        layout.addWidget(self.f_scale_box, 6, 0)
        layout.addWidget(self.e_scale_box, 6, 1)
        layout.addWidget(self.ie_scale_box, 6, 2)
        layout.addWidget(self.es_scaling_label, 7, 0)
        layout.addWidget(self.es_scaling_dropdown, 7, 1)
        layout.addWidget(self.freq_selector, 8, 0)
        layout.addWidget(self.polan_button, 8, 0)
        layout.addWidget(self.reset_zoom_button, 8, 2)
        layout.addWidget(self.save_scale_button, 8, 0)
        layout.addWidget(self.clear_scale_button, 8, 1)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Initialize signal handling
        self.table_widget.dropdown_changed.connect(self._on_dropdown_changed)
        self.table_widget.right_dropdown_changed.connect(self._on_right_dropdown_changed)
        self.table_widget.left_clicked.connect(self._prev_option)
        self.table_widget.right_clicked.connect(self._next_option)

        self.setLayout(layout)
        
        self._selected_timestamp = ''
        self._right_selected_timestamp = ''
        self.folder_path = None
        self.prev_folder_path = None
        self.prev_checkbox = None
        self.folder_changed = False

        # Error message dialog box
        self.dlg = QDialog(self)
        self.dlg.setWindowTitle("Error!")
        self.layout_dlg = QVBoxLayout()
        self.textbox_errormsg = QLabel("")
        self.buttonBox_dlg = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttonBox_dlg.clicked.connect(self.dlg.close)
        self.layout_dlg.addWidget(self.textbox_errormsg)
        self.layout_dlg.addWidget(self.buttonBox_dlg)
        self.dlg.setLayout(self.layout_dlg)

        self.threadpool = QThreadPool()
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")
        
    def init_config(self, config: ConfigParser):
        self.polan_dir = Path(config['Locations']['polanoutputdirectory'])
        self.input_dir = Path(config['Locations']['DefaultInputDirectory'])
        self.parquet_cache_dir = Path(config['Locations']['cachedir'])
        self.colormap = config['plotting']['colormap']
        self.scatter_size = config.getint('plotting', 'scattersize')
        self.power_limit = config.getint('plotting', 'powerlimit')
        self.polan_interp_mode = config.get('realheightanalysis', 'interpmode')
        self.scaling_line_width = config.getfloat('scaling', 'linewidth')
        if self.polan_interp_mode not in ['old', 'new', 'OLD', 'NEW']:
            raise ValueError(f"POLAN interpolation mode must be 'old' or 'new', got {self.polan_interp_mode} instead.")
        
    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", dir=str(self.input_dir))
        if folder_path:
            self.folder_path = Path(folder_path)
            self._run_button_callback()
        
    def _run_button_callback(self):
        if self.folder_path:
            self.run_button.setEnabled(False)
            self._loading_folder_path = self.folder_path
            self.service.load_data(self.folder_path)

    def _on_multi_folder_toggled(self, state):
        is_checked = self.multi_folder_checkbox.isChecked()
        self.multi_folder_dropdown.setVisible(is_checked)
        if not is_checked and len(self.multi_folder_data) > 1:
            # Keep only the first folder
            self.multi_folder_data = [self.multi_folder_data[0]]
            from src.utils.pandasutils import PandasUtils
            self.combined_df, self.combined_metadata = PandasUtils.combine_folder_data(self.multi_folder_data)
            self.update_multi_folder_dropdown()
            self.switch_to_combined_data()

    def _on_multi_folder_index_changed(self, index):
        # The folder_dropdown is only an indication of what folders were added
        pass

    def update_multi_folder_dropdown(self):
        self.multi_folder_dropdown.blockSignals(True)
        self.multi_folder_dropdown.clear()
        for data in self.multi_folder_data:
            folder_name = data['folder_path'].name
            self.multi_folder_dropdown.addItem(folder_name)
        
        # Try to keep the current folder selected in the dropdown
        if hasattr(self, 'folder_path'):
            for i, data in enumerate(self.multi_folder_data):
                if data['folder_path'] == self.folder_path:
                    self.multi_folder_dropdown.setCurrentIndex(i)
                    break
        self.multi_folder_dropdown.blockSignals(False)

    def switch_to_combined_data(self):
        # Update metadata display and internal state using combined data
        self.metadata = self.combined_metadata
        self.timepartitions = self.metadata['timepartitions']
        self.files_list = list(dict.fromkeys([filename for data in self.multi_folder_data for filename in data['files_list']]))
        # Use first and last keys from combined timepartitions for selection
        self._selected_timestamp = list(self.timepartitions.keys())[0]
        self._right_selected_timestamp = list(self.timepartitions.keys())[-1]

        if self.md3_checkbox.isChecked():
            keys_list = cadi_keys_list
        elif self.md4_checkbox.isChecked():
            keys_list = cadi_keys_list
        elif self.iono_checkbox.isChecked():
            keys_list = sameer_keys_list
        else:
            keys_list = cadi_keys_list

        # Note: freqs_list and other details are assumed consistent across folders
        # Use freqs_list from the first folder in the multi-folder data if available
        if len(self.multi_folder_data) > 0:
            self.freqs_list = self.multi_folder_data[0]['freqs_list']
            self.freq_selector.setItems(items=[str(freq/1e6) for freq in self.freqs_list])

        # Re-connect signals to avoid recursion
        try:
            self.table_widget.left_clicked.disconnect(self._prev_option)
        except (TypeError, RuntimeError):
            pass
        try:
            self.table_widget.right_clicked.disconnect(self._next_option)
        except (TypeError, RuntimeError):
            pass

        self.table_widget.update_metadata(self.metadata, keys_list)
        self.table_widget.left_clicked.connect(self._prev_option)
        self.table_widget.right_clicked.connect(self._next_option)

        self.has_handled_calculation = False
        self._plot_helper()
        
        if self.multi_folder_checkbox.isChecked():
            self.label.setText(f"Combined data: {len(self.multi_folder_data)} folders")
        else:
            self.label.setText(f"Selected: {self.folder_path.parent.parent.name}/{self.folder_path.parent.name}/{self.folder_path.name}")
        self.run_button.setEnabled(True)

    def _on_freq_selector_updated(self, sel):
        if self.canvas_widget and self.canvas_widget.__class__.__name__ in ('XYPlotCanvas', 'RangeTimeFreqCanvas', 'RangeTimeIntensCanvas'):
            self._plot_helper()

    def _on_tickbox_changed(self):
        if self.md3_checkbox.isChecked():
            self.mode_dropdown.clear()
            self.mode_dropdown.addItems(MainWidget.md3_options)
        elif self.md4_checkbox.isChecked():
            self.mode_dropdown.clear()
            self.mode_dropdown.addItems(MainWidget.md4_options)
        elif self.iono_checkbox.isChecked():
            self.mode_dropdown.clear()
            self.mode_dropdown.addItems(MainWidget.md4_options)

    def _on_dropdown_changed(self, text):
        self._selected_timestamp = text
        self._plot_helper()
    
    def _on_right_dropdown_changed(self, text):
        if self.canvas_widget and self.canvas_widget.__class__.__name__ in ('XYPlotCanvas', 'RangeTimeFreqCanvas', 'RangeTimeIntensCanvas'):
            self._right_selected_timestamp = text
            self._plot_helper()

    def _plot_helper(self):
        new_state = PlotStateFactory.get_state(self)
        curr_checkbox = "md4" if self.md4_checkbox.isChecked() else ("md3" if self.md3_checkbox.isChecked() else "iono")
        
        if self.prev_checkbox is None:
            self.prev_checkbox = curr_checkbox

        need_new_canvas = (
            self.canvas_widget is None or
            not isinstance(self.current_plot_state, type(new_state)) or 
            not self.prev_checkbox == curr_checkbox
        )

        if self.folder_path is not None:
            if self.folder_path != self.prev_folder_path:
                self.folder_changed = True
                self.prev_folder_path = self.folder_path
            else:
                self.folder_changed = False
        else:
            self.folder_changed = True

        if self.folder_changed or need_new_canvas:
            if not self.has_handled_calculation:
                is_computing = self.service.handle_computation(new_state)
                if is_computing:
                    return
            self.folder_changed = False

        if need_new_canvas:
            if self.canvas_widget is not None:
                self.layout().removeWidget(self.canvas_widget)
                self.canvas_widget.setParent(None)
                self.canvas_widget.deleteLater()
                self.canvas_widget = None

            self.canvas_widget = new_state.create_canvas()
            self.canvas_widget.setHidden(True)
            self.layout().addWidget(
                self.canvas_widget,
                self.canvas_layout_row,
                self.canvas_layout_col,
                self.canvas_layout_rowspan,
                self.canvas_layout_colspan,
            )
            self.canvas_widget.setHidden(False)
            self.current_plot_state = new_state
        else:
            self.current_plot_state.update_canvas(self.canvas_widget)
        
        self.prev_checkbox = curr_checkbox
        self.service.polan_auto_helper()
        self._autoscale_helper()

    def _autoscale_helper(self):
        pass

    def _save_manual_scale(self):
        self.service.save_manual_scale()

    def _clean_scaled_canvas(self):
        if self.canvas_widget and self.canvas_widget.__class__.__name__ == 'ScaleIonogramCanvas':
            self.canvas_widget.clean_canvas()

    def _polan_manual_helper(self):
        self.service.polan_manual_helper()

    def _reset_zoom_helper(self):
        if hasattr(self.canvas_widget, 'reset_zoom') and callable(self.canvas_widget.reset_zoom):
            self.canvas_widget.reset_zoom()

    def _on_es_scaling_changed(self, index):
        self._es_scaling_mode = index

    def _prev_option(self):
        dropdown = self.table_widget.timepartitions_dropdown
        current_index = dropdown.currentIndex()
        new_index = current_index - 1 if current_index > 0 else dropdown.count() - 1
        dropdown.setCurrentIndex(new_index)
    
    def _next_option(self):
        dropdown = self.table_widget.timepartitions_dropdown
        current_index = dropdown.currentIndex()
        new_index = current_index + 1 if current_index < dropdown.count() - 1 else 0
        dropdown.setCurrentIndex(new_index)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.table_widget.left_button.click()
        elif event.key() == Qt.Key_Right:
            self.table_widget.right_button.click()
        else:
            super().keyPressEvent(event)
