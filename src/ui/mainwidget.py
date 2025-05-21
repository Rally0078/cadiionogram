from pathlib import Path
from datetime import datetime
from src.errorhandlers.errorhandling import FolderNotContainingData
from src.plot.ionogramcanvas import IonogramCanvas
from src.ui.metadatatable import MetadataTableWidget
from src.ui.metadatakeys import keys_list
from src.plotstate.factory import PlotStateFactory
from src.cadiparser.readrawdata import MDreader
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, 
    QCheckBox, QButtonGroup,
    QSizePolicy, QSpacerItem,
    QGridLayout, QDialog, QDialogButtonBox,
    QComboBox, QMenuBar, QMenu
)
class MainWidget(QWidget):
    md3_options = ['Frequency vs time', 'Height vs time']
    md4_options = ['Display ionogram', 'Autoscale ionogram', 'Real height analysis']
    def __init__(self):
        super().__init__()

        # Canvas parameters to be used later
        self.canvas_layout_row = 2
        self.canvas_layout_col = 3
        self.canvas_layout_rowspan = 6
        self.canvas_layout_colspan = 3
        self.canvas_widget = None
        self.lpointer = -1
        self.rpointer = -1

        # Folder selector buttons and label
        self.label = QLabel("No folder selected")
        self.button = QPushButton("Select Folder")
        
        # Filetype selection
        self.button.clicked.connect(self.open_folder)
        self.md3_checkbox = QCheckBox("md3 format")
        self.md4_checkbox = QCheckBox("md4 format")
        self.md4_checkbox.setChecked(True)
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.md3_checkbox)
        self.button_group.addButton(self.md4_checkbox)
        self.button_group.setExclusive(True)
        self.md3_checkbox.stateChanged.connect(self._on_tickbox_changed)
        self.md4_checkbox.stateChanged.connect(self._on_tickbox_changed)
        
        # Mode selection dropbox
        self.dropbox = QComboBox()
        # Default mode is md4
        self.dropbox.addItems(MainWidget.md4_options)
        
        # Grid layout
        layout = QGridLayout()

        # Folder selection and label
        layout.addWidget(self.button, 1, 0)
        layout.addWidget(self.label, 1, 1)

        # Checkboxes
        layout.addWidget(self.md3_checkbox, 2, 0)
        layout.addWidget(self.md4_checkbox, 2, 1)
        layout.addWidget(self.dropbox, 3,0)
        layout.setColumnStretch(4, 1)

        # Custom table widget for metadata table and navigation
        self.table_widget = MetadataTableWidget()

        # Set the margins and spacing        
        layout.addWidget(self.table_widget, 4, 0, 2, 2)

        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        #Initialize signal handling
        self.table_widget.dropdown_changed.connect(self._on_dropdown_changed)
        self.table_widget.left_clicked.connect(self._prev_option)
        self.table_widget.right_clicked.connect(self._next_option)

        self.setLayout(layout)
        
        self._selected_timestamp = ''

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
        
    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        folder_path = Path(folder_path)
        if folder_path:
            try:
                self.create_table(folder_path)
                self.label.setText(f"Selected: {folder_path}")
            except FolderNotContainingData:
                self.textbox_errormsg.setText("You must choose a folder.")
                self.dlg.exec()
                return
    
    #Create table when correct folder is selected
    def create_table(self, location):
        self.directory = location
        print(f"Currently chosen directory: {self.directory}")
        raw_reader = MDreader()
        if self.md3_checkbox.isChecked():
            extension = 'md3'
        if self.md4_checkbox.isChecked():
            extension = 'md4'
        #Note: Throws FolderNotContainingData exception if md3/4 is not found in the directory
        self.metadata, self.heights, self.freqs, self.freqs_list, self.dops, self.signals = raw_reader.read_raw_data_dir(location, extension)
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
    #Callback to handle changes in dropdown value
    def _on_dropdown_changed(self, text):
        self._selected_timestamp = text
        self._get_lpointer_rpointer(self.timepartitions, timestamp=self._selected_timestamp)
        self.table_widget.set_pointers(self.lpointer, self.rpointer)
        
        self._plot_helper()
    
    def _get_lpointer_rpointer(self, timepartitions, timestamp):
        index = list(timepartitions.keys()).index(timestamp)
        lpointer = -1
        if index == 0:
            lpointer = 0
        else:
            prev_index = index - 1
            lpointer = timepartitions[list(timepartitions.keys())[prev_index]]
        rpointer = timepartitions[timestamp]

        self.lpointer = lpointer
        self.rpointer = rpointer

    def _plot_helper(self):
        state = PlotStateFactory.get_state(self)
        if self.canvas_widget is None:
            self.canvas_widget = state.create_canvas()
            self.canvas_widget.setHidden(True)
            self.layout().addWidget(
            self.canvas_widget,
            self.canvas_layout_row,
            self.canvas_layout_col,
            self.canvas_layout_rowspan,
            self.canvas_layout_colspan,
        )
            self.canvas_widget.setHidden(False)
        if self.canvas_widget is not None:
            state.update_canvas(self.canvas_widget)

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