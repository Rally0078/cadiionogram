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
from copy import deepcopy
from src.utils.pandasutils import PandasUtils
import pandas as pd

def compute_xpha_only(df, freq_list, site='TIR') -> Tuple[pd.DataFrame, pd.DataFrame]:
    _, _, _, _, _, xpow, xpha = compute_xpha_full(df, freq_list, site=site)
    return xpow, xpha

def compute_xpha_full(df: pd.DataFrame, freq_list, site='TIR'):
    signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
    sig_re_name = [f"sensor{i + 1} real" for i in range(4)]
    sig_im_name = [f"sensor{i + 1} imag" for i in range(4)]
    signal_selection = df[signal_col_names]
    mask_to_drop = pd.Series(False, index=df.index)

    for idx in range(4):
        is_zero = (df[f"sensor{idx + 1} real"] == 0) & (df[f"sensor{idx + 1} imag"] == 0)
        mask_to_drop = mask_to_drop | is_zero
    good_idxs = ~mask_to_drop
    df = df.loc[good_idxs]
    new_signal_selection = df[signal_col_names]
    new_freq = df['freq (Hz)']

    #Get cross amplitudes and phases
    xpow = pd.DataFrame({"x1": np.empty(shape=(new_signal_selection.shape[0],)),
                        "x2": np.empty(shape=(new_signal_selection.shape[0],))},
                        index=df.index)
    xpha = pd.DataFrame({"x1": np.empty(shape=(new_signal_selection.shape[0],)),
                        "x2": np.empty(shape=(new_signal_selection.shape[0],))},
                        index=df.index)
    
    from src.utils.siteinfo import SiteInfo
    site_info = SiteInfo.get_from_file(site)
    if site_info is not None:
        PH2_corr = site_info.ph_corr[0] * np.pi / 180
        PH4_corr = site_info.ph_corr[1] * np.pi / 180
        site_sep_ew = site_info.site_separation[0]
        site_sep_ns = site_info.site_separation[1]
    else:
        PH2_corr = 8.8906 * np.pi / 180
        PH4_corr = -29.5086 * np.pi / 180
        site_sep_ew = 30.1
        site_sep_ns = 30.1

    ph_corrections = [PH2_corr, PH4_corr]
    pairwise_antenna13 = [('sensor1 real', 'sensor1 imag'), ('sensor3 real', 'sensor3 imag')]
    pairwise_antenna24 = [('sensor2 real', 'sensor2 imag'), ('sensor4 real', 'sensor4 imag')]
    cross_names = ['x1', 'x2']
    for pair1, pair2, cross_name, ph_corr in zip(pairwise_antenna13, pairwise_antenna24, cross_names, ph_corrections):
        ant0_re = new_signal_selection[pair1[0]].to_numpy().astype(np.int32)
        ant0_im = new_signal_selection[pair1[1]].to_numpy().astype(np.int32)
        ant1_re = new_signal_selection[pair2[0]].to_numpy().astype(np.int32)
        ant1_im = new_signal_selection[pair2[1]].to_numpy().astype(np.int32)
        s = (ant0_re + 1j * ant0_im) * np.conjugate((ant1_re + 1j * ant1_im))
        s = -s  #Site dependent, use polarity to determine according to the IDL code
        xpow[cross_name] = np.abs(s)**2
        xpha[cross_name] = np.angle(s) + ph_corr
        xpha.loc[xpha[cross_name] > np.pi, cross_name] -= 2*np.pi
        xpha.loc[xpha[cross_name] < -np.pi, cross_name] += 2*np.pi

    #Reject data with cross phases outside limits
    k_mag = 2*np.pi/(2.998e8) * np.array(freq_list)
    kd = np.empty(shape=(np.array(freq_list).shape[0], 2))
    kd[:,0] = k_mag * site_sep_ew
    kd[:,1] = k_mag * site_sep_ns
    phase_limit = kd
        
    freq_idxs = np.digitize(new_freq, freq_list) - 1
    final_good_mask = (xpha['x1'].abs() <= phase_limit[freq_idxs, 0]) & (xpha['x2'].abs() <= phase_limit[freq_idxs, 1])
    output_df = df.loc[final_good_mask]
    output_xpow = xpow.loc[final_good_mask]
    output_xpha = xpha.loc[final_good_mask]
    return output_df, output_xpow, output_xpha

