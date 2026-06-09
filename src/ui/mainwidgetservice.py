import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta
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
            'folder_path': self.main_widget._loading_folder_path,
            'file_paths': [self.main_widget._loading_folder_path / filename for filename in files_list]
        }

        if self.main_widget.multi_folder_checkbox.isChecked():
            # Check if this folder is already in the list to avoid duplicates
            already_exists = False
            for data in self.main_widget.multi_folder_data:
                if len(data['file_paths']) != len(new_data['file_paths']):
                    break
                for old_file, new_file in zip(data['file_paths'], new_data['file_paths']):
                    if old_file == new_file:
                        already_exists = True
                        break
            
            if not already_exists:
                if len(self.main_widget.multi_folder_data) >= 1:
                    if self.main_widget.multi_folder_data[0]['metadata']['extension'] != new_data['metadata']['extension']:
                        self.main_widget.multi_folder_data = []
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
        from src.plotstate.mdx_skymap_state import MdxSkymapState
        if not self.main_widget.has_handled_calculation and isinstance(new_state, (MdxXYplotCanvasState, MdxSkymapState)):
            self.main_widget.label.setText("Computing...")
            worker = ComputationWorker(
                self.main_widget.multi_folder_data[0]['metadata']['datetime'],
                self.main_widget.combined_df,
                self.main_widget._selected_timestamp, self.main_widget._right_selected_timestamp, 
                self.main_widget.multi_folder_data[0]['freqs_list']
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
            short_datetime: datetime = datetime.strptime(self.main_widget._selected_timestamp, "%Y-%m-%d %H:%M:%S")
            short_datetime = short_datetime.replace(tzinfo=site_dict[self.main_widget.metadata['site']].get_tzinfo(short_datetime))
            current_timestamp = self.main_widget._selected_timestamp.split(' ')[-1]
            
            with open("a.a", 'w') as polan_input:
                polan_input.write("OUTPUT MODE ==>          -9.00  0.0  0.0  0.0    0\n")
                polan_input.write(f"Date = {short_datetime.year-2000}{short_datetime.month:02d}{short_datetime.day:02d}{site_dict[self.main_widget.metadata['site']].short_site}           {site_dict[self.main_widget.metadata['site']].FH:.2f}  {site_dict[self.main_widget.metadata['site']].dip:.1f}  0.0 0.00    0\n")
                polan_input.write(f"{current_timestamp}                    0.0\n")
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
                # Get output filename in the format
                # year(single last digit)month(letter A-L)day(0 padded)time(HH:MM)
                new_timestamp = current_timestamp.replace(':', '')[:-2]
                output_file_nominute_name = datetime.strftime(short_datetime, "%Y%m%d")
                output_file_nominute_name = output_file_nominute_name[3:]
                output_file_year, output_file_day = output_file_nominute_name[0], output_file_nominute_name[3:]
                output_file_nominute_name = output_file_year + chr(short_datetime.month + 64) + output_file_day
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
            target_time_str = self.main_widget._selected_timestamp
            date_of_obs = self.main_widget.combined_metadata['datetime']
            if self.main_widget.multi_folder_checkbox.isChecked():
                time_obj = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
                target_dtime = time_obj
            else:
                time_obj = datetime.strptime(target_time_str.split(' ')[-1], "%H:%M:%S")
                target_dtime = time_obj.replace(year=date_of_obs.year, month=date_of_obs.month, day=date_of_obs.day)
            target_dtime = target_dtime.replace(tzinfo=date_of_obs.tzinfo)

            df_at_time = self.main_widget.combined_df.loc[target_dtime]
            signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
            
            freqs, heights, dops = df_at_time['freq (Hz)'].to_numpy(), df_at_time['height (km)'].to_numpy(), df_at_time['dopplershift'].to_numpy()
            signals = df_at_time[signal_col_names].to_numpy()
            if self.main_widget.extension == 'md4':
                freqs_interp, heights_interp, ml_freqs, ml_heights = self.main_widget.canvas_widget.draw_auto_curve(freqs, heights, dops, signals)
                self.run_polan(freqs_interp, heights_interp, ml_freqs, ml_heights)
            else:
                print("Automatic curvefitting for .iono files is not implemented yet")

    def save_manual_scale(self):
        if self.main_widget.canvas_widget and self.main_widget.canvas_widget.__class__.__name__ == 'ScaleIonogramCanvas':
            short_datetime: datetime = datetime.strptime(self.main_widget._selected_timestamp, "%Y-%m-%d %H:%M:%S")
            short_datetime = short_datetime.replace(tzinfo=site_dict[self.main_widget.metadata['site']].get_tzinfo(short_datetime))
            current_timestamp = self.main_widget._selected_timestamp.split(' ')[-1]

            timestamp_hour = int(current_timestamp.replace(':', '')[:2])
            timestamp_minute = int(current_timestamp.replace(':', '')[2:4])
            timestamp_second = int(current_timestamp.replace(':', '')[4:6])
            output_filename = f"{short_datetime.strftime('%y%m%d')}{site_dict[self.main_widget.metadata['site']].short_site}_F.tfh"
            output_file_name = self.main_widget.polan_dir / output_filename
            
            scaled_values_state = self.main_widget.canvas_widget.scaled_values_lines
            scaled_values_state.set_region(self.main_widget.config.get('scaling','scalingoption1'))
            f1, h1 = scaled_values_state.f, scaled_values_state.h
            scaled_values_state.set_region(self.main_widget.config.get('scaling','scalingoption2'))
            f2, h2 = scaled_values_state.f, scaled_values_state.h
            scaled_values_state.set_region(self.main_widget.config.get('scaling','scalingoption3'))
            f3, h3 = scaled_values_state.f, scaled_values_state.h
            
            with open(output_file_name, 'a') as f:
                f.write((f"{timestamp_hour:02d} {timestamp_minute:02d} {timestamp_second:02d} "
                         f"{'NaN ' if isnan(f1) else f'{f1:.2f}'} {'NaN ' if isnan(h1) else f'{h1:.2f}'} "
                         f"{'NaN ' if isnan(f2) else f'{f2:.2f}'} {'NaN ' if isnan(h2) else f'{h2:.2f}'} "
                         f"{'NaN ' if isnan(f3) else f'{f3:.2f}'} {'NaN ' if isnan(h3) else f'{h3:.2f}'} "
                         f"{self.main_widget._es_scaling_mode} "
                         f"{self.main_widget._spread_f_scaling_mode}\n"))
        else:
            print("Not scaling canvas! Use the appropriate canvas")
