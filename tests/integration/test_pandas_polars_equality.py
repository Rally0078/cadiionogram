import numpy as np
import pandas as pd
import polars as pl
from src.utils.pandasutils import PandasUtils
from src.utils.polarsutils import PolarsUtils


class TestPandasPolarsEquality:
    """Integration test to verify pandas and polars dataframes are equivalent."""
    
    def test_dataframe_equality(self, mock_data):
        """
        Test that pandas and polars dataframes created from the same arrays are equivalent.
        """
        file_list, metadata, heights, frequencies, freq_list, dop_shifts, sensors = mock_data
        
        # Create pandas dataframe
        df_pandas = PandasUtils.create_pandas_from_arrays(
            metadata, 
            freqs=frequencies, 
            heights=heights, 
            dop_shifts=dop_shifts, 
            sensors=sensors
        )
        
        # Create polars dataframe
        df_polars = PolarsUtils.create_polars_from_arrays(
            metadata, 
            freqs=frequencies, 
            heights=heights, 
            dop_shifts=dop_shifts, 
            sensors=sensors
        )
        
        # Verify both have the same number of rows
        assert len(df_pandas) == len(df_polars), "Row counts should match"
        assert len(df_pandas) == len(heights), "Row count should match input data length"
        
        # Verify column names match (excluding datetime/index differences)
        pandas_cols = set(df_pandas.columns)
        polars_cols = set(df_polars.columns)
        # Remove datetime column from polars as pandas uses it as index
        polars_cols.discard("datetime")
        
        assert pandas_cols == polars_cols, f"Column names should match. Pandas: {pandas_cols}, Polars: {polars_cols}"
        
        # Convert pandas index (datetime) to series for comparison
        pandas_datetime = df_pandas.index.to_series().reset_index(drop=True)
        polars_datetime = df_polars["datetime"].to_pandas()
        
        # Compare datetime columns (handle timezone-aware datetimes)
        pandas_datetime_dt = pd.to_datetime(pandas_datetime, utc=True)
        polars_datetime_dt = pd.to_datetime(polars_datetime, utc=True)
        
        # Both should be in the same order (based on timepartitions)
        # Convert to numpy arrays for element-wise comparison
        pandas_datetime_np = pandas_datetime_dt.values
        polars_datetime_np = polars_datetime_dt.values
        
        # Check if all datetime values match (in order)
        assert len(pandas_datetime_np) == len(polars_datetime_np), "Datetime arrays should have same length"
        assert np.array_equal(pandas_datetime_np, polars_datetime_np), "Datetime values should match in order"
        
        # Compare each column's data (in the same order)
        for col in pandas_cols:
            pandas_values = df_pandas[col].values
            polars_values = df_polars[col].to_numpy()
            
            # Verify arrays have same length
            assert len(pandas_values) == len(polars_values), \
                f"Column {col} should have same length. Pandas: {len(pandas_values)}, Polars: {len(polars_values)}"
            
            # Use numpy allclose for floating point comparison, exact match for integers
            if np.issubdtype(pandas_values.dtype, np.floating):
                assert np.allclose(pandas_values, polars_values, equal_nan=True), \
                    f"Column {col} values should match (floating point comparison)"
            else:
                assert np.array_equal(pandas_values, polars_values), \
                    f"Column {col} values should match (exact comparison)"
        
        # Verify data types are compatible
        for col in pandas_cols:
            pandas_dtype = df_pandas[col].dtype
            # Get polars dtype from the actual numpy array (more reliable)
            polars_values = df_polars[col].to_numpy()
            polars_np_dtype = polars_values.dtype
            
            # Check if types are compatible (allowing for some flexibility)
            # First check exact match
            if pandas_dtype == polars_np_dtype:
                continue
            
            # Then check if both are floating point types
            pandas_is_float = np.issubdtype(pandas_dtype, np.floating)
            polars_is_float = np.issubdtype(polars_np_dtype, np.floating)
            if pandas_is_float and polars_is_float:
                continue
            
            # Then check if both are integer types
            pandas_is_int = np.issubdtype(pandas_dtype, np.integer)
            polars_is_int = np.issubdtype(polars_np_dtype, np.integer)
            if pandas_is_int and polars_is_int:
                continue
            
            # If none of the above conditions match, fail
            assert False, \
                f"Column {col} dtypes should be compatible. Pandas: {pandas_dtype}, Polars: {polars_np_dtype}"
