def get_md4_display_iono_state():
    from src.plotstate.md4_display_iono_state import Md4DisplayIonogramState
    return Md4DisplayIonogramState

def get_md4_realheight_state():
    from src.plotstate.md4_realheight_state import Md4RealheightAnalysisState
    return Md4RealheightAnalysisState

def get_mdx_rangetimefreq_state():
    from src.plotstate.mdx_rangetimefreq_state import MdxRangeTimeFreqState
    return MdxRangeTimeFreqState

def get_md4_manualscale_state():
    from src.plotstate.md4_manualscale_state import Md4ScaleIonogramState
    return Md4ScaleIonogramState

def get_mdx_xyplot_state():
    from src.plotstate.mdx_xyplot_state import MdxXYplotCanvasState
    return MdxXYplotCanvasState

def get_mdx_rangetimeintens_state():
    from src.plotstate.mdx_rangetimeintens_state import MdxRangeTimeIntensState
    return MdxRangeTimeIntensState

def get_mdx_skymap_state():
    from src.plotstate.mdx_skymap_state import MdxSkymapState
    return MdxSkymapState

def get_md4_display_alliono_state():
    from src.plotstate.md4_display_alliono_state import Md4DisplayAllIonogramState
    return Md4DisplayAllIonogramState

def get_md4_autoscale_state():
    from src.plotstate.md4_autoscale_state import Md4AutoScaleIonogramState
    return Md4AutoScaleIonogramState

def get_md4_ewns_range_state():
    from src.plotstate.md4_ewns_range_state import Md4EwnsRangeState
    return Md4EwnsRangeState

options_states_md4_dict = {
    'Scale ionogram': get_md4_manualscale_state,
    'Autoscale Ionogram': get_md4_autoscale_state,
    'All Receiver Ionogram': get_md4_display_alliono_state,
    'Display ionogram': get_md4_display_iono_state,
    'Real height analysis': get_md4_realheight_state,
    'Range Time Intensity': get_mdx_rangetimeintens_state,
    'Skymap': get_mdx_skymap_state,
    'EW-NS vs Range': get_md4_ewns_range_state,
}

options_states_md3_dict = {
    'Range Time Frequency': get_mdx_rangetimefreq_state,
    'Range Time Intensity': get_mdx_rangetimeintens_state,
    'EW-NS timeseries': get_mdx_xyplot_state,
    'Skymap': get_mdx_skymap_state,
    'Drift velocity timeseries': NotImplementedError
}

timeseries_options = [
    'Range Time Frequency',
    'Range Time Intensity',
    'EW-NS timeseries',
    'Drift velocity timeseries'
]

plot_fig_save_names = {
    'Range Time Frequency': 'RTI',
    'Range Time Intensity': 'RTI',
    'EW-NS timeseries':'EWNSPosTimeSeries',
    'Drift velocity timeseries':'DriftVelTimeSeries',
    'Scale ionogram': 'ScaledIono',
    'Autoscale Ionogram': 'Autoscale',
    'Display ionogram': 'Iono',
    'All Receiver Ionogram': "AllIono",
    'Real height analysis': 'RealHeight',
    'Skymap': 'Skymap',
    'EW-NS vs Range': 'EWNSPosRange',
}
