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
```

Running as a python script
```
    python -m src.ui.main.py
```
