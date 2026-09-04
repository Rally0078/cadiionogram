import polars as pl
from typing import Tuple
import numpy as np
def compute_xpha_only(df: pl.DataFrame, freq_list, site: str = 'TIR') -> Tuple[pl.DataFrame, pl.DataFrame]:
    _, xpow, xpha = compute_xpha_full(df, freq_list, site=site)
    return xpow, xpha

def compute_xpha_full(df: pl.DataFrame, freq_list, site: str = 'TIR'):
    # 1. Filter out rows where any sensor has both real and imag as zero
    conditions = [
        (pl.col(f"sensor{idx} real") == 0) & (pl.col(f"sensor{idx} imag") == 0)
        for idx in range(1, 5)
    ]
    # Combine conditions with OR, then negate to keep "good" rows
    any_zero = conditions[0]
    for cond in conditions[1:]:
        any_zero = any_zero | cond
    
    filtered_df = df.filter(~any_zero)
    
    # 2. Compute cross amplitudes and phases
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
    
    # Pairwise definitions: (ant0_re, ant0_im, ant1_re, ant1_im)
    pairs = {
        "x1": ("sensor1 real", "sensor1 imag", "sensor2 real", "sensor2 imag", PH2_corr),
        "x2": ("sensor3 real", "sensor3 imag", "sensor4 real", "sensor4 imag", PH4_corr)
    }
    
    xpow_exprs = {}
    xpha_exprs = {}
    
    for name, (a0_re, a0_im, a1_re, a1_im, corr) in pairs.items():
    # Cast to float64 first to match np.float64 precision behavior
        a0_re_f = pl.col(a0_re).cast(pl.Float64)
        a0_im_f = pl.col(a0_im).cast(pl.Float64)
        a1_re_f = pl.col(a1_re).cast(pl.Float64)
        a1_im_f = pl.col(a1_im).cast(pl.Float64)

        s_real = -(a0_re_f * a1_re_f + a0_im_f * a1_im_f)
        s_imag = a0_re_f * a1_im_f - a0_im_f * a1_re_f

        xpow_exprs[name] = (s_real.pow(2) + s_imag.pow(2)).cast(pl.Float32)

        angle_expr = pl.arctan2(s_imag, s_real) + corr

        angle_expr = (
            pl.when(angle_expr > np.pi)
            .then(angle_expr - 2 * np.pi)
            .when(angle_expr < -np.pi)
            .then(angle_expr + 2 * np.pi)
            .otherwise(angle_expr)
        )
        xpha_exprs[name] = angle_expr

    # Evaluate the cross power and phase dataframes
    xpow = filtered_df.select([expr.alias(name) for name, expr in xpow_exprs.items()])
    xpha = filtered_df.select([expr.alias(name) for name, expr in xpha_exprs.items()])
    
    # 3. Reject data with cross phases outside limits
    # Digitize the frequency column using NumPy, then map to the calculated limits
# Match the exact array positioning behavior from Pandas
    freq_arr = filtered_df["freq (Hz)"].to_numpy()
    freq_idxs = np.digitize(freq_arr, freq_list) - 1

    # Generate the bounds Series matching the filtered dataframe shape explicitly
    phase_limit_ew = pl.Series((2 * np.pi / 2.998e8) * np.array(freq_list, dtype=np.float64)[freq_idxs] * site_sep_ew, dtype=pl.Float64)
    phase_limit_ns = pl.Series((2 * np.pi / 2.998e8) * np.array(freq_list, dtype=np.float64)[freq_idxs] * site_sep_ns, dtype=pl.Float64)
    # Build final mask
    final_good_mask = (
        (xpha["x1"].abs() <= phase_limit_ew) & 
        (xpha["x2"].abs() <= phase_limit_ns)
    )
    
    
    # Filter outputs
    output_df = filtered_df.filter(final_good_mask)
    output_xpow = xpow.filter(final_good_mask)
    output_xpha = xpha.filter(final_good_mask)
    
    return output_df, output_xpow, output_xpha

