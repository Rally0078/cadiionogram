import numpy as np
from scipy.stats import describe, mode

def calculate_pixbins(freqs, heights):
    pixel_counts = []
    medians = []
    freqs_flayer = []
    freq_bins = np.unique(freqs)
    prev_median = 0
    for idx, freq in enumerate(freq_bins):
        freq_idx = np.argwhere(freqs == freq)
        height_flayer_idx = np.argwhere(heights >= 160)
        filter_indices = np.intersect1d(freq_idx.flatten(), height_flayer_idx.flatten())
        heights_flayer_filtered = heights[filter_indices]
        if len(filter_indices) > 0:
            pixel_counts.append((idx, freq, filter_indices, heights_flayer_filtered))
            median = np.median(heights_flayer_filtered)
            if median > 1.5 * np.min(heights_flayer_filtered) and median > 1.25 * prev_median:
                median = prev_median + 10
            medians.append(median)
            freqs_flayer.append(freq)
            prev_median = median
    return pixel_counts, medians, freqs_flayer

def freq_filter(freqs, heights):
    pixel_counts, medians, freqs_flayer = calculate_pixbins(freqs, heights)
    vertical_line_noise = []
    reflection_noise = []
    freq_bins_nonempty = []
    height_bin_size = []
    freq_bins = []
    height_bins = []
    indices_noise = []

    for freq_bin in pixel_counts:
        idx, freq, indices, hgts = freq_bin
        freq_bins.append(freq)
        height_bins.append(len(hgts))
        indices_noise.append(indices)
        max_min = np.max(hgts) - np.min(hgts)
        mean = np.mean(hgts)
        median = np.median(hgts)
        if len(hgts) == 1:
            stdev = 0
            mode_hgts = hgts[0]
            height_bin_size.append(np.sum(hgts))
            freq_bins_nonempty.append(freq)
            skewness = 0
        else:
            description = describe(hgts)
            mode_hgts = mode(hgts)[0]
            stdev = np.sqrt(describe(hgts).variance)
            #Vertical line noise
            if max_min > 2 * mode_hgts:
                vertical_line_noise.append((freq, indices, hgts))
            #Reflection signals
            elif np.any(hgts > 1.8 * np.min(hgts)):
                indices_reflection = indices[hgts > 1.8 * np.min(hgts)]
                reflection_noise.append((freq, indices_reflection, hgts))
            else:
                height_bin_size.append(np.sum(hgts))
                freq_bins_nonempty.append(freq)
            skewness = description.skewness

    noise_idx = np.array([], dtype=np.int64)
    for noise in vertical_line_noise:
        noise_idx = np.union1d(noise_idx, noise[1])
    for noise in reflection_noise:
        noise_idx = np.union1d(noise_idx, noise[1])
    noise_idx = noise_idx.astype(int)
    freqs_filtered = np.delete(freqs, noise_idx)
    heights_filtered = np.delete(heights, noise_idx)
    _, new_medians, new_freqs_flayer = calculate_pixbins(freqs_filtered, heights_filtered)
    return noise_idx, new_freqs_flayer, new_medians