import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
from pathlib import Path
from src.utils.pandasutils import PandasUtils
from datetime import datetime
import json

class ParquetUtils:
    def __init__(self):
        pass
    @staticmethod
    def write_to_parquet(metadata: dict, freqs: np.ndarray, heights: np.ndarray, freq_list: np.ndarray, dop_shifts: np.ndarray, sensors: np.ndarray, 
                         filename: Path, parent: Path, extension: str):
        df_sensors = PandasUtils.create_pandas_from_arrays(metadata, freqs, heights, dop_shifts, sensors)
        pa_table = pa.Table.from_pandas(df_sensors)
        metadata['datetime'] = str(metadata['datetime'])
        metadata['freqbins'] = str(list(freq_list.data))
        metadata_bytes = {
            str(k).encode('utf8'): str(v).encode('utf8') for k, v in metadata.items()
        }
        pa_table = pa_table.replace_schema_metadata(metadata_bytes)
        pq.write_table(pa_table, f"{parent / filename.stem}_{extension}.parquet")
    
    @staticmethod
    def read_from_parquet(filename: str | Path):
        file_list = []
        new_table_pa = pq.read_table(filename)
        decoded_metadata = {k.decode(): v.decode() for k, v in new_table_pa.schema.metadata.items()}
        new_table_df = new_table_pa.to_pandas()
        new_table_df = new_table_df.set_index('__index_level_0__')
        new_table_df.index.name = None
        decoded_metadata['timepartitions'] = json.loads(decoded_metadata['timepartitions'].replace("'", '"'))
        decoded_metadata['freqbins'] = json.loads(decoded_metadata['freqbins'].replace("'", ''))
        #Refactor these two lists below into a new file?
        converted_value_keys = ['ndops', 'dheight', 'nfreqs', 'nheights', 'minheight', 'maxheight', 'pps', 'npulses_avgd', 'dtime', 'noofreceivers', 'freqbins']
        converted_value_key_types = [int, float, int, int, int, int, int, int, int, int, np.array]
        for key, type_to_convert in zip(converted_value_keys, converted_value_key_types):
            decoded_metadata[key] = type_to_convert(decoded_metadata[key])
        frequency, height, dop_shifts, complex_signal = PandasUtils.create_arrays_from_pandas(decoded_metadata, new_table_df)
        filename_str = filename.name if isinstance(filename, Path) else filename    #'5D090700_md4.parquet'
        for _ in range(len(decoded_metadata['timepartitions'])):
            file_list.append(filename_str[:-8].replace("_", '.'))
        decoded_metadata['datetime'] = datetime.strptime(decoded_metadata['datetime'], '%Y-%m-%d %H:%M:%S%z')
        freqs = decoded_metadata['freqbins']
        del decoded_metadata['freqbins']
        metadata = decoded_metadata
        return file_list, metadata, height, frequency, freqs, dop_shifts, complex_signal
    