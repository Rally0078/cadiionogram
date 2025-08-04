#PlotStateFactory
#Returns an instance of a PlotState by selecting the appropriate PlotState through the input options
from src.plotstate.md4_display_iono_state import Md4DisplayIonogramState
from src.plotstate.md4_realheight_state import Md4RealheightAnalysisState
from src.plotstate.mdx_height_day_state import MdxHeightDayCanvasState
from src.plotstate.md4_autoscaling_state import Md4ScaleIonogramState
from src.plotstate.mdx_xyplot_state import MdxXYplotCanvasState

class PlotStateFactory:
    @staticmethod
    def get_state(main_widget):
        is_md3 = main_widget.md3_checkbox.isChecked()
        is_md4 = main_widget.md4_checkbox.isChecked()
        is_iono = main_widget.iono_checkbox.isChecked()
        option = main_widget.mode_dropdown.currentText()
        main_widget.polan_button.setVisible(False)
        main_widget.save_scale_button.setVisible(False)
        main_widget.table_widget.end_timepartitions_dropdown.setVisible(False)

        #Handle buttons common for different canvases
        if option in ['Display ionogram', 'Real height analysis', 'Scale ionogram', 'EW NS timeseries plot']:
            PlotStateFactory._set_tablewidget_buttons_visibility(main_widget,True)
        elif option in ['Range vs Time (Freq colored)']:
            PlotStateFactory._set_tablewidget_buttons_visibility(main_widget,False)
        
        #Handle buttons and canvases for each state
        if (is_md4 or is_iono) and (option == 'Scale ionogram'):
            main_widget.save_scale_button.setVisible(True)
            return Md4ScaleIonogramState(main_widget)
        if (is_md4 or is_iono) and option == 'Display ionogram':
            return Md4DisplayIonogramState(main_widget)
        elif (is_md4 or is_iono) and option == 'Real height analysis':
            main_widget.polan_button.setVisible(True)
            return Md4RealheightAnalysisState(main_widget)
        elif option == 'Range vs Time (Freq colored)':
            return MdxHeightDayCanvasState(main_widget)
        elif is_md3 and option == 'EW NS timeseries plot':
            main_widget.table_widget.end_timepartitions_dropdown.setVisible(True)
            return MdxXYplotCanvasState(main_widget)
        else:
            raise ValueError(f"No valid PlotState for combination: md3={is_md3}, md4={is_md4}, option={option}")
        
    @staticmethod 
    def _set_tablewidget_buttons_visibility(main_widget, state):
        main_widget.table_widget.left_button.setVisible(state)
        main_widget.table_widget.right_button.setVisible(state)
        main_widget.table_widget.timepartitions_dropdown.setVisible(state)
        main_widget.table_widget.pointers_label.setVisible(state)
        if state is False:
            main_widget.table_widget.end_timepartitions_dropdown.setVisible(state)