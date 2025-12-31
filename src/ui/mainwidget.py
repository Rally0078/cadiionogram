from pathlib import Path
from datetime import datetime
from src.errorhandlers.errorhandling import FolderNotContainingData
from src.plot.realheightanalysis import RealHeightAnalysisCanvas
from src.plot.autoscaling import ScaleIonogramCanvas
from src.plot.xyplotcanvas import XYPlotCanvas
from src.ui.metadatatable import MetadataTableWidget
from src.ui.metadatakeys import cadi_keys_list, sameer_keys_list
from src.ui.freq_list_dropdown import CheckableDropdown
from src.utils.siteinfo import site_dict
from src.plotstate.factory import PlotStateFactory
from src.ionogramparser.mdxreader import MDreader
from src.ionogramparser.sameerreader import SameerReader
from src.utils.rawdatadiriterator import RawDataDirIterator
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, 
    QCheckBox, QButtonGroup,
    QGridLayout, QDialog, QDialogButtonBox,
    QComboBox, QHBoxLayout
)
import subprocess
import shutil
from math import isnan

class MainWidget(QWidget):
    md3_options = ['Range Time Frequency', 'Range Time Intensity', 'EW-NS timeseries', 'Drift velocity timeseries']
    md4_options = ['Display ionogram', 'Real height analysis', 'Scale ionogram', 'EW-NS vs Range', 'Range Time Intensity']
    def __init__(self):
        super().__init__()
        self.polan_dir = None
        # Canvas parameters to be used later
        self.canvas_layout_row = 2
        self.canvas_layout_col = 3
        self.canvas_layout_rowspan = 8
        self.canvas_layout_colspan = 3
        self.canvas_widget = None
        self.lpointer = -1
        self.rpointer = -1
        self.current_plot_state = None

        # Folder selector buttons and label
        self.label = QLabel("No folder selected")
        self.button = QPushButton("Select Folder")
        
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
        #Save Scaling button
        self.save_scale_button = QPushButton("Save Scaling")
        self.save_scale_button.setVisible(False)  # Hidden initially
        self.save_scale_button.clicked.connect(self._save_manual_scale)
        self.clear_scale_button = QPushButton("Clear Scaling")
        self.clear_scale_button.setVisible(False)  # Hidden initially
        self.clear_scale_button.clicked.connect(self._clean_scaled_canvas)
        #Manual scaling modes
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
        
        # Mode selection dropdown
        self.mode_dropdown = QComboBox()
        
        # Default mode is md4
        self.mode_dropdown.addItems(MainWidget.md4_options)
        
        # Create container widget + layout for dropdown + Run button
        self.mode_dropdown_container = QWidget()
        self.mode_dropdown_layout = QHBoxLayout()
        self.mode_dropdown_layout.setContentsMargins(0, 0, 0, 0)
        self.mode_dropdown_layout.setSpacing(5)
        self.mode_dropdown_container.setContentsMargins(0, 0, 0, 0)
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

        # Folder selection and label
        layout.addWidget(self.button, 1, 0)
        #layout.addWidget(self.label, 4, 0)

        # Checkboxes
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
        layout.addWidget(self.f_scale_box, 6,0)
        layout.addWidget(self.e_scale_box, 6,1)
        layout.addWidget(self.ie_scale_box, 6,2)
        layout.addWidget(self.freq_selector, 7,2)
        layout.addWidget(self.polan_button, 7, 1)
        layout.addWidget(self.save_scale_button, 7,0)
        layout.addWidget(self.clear_scale_button, 7, 1)
        # Set margins and spacing
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        #Initialize signal handling
        self.table_widget.dropdown_changed.connect(self._on_dropdown_changed)
        self.table_widget.right_dropdown_changed.connect(self._on_right_dropdown_changed)
        self.table_widget.left_clicked.connect(self._prev_option)
        self.table_widget.right_clicked.connect(self._next_option)

        self.setLayout(layout)
        
        self._selected_timestamp = ''
        self._right_selected_timestamp = ''
        self.directory = None

        #Error message dialog box
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
        self.prev_checkbox = None
        self.last_folder_path = None
        
    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", dir=str(self.input_dir))
        folder_path = Path(folder_path)
        self.last_folder_path = folder_path
        self._run_button_callback()
        
    def _run_button_callback(self):
        if self.last_folder_path:
            try:
                self.plot_widget_table(self.last_folder_path)
                self.label.setText(f"Selected: {self.last_folder_path.parent.parent.name +  self.last_folder_path.parent.name + self.last_folder_path.name}")
                self.run_button.setEnabled(True)
            except FolderNotContainingData:
                self.textbox_errormsg.setText("You must choose a folder containing the data.")
                self.dlg.exec()
                self.run_button.setEnabled(False)
                return
    #Create table and plot the selected canvas when a valid folder is selected.
    def plot_widget_table(self, location):
        self.directory = location
        print(f"Currently chosen directory: {self.directory}")
        
        #TODO: Dropdown list for md1-md4 formats?
        if self.md3_checkbox.isChecked():
            extension = 'md3'
            raw_reader = MDreader()
            keys_list = cadi_keys_list
        if self.md4_checkbox.isChecked():
            extension = 'md4'
            raw_reader = MDreader()
            keys_list = cadi_keys_list
        if self.iono_checkbox.isChecked():
            extension = 'iono'
            raw_reader = SameerReader()
            keys_list = sameer_keys_list
        self.extension = extension
        #Note: Throws FolderNotContainingData exception if md3/4 is not found in the directory
        self.files_list, self.metadata, self.heights, self.freqs, self.freqs_list, self.dops, self.signals = raw_reader.read_raw_data_dir(location, extension)
        self.freq_selector.setItems(items=[str(freq/1e6) for freq in self.freqs_list])
        self.timepartitions = self.metadata['timepartitions']
        #Default timestamp to start with is the first timestamp
        self._selected_timestamp = list(self.timepartitions.keys())[0]
        self._right_selected_timestamp = list(self.timepartitions.keys())[-1]

        #Update metadata when new folder is selected
        #Disconnect signals before updating
        self.table_widget.left_clicked.disconnect(self._prev_option)
        self.table_widget.right_clicked.disconnect(self._next_option)

        # Call the update_metadata function in MetadataTableWidget
        self.table_widget.update_metadata(self.metadata, keys_list)

        # Reconnect the signals after the update to ensure the buttons work again
        self.table_widget.left_clicked.connect(self._prev_option)
        self.table_widget.right_clicked.connect(self._next_option)
        
        #Do the initial plotting with the given lpointer and rpointer
        self._plot_helper()

    def _on_freq_selector_updated(self, sel):
        if isinstance(self.canvas_widget, XYPlotCanvas):
            self._plot_helper()

    #Callback to handle tickboxes
    def _on_tickbox_changed(self):
        if self.md3_checkbox.isChecked():
            self.mode_dropdown.clear()
            self.mode_dropdown.addItems(MainWidget.md3_options)
        if self.md4_checkbox.isChecked():
            self.mode_dropdown.clear()
            self.mode_dropdown.addItems(MainWidget.md4_options)
        if self.iono_checkbox.isChecked():
            self.mode_dropdown.clear()
            self.mode_dropdown.addItems(MainWidget.md4_options)

    #Callback to handle changes in dropdown value
    def _on_dropdown_changed(self, text):
        self._selected_timestamp = text
        self._plot_helper()
    
    #Callback to handle changes in right side dropdown value
    def _on_right_dropdown_changed(self, text):
        if isinstance(self.canvas_widget, XYPlotCanvas):
            self._right_selected_timestamp = text
            self._plot_helper()
        else:
            pass
    
    #Main plotting function. Delegates the choice of canvas to PlotStateFactory based on the mdx file option and the type of plot
    def _plot_helper(self):
        new_state = PlotStateFactory.get_state(self)
        curr_checkbox = "md4" if self.md4_checkbox.isChecked() else "md3"
        if self.prev_checkbox is None:
            self.prev_checkbox = curr_checkbox
        # Determine whether the canvas needs to be replaced
        need_new_canvas = (
            self.canvas_widget is None or
            not isinstance(self.current_plot_state, type(new_state)) or 
            not self.prev_checkbox == curr_checkbox
        )
        print(f"is new canvas needed: {need_new_canvas}, prev_checkbox={self.prev_checkbox}, curr_checkbox={curr_checkbox}, equal? {self.prev_checkbox == curr_checkbox}")
        if need_new_canvas:
            # Remove and delete the existing canvas widget if it exists
            if self.canvas_widget is not None:
                self.layout().removeWidget(self.canvas_widget)
                self.canvas_widget.setParent(None)
                self.canvas_widget.deleteLater()
                self.canvas_widget = None

            # Create and add the new canvas
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

        # Update the canvas using the new state
        else:
            new_state.update_canvas(self.canvas_widget)
        self.prev_checkbox = curr_checkbox
        # Track the current state
        self.current_plot_state = new_state
        self._polan_auto_helper()
        self._autoscale_helper()
    
    #TODO
    def _autoscale_helper(self):
        pass

    def _save_manual_scale(self):
        if isinstance(self.canvas_widget, ScaleIonogramCanvas):
            datetime_obs: datetime = self.metadata['datetime']
            new_timestamp = self._selected_timestamp.replace(':', '')[:-2]
            timestamp_hour = int(self._selected_timestamp.replace(':', '')[:2])
            timestamp_minute = int(self._selected_timestamp.replace(':', '')[2:4])
            timestamp_second = int(self._selected_timestamp.replace(':', '')[4:6])
            output_file_nominute_name = Path(self.files_list[timestamp_hour]).stem[:4]
            output_filename = f"{datetime_obs.strftime('%y%m%d')}{site_dict[self.metadata['site']].short_site}_F.tfh"
            output_file_name = f"{self.polan_dir / output_filename}"
            scaled_values_state = self.canvas_widget.scaled_values_lines
            scaled_values_state.set_region('F')
            fof = scaled_values_state.f
            hprimef = scaled_values_state.h
            scaled_values_state.set_region('E')
            foe = scaled_values_state.f
            hprimee = scaled_values_state.h
            scaled_values_state.set_region('IE')
            foie = scaled_values_state.f
            hprimeie = scaled_values_state.h
            with open(output_file_name, 'a') as f:
                f.write((f"{timestamp_hour:02d} {timestamp_minute:02d} {timestamp_second:02d} " \
                f"{'NaN ' if isnan(fof) else f'{fof:.2f}'} {'NaN ' if isnan(hprimef) else f'{hprimef:.2f}'} " \
                f"{'NaN ' if isnan(foe) else f'{foe:.2f}'} {'NaN ' if isnan(hprimee) else f'{hprimee:.2f}'} " \
                f"{'NaN ' if isnan(foie) else f'{foie:.2f}'} {'NaN ' if isnan(hprimeie) else f'{hprimeie:.2f}'}\n"))
        else:
            print(f"Not scaling canvas! Use the appropriate canvas")
    def _clean_scaled_canvas(self):
        if isinstance(self.canvas_widget, ScaleIonogramCanvas):
            self.canvas_widget.clean_canvas()

    # Run POLAN by outputting fit curve into a file and executing the POLAN executable, then read from the POLAN's output text file POLOUT.T
    def _run_polan(self, freqs, heights, ml_freqs, ml_heights):
        real_freqs = []
        real_heights = []
        if len(freqs) > 0:
            short_datetime: datetime = self.metadata['datetime']
            with open("a.a", 'w') as polan_input:
                polan_input.write("OUTPUT MODE ==>          -9.00  0.0  0.0  0.0    0\n")
                polan_input.write(f"Date = {short_datetime.year-2000}{short_datetime.month:02d}{short_datetime.day:02d}{site_dict[self.metadata['site']].short_site}           {site_dict[self.metadata['site']].FH:.2f}  {site_dict[self.metadata['site']].dip:.1f}  0.0 0.00    0\n")
                polan_input.write(f"{self._selected_timestamp}                    0.0\n")
                for idx, (freq, height) in enumerate(zip(freqs, heights)):
                    if idx == len(freqs) - 1:
                        height = 0.0
                    polan_input.write(f"{freq}, {float(round(height)):.2f}\n")
                polan_input.write(f"0.0, 0.0")
            subprocess.run('./polan.exe')
            stop_reading = False
            with open("POLOUT.T", 'r') as polan_output:
                lines = polan_output.readlines()
                for i, line in enumerate(lines):
                    if "Real Heights" in line:
                        data_start_index = i + 1
                        break
                else:
                    raise ValueError('"Real Heights" not found in file')
                for line in lines[data_start_index:]:
                    if stop_reading:
                        break
                    if line.strip() == '' or '*' in line:
                        break
                    try:
                        floats = list(map(float, line.strip().split()))
                    except ValueError:
                        # Raise exception if non numeric value, cant parse as a number.
                        raise ValueError(f"Non-numeric value found in line: {line}")
                    line_freqs = floats[::2]
                    line_heights = floats[1::2]
                    
                    for f, h in zip(line_freqs, line_heights):
                        if h <= 50 or f <= 0.25:
                            stop_reading = True
                            break
                        real_freqs.append(f)
                        real_heights.append(h)
            input_file_name = f"POLOUT.T"
            new_timestamp = self._selected_timestamp.replace(':', '')[:-2]
            timestamp_hour = int(self._selected_timestamp.replace(':', '')[:2])
            #Warn: The following line works only for H type (hourly) MDx files 
            #This might not work as intended with I type(file per observation) MDx files
            output_file_nominute_name = Path(self.files_list[timestamp_hour]).stem[:4]
            
            new_output_file_name = output_file_nominute_name + new_timestamp
            output_file_name = f"{self.polan_dir / new_output_file_name}.pol"
            #ml_output_filename = f"{self.polan_dir / new_output_file_name}.txt"
            shutil.copyfile(input_file_name, output_file_name)
            """with open(ml_output_filename, 'w') as f:
                for freq, height in zip(ml_freqs, ml_heights):
                    f.write(f"{freq}, {float(round(height)):.2f}\n")
                    """
            self.canvas_widget.plot_polan(real_freqs, real_heights, ml_freqs, ml_heights)
        else:
            print("No drawn curve or ionogram data to match.")
    #Run POLAN function that takes interpolated input data.
    #Could be moved into the real height canvas?
    def _polan_manual_helper(self):
        if isinstance(self.canvas_widget, RealHeightAnalysisCanvas):
            freqs, heights, ml_freqs, ml_heights = self.canvas_widget.draw_manual_curve()
            self._run_polan(freqs, heights, ml_freqs, ml_heights)
        else:
            print("Current canvas is not RealHeightAnalysisCanvas. POLAN analysis skipped.")

    def _polan_auto_helper(self):
        if isinstance(self.canvas_widget, RealHeightAnalysisCanvas):
            it = RawDataDirIterator(self.metadata, self.freqs, self.heights, self.dops, self.signals)
            freqs, heights, dops, signals = it[self._selected_timestamp]
            if self.extension == 'md4':
                freqs_interp, heights_interp, ml_freqs, ml_heights = self.canvas_widget.draw_auto_curve(freqs, heights, dops, signals)
                self._run_polan(freqs_interp, heights_interp, ml_freqs, ml_heights)
            else:
                print("Automatic curvefitting for .iono files is not implemented yet")
        else:
            print("Current canvas is not RealHeightAnalysisCanvas. POLAN analysis skipped.")
    #Callback to handle clicking left arrow or pressing left arrow key
    #Setting current index in dropdown calls the _on_dropdown_changed() with the new index as timestamp
    def _prev_option(self):
        dropdown = self.table_widget.timepartitions_dropdown
        current_index = dropdown.currentIndex()
        new_index = current_index - 1 if current_index > 0 else dropdown.count() - 1
        dropdown.setCurrentIndex(new_index)
    
    #Callback to handle clicking right arrow or pressing right arrow key
    #Setting current index in dropdown calls the _on_dropdown_changed() with the new index as timestamp
    def _next_option(self):
        dropdown = self.table_widget.timepartitions_dropdown
        current_index = dropdown.currentIndex()
        new_index = current_index + 1 if current_index < dropdown.count() - 1 else 0
        dropdown.setCurrentIndex(new_index)

    #Keypress event handler
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.table_widget.left_button.click()
        elif event.key() == Qt.Key_Right:
            self.table_widget.right_button.click()
        else:
            super().keyPressEvent(event)