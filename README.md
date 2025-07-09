# CADI Ionogram Plotting Software

Written in Python using Qt6. 

Run tests before using
```
    pytest -v
```

Installation:
```
    conda env create -f environment.yml
    conda activate cadiionogram
    python -m PyInstaller ./src/ui/main.py -D --distpath ./cadireader --exclude PyQt5 --exclude tkinter --exclude  matplotlib --exclude PyQt6 --exclude scipy --exclude pillow --exclude IPython --exclude PIL --exclude numba
    python -m PyInstaller ./src/plot/main.py -D --distpath . --exclude PyQt5 --exclude tkinter --exclude PyQt6 --exclude torch --exclude pillow --exclude IPython --exclude numba --exclude jupyter_client --exclude jupyter_code --exclude jupyterlab_widgets
```

Running as a python script
```
    python -m src.ui.main.py
    python -m src.plot.main.py
```
