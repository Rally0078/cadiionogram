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
from numba import njit
from scipy.integrate import simpson
from joblib import Parallel


def preprocess_data(metadata: dict, freqs: np.ndarray, heights: np.ndarray, dop_shifts: np.ndarray, 
                    signals: np.ndarray, timestamp: str | int, timestamp2: str | int, index_mode: bool = False):
    """
        Function to read observation data from lists containing data for an hour/day. 
        Timestamps are provided as strings in HH:MM:SS format, or as an index in the whole day's array.

        Returns freqs, heights, doppler shifts, and median power between timestamps
    """
    
    timepartitions = metadata['timepartitions']
    if index_mode == False:
        height_selection: np.ndarray = heights[timepartitions[timestamp]:timepartitions[timestamp2]]
        #height_bins = np.unique(height_selection)
        dop_selection: np.ndarray = dop_shifts[timepartitions[timestamp]:timepartitions[timestamp2]]
        #dop_bins = np.unique(dop_selection)
        freq_selection: np.ndarray = freqs[timepartitions[timestamp]:timepartitions[timestamp2]]
        #freq_bins = np.unique(freq_selection)
        real_signals = np.median(np.abs(signals[timepartitions[timestamp]:timepartitions[timestamp2], :]), axis=1)
    else:
        height_selection: np.ndarray = heights[timestamp:timestamp2]
        #height_bins = np.unique(height_selection)
        dop_selection: np.ndarray = dop_shifts[timestamp:timestamp2]
        #dop_bins = np.unique(dop_selection)
        freq_selection: np.ndarray = freqs[timestamp:timestamp2]
        real_signals = np.median(np.abs(signals[timestamp:timestamp2, :]), axis=1)

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

def plot_timestamp(metadata: dict, freqs: np.ndarray, heights: np.ndarray, dop_shifts: np.ndarray, 
                    signals: np.ndarray, timestamp: str, timestamp2: str, output_path: str | Path,
                    threshold_freq_scale=0.3, threshold_height_scale=0.25, threshold_height_km=160, index_mode: bool = False):
    freq_selection, height_selection, dop_selection, median_power_selection = preprocess_data(metadata, freqs, heights, dop_shifts, 
                    signals, timestamp, timestamp2, index_mode=index_mode)
    freq_bins, height_bins = np.unique(freq_selection), np.unique(height_selection)
    x_edges, y_edges = make_edges(freq_bins, height_bins)
    freq_map = {val: idx for idx, val in enumerate(freq_bins)}
    height_map = {val: idx for idx, val in enumerate(height_bins)}
    timepartitions = metadata['timepartitions']
    rows = np.array([height_map[val] for val in height_selection])
    cols = np.array([freq_map[val] for val in freq_selection])
    if index_mode:
        ionogram_title = str(list(timepartitions.keys())[list(timepartitions.values()).index(timestamp2)])
        filename = ionogram_title.replace(':','')
    else:
        ionogram_title = timestamp
        if type(timestamp) == str:
            filename = timestamp.replace(':','')
    nx, ny = len(freq_bins), len(height_bins)
    Z = rasterize_scatter_with_radius(freq_selection, height_selection, median_power_selection,
                                      width=512, height=512, radius=2)
    img_tmp = Z.copy()
    img_tmp[img_tmp == 0] = np.nan
    fig = plt.figure(figsize=(12, 16))
    ax_top = fig.add_subplot(211)
    qm_top = ax_top.imshow(img_tmp, extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]], aspect='auto', cmap='grey')
    ax_top.scatter(freq_selection, height_selection, s=7.5, c=median_power_selection, cmap='pink', alpha=0.25)
    #cbar = fig.colorbar(qm, ticks=np.arange(0, 50, 10))
    #cbar.ax.set_ylim(0, 45)
    ax_top.set_xticks(np.arange(0, 18e6, 2e6))
    ax_top.set_xlim(1e6, 16e6)
    ax_top.set_yticks(np.arange(0, 1100, 50))
    ax_top.set_ylim(50, 1100)
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((6, 6))  # Force 1e6 scale

    ax_top.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax_top.xaxis.set_major_formatter(formatter)
    ax_top.set_xlabel("Frequency")
    ax_top.set_ylabel("Height (km)")
    ax_top.grid()
    ax_top.set_title(f"Unfiltered ionogram at {ionogram_title}")

    Z_filtered = filter_ionogram(Z, freq_bins=freq_bins, height_bins=height_bins, 
                                 threshold_freq_scale=threshold_freq_scale, 
                                 threshold_height_scale=threshold_height_scale, 
                                 threshold_height_km=threshold_height_km)
    img_tmp = Z_filtered.copy()
    img_tmp[img_tmp == 0] = np.nan
    ax_bottom = fig.add_subplot(212)

    qm_bottom = ax_bottom.imshow(img_tmp, extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]], aspect='auto', cmap='grey')
    ax_bottom.scatter(freq_selection, height_selection, s=7.5, c=median_power_selection, cmap='pink', alpha=0.25)
    #cbar = fig.colorbar(qm, ticks=np.arange(0, 50, 10))
    #cbar.ax.set_ylim(0, 45)
    ax_bottom.set_xticks(np.arange(0, 18e6, 2e6))
    ax_bottom.set_xlim(1e6, 16e6)
    ax_bottom.set_yticks(np.arange(0, 1100, 50))
    ax_bottom.set_ylim(50, 1100)
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((6, 6))  # Force 1e6 scale

    ax_bottom.yaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax_bottom.xaxis.set_major_formatter(formatter)
    ax_bottom.set_xlabel("Frequency")
    ax_top.set_ylabel("Height (km)")
    ax_bottom.grid()
    ax_bottom.set_title(f"Filtered ionogram at {ionogram_title}")

    if output_path:
        fig.savefig(output_path / f"{filename}.jpg", dpi=150, bbox_inches='tight')
    else:
        fig.show()
    plt.close(fig)

