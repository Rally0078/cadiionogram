import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.interpolate import interp1d

def fft_filter(igrmarr):
    """
    Filters the ionogram using a 2D FFT to remove noise.
    This replicates the FFT filtering logic from the IDL script.

    Args:
        igrmarr (np.ndarray): The 2D ionogram data array (n_freqs, n_heights).

    Returns:
        np.ndarray: The filtered ionogram data as a real-valued array.
    """
    n_freqs, n_heights = igrmarr.shape
    if n_freqs == 0 or n_heights == 0:
        return igrmarr

    # Perform 2D FFT
    transformed_igrm = np.fft.fft2(igrmarr)

    # The IDL code zeros out frequency components from 20% to 80% of the
    # array indices in the Fourier domain. This acts as a filter to
    # remove periodic noise and sharpen the main trace.
    f_start, f_end = int(0.2 * n_freqs), int(0.8 * n_freqs)
    h_start, h_end = int(0.2 * n_heights), int(0.8 * n_heights)

    transformed_igrm[f_start:f_end, :] = 0
    transformed_igrm[:, h_start:h_end] = 0

    # Perform inverse FFT and return the magnitude
    filtered_igrm = np.fft.ifft2(transformed_igrm)
    return np.abs(filtered_igrm)

def weighted_average(input_array, threshold):
    """
    Calculates the weighted average of the indices of an array.
    The weights are derived from the array values, and only values above
    the threshold are considered. This replicates the `w_avg` function in IDL.

    Args:
        input_array (np.ndarray): 1D array of signal strengths.
        threshold (float): The minimum signal strength to consider.

    Returns:
        float: The weighted average of the indices, or 0 if no data is above threshold.
    """
    if input_array.size == 0:
        return 0
        
    indices = np.arange(len(input_array))
    weights = np.abs(input_array)

    valid_mask = weights > threshold
    if not np.any(valid_mask):
        return 0

    weights = weights[valid_mask]
    indices = indices[valid_mask]

    # The IDL code converts from a dB-like scale to a power scale and cubes it
    # to give more weight to peaks.
    power_weights = (10.0**(weights / 70.0))**3

    sum_w = np.sum(power_weights)
    sum_wh = np.sum(indices * power_weights)

    return sum_wh / sum_w if sum_w > 0 else 0