def compute_kvector(df, freq_list, sort_by_freq=False, points_thres=5, site='TIR'):
    """
        Computes k vector, given the raw data for one time observation.

        Parameters
        ----------
        freq_list : `List | np.ndarray`
            Frequency bins from the raw data.
        sort_by_freq : `bool`, optional
            Sort data by frequency.
        points_thres : `int`, optional
            Minimum number of samples to consider for the computation of k vector. Works only when sort_by_freq is true.
        
        Returns
        -------
        k_out_with_ts : `pd.DataFrame`
            A DataFrame consisting of `kx`, `ky`, `kz` values, and the corresponding frequency.
        output_freqs : `pd.Series`
            A Series consisting of the frequencies corresponding to each k vector row in the dataframe.
        output_heights : `pd.Series`
            A Series consisting of the heights corresponding to each k vector row in the dataframe.
        output_dops : `pd.Series`
            A Series consisting of the doppler shifts corresponding to each k vector row in the dataframe.
        output_signals : `pd.DataFrame`
            A DataFrame consisting of the signals corresponding to each k vector row in the dataframe.
        output_xpow : `pd.DataFrame`
            A DataFrame consisting of the cross-powers of pairwise sensors corresponding to each k vector row in the dataframe.
    """
    if len(np.unique(df.index)) > 1:
        raise ValueError("Only a single timestamp can be used for the calculation of k vector")
    k_out_with_ts = pd.DataFrame(columns=['kx', 'ky', 'kz'])
    timeindex_series = pd.Series([])
    df, xpow, xpha = compute_xpha_full(df, freq_list, site=site)
    signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
    k_xarr = np.array([])
    k_yarr = np.array([])
    k_zarr = np.array([])
    output_heights = pd.Series([])
    output_xpow = pd.DataFrame(columns=['x1', 'x2'])

    new_signal_selection = df[signal_col_names]
    new_freq = df['freq (Hz)']
    new_height = df['height (km)']
    new_dops = df['dopplershift']
    output_freqs = pd.Series([])
    output_dops = pd.Series([])

    from src.utils.siteinfo import SiteInfo
    site_info = SiteInfo.get_from_file(site)
    if site_info is not None:
        site_sep_ew = site_info.site_separation[0]
        site_sep_ns = site_info.site_separation[1]
    else:
        site_sep_ew = 30.1
        site_sep_ns = 30.1

    k_mag = 2*np.pi/(2.998e8) * np.array(freq_list)
    if sort_by_freq:
        output_signals = pd.DataFrame()
        for idx, freq in enumerate(freq_list):
            df_single_freq = df[df['freq (Hz)'] == freq]
            n_points_per_freq = len(df_single_freq)
            if n_points_per_freq >= points_thres:
                y_df = df_single_freq['dopplershift']
                hgts = df_single_freq['height (km)']
                new_signals = df_single_freq[signal_col_names]
                single_freq_idx = df['freq (Hz)'] == freq
                good_phases = xpha.loc[single_freq_idx]
                good_powers = xpow.loc[single_freq_idx]
                
                new_kd = np.empty(shape=(np.array(freq_list).shape[0], 2))
                new_kd[:, 0] = k_mag * site_sep_ew
                new_kd[:, 1] = k_mag * site_sep_ns
                temp_xy = good_phases/new_kd[idx]
                new_xy = temp_xy/np.sqrt(1.0 - temp_xy**2)
                kz = - k_mag[idx] / np.sqrt(1+ np.sum(new_xy*new_xy,axis=1))
                kx = kz * new_xy['x1']
                ky = kz * new_xy['x2']

                output_heights = pd.concat([output_heights if not output_heights.empty else None, hgts])
                output_freqs = pd.concat([output_freqs if not output_freqs.empty else None, pd.Series(np.repeat(freq, len(kx)), index=hgts.index, name='freq')])
                output_xpow = pd.concat([output_xpow if not output_xpow.empty else None, good_powers])
                output_dops = pd.concat([output_dops if not output_dops.empty else None, y_df])
                output_signals = pd.concat([output_signals if not output_signals.empty else None, new_signals])
                
                k_xarr = np.append(k_xarr, kx)
                k_yarr = np.append(k_yarr, ky)
                k_zarr = np.append(k_zarr, kz)
                timeindex_series = pd.concat([timeindex_series if not timeindex_series.empty else None, hgts.index.to_series()])
        karray = np.vstack([k_xarr, k_yarr, k_zarr]).T
    else:
        new_freq = df['freq (Hz)']
        new_freq_idxs = np.digitize(new_freq, freq_list) - 1
        new_height = df['height (km)']
        new_dops = df['dopplershift']
        output_freqs = new_freq
        output_heights = new_height
        output_dops = new_dops
        output_signals = new_signal_selection
        good_phases = xpha
        good_powers = xpow
        output_xpow = pd.concat([output_xpow if not output_xpow.empty else None, good_powers])
        timeindex_series = new_height.index
        new_kd = np.empty(shape=(np.array(freq_list).shape[0], 2))
        new_kd[:, 0] = k_mag * site_sep_ew
        new_kd[:, 1] = k_mag * site_sep_ns
        temp_xy = good_phases/new_kd[new_freq_idxs]
        new_xy = temp_xy/np.sqrt(1.0 - temp_xy**2)
        kz = - k_mag[new_freq_idxs] / np.sqrt(1+ np.sum(new_xy*new_xy,axis=1))
        kx = kz * new_xy['x1']
        ky = kz * new_xy['x2']
        karray = np.vstack([kx, ky, kz]).T

    k_out_with_ts = pd.DataFrame({'kx': karray[:,0], 'ky': karray[:,1], 'kz': karray[:,2]}, index=timeindex_series)
    return k_out_with_ts, output_freqs, output_heights, output_dops, output_signals, output_xpow