def filter_ionogram(Z_raw: np.ndarray, freq_bins: np.ndarray, height_bins: np.ndarray, 
                    threshold_freq_scale=0.3, threshold_height_scale=0.25, threshold_height_km=160):
    Z_binary = copy.deepcopy(Z_raw)
    Z_tmp = copy.deepcopy(Z_raw)
    nan_args = np.argwhere(np.isnan(Z_tmp))
    #Z_tmp[nan_args] = 0
    Z_binary[np.isnan(Z_binary)] = 0

    Z_binary[Z_binary < 0] = 0
    Z_binary[Z_binary > 0] = 1

    proj_freq = np.sum(Z_binary, axis=0)

    integrals = []
    subarrays, indices = split_at_zeros_with_indices(proj_freq)

    for subarray, index in zip(subarrays, indices):
        integral = simpson(subarray, freq_bins[index])/1e7
        integrals.append(integral)
    integrals = np.array(integrals)
    avg_integral = np.average(integrals)
    to_delete_freqs = np.array([], dtype=np.int64)
    max_freq = 0
    max_idx = -1
    for idx, (subarray, index) in enumerate(zip(subarrays, indices)):
        if integrals[idx] < threshold_freq_scale * avg_integral:
            to_delete_freqs = np.append(to_delete_freqs, index)
    idx = np.argmax(integrals)
    max_freq = np.max(freq_bins[indices[idx]])
    max_idx = np.max(indices[idx])
    to_delete_freqs = np.append(to_delete_freqs, np.arange(max_idx, len(proj_freq)))

    #Z_tmp[np.isnan(Z_tmp)] = 0
    #nan_args = np.argwhere(np.isnan(Z_tmp)).flatten()
    Z_binary[:, to_delete_freqs] = 0
    Z_tmp[:, to_delete_freqs] = np.nan
    #Z_tmp[nan_args] = np.nan

    proj_height = np.sum(Z_binary, axis=1)
    subarrays, indices = split_at_zeros_with_indices(proj_height)
    integrals = []
    for subarray, index in zip(subarrays, indices):
        integral = simpson(subarray, height_bins[index])/100
        integrals.append(integral)
    integrals = np.array(integrals)
    avg_integral = np.average(integrals)
    to_delete_heights = np.array([], dtype=np.int64)
    for idx, (subarray, index) in enumerate(zip(subarrays, indices)):
        if (integrals[idx] < threshold_height_scale * avg_integral) and (np.min(height_bins[index]) > threshold_height_km):
            to_delete_heights = np.append(to_delete_heights, index)
    
    Z_tmp[to_delete_heights, :] = np.nan
    #Z_tmp[nan_args] = np.nan
    return Z_tmp

def rasterize_scatter_with_radius(x, y, intensity, width=1024, height=1024, radius=3):
    x = np.asarray(x)
    y = np.asarray(y)

    intensity = np.asarray(intensity, dtype=np.float32)

     # Bounds and scale for normalization
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()
    x_range = xmax - xmin or 1.0
    y_range = ymax - ymin or 1.0

    # Normalize to pixel grid
    x_idx = np.round((x - xmin) / x_range * (width - 1)).astype(int)
    y_idx = np.round((y - ymin) / y_range * (height - 1)).astype(int)
    y_idx = height - 1 - y_idx  # Flip for image coordinates

    # Clip to avoid out-of-bounds
    x_idx = np.clip(x_idx, 0, width - 1)
    y_idx = np.clip(y_idx, 0, height - 1)

    # Create image and count arrays
    image = np.zeros((height, width), dtype=np.float32)
    
    # Splat each point within the defined radius
    for xi, yi, val in zip(x_idx, y_idx, intensity):
        # Define the region around the point (radius)
        x_min = max(xi - radius, 0)
        x_max = min(xi + radius + 1, width)
        y_min = max(yi - radius, 0)
        y_max = min(yi + radius + 1, height)
        
        # Splat intensity over the region
        image[y_min:y_max, x_min:x_max] += val
    
    return image