def autoscale_ionogram(freqs, heights, signals, freq_list, height_list, threshold=30):
    """
    Performs automatic scaling of an ionogram from scatter data to extract the F-layer trace.

    Args:
        freqs (np.ndarray): 1D array of frequency values for each data point (x-coords).
        heights (np.ndarray): 1D array of height values for each data point (y-coords).
        signals (np.ndarray): 1D array of signal strengths for each (x,y) point.
        freq_list (np.ndarray): 1D array of frequency bin values for the grid's x-axis.
        height_list (np.ndarray): 1D array of height bin values for the grid's y-axis.
        threshold (float): Signal strength threshold for the weighted_average function.

    Returns:
        tuple: A tuple containing:
            - np.ndarray: Interpolated frequency points of the trace.
            - np.ndarray: Interpolated height points of the trace.
        Returns (None, None) if scaling is not possible.
    """
    # 1. Construct the 2D Ionogram Grid from scatter data
    n_freq_bins = len(freq_list)
    n_height_bins = len(height_list)
    igrmarr = np.zeros((n_freq_bins, n_height_bins))
    freqs_mhz = freqs / 1e6
    freqs_rounded = np.round(freqs_mhz, 1)

    unique_freqs, inverse_indices = np.unique(freqs_rounded,
                                            return_inverse=True)
    avg_heights = np.zeros_like(unique_freqs)
    for i in range(len(unique_freqs)):
        avg_heights[i] = heights[inverse_indices == i].mean()

    # Find the bin index for each data point
    freq_indices = np.searchsorted(freq_list, freqs, side='right') - 1
    height_indices = np.searchsorted(height_list, heights, side='right') - 1

    # Populate the grid, keeping the max signal in each bin
    for i in range(len(signals)):
        f_idx, h_idx = freq_indices[i], height_indices[i]
        if 0 <= f_idx < n_freq_bins and 0 <= h_idx < n_height_bins:
            igrmarr[f_idx, h_idx] = max(igrmarr[f_idx, h_idx], signals[i])

    # 2. FFT Filtering
    filtered_igrm = fft_filter(igrmarr)

    # 3. Find the peak of the ionogram to start tracing
    if np.max(filtered_igrm) < threshold:
        print("No data above threshold for autoscaling.")
        return None, None,  unique_freqs, avg_heights

    max_idx_flat = np.argmax(filtered_igrm)
    start_freq_idx, _ = np.unravel_index(max_idx_flat, filtered_igrm.shape)

    # 4. Trace the curve using weighted averages
    ymindex = round(weighted_average(filtered_igrm[start_freq_idx, :], threshold))
    if ymindex == 0:
        print("Can't start autoscale, no data above threshold at peak frequency.")
        return None, None,  unique_freqs, avg_heights

    xwmeanarr, ywmeanarr = [start_freq_idx], [ymindex]

    # --- Trace upwards in frequency ---
    xindex, ylow, deltay = start_freq_idx, ymindex, 0
    while deltay < 2:
        xindex += 1
        if xindex >= n_freq_bins: break
        
        h_win_start = max(0, ylow - 10)
        h_win_end = min(n_height_bins, ylow + 11)
        search_window = filtered_igrm[xindex, h_win_start:h_win_end]
        ymindex_win = round(weighted_average(search_window, threshold))

        if ymindex_win > 0:
            deltay = ymindex_win - (ylow - h_win_start)
            ylow = h_win_start + ymindex_win
            xwmeanarr.append(xindex)
            ywmeanarr.append(ylow)
        else: break

    # --- Trace downwards in frequency ---
    xindex, ylow = start_freq_idx - 1, ywmeanarr[0]
    while xindex > 0:
        h_win_start = max(0, ylow - 15)
        h_win_end = min(n_height_bins, ylow + 16)
        search_window = filtered_igrm[xindex, h_win_start:h_win_end]
        ymindex_win = round(weighted_average(search_window, threshold))
        
        if ymindex_win > 0:
            ylow = h_win_start + ymindex_win
            xwmeanarr.insert(0, xindex)
            ywmeanarr.insert(0, ylow)
        else: break
        xindex -= 1

    if len(xwmeanarr) < 5:
        print("Not enough points found for a reliable trace.")
        return None, None,  unique_freqs, avg_heights

    # 5. Smooth the traced curve
    xwmeanarr, ywmeanarr = np.array(xwmeanarr), np.array(ywmeanarr)
    size = 11 if len(xwmeanarr) > 11 else len(xwmeanarr)
    if size > 0:
        xsmoothed = uniform_filter1d(xwmeanarr.astype(float), size=size, mode='reflect')
        ysmoothed = uniform_filter1d(ywmeanarr.astype(float), size=size, mode='reflect')
    else:
        return None, None,  unique_freqs, avg_heights

    # 6. Interpolate onto a regular frequency grid
    xfreqsmooth = freq_list[xsmoothed.astype(int)]
    unique_freqs, unique_indices = np.unique(xfreqsmooth, return_index=True)
    
    if len(unique_freqs) < 2:
        print("Not enough unique frequency points to interpolate.")
        return None, None,  unique_freqs, avg_heights

    unique_heights_indices = ysmoothed[unique_indices]
    interp_height_values = height_list[unique_heights_indices.astype(int)]
    
    minf, maxf = unique_freqs.min(), unique_freqs.max()
    finc = 0.2 if (maxf - minf) > 8 else 0.1
    fsarr10 = np.arange(minf, maxf, finc)
    
    interp_func = interp1d(unique_freqs, interp_height_values, kind='linear', bounds_error=False, fill_value='extrapolate')
    final_heights = interp_func(fsarr10)

    return fsarr10, final_heights, unique_freqs, avg_heights