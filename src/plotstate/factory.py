#PlotStateFactory
#Returns an instance of a PlotState by selecting the appropriate PlotState through the input options
from src.plotstate.plotstate_options import options_states_md3_dict, options_states_md4_dict, timeseries_options

class PlotStateFactory:
    @staticmethod
    def get_state(main_widget):
        is_md3 = main_widget.md3_checkbox.isChecked()
        is_md4 = main_widget.md4_checkbox.isChecked()
        is_iono = main_widget.iono_checkbox.isChecked()
        option = main_widget.mode_dropdown.currentText()
        is_timeseries = PlotStateFactory._is_timeseries(option)
        PlotStateFactory._reset_visibility(main_widget)
        try:
            if is_md4 or is_iono:   # Ionogram mode plots
                PlotStateFactory._set_tablewidget_buttons_visibility(main_widget, is_timeseries)
                new_plotstate = options_states_md4_dict[option]
                if new_plotstate == NotImplementedError:
                    raise KeyError("Not implemented")
            elif is_md3:    # Drift mode plots
                PlotStateFactory._set_tablewidget_buttons_visibility(main_widget, is_timeseries, is_md3)
                new_plotstate = options_states_md3_dict[option]
                if new_plotstate == NotImplementedError:
                    raise KeyError("Not implemented")
            else:
                raise KeyError
            return new_plotstate(main_widget)
        except KeyError:
            raise ValueError(f"No valid PlotState for combination: md3={is_md3}, md4={is_md4}, option={option}")
        
    @staticmethod
    def _is_timeseries(option):
        if option in timeseries_options:
            return True
        return False
    
    @staticmethod 
    def _set_tablewidget_buttons_visibility(main_widget, state, is_md3=False):
        """Handles buttons common for MD3"""
        main_widget.table_widget.end_timepartitions_dropdown.setVisible(state)
        main_widget.table_widget.left_button.setVisible(not state)
        main_widget.table_widget.right_button.setVisible(not state)
        main_widget.freq_selector.setVisible(state and is_md3)
        main_widget.table_widget.end_timepartitions_dropdown.setVisible(state)
    
    @staticmethod
    def _reset_visibility(main_widget):
        """Reset back to default MD4 view"""
        main_widget.polan_button.setVisible(False)
        main_widget.reset_zoom_button.setVisible(False)
        main_widget.save_scale_button.setVisible(False)
        main_widget.f_scale_box.setVisible(False)
        main_widget.e_scale_box.setVisible(False)
        main_widget.ie_scale_box.setVisible(False)
        main_widget.clear_scale_button.setVisible(False)
        main_widget.es_scaling_label.setVisible(False)
        main_widget.es_scaling_dropdown.setVisible(False)
        main_widget.table_widget.end_timepartitions_dropdown.setVisible(False)
        main_widget.table_widget.left_button.setVisible(True)
        main_widget.table_widget.right_button.setVisible(True)
        main_widget.freq_selector.setVisible(False)