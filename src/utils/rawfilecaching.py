#TODO:
#Implement caching of ionosonde data given an input file/folder
#Ideas: SQLite database to store cache locations corresponding to some unique key based on the input file name(?)
#Handle caching for single hour/observation file and for the whole folder separately.

def enable_cache(func):
    raise NotImplementedError
    """Decorator to use caching features.

        Example usage:

        ```@enable_cache
        file_list, metadata, heights, frequencies, freq_lists, dop_shifts, sensors = MDreader.read_raw_data(filename)
        ```
        """
    def wrapper(*args, **kwargs):
        #Do some SQLite cache checking
        #If cached parquet exists, read the contents from the parquet
        #Read contents and store contents in the appropriate variables for returning
        #Else, perform the following line
        file_list, metadata, heights, frequencies, freq_lists, dop_shifts, sensors = func(args)
        #Create cache for the parquet and update SQLite db
        
        return file_list, metadata, heights, frequencies, freq_lists, dop_shifts, sensors
    return wrapper
