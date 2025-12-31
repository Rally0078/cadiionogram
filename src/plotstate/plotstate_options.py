from src.plotstate.md4_display_iono_state import Md4DisplayIonogramState
from src.plotstate.md4_realheight_state import Md4RealheightAnalysisState
from src.plotstate.mdx_rangetimefreq_state import MdxRangeTimeFreqState
from src.plotstate.md4_autoscaling_state import Md4ScaleIonogramState
from src.plotstate.mdx_xyplot_state import MdxXYplotCanvasState
from src.plotstate.mdx_rangetimeintens_state import MdxRangeTimeIntensState

options_states_md4_dict = {
    'Scale ionogram': Md4ScaleIonogramState,
    'Display ionogram': Md4DisplayIonogramState,
    'Real height analysis': Md4RealheightAnalysisState,
    'Range Time Intensity': MdxRangeTimeIntensState,
    'EW-NS vs Range': NotImplementedError,
}
options_states_md3_dict = {
    'Range Time Frequency': MdxRangeTimeFreqState,
    'Range Time Intensity': MdxRangeTimeIntensState,
    'EW-NS timeseries': MdxXYplotCanvasState,
    'Drift velocity timeseries': NotImplementedError
}
timeseries_options = {
    'Range Time Frequency': MdxRangeTimeFreqState,
    'Range Time Intensity': MdxRangeTimeIntensState,
    'EW-NS timeseries': MdxXYplotCanvasState,
    'Drift velocity timeseries': NotImplementedError
}