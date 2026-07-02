import numpy as np
from scipy.stats import describe, mode
from scipy import ndimage
from scipy.fft import fft2, ifft2
from scipy.signal import savgol_filter,argrelextrema
from skimage import measure, filters
from scipy.interpolate import CubicSpline
from typing import Literal

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

def o_x_separation(freq_selection, height_selection, dop_selection, sensors_selection, mode: Literal['O','X']='O', phchoice: Literal['14','23']='14', site: str = 'TIR'):
    """
        Separate O and X mode based on phase14 of the CADI system. Note that old CADI TIR Data has the phase signs flipped for some reason.
    """
    if mode not in ['O', 'X']:
        raise ValueError("Only O and X modes are available")
    if phchoice not in ['14', '23']:
        raise ValueError("Only phase difference 1-4 and 2-3 are available")
        #Site Info, loaded from siteinfo.py
    from src.utils.siteinfo import site_dict
    site_info = site_dict.get(site)

    if site_info is not None:
        PH2_corr = site_info.ph_corr[0] * np.pi / 180
        PH4_corr = site_info.ph_corr[1] * np.pi / 180
        site_sep_ew = site_info.site_separation[0]
        site_sep_ns = site_info.site_separation[1]
        polarity = site_info.polarity
    else:
        PH2_corr = np.pi + 45 * np.pi / 180
        PH4_corr = np.pi - 20 * np.pi / 180
        site_sep_ew = 30.1
        site_sep_ns = 30.1
        polarity = [1,-1,1,-1]
    sensor1_phase = np.angle(sensors_selection[:, 0] * polarity[0] + 1j * sensors_selection[:, 1] * polarity[0])
    sensor2_phase = np.angle(sensors_selection[:, 2] * polarity[1] + 1j * sensors_selection[:, 3] * polarity[1])
    sensor3_phase = np.angle(sensors_selection[:, 4] * polarity[2] + 1j * sensors_selection[:, 5] * polarity[2])
    sensor4_phase = np.angle(sensors_selection[:, 6] * polarity[3] + 1j * sensors_selection[:, 7] * polarity[3])
    sensor1_phase = sensor1_phase + PH2_corr
    sensor3_phase = sensor3_phase + PH4_corr
    if phchoice == '12':
        phdiff = sensor1_phase - sensor4_phase
        phdiff[phdiff < np.pi] += 2*np.pi
        phdiff[phdiff > np.pi] -= 2*np.pi
    else:
        phdiff = sensor2_phase - sensor3_phase
        phdiff[phdiff < np.pi] += 2*np.pi
        phdiff[phdiff > np.pi] -= 2*np.pi       
    if mode == 'O':
        return freq_selection[phdiff > 0], height_selection[phdiff > 0], dop_selection[phdiff > 0], sensors_selection[phdiff > 0]
    else:
        return freq_selection[phdiff < 0], height_selection[phdiff < 0], dop_selection[phdiff < 0], sensors_selection[phdiff < 0]

def bin_edges(x):
    x = np.sort(np.unique(x))
    dx = np.diff(x)
    edges = np.concatenate([[x[0] - dx[0]/2], x[:-1], [x[-1] + dx[-1]/2]])
    return edges

def autoscale(freqs, heights, freq_list, height_list, n_dilations=2, n_erosions=2, interp_points=125):
    f_edges, h_edges = bin_edges(freq_list), bin_edges(height_list)
    freqs_omode, height_omode = freqs[heights >= 150], heights[heights >= 150]
    hist, f_edgesout, h_edgesout = np.histogram2d(freqs_omode, height_omode, bins=[f_edges, h_edges])
    image = hist.T
    image_binary = np.copy(image)

    dilated_image_binary = np.copy(image_binary)
    for n in range(n_dilations):
        dilated_image_binary = ndimage.binary_dilation(dilated_image_binary)
    labeled_binary_img = measure.label(dilated_image_binary, background=0, connectivity=2)
    labels, counts = np.unique_counts(labeled_binary_img)
    labels = labels[1:]
    counts = counts[1:]
    filtered_binary_image = np.copy(labeled_binary_img)
    filtered_binary_image[filtered_binary_image != (np.argmax(counts) + 1)] = 0
    filtered_binary_image[filtered_binary_image == (np.argmax(counts) + 1)] = 1
    for n in range(n_erosions):
        filtered_binary_image = ndimage.binary_erosion(filtered_binary_image)
    freq_output = np.array(freq_list)[sorted(np.where(filtered_binary_image == True)[1])]
    height_output = height_list[np.where(filtered_binary_image == True)[0]]
    unique_freqs, idxs = np.unique(freq_output, return_index=True)
    unique_height = height_output[idxs]
    interp_input = np.linspace(unique_freqs.min(), unique_freqs.max(), interp_points)
    height_interp = np.interp(interp_input, unique_freqs, unique_height)
    #height_output_unique = np.interp(interp_input, freq_output, height_output)
    spline = CubicSpline(unique_freqs, unique_height)
    spline_y = spline(interp_input)
    spline_x = interp_input
    #f_smooth = savgol_filter(freq_output, window_length=3, polyorder=2)
    #h_smooth = savgol_filter(height_output, window_length=3, polyorder=2)

    dndh = np.gradient(spline_y, spline_x)
    #dndh = dndh/dndh.max() * 1023
    #max_indices = argrelextrema(dndh, np.greater)[0]
    #min_indices = argrelextrema(dndh, np.less)[0]
    #d2ndh2 = np.gradient(dndh)
    output = {
        'freq_output': freq_output,
        'height_output': height_output,
        'unique_freqs': unique_freqs,
        'unique_heights': unique_height,
        'spline_x': spline_x,
        'spline_y': spline_y,
        'grad': dndh,
    }
    return output
