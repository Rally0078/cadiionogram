import numpy as np
from scipy.stats import describe
from scipy.ndimage import uniform_filter1d, label

def get_frequency_height_bins(freqs, heights_in):
    freqs_unique = np.unique(freqs)
    pixel_counts = []
    medians = []
    freqs_flayer = []
    for idx, freq in enumerate(freqs_unique):
        freq_idx = np.argwhere(freqs == freq)
        height_flayer_idx = np.argwhere(heights_in >= 160)
        filter_indices = np.intersect1d(freq_idx.flatten(), height_flayer_idx.flatten())
        heights_flayer_filtered = heights_in[filter_indices]
        if len(filter_indices) > 0:
            pixel_counts.append((idx, freq, filter_indices, heights_flayer_filtered))
            medians.append(np.median(heights_flayer_filtered))
            freqs_flayer.append(freq)
    return pixel_counts, medians

def clean_vertical_line(freqs, heights_in, sig):
    pass

def clean_ionogram(freqs, heights_in, signal_single_receiver):
    freqs_unique = np.unique(freqs)
    pixel_counts = []
    medians = []
    freqs_flayer = []
    for idx, freq in enumerate(freqs_unique):
        freq_idx = np.argwhere(freqs == freq)
        height_flayer_idx = np.argwhere(heights_in >= 160)
        filter_indices = np.intersect1d(freq_idx.flatten(), height_flayer_idx.flatten())
        heights_flayer_filtered = heights_in[filter_indices]
        if len(filter_indices) > 0:
            pixel_counts.append((idx, freq, filter_indices, heights_flayer_filtered))
            medians.append(np.median(heights_flayer_filtered))
            freqs_flayer.append(freq)
    if len(freqs_flayer) <= 1:
        return np.array([]), np.array([]), np.array([])
    sig_copy = np.copy(signal_single_receiver)
    #Tuple containing (freq_unique idx, type of noise)
    #Type of noise: 0 - vertical line noise, 1 - reflection noise, 2 - individial pixel noise, 3 - no noise
    noise_type = ['vertical line', 'reflection', 'individial pixel', 'no noise']
    noise_bin_idx_type = [(0,0) for idx in range(len(medians))]

    for f_layer_freq_idx, (pixel_count, median) in enumerate(zip(pixel_counts, medians)):
        idx, freq, filter_indices, heights = pixel_count
        if len(heights) > 1:
            stdev = np.sqrt(describe(heights).variance)
        else:
            stdev = 0.0
        max_min_diff = np.max(heights) - np.min(heights)
        multi_point_noise = True
        #Vertical line noise
        height_comparison = min(median, np.min(heights))
        if (stdev > 0.1 * height_comparison) and max_min_diff > 1.2 * height_comparison:
            noise_type_freq = noise_type[0]
            noise_bin_idx_type[f_layer_freq_idx] = (idx, noise_type_freq)
            if (f_layer_freq_idx > 0) and (f_layer_freq_idx < len(medians) - 1):
                if (medians[f_layer_freq_idx] > medians[f_layer_freq_idx + 1]) and (medians[f_layer_freq_idx] > medians[f_layer_freq_idx - 1]):
                    possible_median = np.min(heights)
                    medians[f_layer_freq_idx] = min(possible_median, np.average(medians[f_layer_freq_idx-1:f_layer_freq_idx+2]))
                    median = medians[f_layer_freq_idx]
                    noise_idx = filter_indices[(np.abs(heights - median) > 30) | (heights - np.min(heights) > 100)]
                    sig_copy[noise_idx] = 0
                else:
                    sig_copy[filter_indices] = 0
                    
        #Reflection noise
        elif(np.max(heights) > 1.3 * height_comparison) or (median > 1.2 * np.min(heights)):
            noise_type_freq = noise_type[1]
            noise_bin_idx_type[f_layer_freq_idx] = (idx, noise_type_freq)
            if (f_layer_freq_idx > 0) and (f_layer_freq_idx < len(medians) - 1):
                if (medians[f_layer_freq_idx] > medians[f_layer_freq_idx + 1]) and (medians[f_layer_freq_idx] > medians[f_layer_freq_idx - 1]):
                    possible_median = np.min(heights)
                    medians[f_layer_freq_idx] = min(possible_median, np.average(medians[f_layer_freq_idx-1:f_layer_freq_idx+2]))
                    median = medians[f_layer_freq_idx]
                    noise_idx = filter_indices[(np.abs(heights - median) > 30) | (heights - np.min(heights) > 100)]
                    sig_copy[noise_idx] = 0
            else:
                noise_idx = filter_indices[(heights > 1.2 * median) | (heights < 0.9 * median) | (np.abs(heights - median) > 100)]
                sig_copy[noise_idx] = 0
        else:
            multi_point_noise = False
            if len(heights) == 1:
                if (f_layer_freq_idx > 0) and (f_layer_freq_idx < len(medians) - 1):
                    if (np.abs(medians[f_layer_freq_idx] - medians[f_layer_freq_idx + 1]) > 100) or (np.abs(medians[f_layer_freq_idx] - medians[f_layer_freq_idx - 1]) > 100):
                        noise_type_freq = noise_type[2]
                        noise_bin_idx_type[f_layer_freq_idx] = (idx, noise_type_freq)
                        sig_copy[f_layer_freq_idx] = 0
            else:
                noise_type_freq = noise_type[3]
                noise_bin_idx_type[f_layer_freq_idx] = (idx, noise_type_freq)
    nonzero_mask = np.abs(sig_copy) > 0
    if len(nonzero_mask) != len(freqs):
        return np.array([]), np.array([]), np.array([])
    y = medians.copy()
    freqs_flayer = np.array(freqs_flayer)
    medians = np.array(medians)

    # Compute local variation
    dy = np.abs(np.diff(y))  # len(dy) = len(y) - 1

    # Smooth the variation
    smoothed_dy = uniform_filter1d(dy, size=8)

    # Threshold to detect low-noise regions
    threshold = np.percentile(smoothed_dy, 60)
    low_noise = smoothed_dy < threshold  # len = len(y) - 1

    # Find largest contiguous region of low-noise
    labels, num = label(low_noise)
    lengths = np.bincount(labels[labels > 0])
    best_label = np.argmax(lengths) + 1
    signal_mask_diff = labels == best_label  # len = len(y) - 1

    signal_mask = np.concatenate(([False], signal_mask_diff))  # len = len(y)

    # Apply mask
    x_signal = freqs_flayer[signal_mask]
    y_signal = medians[signal_mask]

    return freqs[nonzero_mask], heights_in[nonzero_mask], sig_copy[nonzero_mask], freqs_flayer, medians