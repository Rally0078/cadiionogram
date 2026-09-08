from PySide6.QtCore import QObject
from pathlib import Path
from copy import deepcopy
from datetime import datetime
from src.utils.siteinfo import SiteInfo
from math import isnan
from src.workers.file_saving_workers import ImageSavingWorker

class FileSavingService(QObject):
    def __init__(self, main_widget):
        super().__init__()
        self.main_widget = main_widget
    
    def save_data(self):
        pass
    def save_plot(self, canvas, output_path):
        worker = ImageSavingWorker(deepcopy(canvas.figure), output_path)
        self.main_widget.threadpool.start(worker)

    def get_plot_filename(self):
        from src.plotstate.plotstate_options import timeseries_options, plot_fig_save_names
        option = self.main_widget.mode_dropdown.currentText()
        start_datetime = datetime.strptime(self.main_widget._selected_timestamp,"%Y-%m-%d %H:%M:%S")
        filename = f"{plot_fig_save_names[option]}"
        if option in timeseries_options:     
            end_datetime = datetime.strptime(self.main_widget._right_selected_timestamp,"%Y-%m-%d %H:%M:%S")
            filename += self._generate_plot_filename_dt(start_datetime, end_datetime)
        else:
            filename += start_datetime.strftime("%y%m%d_%H%M%S")
        filename = self.main_widget.output_dir / Path(filename)
        return filename

    def _generate_plot_filename_dt(self, dt1, dt2):
        if dt1 > dt2:
            dt1, dt2 = dt2, dt1
        base_format = "%y%m%d_%H%M%S"
        if dt1.year != dt2.year:
            suffix_format = "-%y%m%d_%H%M%S"
        elif dt1.month != dt2.month:
            suffix_format = "-%m%d_%H%M%S"
        elif dt1.day != dt2.day:
            suffix_format = "-%d_%H%M%S"
        else:
            suffix_format = "-%H%M%S"
        return f"{dt1.strftime(base_format)}{dt2.strftime(suffix_format)}" 
    
    def save_manual_scale(self):
        if self.main_widget.canvas_widget and self.main_widget.canvas_widget.__class__.__name__ == 'ScaleIonogramCanvas':
            short_datetime: datetime = datetime.strptime(self.main_widget._selected_timestamp, "%Y-%m-%d %H:%M:%S")
            short_datetime = short_datetime.replace(tzinfo=SiteInfo.from_file(self.main_widget.metadata['site']).get_tzinfo(short_datetime))
            current_timestamp = self.main_widget._selected_timestamp.split(' ')[-1]

            output_filename = f"{short_datetime.strftime('%y%m%d')}{SiteInfo.from_file(self.main_widget.metadata['site']).short_site}_F.tfh"
            output_filename = self.main_widget.polan_dir / output_filename
            
            scaled_values_state = self.main_widget.canvas_widget.scaled_values_lines
            scaled_values_state.set_region(self.main_widget.config.get('scaling','scalingoption1'))
            f1, h1 = scaled_values_state.f, scaled_values_state.h
            scaled_values_state.set_region(self.main_widget.config.get('scaling','scalingoption2'))
            f2, h2 = scaled_values_state.f, scaled_values_state.h
            scaled_values_state.set_region(self.main_widget.config.get('scaling','scalingoption3'))
            f3, h3 = scaled_values_state.f, scaled_values_state.h
            timestamp_hour = int(current_timestamp.replace(':', '')[:2])
            timestamp_minute = int(current_timestamp.replace(':', '')[2:4])
            timestamp_second = int(current_timestamp.replace(':', '')[4:6])
            with open(output_filename, 'a') as f:
                f.write((f"{short_datetime.strftime("%Y %m %d")} "
                        f"{timestamp_hour:02d} {timestamp_minute:02d} {timestamp_second:02d} "
                        f"{'NaN ' if isnan(f1) else f'{f1:.2f}'} {'NaN ' if isnan(h1) else f'{h1:.2f}'} "
                        f"{'NaN ' if isnan(f2) else f'{f2:.2f}'} {'NaN ' if isnan(h2) else f'{h2:.2f}'} "
                        f"{'NaN ' if isnan(f3) else f'{f3:.2f}'} {'NaN ' if isnan(h3) else f'{h3:.2f}'} "
                        f"{self.main_widget._es_scaling_mode} "
                        f"{self.main_widget._spread_f_scaling_mode}\n"))
        else:
            print("Not scaling canvas! Use the appropriate canvas")
        