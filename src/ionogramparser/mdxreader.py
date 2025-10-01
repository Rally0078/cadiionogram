"""
    MDx binary format ionogram parser.

    Classes
    ---------
    MDreader
        Static Methods
        ---------
        read_raw_data: Reads ionogram data from mdx file.

        read_raw_data_dir: Reads ionogram data from a directory containing one or more mdx files.
"""
import multiprocessing
import joblib
multiprocessing.freeze_support()

import os
import copy
from pathlib import Path
import struct
import datetime
from datetime import timezone
from time import strptime
from io import BufferedReader

from src.errorhandlers.errorhandling import FolderNotContainingData
from src.ionogramparser.baserawreader import DataReader
import numpy as np



#MDn format reader, extended from DataReader baseclass
class MDreader(DataReader):
    def __init__(self):
        pass
    
    @staticmethod
    def _safe_reader(file: BufferedReader, bytes):
        data = file.read(bytes)
        if data is None or len(data) < bytes:
            raise EOFError
        return data
    
    @staticmethod
    def read_raw_data(filename: Path) -> tuple[list, dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Read CADI ionogram data from mdx binary formats(x=1,2,3,4).

        Parameters
        ----------
        filename : `Path`
            Location of the mdx file to parse.

        Returns
        ----------
        Returns multiple values as follows, where the arrays can be partitioned by the timepartitions provided in `metadata`.

        file_list : `List[str]`
            List containing the name of the file.

        metadata : `Dict`
            Dictionary containing metadata of the observations. Contains header info stored in the mdx file and \
        time partitions in key-value pairs to partition the observations by time.

        height : `numpy.ndarray`
            Heights in km from all the observations in the file. Use the time_partitions to \
        partition the heights by observation time.

        frequency : `numpy.ndarray` 
            Frequencies in Hz from all the observations in the file. Use the time_partitions to \
        partition the heights by observation time.

        freqs : `numpy.ndarray`
            List of all frequencies used by the Ionosonde.

        dop_shifts : `numpy.ndarray`
            Contains the scaled doppler shift values of all the observations.

        dopbin_iq : `numpy.ndarray`
            Contains the complex signal value from each receiver. Use the time_partitions \
        to partition the signals by observation time.

        Examples
        --------
        Read one md4 file from current directory
        
        >>> files, metadata, heights, frequencies, freq_list, dop_shifts, signals = MDreader.read_raw_data(Path('./input.md4'))
        
        """
        max_ntimes = 256
        max_ndopbins = 300000
        dheight = 3.0  # not defined in data file
        if isinstance(filename, Path):
            extension = filename.suffix.replace('.', '')
        else:
            extension='unknown'
        file_list = []
        metadata = dict({
                    "site": '',
                    "datetime": '',
                    "source": filename.name if isinstance(filename, Path) else filename,
                    "filetype": '',
                    "ndops": 0,
                    "nfreqs": 0,
                    "nheights": 0,
                    "minheight": 0,
                    "maxheight": 0,
                    "dheight": 0,
                    "pps": 0,
                    "npulses_avgd": 0,
                    "dtime": 0,
                    "extension": extension,
                    "noofreceivers": 0,
                    "timepartitions": 0,
        })
        
        try:
            with open(filename, "rb") as f:
                f.seek(-1,2)     # go to the file end.
                eof = f.tell()   # get the end of file location
                f.seek(0,0)      # go back to file beginning
                # 1) read header information as described in the documentation p. 26-27
                site = MDreader._safe_reader(f, 3).decode("utf-8")
                ascii_datetime = MDreader._safe_reader(f, 22).decode("utf-8")
                filetype = MDreader._safe_reader(f, 1).decode("utf-8")

                nfreqs = struct.unpack("<H", MDreader._safe_reader(f, 2))[0]

                ndops = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                minheight = struct.unpack("<H", MDreader._safe_reader(f, 2))[0]

                maxheight = struct.unpack("<H", MDreader._safe_reader(f, 2))[0]
                pps = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]

                npulses_avgd = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                base_thr100 = struct.unpack("<H", MDreader._safe_reader(f, 2))[0]
                noise_thr100 = struct.unpack("<H", MDreader._safe_reader(f, 2))[0]
                min_dop_forsave = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                dtime = struct.unpack("<H", MDreader._safe_reader(f, 2))[0]
                gain_control = MDreader._safe_reader(f, 1).decode("utf-8")
                sig_process = MDreader._safe_reader(f, 1).decode("utf-8")
                noofreceivers = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                spares = MDreader._safe_reader(f, 11).decode("utf-8")

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

                freqs = np.array([struct.unpack("<f", MDreader._safe_reader(f, 4))[0] for i in range(nfreqs)], dtype=np.float32)

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
                file_list = []
                time_partitions = dict()

                time_min = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                
                # Read complex sensor data from all receivers of all observations till eof.
                while f.tell() < eof and time_min != 255 and  time_min < 60:
                    #Iterate through each time of observation
                    time_sec = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                    flag = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]  # gainflag
                    timex += 1
                    time_partition = datetime.time(hour=hour, minute=time_min, second=time_sec, tzinfo=timezone.utc)
                    for freqx in range(nfreqs):
                        #Iterate through each frequency at a given time of observation
                        noise_flag = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]  # noiseflag
                        noise_power10 = struct.unpack("<H", MDreader._safe_reader(f, 2))[0]
                        frebinx += 1
                        frebins_gain_flag.append(flag)
                        frebins_noise_flag.append(noise_flag)
                        frebins_noise_power10.append(noise_power10)
                        flag = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                        while flag < 224:
                            #Iterate through all sensor values at a given time and at a given frequency
                            ndops_oneh = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                            hflag = flag
                            if ndops_oneh >= 128:
                                ndops_oneh = ndops_oneh - 128
                                hflag = hflag + 200
                            for dopx in range(ndops_oneh):
                                dop_flag = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]
                                for rec in range(noofreceivers):
                                    re_part = MDreader._safe_reader(f, 1)
                                    im_part = MDreader._safe_reader(f, 1)
                                    if re_part == None or im_part == None:
                                        bad_byte_flag = True
                                        break
                                    iq_bytes[rec, 0] = struct.unpack("<B", re_part)[0]
                                    iq_bytes[rec, 1] = struct.unpack("<B", im_part)[0]
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
                            flag = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]  # next hflag/gainflag/FF
                    time_partitions[f"{time_partition.hour:02d}:{time_partition.minute:02d}:{time_partition.second:02d}"] = len(dopbin_iq)
                    file_list.append(filename.name if isinstance(filename, Path) else filename)
                    time_min = flag
                    if ((f.tell() - 1) != eof):
                        time_min = struct.unpack("<B", MDreader._safe_reader(f, 1))[0]  # next record
        except EOFError:
            return file_list, metadata, np.array([]), np.array([]), np.array([]), np.array([]), np.array([])

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
        complex_signal = np.empty(shape=(len(frequency), 2 * noofreceivers), dtype=np.int8)
        for receiver_re_im in range(2 * noofreceivers):
            #Real component
            if receiver_re_im % 2 == 0:
                complex_signal[:, receiver_re_im] = dopbin_iq[:, receiver_re_im//2, 0]
            #Imaginary component
            else:
                complex_signal[:, receiver_re_im] = dopbin_iq[:, receiver_re_im//2, 1]
        
        metadata = dict({
        "site": site,
        "datetime": datetime_init_observation,
        "source": filename.name if isinstance(filename, Path) else filename,
        "filetype": filetype,
        "ndops": ndops,
        "nfreqs": nfreqs,
        "nheights": nheights,
        "minheight": minheight,
        "maxheight": maxheight,
        "dheight": dheight,
        "pps": pps,
        "npulses_avgd": npulses_avgd,
        "dtime": dtime,
        "extension": filename.suffix.replace('.','') if isinstance(filename, Path) else "unknown",
        "noofreceivers": noofreceivers,
        "timepartitions": time_partitions,
        })

        height = height.astype(np.float32)
        dop_shifts = dop_shifts.astype(np.float16)
        complex_signal = complex_signal.astype(np.int8)
        return file_list, metadata, height, frequency, freqs, dop_shifts, complex_signal

    @staticmethod
    def read_raw_data_dir(input_dir: Path, extension: str, 
                          multithread=False, backend='threading') -> tuple[list, dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Reads mdx binary format raw data from a folder containing data for an entire day. Reads all mdx formats, switchable with argument.

        Parameters
        ----------
        folder : `Path`
            Path to the folder containing the mdx files to parse.

        extension : `str`
            Extension of the mdx format file to be parsed. Possible values are `'md1'`, `'md2'`, `'md3'`, `'md4'` Can parse only one extension at a time from a folder.

        multithread : `bool`
            Enable multithreaded reading using joblib. `False` by default. **Do not** use this option within the **PySide6 GUI code**, \
                otherwise each joblib job opens an instance of the GUI when particular backends are selected.
        
        backend : `str`
            Backend for joblib. `'threading'` by default. The `'loky'` and `'multiprocessing'` backends cannot be used within the PySide 6 GUI \
                due to the reason mentioned above.

        Returns
        ----------
        Returns multiple values as follows, where the arrays can be partitioned by the timepartitions provided in `metadata`.

        file_list : `List[str]`
            List containing the name of the file.

        metadata : `Dict`
            Dictionary containing metadata of the observations. Contains header info stored in the mdx file and \
        time partitions in key-value pairs to partition the observations by time.

        height : `numpy.ndarray`
            Heights in km from all the observations in the file. Use the time_partitions to \
        partition the heights by observation time.

        frequency : `numpy.ndarray` 
            Frequencies in Hz from all the observations in the file. Use the time_partitions to \
        partition the heights by observation time.

        freqs : `numpy.ndarray`
            List of all frequencies used by the Ionosonde.

        dop_shifts : `numpy.ndarray`
            Contains the scaled doppler shift values of all the observations.

        dopbin_iq : `numpy.ndarray`
            Contains the complex signal value from each receiver. Use the time_partitions \
        to partition the signals by observation time.

        Examples
        --------
        Read all md4 files from a directory.
        
        >>> files, metadata, heights, frequencies, freq_list, dop_shifts, signals = MDreader.read_raw_data_dir(Path('./datafolder'), extension='md4')
        
        """
        all_heights, all_freqs, all_freq_list, all_dopshifts, all_sensors = np.array([], dtype=np.int32), np.array([], dtype=np.float32), np.array([], dtype=np.float32), \
                                                                            np.array([], dtype=np.float16), np.empty(shape=(0,8), dtype=np.int8)
        all_files_list = []
        all_metadata = dict()
        files_list = list(Path(input_dir).glob(f"*.{extension}"))
        if len(files_list) == 0:
            raise FolderNotContainingData(input_dir)
        lpointer = 0
        if multithread:
            cpu_count = multiprocessing.cpu_count()
            with joblib.Parallel(n_jobs=cpu_count, backend=backend) as parallel:
                results = parallel(joblib.delayed(MDreader.read_raw_data)(files) for files in files_list)
            for idy, result in enumerate(results):
                files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = result  # type: ignore
                if len(heights) > 0:
                    time_partitions = metadata['timepartitions']
                    new_timepartition = dict()
                    for time_partition, idz in time_partitions.items():
                        #time_partition = datetime.datetime.strptime(time_partition, "%H:%M:%S")
                        #new_timepartition_key = f"{metadata['datetime'].hour:02d}:{minute:02d}
                        new_timepartition[time_partition] = idz + lpointer

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
                        all_freq_list = np.append(all_freq_list, freq_list)
                        all_sensors = all_sensors.reshape((0, 2 * metadata['noofreceivers']))
                        

                    all_metadata['timepartitions'] |= new_timepartition
                    all_files_list.extend(files_list)
                    all_heights = np.append(all_heights, heights, axis=0)
                    all_freqs = np.append(all_freqs, freqs, axis=0)
                    all_dopshifts = np.append(all_dopshifts, dop_shifts, axis=0)
                    all_sensors = np.append(all_sensors, sensors, axis=0)
                    lpointer = all_metadata['timepartitions'][max(all_metadata['timepartitions'])]
                else:
                    continue

        else:
            for idy, input_file in enumerate(files_list):
                if input_file.exists():
                    files_list, metadata, heights, freqs, freq_list, dop_shifts, sensors = MDreader.read_raw_data(input_file)
                    if len(heights) > 0:
                        time_partitions = metadata['timepartitions']
                        new_timepartition = dict()
                        for time_partition, idz in time_partitions.items():
                        #time_partition = datetime.datetime.strptime(time_partition, "%H:%M:%S")
                        #new_timepartition_key = f"{metadata['datetime'].hour:02d}:{minute:02d}"
                            new_timepartition[time_partition] = idz + lpointer

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
                            all_freq_list = np.append(all_freq_list, freq_list)

                        all_metadata['timepartitions'] |= new_timepartition
                        all_files_list.extend(files_list)
                        #Avoid appending, run two passes of the iteration
                        all_heights = np.append(all_heights, heights, axis=0)
                        all_freqs = np.append(all_freqs, freqs, axis=0)
                        all_dopshifts = np.append(all_dopshifts, dop_shifts, axis=0)
                        all_sensors = np.append(all_sensors, sensors, axis=0)
                        lpointer = all_metadata['timepartitions'][max(all_metadata['timepartitions'])]
                    else:
                        continue
        return all_files_list, all_metadata, all_heights, all_freqs, all_freq_list, all_dopshifts, all_sensors
