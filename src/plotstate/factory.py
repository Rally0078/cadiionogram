#PlotStateFactory
#Returns an instance of a PlotState by selecting the appropriate PlotState through the input options
from src.plotstate.md4_display_iono_state import Md4DisplayIonogramState
from src.plotstate.md4_realheight_state import Md4RealheightAnalysisState
from src.plotstate.mdx_height_day_state import MdxHeightDayCanvasState
from src.plotstate.md4_autoscaling_state import Md4ScaleIonogramState
from src.plotstate.mdx_xyplot_state import MdxXYplotCanvasState
from src.plotstate.mdx_rangetimeintens_state import MdxRangeTimeIntensState

class PlotStateFactory:
    @staticmethod
    def get_state(main_widget):
        is_md3 = main_widget.md3_checkbox.isChecked()
        is_md4 = main_widget.md4_checkbox.isChecked()
        is_iono = main_widget.iono_checkbox.isChecked()
        option = main_widget.mode_dropdown.currentText()

        PlotStateFactory._reset_visibility(main_widget)

        try:
            options_states_md4_dict = {
                'Scale ionogram': Md4ScaleIonogramState,
                'Display ionogram': Md4DisplayIonogramState,
                'Real height analysis': Md4RealheightAnalysisState,
                'EW-NS vs Range': NotImplementedError,
            }
            options_states_md3_dict = {
                'Range Time Frequency': MdxHeightDayCanvasState,
                'Range Time Intensity': MdxRangeTimeIntensState,
                'EW-NS timeseries': MdxXYplotCanvasState,
                'Drift velocity timeseries': NotImplementedError
            }
            if is_md4 or is_iono:
                PlotStateFactory._set_tablewidget_buttons_visibility(main_widget, False)
                new_plotstate = options_states_md4_dict[option]
                if new_plotstate == NotImplementedError:
                    raise KeyError("Not implemented")
            elif is_md3:
                PlotStateFactory._set_tablewidget_buttons_visibility(main_widget, True)
                new_plotstate = options_states_md3_dict[option]
                if new_plotstate == NotImplementedError:
                    raise KeyError("Not implemented")
            else:
                raise KeyError
            return new_plotstate(main_widget)
        except KeyError:
            raise ValueError(f"No valid PlotState for combination: md3={is_md3}, md4={is_md4}, option={option}")
        
    @staticmethod 
    def _set_tablewidget_buttons_visibility(main_widget, state):
        """Handles buttons common for MD3"""
        main_widget.table_widget.end_timepartitions_dropdown.setVisible(state)
        main_widget.table_widget.left_button.setVisible(not state)
        main_widget.table_widget.right_button.setVisible(not state)
        main_widget.freq_selector.setVisible(state)
        main_widget.table_widget.end_timepartitions_dropdown.setVisible(state)
    
    @staticmethod
    def _reset_visibility(main_widget):
        main_widget.polan_button.setVisible(False)
        main_widget.save_scale_button.setVisible(False)
        main_widget.f_scale_box.setVisible(False)
        main_widget.e_scale_box.setVisible(False)
        main_widget.ie_scale_box.setVisible(False)
        main_widget.clear_scale_button.setVisible(False)
        main_widget.table_widget.end_timepartitions_dropdown.setVisible(False)
        main_widget.table_widget.left_button.setVisible(True)
        main_widget.table_widget.right_button.setVisible(True)
        main_widget.freq_selector.setVisible(False)