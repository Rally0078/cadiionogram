import multiprocessing
multiprocessing.freeze_support()

import copy
from pathlib import Path
import struct
import datetime
from datetime import timezone
from time import strptime
import joblib

from src.errorhandlers.errorhandling import FolderNotContainingData
import numpy as np


type time_partition_dict = dict[int, int]



#Base class for data readers
class DataReader:
    pass

#MDn format reader, extended from DataReader baseclass
#Use dependency injection to connect with the CSV IO class
class MDreader(DataReader):
    def __init__(self):
        pass

    def read_raw_data(self, filename: Path) -> tuple[dict, time_partition_dict, np.ndarray, np.ndarray, np.ndarray]:
        """Read CADI ionogram data in md2/md4 formats.
        ### Parameters
        filename : Path object
            - Location of the md2/md4 file to parse.
        ### Returns
        Returns multiple values as follows:

        metadata : Dict
        - Dictionary containing metadata of the observations. Contains site name, datetime object representing \
        the date and time of observation in UTC, time partitions in key-value pairs to partition the observations by time, \
        and number of receivers.

        height : numpy.ndarray 
        - Heights in km from all the observations in the file. Use the time_partitions to \
        partition the heights by observation time.

        frequency : numpy.ndarray 
        - Frequencies in Hz from all the observations in the file. Use the time_partitions to \
        partition the heights by observation time.

        dopbin_iq : numpy.ndarray
        - numpy.ndarray containing complex signal value from each receiver. Use the time_partitions \
        to partition the signals by observation time.

        ### Examples
        Read from current directory
        ```
            metadata, heights, frequencies, signals = read_raw_data('input.md4')
        ```
        """
        max_ntimes = 256
        max_ndopbins = 300000
        dheight = 3.0  # not defined in data file
        with open(filename, "rb") as f:
            f.seek(-1,2)     # go to the file end.
            eof = f.tell()   # get the end of file location
            f.seek(0,0)      # go back to file beginning
            # 1) read header information as described in the documentation p. 26-27
            site = f.read(3).decode("utf-8")
            ascii_datetime = f.read(22).decode("utf-8")
            filetype = f.read(1).decode("utf-8")

            nfreqs = struct.unpack("<H", f.read(2))[0]

            ndops = struct.unpack("<B", f.read(1))[0]
            minheight = struct.unpack("<H", f.read(2))[0]

            maxheight = struct.unpack("<H", f.read(2))[0]
            pps = struct.unpack("<B", f.read(1))[0]

            npulses_avgd = struct.unpack("<B", f.read(1))[0]
            base_thr100 = struct.unpack("<H", f.read(2))[0]
            noise_thr100 = struct.unpack("<H", f.read(2))[0]
            min_dop_forsave = struct.unpack("<B", f.read(1))[0]
            dtime = struct.unpack("<H", f.read(2))[0]
            gain_control = f.read(1).decode("utf-8")
            sig_process = f.read(1).decode("utf-8")
            noofreceivers = struct.unpack("<B", f.read(1))[0]
            spares = f.read(11).decode("utf-8")

            month = ascii_datetime[1:4]
            day = int(ascii_datetime[5:7])
            hour = int(ascii_datetime[8:10])
            minute = int(ascii_datetime[11:13])
            sec = int(ascii_datetime[14:16])
            year = int(ascii_datetime[17:21])

            month_number = strptime(month, '%b').tm_mon
            mydate = datetime.date(year, month_number, day)
            jd = mydate.toordinal() + 1721424.5
            jd0jd = datetime.date(1986, 1, 1)
            jd0 = jd0jd.toordinal() + 1721424.5

            time_header = (jd - jd0) * 86400 + hour * 3600 + minute * 60 + sec
            time_hour = time_header

            # 2) read all frequencies used

            freqs = np.array([struct.unpack("<f", f.read(4))[0] for i in range(nfreqs)], dtype=np.float32)

            if filetype == 'I':
                max_nfrebins = nfreqs
            else:
                max_nfrebins = min(max_ntimes * nfreqs, max_ndopbins)

            nheights = int(maxheight / dheight + 1)

            times = []
            frebins = []
            frebins_x = []
            frebins_gain_flag = []
            frebins_noise_flag = []
            frebins_noise_power10 = []
            time_min = 0
            time_sec = 0
            timex = -1
            freqx = nfreqs - 1
            dopbinx = -1
            frebinx = -1
            iq_bytes = np.zeros((noofreceivers, 2))
            dopbin_x_timex = []
            dopbin_x_freqx = []
            dopbin_x_hflag = []
            dopbin_x_dop_flag = []
            dopbin_iq = []
            hflag = 0

            time_partitions = dict()

            time_min = struct.unpack("<B", f.read(1))[0]
            
            # Read complex sensor data from all receivers of all observations till eof.
            while time_min != 255:
                #Iterate through each time of observation
                time_sec = struct.unpack("<B", f.read(1))[0]
                flag = struct.unpack("<B", f.read(1))[0]  # gainflag
                timex += 1
                times.append(time_hour + 60 * time_min + time_sec)
                for freqx in range(nfreqs):
                    #Iterate through each frequency at a given time of observation
                    noise_flag = struct.unpack("<B", f.read(1))[0]  # noiseflag
                    noise_power10 = struct.unpack("<H", f.read(2))[0]
                    frebinx += 1
                    frebins_gain_flag.append(flag)
                    frebins_noise_flag.append(noise_flag)
                    frebins_noise_power10.append(noise_power10)
                    flag = struct.unpack("<B", f.read(1))[0]
                    while flag < 224:
                        #Iterate through all sensor values at a given time and at a given frequency
                        ndops_oneh = struct.unpack("<B", f.read(1))[0]
                        hflag = flag
                        if ndops_oneh >= 128:
                            ndops_oneh = ndops_oneh - 128
                            hflag = hflag + 200
                        for dopx in range(ndops_oneh):
                            dop_flag = struct.unpack("<B", f.read(1))[0]
                            for rec in range(noofreceivers):
                                iq_bytes[rec, 0] = struct.unpack("<B", f.read(1))[0]
                                iq_bytes[rec, 1] = struct.unpack("<B", f.read(1))[0]
                            dopbinx += 1
                            dopbin_iq.append(copy.deepcopy(iq_bytes))
                            dopbin_x_timex.append(timex)
                            dopbin_x_freqx.append(freqx)
                            dopbin_x_hflag.append(hflag)
                            if dop_flag < int(ndops / 2):
                                dop_flag = dop_flag + int(ndops / 2)
                            else:
                                dop_flag = dop_flag - int(ndops / 2)
                            dopbin_x_dop_flag.append(dop_flag)
                        flag = struct.unpack("<B", f.read(1))[0]  # next hflag/gainflag/FF
                time_partitions[time_min] = len(dopbin_iq)
                time_min = flag
                if ((f.tell() - 1) != eof):
                    time_min = struct.unpack("<B", f.read(1))[0]  # next record

        #Raw signal values from the four receivers
        #Use 20 log(value) to get power in dB
        frequency = np.zeros(shape=(len(dopbin_iq)))
        for idx in range(len(dopbin_iq)):
            #Shape of data in dopbin_iq (Re, Im) component array
            #[[  5., 239.],
            #   [  8.,  14.],
            #   [252.,   2.],
            #   [  5.,   1.]])
            # transform coordinates
            for receiver in range(noofreceivers):
                for component in range(2):
                    if dopbin_iq[idx][receiver][component] > 127:
                        dopbin_iq[idx][receiver][component] = dopbin_iq[idx][receiver][component] - 256
                
                #Get absolute value of complex signal
                #absvalue = np.sqrt(dopbin_iq[idx][receiver][0]**2 + dopbin_iq[idx][receiver][1]**2)
                #receiver_values[receiver][idx] = absvalue
        frequency = freqs[dopbin_x_freqx]
        height = np.array(dopbin_x_hflag) * 3

        dopbin_x_dop_flag = np.array(dopbin_x_dop_flag)
        dopsn2 = 1/(ndops * npulses_avgd/pps)
        dop_shifts = (dopbin_x_dop_flag - ndops/2) * dopsn2
        
        #datetime object representing time of first observation in UTC
        datetime_init_observation =  datetime.datetime(year=year, month=month_number,day=day, 
                                                    hour=hour, minute=minute, second=sec,tzinfo=timezone.utc)
        dopbin_iq = np.array(dopbin_iq)
        #Combine the real and imaginary parts into one complex part
        complex_signal = dopbin_iq[:,:, 0] + 1j * dopbin_iq[:,:,1]
        return dict({
            "site": site,
            "datetime": datetime_init_observation,
            "source": filename.name,
            "ndops": ndops,
            "filetype": filetype,
            "nfreqs": nfreqs,
            "minheight": minheight,
            "maxheight": maxheight,
            "pps": pps,
            "dtime": dtime,
            "extension": filename.suffix.replace('.',''),
            "noofreceivers": noofreceivers,
            "timepartitions": time_partitions,
        }), height, frequency, dop_shifts, complex_signal

    def read_raw_data_dir(self, input_dir: Path, extension: str, multithread=False, backend='threading'):
        """
        Reads raw data from a folder containing data for an entire day. Reads both md3 and md4 extensions, switchable with argument.

        Returns metadata, and the arrays containing height, frequency, and signals from the receivers.

        TODO: Description
        """
        all_heights, all_freqs, all_dopshifts, all_sensors = np.array([], dtype=np.int32), np.array([], dtype=np.float64), np.array([], dtype=np.float32), np.empty(shape=(0,4), dtype=np.complex128)
        all_metadata = dict()
        files_list = list(Path(input_dir).glob(f"*.{extension}"))
        if len(files_list) == 0:
            raise FolderNotContainingData(input_dir)
        lpointer = 0
        if multithread:
            cpu_count = multiprocessing.cpu_count()
            with joblib.Parallel(n_jobs=cpu_count, backend=backend, verbose=True) as parallel:
                results = parallel(joblib.delayed(self.read_raw_data)(files) for files in files_list)
            for idy, result in enumerate(results):
                metadata, heights, freqs, dop_shifts, sensors = result
                time_partitions = metadata['timepartitions']
                new_timepartition = dict()
                for minute, idz in time_partitions.items():
                    new_timepartition_key = f"{metadata['datetime'].hour:02d}:{minute:02d}"
                    new_timepartition[new_timepartition_key] = idz + lpointer

                if(idy == 0):
                    obs_datetime: datetime.datetime = metadata['datetime']
                    obs_dateonly = datetime.datetime(year=obs_datetime.year, month=obs_datetime.month, 
                                                    day=obs_datetime.day, tzinfo=obs_datetime.tzinfo,
                                                    hour=0,minute=0,second=0)
                    all_metadata = metadata
                    all_metadata['datetime'] = obs_dateonly
                    all_metadata['source'] = input_dir.name
                    all_metadata['extension'] = extension
                    all_metadata['timepartitions'] = dict()
                    

                all_metadata['timepartitions'] |= new_timepartition
                all_heights = np.append(all_heights, heights, axis=0)
                all_freqs = np.append(all_freqs, freqs, axis=0)
                all_dopshifts = np.append(all_dopshifts, dop_shifts, axis=0)
                all_sensors = np.append(all_sensors, sensors, axis=0)
                lpointer = all_metadata['timepartitions'][max(all_metadata['timepartitions'])]

        else:
            for idy, input_file in enumerate(files_list):
                if input_file.exists():
                    metadata, heights, freqs, dop_shifts, sensors = self.read_raw_data(input_file)
                    #Todo: Read metadata first, and then have fixed size arrays
                    time_partitions = metadata['timepartitions']
                    new_timepartition = dict()
                    for minute, idz in time_partitions.items():
                        new_timepartition_key = f"{metadata['datetime'].hour:02d}:{minute:02d}"
                        new_timepartition[new_timepartition_key] = idz + lpointer

                    if(idy == 0):
                        obs_datetime: datetime.datetime = metadata['datetime']
                        obs_dateonly = datetime.datetime(year=obs_datetime.year, month=obs_datetime.month, 
                                                        day=obs_datetime.day, tzinfo=obs_datetime.tzinfo,
                                                        hour=0,minute=0,second=0)
                        all_metadata = metadata
                        all_metadata['datetime'] = obs_dateonly
                        all_metadata['source'] = input_dir.name
                        all_metadata['extension'] = extension
                        all_metadata['timepartitions'] = dict()

                    all_metadata['timepartitions'] |= new_timepartition
                    #Avoid appending, run two passes of the iteration
                    all_heights = np.append(all_heights, heights, axis=0)
                    all_freqs = np.append(all_freqs, freqs, axis=0)
                    all_dopshifts = np.append(all_dopshifts, dop_shifts, axis=0)
                    all_sensors = np.append(all_sensors, sensors, axis=0)
                    lpointer = all_metadata['timepartitions'][max(all_metadata['timepartitions'])]
        return all_metadata, all_heights, all_freqs, all_dopshifts, all_sensors
