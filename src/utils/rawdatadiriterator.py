import numpy as np

class RawDataDirIterator:
    """
        Iterable and indexable class for accessing raw data given the data arrays and timepartitions. 
        This is not a Python iterator in a technical sense for reasons mentioned below, but it is an iterable container that allows for random access
        through indexing by an integer or a timestamp string.

        Examples
        --------

        >>> it = RawDataDirIterator(metadata, freqs, heights, dops, sensors)
        >>> for data in it:
        >>>     freq, height, dop, sensor = data
        >>>     ...

        It can also be indexed using a timestamp str or integer index, or a slice of them. 
        Note that when slicing using timestamp strs, the end timestamp is **inclusive** unlike the standard Python slice convention. 

        >>> data_at_time = it['12:30:00']
        >>> data_at_index = it[10]

        These are iterables that can be looped through in a for loop.

        >>> data_in_slice_ints = it[5:12]   #12 is exclusive as usual. Slice contains data of timestamps 5, 6, 7, 8, 9, 10, and 11.
        >>> data_in_slice_timestamp = it['12:45:00':'14:15:00'] #End time '14:15:00' is **inclusive**, unlike the standard Python convention.
        >>> for obs in data_in_slice_ints:
        >>>     freq, height, dop, sensor = obs

        To obtain the concatenated values for all the timestamps, use the `as_block()` method.

        >>> data_array = it[5:12].as_block()
        >>> freqs, heights, dops, sensors = data_array
    """
    def __init__(self, metadata, freqs, heights, dops, sensors, start=0, stop=None):
        self.freqs = freqs
        self.heights = heights
        self.dops = dops
        self.metadata = metadata
        self.sensors = sensors
        self.timepartitions = self.metadata['timepartitions']
        self.timepartition_timestamps = list(self.timepartitions.keys())
        self.start = 0 if start is None else start
        self.stop = len(self.timepartition_timestamps)-1 if stop is None else stop

    def __iter__(self):
        for i in range(self.start, self.stop):
            lpointer, rpointer = self._handle_single_index(i)
            yield self.freqs[lpointer:rpointer], self.heights[lpointer:rpointer], self.dops[lpointer:rpointer], self.sensors[lpointer:rpointer]

    def __getitem__(self, idx):
        """
            Handles the indexing for the [] operator. 
        """
        #Index is a single integer. This integer corresponds to the timestamp in the metadata.
        if isinstance(idx, int):
            lpointer, rpointer = self._handle_single_index(idx)
            return self.freqs[lpointer:rpointer], self.heights[lpointer:rpointer], self.dops[lpointer:rpointer], self.sensors[lpointer:rpointer]
        
        #Index is a timestamp string containing the timestamp of observation.
        elif isinstance(idx, str):
            idx_int = self.timepartition_timestamps.index(idx)
            lpointer, rpointer = self._handle_single_index(idx_int)
            return self.freqs[lpointer:rpointer], self.heights[lpointer:rpointer], self.dops[lpointer:rpointer], self.sensors[lpointer:rpointer]
        
        #Index is a slice containing either two integers, or two timestamp strings. Step size is not allowed.
        elif isinstance(idx, slice):
            start_idx = idx.start
            stop_idx = idx.stop
            step_idx = idx.step

            if step_idx is not None:
                raise RuntimeWarning("Step size is not implemented")
            
            start_idx, stop_idx = self._get_start_stop_idxs(start_idx, stop_idx)

            return RawDataDirIterator(self.metadata, self.freqs, 
                                      self.heights, self.dops, 
                                      self.sensors,start_idx, stop_idx)
        else:
            raise TypeError("Index can only be of timestamp str or integer.")

    def _get_start_stop_idxs(self, start_idx, stop_idx):
        #No index is given
        if (start_idx == None) and (stop_idx == None):
            stop_idx = len(self.timepartition_timestamps) - 1
            start_idx = 0
        #Either start index or stop index is not given
        elif (start_idx == None) ^ (stop_idx == None):
            if start_idx == None:
                #stop str index is INCLUSIVE unlike normal Python indexing.
                if isinstance(stop_idx, str):
                    stop_idx = self.timepartition_timestamps.index(stop_idx)
                    stop_idx += 1
                elif isinstance(stop_idx, int):
                    pass
                else:
                    raise IndexError("Stop index must be either int or str.")
            else:
                stop_idx = len(self.timepartition_timestamps) - 1
                if isinstance(start_idx, str):
                    start_idx = self.timepartition_timestamps.index(start_idx)
                elif isinstance(start_idx, int):
                    pass
                else:
                    raise IndexError("Start index must be either int or str.")
        elif isinstance(start_idx, int) and isinstance(stop_idx, int):
            pass
        #Handle two str timestamp indices, stop index is INCLUSIVE unlike normal Python indexing.
        elif isinstance(start_idx, str) and isinstance(stop_idx, str):
            start_idx = self.timepartition_timestamps.index(start_idx)
            stop_idx = self.timepartition_timestamps.index(stop_idx)
            stop_idx += 1
        else:
            raise IndexError("Both indices must be either ints or str.")
        if stop_idx > len(self.timepartition_timestamps):
            raise IndexError("Slice stop index out of range")

        return start_idx, stop_idx

    def as_block(self):
        lpointer, rpointer = self._handle_slice_indices(self.start, self.stop)
        return self.freqs[lpointer:rpointer], self.heights[lpointer:rpointer], self.dops[lpointer:rpointer], self.sensors[lpointer:rpointer]
    
    def _handle_single_index(self, idx):
        if idx == 0:
                lpointer = 0
        else:
            prev_index = idx - 1
            lpointer = self.timepartitions[self.timepartition_timestamps[prev_index]]
        rpointer = self.timepartitions[self.timepartition_timestamps[idx]]

        return lpointer, rpointer
    
    def _handle_slice_indices(self, start_idx, stop_idx):
        if start_idx not in range(len(self.timepartition_timestamps)) or (stop_idx) not in range(len(self.timepartition_timestamps)+1):
            raise IndexError
        if start_idx > stop_idx:
            raise IndexError("Start index must be less than or equal to the stop index.")
        if start_idx == 0:
            lpointer = 0
        else:
            prev_index = start_idx - 1
            lpointer = self.timepartitions[self.timepartition_timestamps[prev_index]]
        rpointer = self.timepartitions[self.timepartition_timestamps[stop_idx-1]]

        return lpointer, rpointer
    
    def __len__(self):
        return self.stop - self.start + 1