from pathlib import Path
from datetime import datetime
from src.errorhandlers.errorhandling import FolderNotContainingData
from src.plot.realheightanalysis import RealHeightAnalysisCanvas
from src.ui.metadatatable import MetadataTableWidget
from src.ui.metadatakeys import cadi_keys_list, sameer_keys_list
from src.utils.siteinfo import site_dict
from src.plotstate.factory import PlotStateFactory
from src.ionogramparser.mdxreader import MDreader
from src.ionogramparser.sameerreader import SameerReader
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

class MainWidget(QWidget):
    md3_options = ['Range vs Time (Freq colored)']
    md4_options = ['Display ionogram', 'Real height analysis', 'Range vs Time (Freq colored)']
    def __init__(self):
        super().__init__()
        self.polan_dir = None
        # Canvas parameters to be used later
        self.canvas_layout_row = 2
        self.canvas_layout_col = 3
        self.canvas_layout_rowspan = 6
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
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.md3_checkbox)
        self.button_group.addButton(self.md4_checkbox)
        self.button_group.addButton(self.iono_checkbox)
        self.button_group.setExclusive(True)
        self.md3_checkbox.stateChanged.connect(self._on_tickbox_changed)
        self.md4_checkbox.stateChanged.connect(self._on_tickbox_changed)
        self.iono_checkbox.stateChanged.connect(self._on_tickbox_changed)
        self.polan_button = QPushButton("POLAN")
        self.polan_button.setVisible(False)  # Hidden initially
        self.polan_button.clicked.connect(self._polan_manual_helper)
          # Next to dropdown
        
        # Mode selection dropbox
        self.dropbox = QComboBox()
        
        # Default mode is md4
        self.dropbox.addItems(MainWidget.md4_options)
        
        # Create container widget + layout for dropbox + Run button
        self.dropbox_container = QWidget()
        self.dropbox_layout = QHBoxLayout()
        self.dropbox_layout.setContentsMargins(0, 0, 0, 0)
        self.dropbox_layout.setSpacing(5)
        self.dropbox_container.setContentsMargins(0, 0, 0, 0)
        self.dropbox_container.setLayout(self.dropbox_layout)

        # Add dropbox and Run button to this layout
        self.run_button = QPushButton("Run")
        self.run_button.setEnabled(False)
        self.dropbox_layout.addWidget(self.dropbox)
        self.dropbox_layout.addWidget(self.run_button)
        self.run_button.clicked.connect(self._run_button_callback)
        
        # Grid layout
        layout = QGridLayout()

        # Folder selection and label
        layout.addWidget(self.button, 1, 0)
        #layout.addWidget(self.label, 4, 0)

        # Checkboxes
        layout.addWidget(self.md3_checkbox, 2, 0)
        layout.addWidget(self.md4_checkbox, 2, 1)
        layout.addWidget(self.iono_checkbox, 2, 2)
        layout.addWidget(self.dropbox_container, 3, 0, 1, 2)

        layout.setColumnStretch(4, 1)

        # Custom table widget for metadata table and navigation
        self.table_widget = MetadataTableWidget()

        # Set the margins and spacing        
        layout.addWidget(self.table_widget, 5, 0, 2, 2)
        layout.addWidget(self.polan_button, 7, 1)

        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        #Initialize signal handling
        self.table_widget.dropdown_changed.connect(self._on_dropdown_changed)
        self.table_widget.left_clicked.connect(self._prev_option)
        self.table_widget.right_clicked.connect(self._next_option)

        self.setLayout(layout)
        
        self._selected_timestamp = ''
        self.directory = None

        #Error message box
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
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
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
        self.timepartitions = self.metadata['timepartitions']
        #Default timestamp to start with is the first timestamp
        self._selected_timestamp = list(self.timepartitions.keys())[0]
        
        #Set initial lpointer and rpointer
        self._get_lpointer_rpointer(self.timepartitions, self._selected_timestamp)

        #Update metadata when new folder is selected
        #Disconnect signals before updating
        self.table_widget.left_clicked.disconnect(self._prev_option)
        self.table_widget.right_clicked.disconnect(self._next_option)

        # Call the update_metadata function in MetadataTableWidget
        self.table_widget.update_metadata(self.metadata, keys_list)

        # Reconnect the signals after the update to ensure the buttons work again
        self.table_widget.left_clicked.connect(self._prev_option)
        self.table_widget.right_clicked.connect(self._next_option)
        
        #Set initial pointers in the label
        self.table_widget.set_pointers(self.lpointer, self.rpointer)
        
        #Do the initial plotting with the given lpointer and rpointer
        self._plot_helper()
    
    #Callback to handle tickboxes
    def _on_tickbox_changed(self):
        if self.md3_checkbox.isChecked():
            self.dropbox.clear()
            self.dropbox.addItems(MainWidget.md3_options)
        if self.md4_checkbox.isChecked():
            self.dropbox.clear()
            self.dropbox.addItems(MainWidget.md4_options)
        if self.iono_checkbox.isChecked():
            self.dropbox.clear()
            self.dropbox.addItems(MainWidget.md4_options)

    #Callback to handle changes in dropdown value
    def _on_dropdown_changed(self, text):
        self._selected_timestamp = text
        self._get_lpointer_rpointer(self.timepartitions, timestamp=self._selected_timestamp)
        self.table_widget.set_pointers(self.lpointer, self.rpointer)
        self._plot_helper()

    #Get lpointer and rpointer for plotting
    def _get_lpointer_rpointer(self, timepartitions, timestamp):
        index = list(timepartitions.keys()).index(timestamp)
        self.file_timestamp_index = index
        lpointer = -1
        if index == 0:
            lpointer = 0
        else:
            prev_index = index - 1
            lpointer = timepartitions[list(timepartitions.keys())[prev_index]]
        rpointer = timepartitions[timestamp]
        self.timestamp = timestamp
        self.lpointer = lpointer
        self.rpointer = rpointer
    
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

    
    def _run_polan(self, freqs, heights, ml_freqs, ml_heights):
        real_freqs = []
        real_heights = []
        if len(freqs) > 0:
            short_datetime: datetime = self.metadata['datetime']
            with open("a.a", 'w') as polan_input:
                polan_input.write("OUTPUT MODE ==>          -9.00  0.0  0.0  0.0    0\n")
                polan_input.write(f"Date = {short_datetime.year-2000}{short_datetime.month:02d}{short_datetime.day:02d}{site_dict[self.metadata['site']].short_site}           {site_dict[self.metadata['site']].FH:.2f}  {site_dict[self.metadata['site']].dip:.1f}  0.0 0.00    0\n")
                polan_input.write(f"{self.timestamp}                    0.0\n")
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
                        # Skip or stop on bad data depending on desired behavior
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
            new_timestamp = self.timestamp.replace(':', '')[:-2]
            timestamp_hour = int(self.timestamp.replace(':', '')[:2])
            #Warn: The following line works only for H type (hourly) MDx files 
            #This might not work as intended with I type(file per observation) MDx files
            output_file_nominute_name = Path(self.files_list[timestamp_hour]).stem[:4]
            
            new_output_file_name = output_file_nominute_name + new_timestamp
            output_file_name = f"{self.polan_dir / new_output_file_name}.pol"
            ml_output_filename = f"{self.polan_dir / new_output_file_name}.txt"
            shutil.copyfile(input_file_name, output_file_name)
            with open(ml_output_filename, 'w') as f:
                for freq, height in zip(ml_freqs, ml_heights):
                    f.write(f"{freq}, {float(round(height)):.2f}\n")
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
            freqs = self.freqs[self.lpointer:self.rpointer]
            heights = self.heights[self.lpointer:self.rpointer]
            dops = self.dops[self.lpointer:self.rpointer]
            signals = self.signals[self.lpointer:self.rpointer]
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