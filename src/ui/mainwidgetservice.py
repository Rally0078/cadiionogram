import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from math import isnan
from PySide6.QtCore import QObject
from src.utils.pandasutils import PandasUtils
from src.workers.data_loader_worker import DataLoaderWorker
from src.workers.computation_worker import ComputationWorker
from src.ionogramparser.mdxreader import MDreader
from src.ionogramparser.sameerreader import SameerReader
from src.ui.metadatakeys import cadi_keys_list, sameer_keys_list
from src.utils.siteinfo import site_dict
from src.utils.rawdatadiriterator import RawDataDirIterator

class MainWidgetService(QObject):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget

    def load_data(self, location):
        if self.main_widget.md3_checkbox.isChecked():
            extension = 'md3'
            raw_reader = MDreader()
        elif self.main_widget.md4_checkbox.isChecked():
            extension = 'md4'
            raw_reader = MDreader()
        elif self.main_widget.iono_checkbox.isChecked():
            extension = 'iono'
            raw_reader = SameerReader()
        
        self.main_widget.extension = extension       
        worker = DataLoaderWorker(location, extension, raw_reader)
        worker.signals.finished.connect(self.data_loaded)
        worker.signals.error.connect(self.data_loading_error)
        self.main_widget.threadpool.start(worker)

    def data_loaded(self, files_list, metadata, heights, freqs, freqs_list, dops, signals):
        new_data = {
            'files_list': files_list,
            'metadata': metadata,
            'heights': heights,
            'freqs': freqs,
            'freqs_list': freqs_list,
            'dops': dops,
            'signals': signals,
            'folder_path': self.main_widget._loading_folder_path
        }

        if self.main_widget.multi_folder_checkbox.isChecked():
            # Check if this folder is already in the list to avoid duplicates
            already_exists = False
            for data in self.main_widget.multi_folder_data:
                if data['folder_path'] == new_data['folder_path']:
                    already_exists = True
                    break
            
            if not already_exists:
                self.main_widget.multi_folder_data.append(new_data)
                self.main_widget.multi_folder_data.sort(key=lambda x: x['metadata']['datetime'])
            
            # Combine all data into unified structures
            combined_df, combined_metadata = PandasUtils.combine_folder_data(self.main_widget.multi_folder_data)
            self.main_widget.combined_df = combined_df
            self.main_widget.combined_metadata = combined_metadata
            
            self.main_widget.update_multi_folder_dropdown()
            self.main_widget.switch_to_combined_data()
        else:
            self.main_widget.multi_folder_data = [new_data]
            self.main_widget.combined_df = PandasUtils.create_pandas_from_arrays(metadata, freqs, heights, dops, signals)
            self.main_widget.combined_metadata = metadata
            
            self.main_widget.update_multi_folder_dropdown()
            self.main_widget.switch_to_combined_data()

    def data_loading_error(self, message):
        self.main_widget.textbox_errormsg.setText(message)
        self.main_widget.dlg.exec()
        self.main_widget.run_button.setEnabled(False)
        self.main_widget.label.setText("No folder selected")

    def handle_computation(self, new_state):
        from src.plotstate.mdx_xyplot_state import MdxXYplotCanvasState
        if not self.main_widget.has_handled_calculation and isinstance(new_state, MdxXYplotCanvasState):
            self.main_widget.label.setText("Computing...")
            worker = ComputationWorker(
                self.main_widget.metadata, self.main_widget.freqs, self.main_widget.heights, 
                self.main_widget.dops, self.main_widget.signals, 
                self.main_widget._selected_timestamp, self.main_widget._right_selected_timestamp, 
                self.main_widget.freqs_list
            )
            worker.signals.finished.connect(self.computation_finished)
            worker.signals.error.connect(self.computation_error)
            self.main_widget.threadpool.start(worker)
            return True
        return False

    def computation_finished(self, df_all_outputs, all_output_freqs):
        self.main_widget.df_all_outputs = df_all_outputs
        self.main_widget.all_output_freqs = all_output_freqs
        self.main_widget.has_handled_calculation = True
        self.main_widget._plot_helper()

    def computation_error(self, message):
        self.main_widget.textbox_errormsg.setText(message)
        self.main_widget.dlg.exec()
        self.main_widget.label.setText("Computation error")

    def run_polan(self, freqs, heights, ml_freqs, ml_heights):
        real_freqs = []
        real_heights = []
        if len(freqs) > 0:
            short_datetime: datetime = self.main_widget.metadata['datetime']
            with open("a.a", 'w') as polan_input:
                polan_input.write("OUTPUT MODE ==>          -9.00  0.0  0.0  0.0    0\n")
                polan_input.write(f"Date = {short_datetime.year-2000}{short_datetime.month:02d}{short_datetime.day:02d}{site_dict[self.main_widget.metadata['site']].short_site}           {site_dict[self.main_widget.metadata['site']].FH:.2f}  {site_dict[self.main_widget.metadata['site']].dip:.1f}  0.0 0.00    0\n")
                polan_input.write(f"{self.main_widget._selected_timestamp}                    0.0\n")
                for idx, (freq, height) in enumerate(zip(freqs, heights)):
                    if idx == len(freqs) - 1:
                        height = 0.0
                    polan_input.write(f"{freq}, {float(round(height)):.2f}\n")
                polan_input.write(f"0.0, 0.0")
            
            subprocess.run(['./polan.exe'])
            
            if Path("POLOUT.T").exists():
                with open("POLOUT.T", 'r') as polan_output:
                    lines = polan_output.readlines()
                    data_start_index = -1
                    for i, line in enumerate(lines):
                        if "Real Heights" in line:
                            data_start_index = i + 1
                            break
                    
                    if data_start_index != -1:
                        stop_reading = False
                        for line in lines[data_start_index:]:
                            if stop_reading or line.strip() == '' or '*' in line:
                                break
                            try:
                                floats = list(map(float, line.strip().split()))
                                line_freqs = floats[::2]
                                line_heights = floats[1::2]
                                for f, h in zip(line_freqs, line_heights):
                                    if h <= 50 or f <= 0.25:
                                        stop_reading = True
                                        break
                                    real_freqs.append(f)
                                    real_heights.append(h)
                            except ValueError:
                                break
                
                new_timestamp = self.main_widget._selected_timestamp.replace(':', '')[:-2]
                timestamp_hour = int(self.main_widget._selected_timestamp.replace(':', '')[:2])
                output_file_nominute_name = Path(self.main_widget.files_list[timestamp_hour]).stem[:4]
                new_output_file_name = output_file_nominute_name + new_timestamp
                output_file_name = self.main_widget.polan_dir / f"{new_output_file_name}.pol"
                shutil.copyfile("POLOUT.T", output_file_name)
                self.main_widget.canvas_widget.plot_polan(real_freqs, real_heights, ml_freqs, ml_heights)
        else:
            print("No drawn curve or ionogram data to match.")

    def polan_manual_helper(self):
        from src.plot.realheightanalysis import RealHeightAnalysisCanvas
        if isinstance(self.main_widget.canvas_widget, RealHeightAnalysisCanvas):
            freqs, heights, ml_freqs, ml_heights = self.main_widget.canvas_widget.draw_manual_curve()
            self.run_polan(freqs, heights, ml_freqs, ml_heights)
        else:
            print("Current canvas is not RealHeightAnalysisCanvas. POLAN analysis skipped.")

    def polan_auto_helper(self):
        from src.plot.realheightanalysis import RealHeightAnalysisCanvas
        if isinstance(self.main_widget.canvas_widget, RealHeightAnalysisCanvas):
            it = RawDataDirIterator(self.main_widget.metadata, self.main_widget.freqs, self.main_widget.heights, self.main_widget.dops, self.main_widget.signals)
            freqs, heights, dops, signals = it[self.main_widget._selected_timestamp]
            if self.main_widget.extension == 'md4':
                freqs_interp, heights_interp, ml_freqs, ml_heights = self.main_widget.canvas_widget.draw_auto_curve(freqs, heights, dops, signals)
                self.run_polan(freqs_interp, heights_interp, ml_freqs, ml_heights)
            else:
                print("Automatic curvefitting for .iono files is not implemented yet")

    def save_manual_scale(self):
        if self.main_widget.canvas_widget and self.main_widget.canvas_widget.__class__.__name__ == 'ScaleIonogramCanvas':
            timestamp_hour = int(self.main_widget._selected_timestamp.replace(':', '')[:2])
            timestamp_minute = int(self.main_widget._selected_timestamp.replace(':', '')[2:4])
            timestamp_second = int(self.main_widget._selected_timestamp.replace(':', '')[4:6])
            output_filename = f"{self.main_widget.metadata['datetime'].strftime('%y%m%d')}{site_dict[self.main_widget.metadata['site']].short_site}_F.tfh"
            output_file_name = self.main_widget.polan_dir / output_filename
            
            scaled_values_state = self.main_widget.canvas_widget.scaled_values_lines
            scaled_values_state.set_region('F')
            fof, hprimef = scaled_values_state.f, scaled_values_state.h
            scaled_values_state.set_region('E')
            foe, hprimee = scaled_values_state.f, scaled_values_state.h
            scaled_values_state.set_region('IE')
            foie, hprimeie = scaled_values_state.f, scaled_values_state.h
            
            with open(output_file_name, 'a') as f:
                f.write((f"{timestamp_hour:02d} {timestamp_minute:02d} {timestamp_second:02d} "
                         f"{'NaN ' if isnan(fof) else f'{fof:.2f}'} {'NaN ' if isnan(hprimef) else f'{hprimef:.2f}'} "
                         f"{'NaN ' if isnan(foe) else f'{foe:.2f}'} {'NaN ' if isnan(hprimee) else f'{hprimee:.2f}'} "
                         f"{'NaN ' if isnan(foie) else f'{foie:.2f}'} {'NaN ' if isnan(hprimeie) else f'{hprimeie:.2f}'} "
                         f"{self.main_widget._es_scaling_mode}\n"))
        else:
            print("Not scaling canvas! Use the appropriate canvas")
