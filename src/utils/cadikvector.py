"""
    Based on the CADI IDL Program to compute k-vector-related quantities.

    The following functions are available:

    Methods
    -------
        `compute_xpha_only` : Computes cross power and phase of receivers using raw data.
        `compute_xpha_full` : Computes Crossphases and also returns the filtered new data with IDL logic.
        `compute_kvector` : Computes k vector using raw data.
        `compute_vel` : Computes drift velocity using raw data.
        `compute_xy` : Computes X and Y position of drifts using raw data.
"""
import numpy as np
from typing import Tuple

def compute_xpha_only(freq_selection, freq_list, height_selection, dop_selection, signal_selection) -> Tuple[np.ndarray, np.ndarray]:
    _, _, _, _, _, xpow, xpha = compute_xpha_full(freq_selection, freq_list, height_selection, 
                 dop_selection, signal_selection)
    return xpow, xpha

def compute_xpha_full(freq_selection, freq_list, height_selection, 
                 dop_selection, signal_selection):
    indices_to_remove = np.array([], dtype=np.int64)
    for idx in range(0, 8, 2):
        rcv_re = signal_selection[:, idx]
        rcv_im = signal_selection[:, idx+1]
        indices_to_remove = np.union1d(indices_to_remove, np.where((rcv_re == 0) & (rcv_im == 0))[0])

    new_signal_selection = np.delete(signal_selection, indices_to_remove,axis=0)
    new_freq = np.delete(freq_selection, indices_to_remove)
    new_height = np.delete(height_selection, indices_to_remove)
    new_dops = np.delete(dop_selection, indices_to_remove)
    #Get cross amplitudes and phases
    xpow = np.empty(shape=(new_signal_selection.shape[0], 2))
    xpha = np.empty(shape=(new_signal_selection.shape[0], 2))
    PH2_corr=0#np.pi+0*np.pi/180, site dependent
    PH4_corr=0#np.pi-0*np.pi/180, site dependent
    for i in range(0, 3, 2):
        ant0_re = new_signal_selection[:, 2*i]
        ant0_im = new_signal_selection[:, 2*i+1]
        ant1_re = new_signal_selection[:, 2*i+2]
        ant1_im = new_signal_selection[:, 2*i+3]

        s = (ant0_re + 1j * ant0_im) * np.conjugate(ant1_re + 1j * ant1_im)
        s = -s  #Site dependent, use polarity to determine according to the IDL code
        xpow[:, i//2] = np.abs(s)**2
        xpha[:, i//2] = np.angle(s)
    xpha[:, 1][xpha[:, 1] > np.pi] -= 2*np.pi
    xpha[:, 1][xpha[:, 1] < -np.pi] += 2*np.pi

    #Reject data with cross phases outside limits
    k_mag = 2*np.pi/(2.998e8) * np.array(freq_list)
    kd = np.empty(shape=(np.array(freq_list).shape[0], 2))
    kd[:,0] = k_mag * 30.1
    kd[:,1] = k_mag * 30.1
    phase_limit = kd
        
    freq_idxs = np.digitize(new_freq, freq_list) - 1
    assert (new_freq == freq_list[freq_idxs]).all()
    good_idxs = np.where((np.abs(xpha[:,0]) <= phase_limit[freq_idxs, 0]) & ((np.abs(xpha[:,1]) <= phase_limit[freq_idxs, 1])))[0]
    return good_idxs, new_freq, new_height, new_dops, new_signal_selection, xpow, xpha

def compute_kvector(freqs, freq_list, heights, dops, signals, sort_by_freq=False, points_thres=5):
    """
        Computes k vector, given the raw data for one time observation.

        Parameters
        ----------
        freqs : `np.ndarray`
            Frequencies in the timestamp.
        freq_list : `List | np.ndarray`
            Frequency bins from the raw data.
        heights : `np.ndarray`
            Heights in the timestamp.
        dops : `np.ndarray`
            Doppler shifts in the timestamp.
        signals : `np.ndarray`
            Signals in the timestamp with the shape (n_samples, 2 * n_receivers).
        sort_by_freq : `bool`, optional
            Sort data by frequency.
        points_thres : `int`, optional
            Minimum number of samples to consider for the computation of k vector. Works only when sort_by_freq is true.
        
        Returns
        -------
        df : `pd.DataFrame`
            A DataFrame consisting of `kx`, `ky`, `kz` values, and the corresponding frequency.
    """

    partitions = []
    n_freqs = []
    output_df = np.array([])
    k_xarr = np.array([])
    k_yarr = np.array([])
    k_zarr = np.array([])
    output_heights = np.array([])
    output_xpow = np.empty(shape=(0,2))
    output_signals = np.empty(shape=(0,signals.shape[1]))
    freq_selection, height_selection, dop_selection, signal_selection = freqs, heights, dops, signals
    good_idxs, new_freq, new_height, new_dops, new_signal_selection, xpow, xpha = compute_xpha_full(freq_selection, freq_list, 
                                                                                              height_selection, dop_selection, signal_selection)
    k_mag = 2*np.pi/(2.998e8) * np.array(freq_list)
    output_idxs = np.array([], dtype=np.int64) 
    if sort_by_freq:
        for idx, freq in enumerate(freq_list):
            n_points_per_freq = len(np.argwhere(new_freq[good_idxs] == freq))
            if n_points_per_freq >= points_thres:
                good_phases = xpha[good_idxs, :]
                good_powers = xpow[good_idxs, :]

                y_df = new_dops[good_idxs]
                hgts = new_height[good_idxs]
                new_signals = new_signal_selection[good_idxs, :]
                single_freq_idx = new_freq[good_idxs] == freq
                good_phases = good_phases[single_freq_idx, :]
                good_powers = good_powers[single_freq_idx, :]
                new_freq_idxs = single_freq_idx
                
                y_df = y_df[new_freq_idxs]
                new_kd = np.empty(shape=(np.array(freq_list).shape[0], 2))
                new_kd[:, 0] = k_mag * 30.1 #Site-specific
                new_kd[:, 1] = k_mag * 30.1 #Site-specific
                temp_xy = good_phases/new_kd[idx]
                new_xy = temp_xy/np.sqrt(1.0 - temp_xy**2)
                kz = - k_mag[idx] / np.sqrt(1+ np.sum(new_xy*new_xy,axis=1))
                kx = kz * new_xy[:, 0]
                ky = kz * new_xy[:, 1]
                n_freqs.append(freq)
                partitions.append(len(kx))
                k_xarr = np.append(k_xarr, kx)
                k_yarr = np.append(k_yarr, ky)
                k_zarr = np.append(k_zarr, ky)
                output_df = np.append(output_df, y_df)
                output_idxs = np.append(output_idxs, np.argwhere(new_freq[good_idxs] == freq).flatten())
                output_heights = np.append(output_heights, hgts[new_freq_idxs])
                output_signals = np.vstack([output_signals, new_signals[new_freq_idxs, :]])
                output_xpow = np.vstack([output_xpow, good_powers])
                """kx[kz < 0] *= -1
                ky[kz < 0] *= -1
                kz[kz < 0] *= -1"""
        output_freqs = np.repeat(n_freqs, partitions)
        karray = np.vstack([k_xarr, k_yarr, k_zarr]).T
    else:
        new_freq_idxs = np.digitize(new_freq[good_idxs], freq_list) - 1
        output_freqs = new_freq[good_idxs]
        output_heights = new_height[good_idxs]
        output_df = new_dops[good_idxs]
        output_signals = new_signal_selection[good_idxs]
        output_xpow = xpow[good_idxs]
        new_kd = np.empty(shape=(np.array(freq_list).shape[0], 2))
        new_kd[:, 0] = k_mag * 30.1 #Site-specific
        new_kd[:, 1] = k_mag * 30.1 #Site-specific
        temp_xy = xpha[good_idxs]/new_kd[new_freq_idxs]
        new_xy = temp_xy/np.sqrt(1.0 - temp_xy**2)
        kz = - k_mag[new_freq_idxs] / np.sqrt(1+ np.sum(new_xy*new_xy,axis=1))
        kx = kz * new_xy[:, 0]
        ky = kz * new_xy[:, 1]
        karray = np.vstack([kx, ky, kz]).T
        
    return output_idxs, karray, output_freqs, output_heights, output_df, output_signals, output_xpow

def compute_vel(freqs, freq_list, heights, dops, signals, points_thres=5):
    freq_selection, height_selection, dop_selection, signal_selection = freqs, heights, dops, signals
    good_idxs, new_freq, new_height, new_dops, new_signal_selection, xpow, xpha = compute_xpha_full(freq_selection, freq_list, 
                                                                                               height_selection, dop_selection, signal_selection)
    v_xarr = np.array([])
    v_yarr = np.array([])
    v_zarr = np.array([])
    output_freqs = np.array([])
    output_idxs = np.array([])
    k_mag = 2*np.pi/(2.998e8) * np.array(freq_list)
    for idx, freq in enumerate(freq_list):
        n_points_per_freq = len(np.argwhere(new_freq[good_idxs] == freq))
        if n_points_per_freq >= points_thres:
            good_phases = xpha[good_idxs, :]
            y_df = new_dops[good_idxs]
            hgts = new_height[good_idxs]
            new_signals = new_signal_selection[good_idxs, :]
            single_freq_idx = new_freq[good_idxs] == freq
            good_phases = good_phases[single_freq_idx]
            new_freq_idxs = single_freq_idx
            
            y_df = y_df[new_freq_idxs]
            new_kd = np.empty(shape=(np.array(freq_list).shape[0], 2))
            new_kd[:, 0] = k_mag * 30.1 #Site-specific
            new_kd[:, 1] = k_mag * 30.1 #Site-specific
            temp_xy = good_phases/new_kd[idx]
            new_xy = temp_xy/np.sqrt(1.0 - temp_xy**2)
            kz = - k_mag[idx] / np.sqrt(1+ np.sum(new_xy*new_xy,axis=1))
            kx = kz * new_xy[:, 0]
            ky = kz * new_xy[:, 1]
            output_freqs = np.append(output_freqs, freq)
            karray = np.vstack([kx, ky, kz]).T
            v = np.linalg.pinv(karray/np.pi) @ y_df
            v_horizontal = np.sqrt(np.sum(np.square(v[:2])))
            azi = np.mod((180/np.pi * np.atan2(v[0], v[1])) + 22.33 , 360.0)    #22.33 is site azimuth information in degrees
            v_xarr = np.append(v_xarr, v[0])
            v_yarr = np.append(v_yarr, v[1])
            v_zarr = np.append(v_zarr, v[2])
            output_idxs = np.append(output_idxs, np.argwhere(new_freq[good_idxs] == freq).flatten())
    return output_idxs, output_freqs, v_xarr, v_yarr, v_zarr

def compute_xy(freqs, freq_list, heights, dops, signals):
    karray, output_freqs, output_heights, output_df, output_signals = compute_kvector(freqs, freq_list, heights, dops, signals, sort_by_freq=True)
    x = karray[:,0]/karray[:,2]
    y = karray[:,1]/karray[:,2]
    return x, y, output_freqs, output_heights, output_df, output_signals