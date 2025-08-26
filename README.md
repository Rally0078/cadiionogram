# CADI Ionogram Plotting Software

Primarily developed to process and plot CADI raw data in various forms. Written in Python using Qt6. 

## Installation:
For using the CADI-related libraries, install the conda environment and activate it the following way:
```bash
    conda env create -f environment.yml
    conda activate cadiionogram
```

Then import the libraries in Python to use them:
```py
    #Add these lines to your Python code that requires the library
    import sys
    #The following two lines are for importing modules from a different folder
    import_path = Path("path/to/the/repo")
    sys.path.append(str(import_path))
```

For manually building the GUI executable, run the following:
```bash
    conda env create -f environment-build.yml
    conda activate cadiionogram-release
    pytest -v
    python -m PyInstaller main.spec
```
The GH Actions should do all these automatically and create a release for each push into the main branch.

## Running as a python script
To run as a python script, run the following. Run it the same way to debug the GUI.
```
    python -m src.plot.main.py
```
