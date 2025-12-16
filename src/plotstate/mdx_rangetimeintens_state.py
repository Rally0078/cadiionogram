#Concrete implementation for range-time-freq plot
from src.plot.rangetimeintens import RangeTimeIntensCanvas
from src.plotstate.base import PlotState
from src.utils.powerpreprocessing import convert_amplitude_to_power
import numpy as np
from datetime import datetime
import pandas as pd

class MdxRangeTimeIntensState(PlotState):
    def create_canvas(self):
        canvas = RangeTimeIntensCanvas(self.main)
        self.update_canvas(canvas)
        return canvas

    def update_canvas(self, canvas):
        freqs = self.main.freqs
        heights = self.main.heights
        dops = self.main.dops
        signals = self.main.signals
        power = convert_amplitude_to_power(signals)
        timepartitions_dict = self.main.metadata['timepartitions']
        date_of_obs = self.main.metadata['datetime']
        timepartitions = np.array(list(timepartitions_dict.values()))
        tmp = timepartitions[0]
        timepartitions = np.diff(timepartitions, prepend=timepartitions[0])
        timepartitions[0] = tmp
        repeating_indices = np.repeat(list(timepartitions_dict.keys()), timepartitions)

        repeating_indices = np.array([datetime.strptime(f"{date_of_obs.year:04d}-{date_of_obs.month:02d}-{date_of_obs.day:02d} {time_str}+00:00", 
                                                        '%Y-%m-%d %H:%M:%S%z') for time_str in repeating_indices])
        time_index = pd.to_datetime(repeating_indices, utc=True)

        canvas.plot_scatter(
            time_index,
            heights,
            power,
            freqs, 
            self.main.metadata['datetime'],
            self.main.metadata['site']
        )