def compute_vel(df, freq_list, points_thres=5, site='TIR'):
    k_out_with_ts, output_freqs, _, output_dops, _, _ = compute_kvector(df, freq_list, sort_by_freq=True, points_thres=points_thres, site=site)
    v_xarr = np.array([])
    v_yarr = np.array([])
    v_zarr = np.array([])
    df_output = pd.DataFrame(columns=['freq (Hz)', 'vx', 'vy', 'vz'])
    for idx, freq in enumerate(freq_list):
        freq_idxs = output_freqs == freq
        y_df = output_dops.loc[freq_idxs]
        k_instance_onefreq = k_out_with_ts.loc[freq_idxs]
        if(len(k_instance_onefreq) > 0):
            karray = k_instance_onefreq.to_numpy()
            v = np.linalg.pinv(karray/np.pi) @ y_df
            v_horizontal = np.sqrt(np.sum(np.square(v[:2])))
            azi = np.mod((180/np.pi * np.atan2(v[0], v[1])) + 22.33 , 360.0)    #22.33 is site azimuth information in degrees
            v_xarr = np.append(v_xarr, v[0])
            v_yarr = np.append(v_yarr, v[1])
            v_zarr = np.append(v_zarr, v[2])
            df_output = pd.concat([df_output if not df_output.empty else None, pd.DataFrame({
                "freq (Hz)": freq,
                "vx": v[0],
                "vy": v[1],
                "vz": v[2],
                "n_points": len(y_df)
            }, index=np.unique(df.index))])
    return df_output

def compute_xy(df, freq_list, sort_by_freq=False, points_thres=5, site='TIR'):
    karray, output_freqs, output_heights, output_dops, output_signals, output_xpow = compute_kvector(df, freq_list, sort_by_freq=sort_by_freq, points_thres=points_thres, site=site)
    kx, ky, kz = karray['kx'], karray['ky'], karray['kz']

    #These sign inversions are needed to plot the EW vs range and NS vs range plots
    kx[kz < 0] *= -1
    ky[kz < 0] *= -1
    kz[kz < 0] *= -1

    kh = np.sqrt(ky**2 + kx**2)
    zangle = np.atan2(kh, kz)
    zangleEW = np.atan2(kx, kz)
    zangleNS = np.atan2(ky, kz)
    zpos = np.cos(zangle) * output_heights
    xpos = np.tan(zangleEW) * zpos
    ypos = np.tan(zangleNS) * zpos
    azangle = np.degrees(np.atan2(xpos, ypos))
    zangle = np.degrees(zangle)
    azangle[azangle < 0] += 360
    df_output = pd.DataFrame({
        'xpos': xpos,
        'ypos': ypos,
        'zpos': zpos,
        'zenith': zangle,
        'azimuth': azangle
    })
    return df_output, output_freqs, output_heights, output_dops, output_signals, output_xpow