import numpy as np
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt
import src.cadiparser.csvio as csvio
import src.cadiparser.readrawdata as readrawdata
from pathlib import Path
import copy
from matplotlib import colormaps, colors, ticker
from PIL import Image, ImageOps
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.neighbors import LocalOutlierFactor
from sklearn.model_selection import train_test_split
from matplotlib.ticker import ScalarFormatter


def preprocess_data(metadata: dict, freqs: np.ndarray, heights: np.ndarray, dop_shifts: np.ndarray, 
                    signals: np.ndarray, timestamp: str, timestamp2: str):
    """
        Function to read observation data from lists containing data for an hour/day. 
        Timestamps are provided as strings in HH:MM:SS format.

        Returns freqs, heights, doppler shifts, and median power between timestamps
    """
    timepartitions = metadata['timepartitions']
    height_selection: np.ndarray = heights[timepartitions[timestamp]:timepartitions[timestamp2]]
    #height_bins = np.unique(height_selection)
    dop_selection: np.ndarray = dop_shifts[timepartitions[timestamp]:timepartitions[timestamp2]]
    #dop_bins = np.unique(dop_selection)
    freq_selection: np.ndarray = freqs[timepartitions[timestamp]:timepartitions[timestamp2]]
    #freq_bins = np.unique(freq_selection)

    real_signals = np.median(np.abs(signals[timepartitions[timestamp]:timepartitions[timestamp2], :]), axis=1)
    median_power_selection: np.ndarray = np.zeros_like(real_signals)
    mask = real_signals <= 0.0
    median_power_selection[mask] = 0.0
    median_power_selection[~mask] = 20*np.log10(real_signals[~mask])

    return freq_selection, height_selection, dop_selection, median_power_selection

def make_edges(freq_bins: np.ndarray, height_bins: np.ndarray):
    """
        Makes edges from unique values of frequencies and heights. 
        Needed for plotting ionogram with scale, since the spacing between freqs and heights can be uneven.

        If length of an input array is 100, then the returning edges will have 101 elements. 
    """
    x_edges: np.ndarray = np.concatenate([
    [freq_bins[0] - (freq_bins[1] - freq_bins[0]) / 2],
    (freq_bins[:-1] + freq_bins[1:]) / 2,
    [freq_bins[-1] + (freq_bins[-1] - freq_bins[-2]) / 2]
    ])

    y_edges: np.ndarray = np.concatenate([
        [height_bins[0] - (height_bins[1] - height_bins[0]) / 2],
        (height_bins[:-1] + height_bins[1:]) / 2,
        [height_bins[-1] + (height_bins[-1] - height_bins[-2]) / 2]
    ])
    return x_edges, y_edges

def split_at_zeros_with_indices(arr):
    """
        Split an array into subarrays about the zeros in the input array. Subarrays exclude the zeros.

        Returns arrays and the original input array indices of the elements in the subarray
    """
    subarrays = []
    index_ranges = []

    # Get indices of zeros
    zero_indices = np.where(arr == 0)[0]

    # Add boundaries
    starts = np.concatenate(([0], zero_indices + 1))
    ends = np.concatenate((zero_indices, [len(arr)]))

    # Extract subarrays and index ranges, excluding zeros
    for start, end in zip(starts, ends):
        sub = arr[start:end]
        if np.any(sub != 0):  # Skip if only zero or empty
            mask = sub != 0
            subarrays.append(sub[mask])
            index_ranges.append(np.arange(start, end)[mask])

    return subarrays, index_ranges