def compute_kvector(df: pl.DataFrame, freq_list, sort_by_freq=False, points_thres=5, site: str = 'TIR'):
    # Polars dataframes don't have a traditional index; assuming an explicit timestamp column exists
    # If your timestamp is a column named "datetime", we verify uniqueness:
    if "datetime" in df.columns and df["datetime"].n_unique() > 1:
        raise ValueError("Only a single timestamp can be used for the calculation of k vector")
        
    # Call the Polars-optimized xpha computation
    df_filtered, xpow, xpha = compute_xpha_full(df, freq_list, site=site)
    
    if df_filtered.is_empty():
        # Handle empty dataframe edge case safely
        empty_k = pl.DataFrame(schema={"kx": pl.Float64, "ky": pl.Float64, "kz": pl.Float64})
        return empty_k, pl.Series(), pl.Series(), pl.Series(), pl.DataFrame(), pl.DataFrame()

    signal_col_names = [f"sensor{i//2 + 1} {'real' if i%2 == 0 else 'imag'}" for i in range(8)]
    k_mag = 2 * np.pi / (2.998e8) * np.array(freq_list)
    
    from src.utils.siteinfo import SiteInfo
    site_info = SiteInfo.get_from_file(site)
    if site_info is not None:
        site_sep_ew = site_info.site_separation[0]
        site_sep_ns = site_info.site_separation[1]
    else:
        site_sep_ew = 30.1
        site_sep_ns = 30.1
    
    # Map frequency to its respective index and k_mag constant beforehand using horizontal/mapping operations
    # Create an expression mapping table for k_mag and new_kd values based on freq_list
    freq_to_idx_map = {f: idx for idx, f in enumerate(freq_list)}
    freq_to_kmag_map = {f: k_mag[idx] for idx, f in enumerate(freq_list)}
    freq_to_kd_ew_map = {f: k_mag[idx] * site_sep_ew for idx, f in enumerate(freq_list)}
    freq_to_kd_ns_map = {f: k_mag[idx] * site_sep_ns for idx, f in enumerate(freq_list)}

    # Inject calculations as columns horizontally
    # xpha data is horizontally joined or combined directly for calculations
    working_df = pl.DataFrame({
        "datetime": df_filtered["datetime"],
        "freq": df_filtered["freq (Hz)"],
        "height": df_filtered["height (km)"],
        "dopplershift": df_filtered["dopplershift"],
        "x1": xpha["x1"],
        "x2": xpha["x2"],
    }).with_columns([
        pl.col("freq").replace(freq_to_kmag_map).alias("k_mag_val"),
        pl.col("freq").replace(freq_to_kd_ew_map).alias("kd_ew_val"),
        pl.col("freq").replace(freq_to_kd_ns_map).alias("kd_ns_val"),
    ])

    # Core mathematical mapping using Polars expressions
    # temp_xy = phase / kd
    # new_xy = temp_xy / sqrt(1 - temp_xy^2)
    working_df = working_df.with_columns([
        (pl.col("x1") / pl.col("kd_ew_val")).alias("temp_x1"),
        (pl.col("x2") / pl.col("kd_ns_val")).alias("temp_x2"),
    ]).with_columns([
        (pl.col("temp_x1") / (1.0 - pl.col("temp_x1").pow(2)).sqrt()).alias("new_x1"),
        (pl.col("temp_x2") / (1.0 - pl.col("temp_x2").pow(2)).sqrt()).alias("new_x2"),
    ])

    # kz = -k_mag / sqrt(1 + new_x1^2 + new_x2^2)
    # kx = kz * new_x1, ky = kz * new_x2
    working_df = working_df.with_columns([
        (-pl.col("k_mag_val") / (1.0 + pl.col("new_x1").pow(2) + pl.col("new_x2").pow(2)).sqrt()).alias("kz")
    ]).with_columns([
        (pl.col("kz") * pl.col("new_x1")).alias("kx"),
        (pl.col("kz") * pl.col("new_x2")).alias("ky"),
    ])
    xpow_renamed = xpow.rename({"x1": "x1_pow", "x2": "x2_pow"})
    # Bring back signal selection columns and xpow values alongside calculated outputs
    combined_output = pl.concat([
        working_df, 
        df_filtered.select(signal_col_names),
        xpow_renamed
    ], how="horizontal")

    if sort_by_freq:
        # Filter points based on the frequency threshold constraint using window functions
        combined_output = (
            combined_output
            .with_columns(pl.len().over("freq").alias("n_points_per_freq"))
            .filter(pl.col("n_points_per_freq") >= points_thres)
            .sort("freq")
        )

    # Extract required modular chunks for the multi-output return structure
    k_out = combined_output.select(["datetime", "kx", "ky", "kz"])
    output_freqs = combined_output["freq"]
    output_heights = combined_output["height"]
    output_dops = combined_output["dopplershift"]
    output_signals = combined_output.select(signal_col_names)
    output_xpow = combined_output.select(["x1_pow", "x2_pow"])

    return k_out, output_freqs, output_heights, output_dops, output_signals, output_xpow

