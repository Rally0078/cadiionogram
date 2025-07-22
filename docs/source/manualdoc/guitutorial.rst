GUI modification tutorial
=========================

.. toctree::
    :hidden:
    :maxdepth: 2

    guitutorial

.. contents::
    :local:
    :depth: 1
    

Add and modify features in the GUI
----------------------------------

When the Ionogram GUI is opened, `src.plot.main` is run, and an instance of `src.ui.mainwidget.MainWidget` is created. 
The `src.plot.main` has the main application class that handles the reading of the config file and initializes the instance of `src.ui.mainwidget.MainWidget`.
This `MainWidget` instance handles all the GUI elements such as buttons, lists, as well as the behaviour when clicking/using these elements.

To add new buttons/lists/etc., to the GUI, it must be added to the `src.ui.mainwidget.MainWidget` class with the appropriate callbacks for its functionality.

The plotting is handled by a separate canvas module located in the package `src.plot`.
Whenever a particular combination of options is chosen (Example: md4 + Display Ionogram), the factory `src.plotstate.factory.PlotStateFactory` handles the 
creation of a canvas that matches the chosen options.

To add a new type of plot to the GUI, the following must be done:

1. Create a new canvas subclassing from `matplotlib.backends.backend_qtagg.FigureCanvasQTAgg` in the package `src.plot`.
2. Add the appropriate conditons to the factory and return the newly created canvas from the `src.plotstate.factory.PlotStateFactory`.
3. (Optional) Handle any file I/O through the `MainWidget`.