import numpy as np

class RawDataDirIterator:
    """
        Iterable and indexable class for accessing raw data given the data arrays and timepartitions. 
        This is not a Python iterator in a technical sense for reasons mentioned below, but it is an iterable container that allows for random access
        through indexing by an integer or a timestamp string.

        Usage
        -----

        >>> it = RawDataDirIterator(metadata, freqs, heights, dops, sensors)
        >>> for data in it:
        >>>     freq, height, dop, sensor = data
        >>>     ...

        It also be indexed using a timestamp str or integer index, or a slice of them. 
        Note that when slicing using timestamp strs, the end timestamp is **inclusive** unlike the standard Python slice convention. 

        >>> data_at_time = it['12:30:00']
        >>> data_at_index = it[10]
        >>> data_in_slice_ints = it[5:12]   #12 is exclusive. Slice contains data of timestamps 5, 6, 7, 8, 9, and 10.
        >>> data_in_slice_timestamp = it['12:45:00':'14:15:00'] #End time '14:15:00' is inclusive, unlike the standard Python convention.
    """
    def __init__(self, metadata, freqs, heights, dops, sensors):
        self.freqs = freqs
        self.heights = heights
        self.dops = dops
        self.metadata = metadata
        self.sensors = sensors
        self.timepartitions = self.metadata['timepartitions']
        self.timepartition_timestamps = list(self.timepartitions.keys())
        self.current_index = 0
        assert len(self.freqs) == len(self.heights)
        assert len(self.heights) == len(self.dops)
        assert len(self.sensors) == len(self.dops)

    #Do not use the following. Making this class a true Python iterator makes the iterator consumable, i.e., usable only for one iteration.
    """    def __iter__(self):
            return self
        
        def __next__(self):
            if self.current_index < len(self.timepartition_timestamps):
                lpointer, rpointer = self._handle_single_index(self.current_index)
                self.current_index += 1
                return self.freqs[lpointer:rpointer], self.heights[lpointer:rpointer], self.dops[lpointer:rpointer], self.sensors[lpointer:rpointer]
            else:
                raise StopIteration
    """

    def __getitem__(self, idx):
        """
            Handles the indexing for the [] operator. 
        """
        #Index is a single integer. This integer corresponds to the timestamp in the metadata.
        if isinstance(idx, int):
            lpointer, rpointer = self._handle_single_index(idx)

        #Index is a timestamp string containing the timestamp of observation.
        elif isinstance(idx, str):
            idx_int = self.timepartition_timestamps.index(idx)
            lpointer, rpointer = self._handle_single_index(idx_int)

        #Index is a slice containing either two integers, or two timestamp strings. Step size is not allowed.
        elif isinstance(idx, slice):
            start_idx = idx.start
            stop_idx = idx.stop
            step_idx = idx.step
            if step_idx is not None:
                raise RuntimeWarning("Step size is not implemented")
            
            #No index is given
            if (start_idx == None) and (stop_idx == None):
                stop_idx_int = len(self.timepartition_timestamps) - 1
                lpointer, rpointer = self._handle_slice_indices(0, stop_idx_int)
            #Either start index or stop index is not given
            elif (start_idx == None) ^ (stop_idx == None):
                if start_idx == None:
                    #stop str index is INCLUSIVE unlike normal Python indexing.
                    if isinstance(stop_idx, str):
                        stop_idx_int = self.timepartition_timestamps.index(stop_idx)
                        lpointer, rpointer = self._handle_slice_indices(0, stop_idx_int)
                    #stop integer index is exclusive just like normal Python indexing.
                    elif isinstance(stop_idx, int):
                        lpointer, rpointer = self._handle_slice_indices(0, stop_idx - 1)
                    else:
                        raise IndexError("Stop index must be either int or str.")
                else:
                    stop_idx_int = len(self.timepartition_timestamps) - 1
                    if isinstance(start_idx, str):
                        start_idx_int = self.timepartition_timestamps.index(start_idx)
                        lpointer, rpointer = self._handle_slice_indices(start_idx_int, stop_idx_int)
                    elif isinstance(start_idx, int):
                        lpointer, rpointer = self._handle_slice_indices(start_idx, stop_idx_int)
                    else:
                        raise IndexError("Stop index must be either int or str.")

            #Handle two int indices, stop index is exclusive just like normal Python indexing.
            elif isinstance(start_idx, int) and isinstance(stop_idx, int):
                lpointer, rpointer = self._handle_slice_indices(start_idx, stop_idx - 1)
            #Handle two str timestamp indices, stop index is INCLUSIVE unlike normal Python indexing.
            elif isinstance(start_idx, str) and isinstance(stop_idx, str):
                start_idx_int = self.timepartition_timestamps.index(start_idx)
                stop_idx_int = self.timepartition_timestamps.index(stop_idx)
                lpointer, rpointer = self._handle_slice_indices(start_idx_int, stop_idx_int)
            else:
                raise IndexError("Both indices must be either ints or str.")
        else:
            raise TypeError("Index can only be of timestamp str or integer.")
        
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
        if start_idx not in range(len(self.timepartition_timestamps)) or stop_idx not in range(len(self.timepartition_timestamps)):
            raise IndexError
        if start_idx > stop_idx:
            raise IndexError("Start index must be less than or equal to the stop index.")
        if start_idx == 0:
            lpointer = 0
        else:
            prev_index = start_idx - 1
            lpointer = self.timepartitions[self.timepartition_timestamps[prev_index]]
        rpointer = self.timepartitions[self.timepartition_timestamps[stop_idx]]

        return lpointer, rpointer
    
    def __len__(self):
        return len(self.timepartitions)