def compute_vel(df: pl.DataFrame, freq_list, points_thres=5, site: str = 'TIR'):
    # Call the Polars implementation of compute_kvector
    k_out, output_freqs, _, output_dops, _, _ = compute_kvector(
        df, freq_list, sort_by_freq=True, points_thres=points_thres, site=site
    )
    
    if k_out.is_empty():
        return pl.DataFrame(schema={"freq (Hz)": pl.Float64, "vx": pl.Float64, "vy": pl.Float64, "vz": pl.Float64, "n_points": pl.Int64})

    # Pack the pieces together to perform a grouped pseudo-inverse calculation
    calc_df = pl.DataFrame({
        "freq": output_freqs,
        "kx": k_out["kx"],
        "ky": k_out["ky"],
        "kz": k_out["kz"],
        "dop": output_dops
    })

    # Schema for the group-by aggregation operation
    output_schema = {
        "freq (Hz)": pl.Float64,
        "vx": pl.Float64,
        "vy": pl.Float64,
        "vz": pl.Float64,
        "n_points": pl.Int64
    }

    # Custom function applied over each frequency group
    def group_pinv(group: pl.DataFrame) -> pl.DataFrame:
        freq_val = group["freq"][0]
        y = group["dop"].to_numpy()
        karray = group.select(["kx", "ky", "kz"]).to_numpy()
        
        # v = pinv(K / pi) @ y
        v = np.linalg.pinv(karray / np.pi) @ y
        
        return pl.DataFrame({
            "freq (Hz)": [freq_val],
            "vx": [v[0]],
            "vy": [v[1]],
            "vz": [v[2]],
            "n_points": [len(y)]
        }, schema=output_schema)

    df_output = calc_df.group_by("freq").map_groups(group_pinv).sort("freq (Hz)")
    return df_output


def compute_xy(df: pl.DataFrame, freq_list, sort_by_freq=False, points_thres=5, site: str = 'TIR'):
    # Call the Polars implementation of compute_kvector
    karray, output_freqs, output_heights, output_dops, output_signals, output_xpow = compute_kvector(
        df, freq_list, sort_by_freq=sort_by_freq, points_thres=points_thres, site=site
    )
    
    # Process geometry changes natively in Polars via expressions
    # Notice the sign inversion tracking logic based on the sign of kz
    if (len(karray) == 0) or ("datetime" not in karray.columns):
        return pl.DataFrame({
            "datetime": [], "xpos":[], "ypos":[], "zpos":[], "zenith":[], "azimuth":[]
        }), output_freqs, output_heights, output_dops, output_signals, output_xpow
    geo_df = karray.with_columns([
        pl.when(pl.col("kz") < 0).then(-pl.col("kx")).otherwise(pl.col("kx")).alias("kx_corr"),
        pl.when(pl.col("kz") < 0).then(-pl.col("ky")).otherwise(pl.col("ky")).alias("ky_corr"),
        pl.when(pl.col("kz") < 0).then(-pl.col("kz")).otherwise(pl.col("kz")).alias("kz_corr"),
        pl.Series("height", output_heights)
    ])
    
    # Apply coordinate and angle transformations element-wise
    geo_df = geo_df.with_columns([
        ((pl.col("ky_corr").pow(2) + pl.col("kx_corr").pow(2)).sqrt()).alias("kh"),
        pl.arctan2(pl.col("kx_corr"), pl.col("kz_corr")).alias("zangleEW"),
        pl.arctan2(pl.col("ky_corr"), pl.col("kz_corr")).alias("zangleNS"),
    ]).with_columns([
        pl.arctan2(pl.col("kh"), pl.col("kz_corr")).alias("zangle_rad"),
        # zpos = cos(zangle) * height
        (pl.arctan2(pl.col("kh"), pl.col("kz_corr")).cos() * pl.col("height")).alias("zpos")
    ]).with_columns([
        # xpos = tan(zangleEW) * zpos
        (pl.col("zangleEW").tan() * pl.col("zpos")).alias("xpos"),
        # ypos = tan(zangleNS) * zpos
        (pl.col("zangleNS").tan() * pl.col("zpos")).alias("ypos"),
        # zenith angle in degrees
        (pl.col("zangle_rad") * (180 / np.pi)).alias("zenith")
    ]).with_columns([
        # azangle = degrees(arctan2(xpos, ypos))
        (pl.arctan2(pl.col("xpos"), pl.col("ypos")) * (180 / np.pi)).alias("azimuth")
    ]).with_columns([
        # Handle wrapping for azimuth angles below 0
        pl.when(pl.col("azimuth") < 0).then(pl.col("azimuth") + 360).otherwise(pl.col("azimuth"))
    ])
    
    df_output = geo_df.select(["datetime", "xpos", "ypos", "zpos", "zenith", "azimuth"])
    
    return df_output, output_freqs, output_heights, output_dops, output_signals, output_xpow