#PlotStateFactory
#Returns an instance of a PlotState by selecting the appropriate PlotState through the input options
from src.plotstate.md4_display_iono_state import Md4DisplayIonogramState

class PlotStateFactory:
    @staticmethod
    def get_state(main_widget):
        is_md3 = main_widget.md3_checkbox.isChecked()
        is_md4 = main_widget.md4_checkbox.isChecked()
        option = main_widget.dropbox.currentText()
        if is_md4 and option == 'Display ionogram':
            return Md4DisplayIonogramState(main_widget)
        else:
            raise ValueError(f"No valid PlotState for combination: md3={is_md3}, md4={is_md4}, option={option}")