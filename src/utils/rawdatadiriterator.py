import numpy as np

class RawDataDirIterator:
    def __init__(self, metadata, freqs, heights, dops, sensors):
        self.freqs = freqs
        self.heights = heights
        self.dops = dops
        self.metadata = metadata
        self.sensors = sensors
        self.timepartitions = self.metadata['timepartitions']

        assert len(self.freqs) == len(self.heights)
        assert len(self.heights) == len(self.dops)
        assert len(self.sensors) == len(self.dops)
    
    def __getitem__(self, idx):
        timepartition_timestamps = list(self.timepartitions.keys())
        if isinstance(idx, int):
            if idx not in range(len(timepartition_timestamps)):
                raise IndexError
            if idx == 0:
                lpointer = 0
            else:
                prev_index = idx - 1
                lpointer = self.timepartitions[timepartition_timestamps[prev_index]]
            rpointer = self.timepartitions[timepartition_timestamps[idx]]
        elif isinstance(idx, str):
            index = timepartition_timestamps.index(idx)
            if index not in range(len(timepartition_timestamps)):
                raise IndexError
            if index == 0:
                lpointer = 0
            else:
                prev_index = index - 1
                lpointer = self.timepartitions[timepartition_timestamps[prev_index]]
            rpointer = self.timepartitions[timepartition_timestamps[index]]
        else:
            raise TypeError("Key can only be of timestamp str or integer index")
        
        return self.freqs[lpointer:rpointer], self.heights[lpointer:rpointer], self.dops[lpointer:rpointer], self.sensors[lpointer:rpointer]
    
    def __len__(self):
        return len(self.timepartitions)